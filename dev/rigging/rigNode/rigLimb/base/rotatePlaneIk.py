import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.core.ikHandle as ikHandleLimb


class RotatePlaneIk(ikHandleLimb.IkHandle):
    INPUT_IK_MATRIX_ATTR = 'inputIkMatrix'
    TWIST_ATTR = 'twist'

    def __init__(self, **kwargs):
        super(RotatePlaneIk, self).__init__(**kwargs)
        self._guide_controls = None
        self._control_manip_orient = None

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
