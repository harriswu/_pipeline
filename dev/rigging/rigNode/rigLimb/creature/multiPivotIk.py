import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.mathUtils as mathUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.base.multiScIk as multiScIk


class MultiPivotIk(multiScIk.MultiScIk):
    ROLL_MATRIX_ATTR = 'rollMatrix'
    RVS_ROLL_MATRIX_ATTR = 'rvsRollMatrix'

    def __init__(self, **kwargs):
        super(MultiPivotIk, self).__init__(**kwargs)
        self._create_joints = True

        self._attach_matrix = None
        self._guide_pivots = None
        self._guide_front = None

        self._pivot_limb = None
        self._front_limb = None

        self._attach_matrix_attr = None
        self._roll_matrix_attr = None
        self._rvs_roll_matrix_attr = None

    @property
    def roll_matrix_attr(self):
        return self._roll_matrix_attr

    @property
    def rvs_roll_matrix_attr(self):
        return self._rvs_roll_matrix_attr

    @property
    def attach_matrix_attr(self):
        return self._attach_matrix_attr

    def get_build_kwargs(self, **kwargs):
        super(MultiPivotIk, self).get_build_kwargs(**kwargs)
        self._guide_pivots = kwargs.get('guide_pivots', [])
        self._guide_front = kwargs.get('guide_front', [])

    def flip_build_kwargs(self):
        super(MultiPivotIk, self).flip_build_kwargs()
        self._guide_pivots = namingUtils.flip_names(self._guide_pivots)
        self._guide_front = namingUtils.flip_names(self._guide_front)

    def create_controls(self):
        super(MultiPivotIk, self).create_controls()
        self.create_pivot_controls()

    def create_pivot_controls(self):
        # create pivot limb
        build_kwargs = {'additional_description': 'pivots',
                        'parent_node': self._sub_nodes_group,
                        'guide_joints': self._guide_pivots,
                        'lock_hide': attributeUtils.TRANSLATE + attributeUtils.SCALE,
                        'control_end_joint': False,
                        'create_joint': False}

        connect_kwargs = {'input_matrix': self._input_matrix_attr,
                          'offset_matrix': self._offset_matrix_attr}

        self._pivot_limb = self.create_rig_node('dev.rigging.rigNode.rigLimb.base.fkChain', name_template=self._node,
                                                build=True, build_kwargs=build_kwargs, connect=True,
                                                connect_kwargs=connect_kwargs, flip=self._flip)

        attributeUtils.connect([self._controls_vis_output_attr, self._joints_vis_output_attr,
                                self._nodes_vis_output_attr],
                               [self._pivot_limb.controls_vis_offset_attr, self._pivot_limb.joints_vis_offset_attr,
                                self._pivot_limb.nodes_local_vis_offset_attr])

        # create front tap limb
        build_kwargs = {'additional_description': 'frontRoll',
                        'parent_node': self._sub_nodes_group,
                        'guide_joints': self._guide_front,
                        'lock_hide': attributeUtils.TRANSLATE + attributeUtils.SCALE,
                        'control_end_joint': False,
                        'create_joint': False}

        connect_kwargs = {'input_matrix': self._input_matrix_attr,
                          'offset_matrix': self._offset_matrix_attr}

        self._front_limb = self.create_rig_node('dev.rigging.rigNode.rigLimb.base.fkChain', name_template=self._node,
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
                                self._front_limb.nodes_local_vis_offset_attr])

        # add controls to control list
        self._controls = self._pivot_limb.controls + self._front_limb.controls

    def connect_ik(self):
        super(MultiPivotIk, self).connect_ik()
        # connect pivot control with ik
        constraintUtils.position_constraint('{0}.{1}'.format(self._pivot_limb.controls[-1],
                                                             controlUtils.HIERARCHY_MATRIX_ATTR), self._ik_groups[0],
                                            maintain_offset=True)
        constraintUtils.position_constraint('{0}.{1}'.format(self._front_limb.controls[0],
                                                             controlUtils.HIERARCHY_MATRIX_ATTR), self._ik_groups[1:],
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

    def get_output_info(self):
        super(MultiPivotIk, self).get_output_info()
        self._roll_matrix_attr = '{0}.{1}'.format(self._output_node, self.ROLL_MATRIX_ATTR)
        self._rvs_roll_matrix_attr = '{0}.{1}'.format(self._output_node, self.RVS_ROLL_MATRIX_ATTR)
