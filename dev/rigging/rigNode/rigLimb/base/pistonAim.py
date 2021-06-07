# import maya python library
import maya.cmds as cmds

# import utils
import utils.common.namingUtils as namingUtils
import utils.common.mathUtils as mathUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

# import limb class
import dev.rigging.rigNode.rigLimb.core.coreLimb as coreLimb


class PistonAim(coreLimb.CoreLimb):
    def __init__(self, **kwargs):
        super(PistonAim, self).__init__(**kwargs)
        self._additional_description = kwargs.get('additional_description', 'piston')
        self._aim_distance_multiplier = kwargs.get('aim_distance_multiplier', 1)
        self._up_distance_multiplier = kwargs.get('up_distance_multiplier', 1)
        self._up_type = kwargs.get('up_type', 'object')

        self._aim_vector = None
        self._up_vector = None
        self._aim_distance = 1
        self._up_distance = 1
        self._aim_node = None
        
    def create_node(self):
        self.get_aim_vectors()
        super(PistonAim, self).create_node()

    def create_controls(self):
        super(PistonAim, self).create_controls()
        tag_parent = self._tag_parent
        for jnt, description, lock_attrs in zip([self._guide_joints[0], self._guide_joints[-1]], ['root', 'target'],
                                                [attributeUtils.ROTATE + attributeUtils.SCALE, attributeUtils.SCALE]):
            # decompose name
            name_info = namingUtils.decompose(jnt)
            # create controller
            ctrl = controlUtils.create(name_info['description'], side=name_info['side'], index=name_info['index'],
                                       limb_index=name_info['limb_index'], additional_description=description, sub=True,
                                       parent=self._controls_group, position=jnt, rotate_order=0, manip_orient=None,
                                       lock_hide=lock_attrs, shape=self._control_shape,
                                       color=self._control_color, size=self._control_size, tag=self._tag_control,
                                       tag_parent=tag_parent)
            self._controls.append(ctrl)

            # override tag parent
            tag_parent = ctrl

        # move aim controller
        zero = controlUtils.get_hierarchy_node(self._controls[-1], 'zero')
        vec_scale = mathUtils.vector.scale(self._aim_vector, self._aim_distance)
        ctrl_pos = mathUtils.point.mult_matrix(vec_scale, cmds.getAttr('{0}.{1}'.format(self._guide_joints[0],
                                                                                        attributeUtils.WORLD_MATRIX)))
        cmds.xform(zero, translation=ctrl_pos, worldSpace=True)

        # create up controller
        if self._up_type != 'none':
            # get up vector control position
            if self._up_type == 'object':
                # get position
                vec_scale = mathUtils.vector.scale(self._up_vector, self._up_distance)
                up_pos = mathUtils.point.mult_matrix(vec_scale,
                                                     cmds.getAttr('{0}.{1}'.format(self._guide_joints[0],
                                                                                   attributeUtils.WORLD_MATRIX)))
                # get lock attrs
                lock_attrs = attributeUtils.ROTATE + attributeUtils.SCALE
            else:
                up_pos = self._joints[0]
                lock_attrs = attributeUtils.TRANSLATE + attributeUtils.SCALE

            # decompose first guide's name
            name_info = namingUtils.decompose(self._guide_joints[0])
            # create up controller to control up vector
            ctrl = controlUtils.create(name_info['description'], side=name_info['side'], index=name_info['index'],
                                       limb_index=name_info['limb_index'], additional_description='up', sub=True,
                                       parent=self._controls_group, position=[up_pos, self._joints[0]], rotate_order=0,
                                       manip_orient=None, lock_hide=lock_attrs, shape=self._control_shape,
                                       color=self._control_color, size=self._control_size, tag=self._tag_control,
                                       tag_parent=self._controls[0])
            # add to control list
            self._controls.insert(1, ctrl)

    def get_aim_vectors(self):
        # get aim vector
        root_pos = cmds.xform(self._guide_joints[0], query=True, translation=True, worldSpace=True)
        end_pos = cmds.xform(self._guide_joints[-1], query=True, translation=True, worldSpace=True)
        self._aim_vector = mathUtils.vector.norm(cmds.getAttr(self._guide_joints[-1] + '.translate')[0])
        # get aim distance
        self._aim_distance = mathUtils.point.get_distance(end_pos, root_pos) * self._aim_distance_multiplier
        # get up vector
        self._up_vector = mathUtils.vector.cross_product([0, 0, 1], self._aim_vector, normalize=True)
        # get up distance
        self._up_distance = mathUtils.point.get_distance(end_pos, root_pos) * self._up_distance_multiplier

    def create_setup(self):
        super(PistonAim, self).create_setup()
        zero_node = cmds.listRelatives(self._setup_nodes[0], parent=True)[0]
        # get zero node's inverse matrix
        ivs_matrix = cmds.getAttr('{0}.{1}'.format(zero_node, attributeUtils.INVERSE_MATRIX))

        # connect root control with setup node's translation
        constraintUtils.position_constraint('{0}.{1}'.format(self._controls[0], controlUtils.OUT_MATRIX_ATTR),
                                            self._setup_nodes[0], parent_inverse_matrices=ivs_matrix,
                                            maintain_offset=False, skip=attributeUtils.ROTATE)

        # do aim constraint
        if self._up_type != 'none':
            up_matrix = '{0}.{1}'.format(self._controls[1], controlUtils.OUT_MATRIX_ATTR)
        else:
            up_matrix = None
        # do an aim constraint with joint
        constraintUtils.aim_constraint('{0}.{1}'.format(self._controls[-1], controlUtils.OUT_MATRIX_ATTR),
                                       self._setup_nodes[0], aim_vector=self._aim_vector, up_vector=self._up_vector,
                                       world_up_type=self._up_type, world_up_matrix=up_matrix,
                                       world_up_vector=self._up_vector, parent_inverse_matrix=ivs_matrix, force=True)

        # add annotation
        if self._up_type == 'object':
            controlUtils.add_annotation(self._controls[1], self._setup_nodes[0], additional_description='annotationUp')
        controlUtils.add_annotation(self._controls[-1], self._setup_nodes[0], additional_description='annotationAim')

    def create_setup_nodes(self):
        super(PistonAim, self).create_setup_nodes()
        # create setup node
        aim_node = transformUtils.create(namingUtils.update(self._node, type='group',
                                                            additional_description='setup'),
                                         parent=self._setup_group, position=self._guide_joints[0])
        transformUtils.offset_group(aim_node, namingUtils.update(aim_node, type='zero'))

        self._setup_nodes.append(aim_node)

    def connect_to_joints(self):
        super(PistonAim, self).connect_to_joints()
        # get setup node's matrix
        zero = cmds.listRelatives(self._setup_nodes[0], parent=True)[0]
        matrix_attrs = attributeUtils.compose_attrs([self._setup_nodes[0], zero], attributeUtils.MATRIX)
        aim_node_matrix = nodeUtils.matrix.mult_matrix(*matrix_attrs,
                                                       name=namingUtils.update(self._setup_nodes[0], type='multMatrix',
                                                                               additional_description='rootMatrix'))
        # constraint with root joint
        constraintUtils.position_constraint(aim_node_matrix, self._joints[0], maintain_offset=False)
