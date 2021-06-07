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
    END_MATRIX_ATTR = 'endMatrix'
    ATTACH_MATRIX_ATTR = 'attachMatrix'

    def __init__(self, **kwargs):
        super(RotatePlaneIk, self).__init__(**kwargs)
        self._guide_controls = kwargs.get('guide_controls', [])
        self._additional_description = kwargs.get('additional_description', 'rpIk')
        self._control_manip_orient = kwargs.get('control_manip_orient', None)

        # connection
        self._input_ik_matrix = None

        self._ik_type = 'ikRPsolver'

        self._input_ik_matrix_attr = None
        self._end_matrix_attr = None
        self._attach_matrix_attr = None

    @property
    def input_ik_matrix(self):
        return cmds.getAttr(self._input_ik_matrix_attr)

    @property
    def input_ik_matrix_attr(self):
        return self._input_ik_matrix_attr

    @property
    def end_matrix_attr(self):
        return self._end_matrix_attr

    @property
    def attach_matrix_attr(self):
        return self._attach_matrix_attr

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
                                       additional_description=self._control_additional_description, sub=True,
                                       parent=self._controls_group, position=guide, rotate_order=0,
                                       manip_orient=manip_orient, lock_hide=lock_attrs, shape=self._control_shape,
                                       color=self._control_color, size=self._control_size, tag=self._tag_control)
            self._controls.append(ctrl)

    def create_setup(self):
        super(RotatePlaneIk, self).create_setup()
        if self._controls:
            self.connect_control()

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

    def register_inputs(self):
        super(RotatePlaneIk, self).register_inputs()
        self._input_ik_matrix_attr = attributeUtils.add(self._input_node, self.INPUT_IK_MATRIX_ATTR,
                                                        attribute_type='matrix')[0]

    def register_outputs(self):
        super(RotatePlaneIk, self).register_outputs()
        self._end_matrix_attr = attributeUtils.add(self._output_node, self.END_MATRIX_ATTR, attribute_type='matrix')[0]
        # get local matrix attrs for all setup nodes
        setup_matrices = attributeUtils.compose_attrs(self._setup_nodes[::-1], attributeUtils.MATRIX)
        nodeUtils.matrix.mult_matrix(*setup_matrices, name=namingUtils.update(self._node, type='multMatrix',
                                                                              additional_description='endMatrix'),
                                     connect_attr=self._end_matrix_attr)

        self._attach_matrix_attr = attributeUtils.add(self._output_node, self.ATTACH_MATRIX_ATTR,
                                                      attribute_type='matrix')[0]
        end_mtx = cmds.getAttr('{0}.{1}'.format(self._guide_joints[-1], attributeUtils.WORLD_MATRIX))
        if self._controls:
            end_ctrl_mtx_attr = '{0}.{1}'.format(self._controls[-1], controlUtils.WORLD_MATRIX_ATTR)
            end_mtx_local = mathUtils.matrix.localize(end_mtx, cmds.getAttr(end_ctrl_mtx_attr))
            nodeUtils.matrix.mult_matrix(end_mtx_local, end_ctrl_mtx_attr,
                                         name=namingUtils.update(self._node, type='multMatrix',
                                                                 additional_description='attachMatrix'),
                                         connect_attr=self._attach_matrix_attr)

    def connect_inputs(self):
        super(RotatePlaneIk, self).connect_inputs()
        if self._input_ik_matrix:
            cmds.connectAttr(self._input_ik_matrix, self._input_ik_matrix_attr)
            # connect input ik matrix with ik node
            ivs_mtx = cmds.getAttr('{0}.{1}'.format(self._ik_groups[0], attributeUtils.INVERSE_MATRIX))
            constraintUtils.position_constraint(self._input_ik_matrix_attr, self._iks[0], maintain_offset=False,
                                                skip=attributeUtils.ROTATE, parent_inverse_matrices=ivs_mtx)

    def get_connection_kwargs(self, **kwargs):
        super(RotatePlaneIk, self).get_connection_kwargs(**kwargs)
        self._input_ik_matrix = kwargs.get('input_ik_matrix', None)

    def get_input_info(self):
        super(RotatePlaneIk, self).get_input_info()
        self._input_ik_matrix_attr = '{0}.{1}'.format(self._input_node, self.INPUT_IK_MATRIX_ATTR)

    def get_output_info(self):
        super(RotatePlaneIk, self).get_output_info()
        self._end_matrix_attr = '{0}.{1}'.format(self._output_node, self.END_MATRIX_ATTR)
        self._attach_matrix_attr = '{0}.{1}'.format(self._output_node, self.ATTACH_MATRIX_ATTR)
