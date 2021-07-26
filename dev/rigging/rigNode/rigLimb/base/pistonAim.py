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
import dev.rigging.utils.limbUtils as limbUtils


class PistonAim(coreLimb.CoreLimb):
    STRETCH_ATTR = 'stretch'
    STRETCH_CLAMP_MIN_ATTR = 'stretchClampMin'
    STRETCH_MIN_ATTR = 'stretchMin'
    STRETCH_CLAMP_MAX_ATTR = 'stretchClampMax'
    STRETCH_MAX_ATTR = 'stretchMax'

    def __init__(self, **kwargs):
        super(PistonAim, self).__init__(**kwargs)
        self._additional_description = None
        self._control_manip_orient = None
        self._aim_distance_multiplier = None
        self._up_distance_multiplier = None
        self._up_type = None

        self._aim_vector = None
        self._up_vector = None
        self._aim_distance = 1
        self._up_distance = 1
        self._aim_node = None

        self._hide_root_control = None

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
        super(PistonAim, self).get_build_kwargs(**kwargs)
        self._additional_description = kwargs.get('additional_description', ['piston'])
        self._control_manip_orient = kwargs.get('control_manip_orient', None)
        self._aim_distance_multiplier = kwargs.get('aim_distance_multiplier', 1)
        self._up_distance_multiplier = kwargs.get('up_distance_multiplier', 1)
        self._up_type = kwargs.get('up_type', 'object')
        self._hide_root_control = kwargs.get('hide_root_control', False)

        self._stretch = kwargs.get('stretch', False)
        self._stretch_clamp_min = kwargs.get('stretch_clamp_min', 1)
        self._stretch_min = kwargs.get('stretch_min', 1)
        self._stretch_clamp_max = kwargs.get('stretch_clamp_max', 0)
        self._stretch_max = kwargs.get('stretch_max', 2)

    def get_left_build_setting(self):
        super(PistonAim, self).get_left_build_setting()
        self._aim_vector = [1, 0, 0]
        self._up_vector = [0, 1, 0]

    def get_right_build_setting(self):
        super(PistonAim, self).get_right_build_setting()
        self._aim_vector = [-1, 0, 0]
        self._up_vector = [0, 1, 0]

    def add_input_attributes(self):
        super(PistonAim, self).add_input_attributes()
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

    def get_distance(self):
        root_pos = cmds.xform(self._guide_joints[0], query=True, translation=True, worldSpace=True)
        end_pos = cmds.xform(self._guide_joints[-1], query=True, translation=True, worldSpace=True)
        # get aim distance
        self._aim_distance = mathUtils.point.get_distance(end_pos, root_pos) * self._aim_distance_multiplier
        # get up distance
        self._up_distance = mathUtils.point.get_distance(end_pos, root_pos) * self._up_distance_multiplier

    def create_controls(self):
        super(PistonAim, self).create_controls()
        if not isinstance(self._control_manip_orient, list):
            self._control_manip_orient = [self._control_manip_orient] * 2
        for jnt, description, lock_attrs, manip in zip([self._guide_joints[0], self._guide_joints[-1]],
                                                       ['root', 'target'],
                                                       [attributeUtils.ROTATE + attributeUtils.SCALE,
                                                        attributeUtils.SCALE],
                                                       self._control_manip_orient):
            # decompose name
            name_info = namingUtils.decompose(jnt)
            # create controller
            ctrl = controlUtils.create(name_info['description'], side=name_info['side'], index=name_info['index'],
                                       limb_index=name_info['limb_index'],
                                       additional_description=self._additional_description + [description], sub=True,
                                       parent=self._controls_group, position=jnt, rotate_order=0, manip_orient=manip,
                                       lock_hide=lock_attrs)
            self._controls.append(ctrl)

        # add stretch attr
        if self._stretch:
            attributeUtils.add(self._controls[-1], self.STRETCH_ATTR, attribute_type='float', value_range=[0, 1],
                               default_value=0, keyable=True)
            attributeUtils.add(self._controls[-1], self.STRETCH_MIN_ATTR, attribute_type='float',
                               value_range=[0, 1],
                               default_value=self._stretch_min, keyable=True)
            attributeUtils.add(self._controls[-1], self.STRETCH_MAX_ATTR, attribute_type='float',
                               value_range=[1, None],
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

        # move aim controller
        self.get_distance()
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
                                       limb_index=name_info['limb_index'],
                                       additional_description=self._additional_description + ['up'], sub=True,
                                       parent=self._controls_group, position=[up_pos, self._joints[0]], rotate_order=0,
                                       manip_orient=None, lock_hide=lock_attrs)
            # add to control list
            self._controls.insert(1, ctrl)

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

        # add stretch
        if self._stretch:
            self.add_stretch()

    def create_setup_nodes(self):
        super(PistonAim, self).create_setup_nodes()
        # create setup nodes
        aim_nodes = []
        parent = self._setup_group
        for jnt in self._guide_joints:
            node = transformUtils.create(namingUtils.update(jnt, type='group',
                                                            additional_description='setup'),
                                         parent=parent, position=jnt)
            parent = node
            aim_nodes.append(node)
        transformUtils.offset_group(aim_nodes[0], namingUtils.update(aim_nodes[0], type='zero'))

        self._setup_nodes += aim_nodes

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

        # add stretchy setup
        limbUtils.function.stretchyUtils.add_stretchy(self._setup_nodes, self._controls[-1], self._stretch_attr,
                                                      dis_stretch + '.distance', distance,
                                                      self._stretch_max_attr, self._stretch_min_attr,
                                                      self._stretch_clamp_max_attr, self._stretch_clamp_min_attr)

    def append_hide_controller(self):
        super(PistonAim, self).append_hide_controller()
        if self._hide_root_control and self._controls:
            self._hide_controls.append(self._controls[0])
