import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.core.ikHandle as ikHandleLimb


class SingleChainIk(ikHandleLimb.IkHandle):
    STRETCH_ATTR = 'stretch'
    STRETCH_CLAMP_MIN_ATTR = 'stretchClampMin'
    STRETCH_MIN_ATTR = 'stretchMin'
    STRETCH_CLAMP_MAX_ATTR = 'stretchClampMax'
    STRETCH_MAX_ATTR = 'stretchMax'

    def __init__(self, **kwargs):
        super(SingleChainIk, self).__init__(**kwargs)
        self._stretch = None
        self._stretch_clamp_min = None
        self._stretch_min = None
        self._stretch_clamp_max = None
        self._stretch_max = None

        self._stretch_attr = None
        self._stretch_clamp_min_attr = None
        self._stretch_min_attr = None
        self._stretch_clamp_max_attr = None
        self._stretch_max_attr = None

    def get_build_kwargs(self, **kwargs):
        super(SingleChainIk, self).get_build_kwargs(**kwargs)
        self._additional_description = kwargs.get('additional_description', ['scIk'])
        self._stretch = kwargs.get('stretch', False)
        self._stretch_clamp_min = kwargs.get('stretch_clamp_min', 1)
        self._stretch_min = kwargs.get('stretch_min', 1)
        self._stretch_clamp_max = kwargs.get('stretch_clamp_max', 0)
        self._stretch_max = kwargs.get('stretch_max', 2)

    def add_input_attributes(self):
        super(SingleChainIk, self).add_input_attributes()
        if self._stretch:
            self._stretch_attr = attributeUtils.add(self._input_node, self.STRETCH_ATTR, attribute_type='float',
                                                    value_range=[0, 1], default_value=0, keyable=True)[0]

            self._stretch_min_attr = attributeUtils.add(self._input_node, self.STRETCH_MIN_ATTR,
                                                        attribute_type='float', value_range=[0, 1],
                                                        default_value=self._stretch_min, keyable=True)[0]
            self._stretch_max_attr = attributeUtils.add(self._input_node, self.STRETCH_MAX_ATTR,
                                                        attribute_type='float', value_range=[1, None],
                                                        default_value=self._stretch_max, keyable=True)[0]

            clamp_attrs = attributeUtils.add(self._input_node,
                                             [self.STRETCH_CLAMP_MIN_ATTR, self.STRETCH_CLAMP_MAX_ATTR],
                                             attribute_type='float', value_range=[0, 1],
                                             default_value=[self._stretch_clamp_min, self._stretch_clamp_max],
                                             keyable=True)
            self._stretch_clamp_min_attr, self._stretch_clamp_max_attr = clamp_attrs

    def create_controls(self):
        super(SingleChainIk, self).create_controls()
        for jnt, description, lock_attrs in zip([self._guide_joints[0], self._guide_joints[-1]], ['root', 'target'],
                                                [attributeUtils.ROTATE + attributeUtils.SCALE, attributeUtils.SCALE]):
            # decompose name
            name_info = namingUtils.decompose(jnt)
            ctrl = controlUtils.create(name_info['description'], side=name_info['side'], index=name_info['index'],
                                       limb_index=name_info['limb_index'], additional_description=description, sub=True,
                                       parent=self._controls_group, position=jnt, rotate_order=0, manip_orient=None,
                                       lock_hide=lock_attrs)
            self._controls.append(ctrl)

        # add stretch attr
        if self._stretch:
            attributeUtils.add(self._controls[-1], self.STRETCH_ATTR, attribute_type='float', value_range=[0, 1],
                               default_value=0, keyable=True)
            attributeUtils.add(self._controls[-1], self.STRETCH_MIN_ATTR, attribute_type='float', value_range=[0, 1],
                               default_value=self._stretch_min, keyable=True)
            attributeUtils.add(self._controls[-1], self.STRETCH_MAX_ATTR, attribute_type='float', value_range=[1, None],
                               default_value=self._stretch_max, keyable=True)
            attributeUtils.add(self._input_node,
                               [self.STRETCH_CLAMP_MIN_ATTR, self.STRETCH_CLAMP_MAX_ATTR],
                               attribute_type='float', value_range=[0, 1],
                               default_value=[self._stretch_clamp_min, self._stretch_clamp_max], keyable=True)

            attributeUtils.connect([self.STRETCH_ATTR, self.STRETCH_MIN_ATTR, self.STRETCH_MAX_ATTR,
                                    self.STRETCH_CLAMP_MIN_ATTR, self.STRETCH_CLAMP_MAX_ATTR],
                                   [self.STRETCH_ATTR, self.STRETCH_MIN_ATTR, self.STRETCH_MAX_ATTR,
                                    self.STRETCH_CLAMP_MIN_ATTR, self.STRETCH_CLAMP_MAX_ATTR],
                                   driver=self._controls[-1], driven=self._input_node)

    def create_setup(self):
        super(SingleChainIk, self).create_setup()
        # connect root control with first joint's translation
        constraintUtils.position_constraint('{0}.{1}'.format(self._controls[0], controlUtils.OUT_MATRIX_ATTR),
                                            self._setup_nodes[0], maintain_offset=False, skip=attributeUtils.ROTATE)

        # connect ik group with controller
        constraintUtils.position_constraint('{0}.{1}'.format(self._controls[-1], controlUtils.OUT_MATRIX_ATTR),
                                            self._ik_groups[0], maintain_offset=True)

        if self._stretch:
            self.add_stretch()

    def add_stretch(self):
        # get root and target position, and calculate the distance
        decompose_nodes = []
        for ctrl in [self._controls[0], self._controls[-1]]:
            decompose = nodeUtils.create('decomposeMatrix',
                                         namingUtils.update(ctrl, type='decomposeMatrix',
                                                            additional_description='stretchPos'))
            cmds.connectAttr('{0}.{1}'.format(ctrl, controlUtils.OUT_MATRIX_ATTR), decompose + '.inputMatrix')
            decompose_nodes.append(decompose)

        dis_stretch = nodeUtils.create('distanceBetween',
                                       namingUtils.update(self._controls[-1], type='distanceBetween',
                                                          additional_description='stretch'))
        cmds.connectAttr(decompose_nodes[0] + '.outputTranslate', dis_stretch + '.point1')
        cmds.connectAttr(decompose_nodes[-1] + '.outputTranslate', dis_stretch + '.point2')

        # get distance
        distance = cmds.getAttr(dis_stretch + '.distance')

        # divide to get stretch weight
        stretch_weight_attr = nodeUtils.arithmetic.equation('{0}.distance/{1}'.format(dis_stretch, distance),
                                                            namingUtils.update(self._controls[-1],
                                                                               additional_description='stretchWeight'))

        # use blender node to blend min and max values
        name = namingUtils.update(self._controls[-1], type='blendColors', additional_description='stretchMaxClamp')
        blend_max = nodeUtils.utility.blend_colors(self._stretch_clamp_max_attr, self._stretch_max_attr,
                                                   stretch_weight_attr, name=name) + 'R'

        name = namingUtils.update(self._controls[-1], type='blendColors', additional_description='stretchMinClamp')
        blend_min = nodeUtils.utility.blend_colors(self._stretch_clamp_min_attr, self._stretch_min_attr,
                                                   stretch_weight_attr, name=name) + 'R'

        # use remap to clamp the value
        remap_stretch = nodeUtils.utility.remap_value(stretch_weight_attr,
                                                      [self._stretch_min_attr, self._stretch_max_attr],
                                                      [blend_min, blend_max],
                                                      name=namingUtils.update(self._controls[-1], type='remapValue',
                                                                              additional_description='stretchWeight'))

        # blend with original weight value to turn it on and off
        name = namingUtils.update(self._controls[-1], type='blendColors', additional_description='stretchWeight')
        blend_stretch = nodeUtils.utility.blend_colors(self._stretch_attr, remap_stretch, 1, name=name) + 'R'
        # multiply translate X to do stretch
        tx_val = cmds.getAttr(self._setup_nodes[-1] + '.translateX')
        nodeUtils.arithmetic.equation('{0}*{1}'.format(tx_val, blend_stretch),
                                      namingUtils.update(self._controls[-1], additional_description='stretch'),
                                      connect_attr=self._setup_nodes[-1] + '.translateX')
