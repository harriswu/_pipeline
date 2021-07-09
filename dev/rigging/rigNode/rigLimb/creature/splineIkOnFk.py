import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.base.splineIk as splineIk


class SplineIkOnFk(splineIk.SplineIk):
    FK_CONTROLS_ATTR = 'fkControls'

    def __init__(self, **kwargs):
        super(SplineIkOnFk, self).__init__(**kwargs)
        self._guide_fk = None
        self._fk_lock_hide = None

        self._fk_limb = None
        self._fk_controls = []

    def get_build_kwargs(self, **kwargs):
        super(SplineIkOnFk, self).get_build_kwargs(**kwargs)
        self._guide_fk = kwargs.get('guide_fk', [])
        self._fk_lock_hide = kwargs.get('fk_lock_hide', attributeUtils.TRANSLATE + attributeUtils.SCALE)

    def flip_build_kwargs(self):
        super(SplineIkOnFk, self).flip_build_kwargs()
        self._guide_fk = namingUtils.flip_names(self._guide_fk)

    def create_controls(self):
        super(SplineIkOnFk, self).create_controls()
        build_kwargs = {'additional_description': 'fk',
                        'parent_node': self._sub_nodes_group,
                        'guide_joints': self._guide_fk,
                        'lock_hide': self._fk_lock_hide,
                        'control_end_joint': True,
                        'create_joint': False}

        connect_kwargs = {'input_matrix': self._input_matrix_attr,
                          'offset_matrix': self._offset_matrix_attr}

        self._fk_limb = self.create_rig_node('dev.rigging.rigNode.rigLimb.base.fkChain', name_template=self._node,
                                             build=True, build_kwargs=build_kwargs, connect=True,
                                             connect_kwargs=connect_kwargs, flip=self._flip)

        attributeUtils.connect([self._controls_vis_output_attr, self._joints_vis_output_attr,
                                self._nodes_vis_output_attr],
                               [self._fk_limb.controls_vis_offset_attr, self._fk_limb.joints_vis_offset_attr,
                                self._fk_limb.nodes_vis_offset_attr])

        self._fk_controls = self._fk_limb.controls

        # connect vis attrs to limb group
        attributeUtils.connect(self._controls_vis_attr, self._fk_limb.controls_vis_offset_attr)

        # connect with ik tip controller
        driven = controlUtils.get_hierarchy_node(self._controls[-1], 'driven')
        zero = controlUtils.get_hierarchy_node(self._controls[-1], 'zero')
        zero_ivs_matrix = cmds.getAttr('{0}.{1}'.format(zero, attributeUtils.INVERSE_MATRIX))
        constraintUtils.position_constraint('{0}.{1}'.format(self._fk_limb.controls[-1],
                                                             controlUtils.HIERARCHY_MATRIX_ATTR),
                                            driven, parent_inverse_matrices=zero_ivs_matrix, maintain_offset=True)

    def add_output_attributes(self):
        super(SplineIkOnFk, self).add_output_attributes()
        fk_attr = attributeUtils.add(self._output_node, self.FK_CONTROLS_ATTR, attribute_type='message', multi=True)[0]
        attributeUtils.connect_nodes_to_multi_attr(self._fk_controls, fk_attr, driver_attr=attributeUtils.MESSAGE)

    def get_output_info(self):
        super(SplineIkOnFk, self).get_output_info()
        self._fk_controls = self.get_multi_attr_value(self.FK_CONTROLS_ATTR, node=self._output_node)

    def tag_controllers(self):
        super(SplineIkOnFk, self).tag_controllers()
        tag_parent = self._tag_parent
        for ctrl in self._fk_controls:
            controlUtils.set_tag_parent(ctrl, tag_parent)
            tag_parent = ctrl
