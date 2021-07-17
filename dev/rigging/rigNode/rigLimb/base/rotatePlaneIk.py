import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.mathUtils as mathUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.core.ikHandle as ikHandleLimb


class RotatePlaneIk(ikHandleLimb.IkHandle):
    INPUT_IK_MATRIX_ATTR = 'inputIkMatrix'
    TWIST_ATTR = 'twist'
    STRETCH_ATTR = 'stretch'
    PV_LOCK_ATTR = 'pvLock'
    SOFT_IK_ATTR = 'softIk'

    def __init__(self, **kwargs):
        super(RotatePlaneIk, self).__init__(**kwargs)
        self._guide_controls = None
        self._control_manip_orient = None
        self._stretch = None
        self._pv_lock = None
        self._soft_ik = None

        self._stretch_attr = None
        self._pv_lock_attr = None
        self._soft_ik_attr = None

        self._section_length = []
        self._chain_length = 0
        self._ik_length = 0
        self._stretch_ratio_attr = None
        self._decompose_root_ctrl = None
        self._decompose_pv_ctrl = None
        self._decompose_ik_ctrl = None

        # connection
        self._input_ik_matrix = None

        self._ik_type = 'ikRPsolver'

        self._input_ik_matrix_attr = None

    @property
    def input_ik_matrix(self):
        return cmds.getAttr(self._input_ik_matrix_attr)

    @property
    def input_ik_matrix_attr(self):
        return self._input_ik_matrix_attr

    def get_build_kwargs(self, **kwargs):
        super(RotatePlaneIk, self).get_build_kwargs(**kwargs)
        self._guide_controls = kwargs.get('guide_controls', [])
        self._additional_description = kwargs.get('additional_description', ['rpIk'])
        self._control_manip_orient = kwargs.get('control_manip_orient', None)
        self._stretch = kwargs.get('stretch', False)
        self._pv_lock = kwargs.get('pv_lock', False)
        self._soft_ik = kwargs.get('soft_ik', False)

    def flip_build_kwargs(self):
        super(RotatePlaneIk, self).flip_build_kwargs()
        self._guide_controls = namingUtils.flip_names(self._guide_controls)
        self._control_manip_orient = namingUtils.flip_names(self._control_manip_orient)

    def get_connect_kwargs(self, **kwargs):
        super(RotatePlaneIk, self).get_connect_kwargs(**kwargs)
        self._input_ik_matrix = kwargs.get('input_ik_matrix', None)

    def flip_connect_kwargs(self):
        super(RotatePlaneIk, self).flip_connect_kwargs()
        self._input_ik_matrix = namingUtils.flip_names(self._input_ik_matrix)

    def add_input_attributes(self):
        super(RotatePlaneIk, self).add_input_attributes()
        self._input_ik_matrix_attr = attributeUtils.add(self._input_node, self.INPUT_IK_MATRIX_ATTR,
                                                        attribute_type='matrix')[0]

        if self._stretch:
            self._stretch_attr = attributeUtils.add(self._input_node, self.STRETCH_ATTR, attribute_type='bool')[0]
        if self._pv_lock:
            self._pv_lock_attr = attributeUtils.add(self._input_node, self.PV_LOCK_ATTR, attribute_type='bool')[0]
        if self._soft_ik:
            self._soft_ik_attr = attributeUtils.add(self._input_node, self.SOFT_IK_ATTR, attribute_type='bool')[0]

    def create_controls(self):
        super(RotatePlaneIk, self).create_controls()
        if not isinstance(self._control_manip_orient, list):
            self._control_manip_orient = [self._control_manip_orient] * 3
        for guide, lock_attrs, manip_orient in zip(self._guide_controls,
                                                   [attributeUtils.ROTATE + attributeUtils.SCALE,
                                                    attributeUtils.ROTATE + attributeUtils.SCALE,
                                                    attributeUtils.SCALE],
                                                   self._control_manip_orient):
            name_info = namingUtils.decompose(guide)
            ctrl = controlUtils.create(name_info['description'], side=name_info['side'], index=name_info['index'],
                                       limb_index=name_info['limb_index'],
                                       additional_description=self._additional_description, sub=True,
                                       parent=self._controls_group, position=guide, rotate_order=0,
                                       manip_orient=manip_orient, lock_hide=lock_attrs)
            self._controls.append(ctrl)

        # add attributes
        if self._stretch:
            attributeUtils.add(self._controls[-1], self.STRETCH_ATTR, attribute_type='bool')
        if self._pv_lock:
            attributeUtils.add(self._controls[-1], self.PV_LOCK_ATTR, attribute_type='bool')
        if self._soft_ik:
            attributeUtils.add(self._controls[-1], self.SOFT_IK_ATTR, attribute_type='bool')

    def create_setup(self):
        super(RotatePlaneIk, self).create_setup()
        if self._controls:
            self.connect_control()
            self.get_stretch_info()
            if self._stretch:
                self.add_stretch()
            if self._pv_lock:
                self.add_pv_lock()
            if self._soft_ik:
                self.add_soft_ik()

    def get_stretch_info(self):
        # get each section's length
        for i, start_node in enumerate(self._setup_nodes[:-1]):
            end_node = self._setup_nodes[i+1]
            # get position
            start_node_pos = cmds.xform(start_node, query=True, translation=True)
            end_node_pos = cmds.xform(end_node, query=True, translation=True)
            # get length
            length = mathUtils.point.get_distance(start_node_pos, end_node_pos)
            # add to list
            self._section_length.append(length)
        # get joint chain's length
        self._chain_length = sum(self._section_length)
        # get ik length, it's from the root joint position to the ik handle position, simple use the ik controller
        self._ik_length = mathUtils.point.get_distance(cmds.xform(self._controls[0], query=True, translation=True,
                                                                  worldSpace=True),
                                                       cmds.xform(self._controls[-1], query=True, translation=True,
                                                                  worldSpace=True))

    def create_decompose_nodes(self):
        # create decompose matrix node to get ik controllers' positions
        decompose_nodes = []
        for ctrl in [self._controls[0], self._controls[-1]]:
            decompose = nodeUtils.create('decomposeMatrix',
                                         namingUtils.update(ctrl, type='decomposeMatrix',
                                                            additional_description='stretchPos'))
            cmds.connectAttr('{0}.{1}'.format(ctrl, controlUtils.OUT_MATRIX_ATTR), decompose + '.inputMatrix')
            decompose_nodes.append(decompose)

        self._decompose_root_ctrl = decompose_nodes[0]
        self._decompose_ik_ctrl = decompose_nodes[-1]

    def add_stretch(self):
        self.create_decompose_nodes()
        # create distance between to get the distance
        dis_stretch = nodeUtils.create('distanceBetween',
                                       namingUtils.update(self._controls[-1], type='distanceBetween',
                                                          additional_description='stretch'))
        cmds.connectAttr(self._decompose_root_ctrl + '.outputTranslate', dis_stretch + '.point1')
        cmds.connectAttr(self._decompose_ik_ctrl + '.outputTranslate', dis_stretch + '.point2')

        # get stretch divide value
        name = namingUtils.update(self._controls[-1], additional_description='stretchRatio')
        self._stretch_ratio_attr = nodeUtils.arithmetic.equation('{0}.distance/{1}'.format(dis_stretch,
                                                                                           self._chain_length), name)
        # condition node to get stretch multiplier
        cond_node = namingUtils.update(self._controls[-1], additional_description='stretchMult')
        stretch_mult_attr = nodeUtils.utility.condition(dis_stretch + '.distance', self._chain_length,
                                                        self._stretch_ratio_attr, 1, operation='>',
                                                        name=cond_node) + 'R'

        # loop into each setup node and connect the translation
        for node in self._setup_nodes[1:]:
            # get translate X value
            tx_val = cmds.getAttr(node + '.translateX')
            # multiply with stretch ratio
            stretch_val_attr = nodeUtils.arithmetic.equation('{0}*{1}'.format(tx_val, stretch_mult_attr),
                                                             namingUtils.update(node,
                                                                                additional_description='stretchVal'))
            # use blend color node to blend with scale weight
            nodeUtils.utility.blend_colors(self._stretch_attr, stretch_val_attr, tx_val,
                                           name=namingUtils.update(node, additional_description='stretchBlend'),
                                           connect_attr=node + '.translateX')

    def add_pv_lock(self):
        if not self._decompose_root_ctrl:
            self.create_decompose_nodes()
        # create decompose node for pole vector
        self._decompose_pv_ctrl = nodeUtils.create('decomposeMatrix',
                                                   namingUtils.update(self._controls[1], type='decomposeMatrix',
                                                                      additional_description='stretchPos'))
        cmds.connectAttr('{0}.{1}'.format(self._controls[1], controlUtils.OUT_MATRIX_ATTR),
                         self._decompose_pv_ctrl + '.inputMatrix')
        # create distance node to get distance from pv to root and ik
        dis_nodes = []
        for decompose_node, reference_node in zip([self._decompose_root_ctrl, self._decompose_ik_ctrl],
                                                  [self._controls[0], self._controls[-1]]):
            dis_node = nodeUtils.create('distanceBetween',
                                        namingUtils.update(reference_node, type='distanceBetween',
                                                           additional_description='pvLockLength'))
            cmds.connectAttr(self._decompose_pv_ctrl + '.outputTranslate', dis_node + '.point1')
            cmds.connectAttr(decompose_node + '.outputTranslate', dis_node + '.point2')
            dis_nodes.append(dis_node)

        # blend distance with setup nodes translate X to get pv lock
        for node, dis in zip([self._setup_nodes[1], self._setup_nodes[-1]], dis_nodes):
            # get translate X value
            tx_val = cmds.getAttr(node + '.translateX')
            # check if translate X value is lesser than 0, flip the distance if so
            if tx_val < 0:
                dis_attr = nodeUtils.arithmetic.equation('-1 * {0}.distance'.format(dis),
                                                         namingUtils.update(dis, additional_description='neg'))
            else:
                dis_attr = dis + '.distance'
            # check if translate X has input plug
            input_plug = cmds.listConnections(node + '.translateX', source=True, destination=False, plugs=True)
            if input_plug:
                tx_val = input_plug[0]
            # use blend color node to blend with pv lock weight
            nodeUtils.utility.blend_colors(self._pv_lock_attr, dis_attr, tx_val,
                                           name=namingUtils.update(node, additional_description='pvLockBlend'),
                                           connect_attr=node + '.translateX')

    def add_soft_ik(self):
        if not self._decompose_root_ctrl:
            self.create_decompose_nodes()
        # and soft start ratio
        soft_start_ratio = self._ik_length / self._chain_length
        # get stretch ratio attr
        if not self._stretch_ratio_attr:
            # create distance between to get the distance
            dis_stretch = nodeUtils.create('distanceBetween',
                                           namingUtils.update(self._controls[-1], type='distanceBetween',
                                                              additional_description='stretch'))
            cmds.connectAttr(self._decompose_root_ctrl + '.outputTranslate', dis_stretch + '.point1')
            cmds.connectAttr(self._decompose_ik_ctrl + '.outputTranslate', dis_stretch + '.point2')
            # divide original length to get ratio
            name = namingUtils.update(self._controls[-1], additional_description='stretchRatio')
            self._stretch_ratio_attr = nodeUtils.arithmetic.equation('{0}.distance/{1}'.format(dis_stretch,
                                                                                               self._chain_length),
                                                                     name)

        # get soft weight
        equation = '(({0} - {1})/(1 - {1}))**2 * ' \
                   '((1 - {0}*{0}*({0} - 3)*({0} - 1))**0.5 - 1)'.format(self._stretch_ratio_attr, soft_start_ratio)
        name = namingUtils.update(self._node, additional_description='softWeight')

        soft_weight_attr = nodeUtils.arithmetic.equation(equation, name)

        # use condition to get soft multiplier
        cond_name = namingUtils.update(self._node, type='condition', additional_description='softMultMin')
        soft_mult_clamp_min = nodeUtils.utility.condition(self._stretch_ratio_attr, soft_start_ratio,
                                                          1, 0, name=cond_name, operation='>') + 'R'
        cond_name = namingUtils.update(self._node, type='condition', additional_description='softMultMax')
        soft_mult_clamp_max = nodeUtils.utility.condition(self._stretch_ratio_attr, 1,
                                                          soft_mult_clamp_min, 0, name=cond_name,
                                                          operation='<') + 'R'
        # mult with soft attr to turn it on and off
        soft_mult = nodeUtils.arithmetic.equation('{0}*{1}'.format(self._soft_ik_attr, soft_mult_clamp_max),
                                                  namingUtils.update(self._node,
                                                                     additional_description='softMultiplier'))
        # get soft stretch weight
        name = namingUtils.update(self._node, additional_description='softStretchWeight')
        soft_stretch_weight = nodeUtils.arithmetic.equation(soft_weight_attr + ' + 1', name)

        # loop in each setup node to blend with original translate value
        for node in self._setup_nodes[1:]:
            # get translate X
            tx_val = cmds.getAttr(node + '.translateX')
            # get soft stretch plug by multiply the weight with original length
            soft_stretch_plug = nodeUtils.arithmetic.equation('{0} * {1}'.format(tx_val, soft_stretch_weight),
                                                              namingUtils.update(node,
                                                                                 additional_description='softIk'))
            input_plug = cmds.listConnections(node + '.translateX', source=True, destination=False, plugs=True)
            if input_plug:
                tx_val = input_plug[0]
            # use blend color node to blend with soft weight
            nodeUtils.utility.blend_colors(soft_mult, soft_stretch_plug, tx_val,
                                           name=namingUtils.update(node, additional_description='softIk'),
                                           connect_attr=node + '.translateX')

    def connect_control(self):
        # connect root control with first joint's translation
        constraintUtils.position_constraint('{0}.{1}'.format(self._controls[0], controlUtils.OUT_MATRIX_ATTR),
                                            self._setup_nodes[0], maintain_offset=False, skip=attributeUtils.ROTATE)

        # create transform node to present pole vector
        grp_pv = transformUtils.create(namingUtils.update(self._controls[1], type='group'),
                                       parent=self._nodes_hide_group, rotate_order=0, visibility=True,
                                       position=self._controls[1])
        constraintUtils.position_constraint('{0}.{1}'.format(self._controls[1], controlUtils.OUT_MATRIX_ATTR),
                                            grp_pv, maintain_offset=False)
        # create pole vector constraint
        # get ik handle's group name
        constraintUtils.pole_vector_constraint('{0}.{1}'.format(grp_pv, attributeUtils.MATRIX), self._iks[0],
                                               self._setup_nodes[0],
                                               ik_parent_inverse_matrix='{0}.{1}'.format(self._ik_groups[0],
                                                                                         attributeUtils.INVERSE_MATRIX))

        # connect ik group with controller
        constraintUtils.position_constraint('{0}.{1}'.format(self._controls[-1], controlUtils.OUT_MATRIX_ATTR),
                                            self._ik_groups[0], maintain_offset=True)

        # add twist attr to controller, and connect with ik
        twist_attr = attributeUtils.add(self._controls[-1], self.TWIST_ATTR, attribute_type='doubleAngle',
                                        keyable=True, channel_box=True)[0]
        cmds.connectAttr(twist_attr, self._iks[0] + '.twist')

        # create annotation shape as pole vector guide
        controlUtils.add_annotation(self._controls[1], self._setup_nodes[0], additional_description='annotationPv')
        controlUtils.add_annotation(self._controls[1], self._setup_nodes[-1], additional_description='annotationPv')

        # connect stretch attrs
        if self._stretch:
            cmds.connectAttr('{0}.{1}'.format(self._controls[-1], self.STRETCH_ATTR), self._stretch_attr)
        if self._pv_lock:
            cmds.connectAttr('{0}.{1}'.format(self._controls[-1], self.PV_LOCK_ATTR), self._pv_lock_attr)
        if self._soft_ik:
            cmds.connectAttr('{0}.{1}'.format(self._controls[-1], self.SOFT_IK_ATTR), self._soft_ik_attr)

    def connect_input_attributes(self):
        super(RotatePlaneIk, self).connect_input_attributes()
        if self._input_ik_matrix:
            cmds.connectAttr(self._input_ik_matrix, self._input_ik_matrix_attr)
            # connect input ik matrix with ik node
            ivs_mtx = cmds.getAttr('{0}.{1}'.format(self._ik_groups[0], attributeUtils.INVERSE_MATRIX))
            constraintUtils.position_constraint(self._input_ik_matrix_attr, self._iks[0], maintain_offset=False,
                                                skip=attributeUtils.ROTATE, parent_inverse_matrices=ivs_mtx)

    def get_input_info(self):
        super(RotatePlaneIk, self).get_input_info()
        self._input_ik_matrix_attr = '{0}.{1}'.format(self._input_node, self.INPUT_IK_MATRIX_ATTR)
