import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.mathUtils as mathUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils
import utils.common.hierarchyUtils as hierarchyUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.core.ikHandle as ikHandle


class MultiPivotIk(ikHandle.IkHandle):
    ROLL_MATRIX_ATTR = 'rollMatrix'
    RVS_ROLL_MATRIX_ATTR = 'rvsRollMatrix'
    CONTROL_INPUT_MATRIX_ATTR = 'controlInputMatrix'
    CONTROL_OFFSET_MATRIX_ATTR = 'controlOffsetMatrix'
    CONTROL_CONNECT_MATRIX_ATTR = 'controlConnectMatrix'

    def __init__(self, **kwargs):
        super(MultiPivotIk, self).__init__(**kwargs)
        self._ik_type = 'ikSCsolver'
        self._create_joints = True

        self._guide_pivots = None
        self._guide_front = None

        self._control_input_matrix = None

        self._ik_handle_group = None

        self._pivot_limb = None
        self._front_limb = None

        self._roll_matrix_attr = None
        self._rvs_roll_matrix_attr = None

        self._control_input_matrix_attr = None
        self._control_offset_matrix_attr = None
        self._control_connect_matrix_attr = None

    @property
    def control_input_matrix_attr(self):
        return self._control_input_matrix_attr

    @property
    def control_offset_matrix_attr(self):
        return self._control_offset_matrix_attr

    @property
    def control_connect_matrix_attr(self):
        return self._control_connect_matrix_attr

    @property
    def roll_matrix_attr(self):
        return self._roll_matrix_attr

    @property
    def rvs_roll_matrix_attr(self):
        return self._rvs_roll_matrix_attr

    def get_build_kwargs(self, **kwargs):
        super(MultiPivotIk, self).get_build_kwargs(**kwargs)
        self._guide_pivots = kwargs.get('guide_pivots', [])
        self._guide_front = kwargs.get('guide_front', [])

    def flip_build_kwargs(self):
        super(MultiPivotIk, self).flip_build_kwargs()
        self._guide_pivots = namingUtils.flip_names(self._guide_pivots)
        self._guide_front = namingUtils.flip_names(self._guide_front)

    def get_connect_kwargs(self, **kwargs):
        super(MultiPivotIk, self).get_connect_kwargs(**kwargs)
        self._control_input_matrix = kwargs.get('control_input_matrix', None)

    def flip_connect_kwargs(self):
        super(MultiPivotIk, self).flip_connect_kwargs()
        self._control_input_matrix = namingUtils.flip_names(self._control_input_matrix)

    def create_controls(self):
        super(MultiPivotIk, self).create_controls()
        self.create_pivot_controls()

    def add_input_attributes(self):
        super(MultiPivotIk, self).add_input_attributes()
        matrix_attrs = attributeUtils.add(self._input_node,
                                          [self.CONTROL_INPUT_MATRIX_ATTR, self.CONTROL_OFFSET_MATRIX_ATTR,
                                           self.CONTROL_CONNECT_MATRIX_ATTR],
                                          attribute_type='matrix')

        mult_matrix_node = namingUtils.update(self._node, type='multMatrix',
                                              additional_description=self.CONTROL_INPUT_MATRIX_ATTR)
        mult_matrix_attr = nodeUtils.matrix.mult_matrix(matrix_attrs[1], matrix_attrs[0], name=mult_matrix_node)
        attributeUtils.connect(mult_matrix_attr, matrix_attrs[2])

        self._control_input_matrix_attr = matrix_attrs[0]
        self._control_offset_matrix_attr = matrix_attrs[1]
        self._control_connect_matrix_attr = matrix_attrs[2]

    def create_pivot_controls(self):
        # create pivot limb
        build_kwargs = {'additional_description': [],
                        'parent_node': self._sub_nodes_group,
                        'guide_joints': self._guide_pivots,
                        'lock_hide': attributeUtils.TRANSLATE + attributeUtils.SCALE,
                        'control_end_joint': False,
                        'create_joints': False}

        connect_kwargs = {'input_matrix': self._control_input_matrix_attr,
                          'offset_matrix': self._control_offset_matrix_attr}

        self._pivot_limb = self.create_rig_node('dev.rigging.rigNode.rigLimb.base.fkChain',
                                                name_template=namingUtils.update(self._node,
                                                                                 additional_description='pivot'),
                                                build=True, build_kwargs=build_kwargs, connect=True,
                                                connect_kwargs=connect_kwargs, flip=self._flip)

        attributeUtils.connect([self._controls_vis_output_attr, self._joints_vis_output_attr,
                                self._nodes_vis_output_attr],
                               [self._pivot_limb.controls_vis_offset_attr, self._pivot_limb.joints_vis_offset_attr,
                                self._pivot_limb.nodes_vis_offset_attr])

        # create front tap limb
        build_kwargs = {'additional_description': [],
                        'parent_node': self._sub_nodes_group,
                        'guide_joints': self._guide_front,
                        'lock_hide': attributeUtils.TRANSLATE + attributeUtils.SCALE,
                        'control_end_joint': False,
                        'create_joints': False}

        connect_kwargs = {'input_matrix': self._control_input_matrix_attr,
                          'offset_matrix': self._control_offset_matrix_attr}

        self._front_limb = self.create_rig_node('dev.rigging.rigNode.rigLimb.base.fkChain',
                                                name_template=namingUtils.update(self._node,
                                                                                 additional_description='frontRoll'),
                                                build=True, build_kwargs=build_kwargs, connect=True,
                                                connect_kwargs=connect_kwargs, flip=self._flip)
        driven = controlUtils.get_hierarchy_node(self._front_limb.controls[0], 'driven')
        zero = controlUtils.get_hierarchy_node(self._front_limb.controls[0], 'zero')
        ivs_mtx = cmds.getAttr('{0}.{1}'.format(zero, attributeUtils.INVERSE_MATRIX))
        constraintUtils.position_constraint('{0}.{1}'.format(self._pivot_limb.controls[-2],
                                                             controlUtils.HIERARCHY_MATRIX_ATTR),
                                            driven, maintain_offset=True, parent_inverse_matrices=ivs_mtx)

        # connect vis attrs
        attributeUtils.connect([self._controls_vis_output_attr, self._joints_vis_output_attr,
                                self._nodes_vis_output_attr],
                               [self._front_limb.controls_vis_offset_attr, self._front_limb.joints_vis_offset_attr,
                                self._front_limb.nodes_vis_offset_attr])

        # add controls to control list
        self._controls = self._pivot_limb.controls + self._front_limb.controls

    def create_ik(self):
        self._ik_handle_group = transformUtils.create(namingUtils.update(self._node, type='group',
                                                                         additional_description='ikHandles'),
                                                      parent=self._nodes_world_group)
        # matrix connect with ik handle group
        constraintUtils.matrix_connect(self._control_connect_matrix_attr, self._ik_handle_group)

        for i, jnt in enumerate(self._setup_nodes[:-1]):
            # create ik handle
            ik_handle = namingUtils.update(jnt, type='ikHandle')
            cmds.ikHandle(startJoint=jnt, endEffector=self._setup_nodes[i + 1], solver=self._ik_type, name=ik_handle)
            hierarchyUtils.parent(ik_handle, self._ik_handle_group)
            self._iks.append(ik_handle)

    def connect_ik(self):
        # create transform group for each ik handle
        for ik_hnd, jnt in zip(self._iks, self._setup_nodes[1:]):
            zero = transformUtils.create(namingUtils.update(ik_hnd, type='zero', additional_description='ik'),
                                         parent=self._ik_handle_group, rotate_order=0, visibility=False,
                                         position=jnt, inherits_transform=True)

            # parent ik under offset group
            cmds.parent(ik_hnd, zero)
            # append list
            self._ik_groups.append(zero)

        # connect pivot control with ik
        constraintUtils.position_constraint('{0}.{1}'.format(self._front_limb.controls[0],
                                                             controlUtils.HIERARCHY_MATRIX_ATTR), self._ik_groups,
                                            maintain_offset=True)

    def add_output_attributes(self):
        super(MultiPivotIk, self).add_output_attributes()
        self._roll_matrix_attr = attributeUtils.add(self._output_node, self.ROLL_MATRIX_ATTR,
                                                    attribute_type='matrix')[0]
        self._rvs_roll_matrix_attr = attributeUtils.add(self._output_node, self.RVS_ROLL_MATRIX_ATTR,
                                                        attribute_type='matrix')[0]

        nodeUtils.matrix.compose_matrix(namingUtils.update(self._node, type='composeMatrix',
                                                           additional_description='rollMatrix'),
                                        rotate=['{0}.{1}'.format(self._joints[1], attributeUtils.ROTATE[0]),
                                                '{0}.{1}'.format(self._joints[1], attributeUtils.ROTATE[1]),
                                                '{0}.{1}'.format(self._joints[1], attributeUtils.ROTATE[2])],
                                        rotate_order='{0}.{1}'.format(self._joints[1], attributeUtils.ROTATE_ORDER),
                                        connect_attr=self._roll_matrix_attr)

        # get root joint's local matrix on roll joint
        root_matrix = cmds.getAttr('{0}.{1}'.format(self._guide_joints[0], attributeUtils.WORLD_MATRIX))
        ctrl_matrix = cmds.getAttr('{0}.{1}'.format(self._pivot_limb.controls[-1], controlUtils.WORLD_MATRIX_ATTR))
        local_matrix = mathUtils.matrix.localize(root_matrix, ctrl_matrix)
        # mult matrix to connect with rvs roll matrix
        nodeUtils.matrix.mult_matrix(local_matrix,
                                     '{0}.{1}'.format(self._pivot_limb.controls[-1],
                                                      controlUtils.HIERARCHY_MATRIX_ATTR),
                                     name=namingUtils.update(self._node, type='multMatrix',
                                                             additional_description='rvsRollMatrix'),
                                     connect_attr=self._rvs_roll_matrix_attr)

    def connect_input_attributes(self):
        super(MultiPivotIk, self).connect_input_attributes()
        if self._control_input_matrix:
            # get input matrix value
            input_matrix_val = cmds.getAttr(self._control_input_matrix)
            # compute offset matrix
            offset_matrix_val = mathUtils.matrix.localize(mathUtils.matrix.IDENTITY, input_matrix_val,
                                                          output_type='list')
            # set offset matrix
            cmds.setAttr(self._control_offset_matrix_attr, offset_matrix_val, type='matrix')
            # connect input matrix
            attributeUtils.connect(self._control_input_matrix, self._control_input_matrix_attr)

    def get_input_info(self):
        super(MultiPivotIk, self).get_input_info()
        self._control_input_matrix_attr = '{0}.{1}'.format(self._input_node, self.CONTROL_INPUT_MATRIX_ATTR)
        self._control_offset_matrix_attr = '{0}.{1}'.format(self._input_node, self.CONTROL_OFFSET_MATRIX_ATTR)
        self._control_connect_matrix_attr = '{0}.{1}'.format(self._input_node, self.CONTROL_CONNECT_MATRIX_ATTR)

    def get_output_info(self):
        super(MultiPivotIk, self).get_output_info()
        self._roll_matrix_attr = '{0}.{1}'.format(self._output_node, self.ROLL_MATRIX_ATTR)
        self._rvs_roll_matrix_attr = '{0}.{1}'.format(self._output_node, self.RVS_ROLL_MATRIX_ATTR)
