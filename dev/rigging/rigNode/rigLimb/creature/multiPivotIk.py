import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.mathUtils as mathUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.base.multiScIk as multiScIk
import dev.rigging.rigNode.rigLimb.base.fkChain as fkChain


class MultiPivotIk(multiScIk.MultiScIk):
    ATTACH_MATRIX_ATTR = 'attachMatrix'
    ROLL_MATRIX_ATTR = 'rollMatrix'
    RVS_ROLL_MATRIX_ATTR = 'rvsRollMatrix'

    def __init__(self, **kwargs):
        super(MultiPivotIk, self).__init__(**kwargs)
        self._attach_matrix = None
        self._guide_pivots = kwargs.get('guide_pivots', [])
        self._guide_front = kwargs.get('guide_front', [])

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

    def register_inputs(self):
        super(MultiPivotIk, self).register_inputs()
        self._attach_matrix_attr = attributeUtils.add(self._input_node, self.ATTACH_MATRIX_ATTR,
                                                      attribute_type='matrix')[0]

    def create_controls(self):
        super(MultiPivotIk, self).create_controls()
        self.create_pivot_controls()

    def create_pivot_controls(self):
        # create pivot limb
        name_info = namingUtils.decompose(self._node)
        self._pivot_limb = fkChain.FkChain(side=name_info['side'], description=name_info['description'],
                                           index=name_info['index'], limb_index=name_info['limb_index'],
                                           additional_description='pivots', parent_node=self._rig_nodes_group,
                                           guide_joints=self._guide_pivots, control_size=self._control_size,
                                           control_color=self._control_color, control_shape=self._control_shape,
                                           tag_control=self._tag_control,
                                           control_additional_description=self._control_additional_description,
                                           lock_hide=attributeUtils.TRANSLATE + attributeUtils.SCALE,
                                           control_end_joint=False, create_joint=False)
        self._pivot_limb.build()
        self._pivot_limb.connect(input_matrix=self._input_matrix_attr, offset_matrix=self._offset_matrix_attr)
        attributeUtils.connect(self._offset_matrix_attr, self._pivot_limb.offset_matrix_attr)
        attributeUtils.connect([self._controls_vis_output_attr, self._joints_vis_output_attr,
                                self._nodes_local_vis_output_attr, self._nodes_world_vis_output_attr],
                               [self._pivot_limb.controls_vis_offset_attr, self._pivot_limb.joints_vis_offset_attr,
                                self._pivot_limb.nodes_local_vis_offset_attr,
                                self._pivot_limb.nodes_world_vis_offset_attr])

        # create front tap limb
        self._front_limb = fkChain.FkChain(side=name_info['side'], description=name_info['description'],
                                           index=name_info['index'], limb_index=name_info['limb_index'],
                                           additional_description='frontRoll', parent_node=self._rig_nodes_group,
                                           guide_joints=self._guide_front,
                                           control_size=self._control_size, control_color=self._control_color,
                                           control_shape=self._control_shape, tag_control=self._tag_control,
                                           control_additional_description=self._control_additional_description,
                                           lock_hide=attributeUtils.TRANSLATE + attributeUtils.SCALE,
                                           control_end_joint=False, create_joint=False)

        self._front_limb.build()
        self._front_limb.connect(input_matrix=self._input_matrix_attr, offset_matrix=self._offset_matrix_attr)
        driven = controlUtils.get_hierarchy_node(self._front_limb.controls[0], 'driven')
        zero = controlUtils.get_hierarchy_node(self._front_limb.controls[0], 'zero')
        ivs_mtx = cmds.getAttr('{0}.{1}'.format(zero, attributeUtils.INVERSE_MATRIX))
        constraintUtils.position_constraint('{0}.{1}'.format(self._pivot_limb.controls[-2],
                                                             controlUtils.HIERARCHY_MATRIX_ATTR),
                                            driven, maintain_offset=True, parent_inverse_matrices=ivs_mtx)

        # connect vis attrs
        attributeUtils.connect([self._controls_vis_output_attr, self._joints_vis_output_attr,
                                self._nodes_local_vis_output_attr, self._nodes_world_vis_output_attr],
                               [self._front_limb.controls_vis_offset_attr, self._front_limb.joints_vis_offset_attr,
                                self._front_limb.nodes_local_vis_offset_attr,
                                self._front_limb.nodes_world_vis_offset_attr])

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

    def register_outputs(self):
        super(MultiPivotIk, self).register_outputs()
        self._roll_matrix_attr = attributeUtils.add(self._output_node, self.ROLL_MATRIX_ATTR,
                                                    attribute_type='matrix')[0]
        self._rvs_roll_matrix_attr = attributeUtils.add(self._output_node, self.RVS_ROLL_MATRIX_ATTR,
                                                        attribute_type='matrix')[0]
        if self._create_joints:
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

    def get_connection_kwargs(self, **kwargs):
        super(MultiPivotIk, self).get_connection_kwargs(**kwargs)
        self._attach_matrix = kwargs.get('attach_matrix', None)

    def connect_inputs(self):
        super(MultiPivotIk, self).connect_inputs()
        # if self._attach_matrix:
        #     attributeUtils.connect(self._attach_matrix, self._attach_matrix_attr)
        #     # get first ik group's input node, it's a constraint node, remove it
        #     input_node = cmds.listConnections('{0}.{1}'.format(self._ik_groups[0], attributeUtils.TRANSLATE[0]),
        #                                       source=True, destination=False, plugs=False)[0]
        #     cmds.delete(input_node)
        #     # point constraint with attach matrix
        #     constraintUtils.position_constraint(self._attach_matrix_attr, self._ik_groups[0],
        #                                         skip=attributeUtils.ROTATE, maintain_offset=True)

    def get_output_info(self):
        super(MultiPivotIk, self).get_output_info()
        self._roll_matrix_attr = '{0}.{1}'.format(self._output_node, self.ROLL_MATRIX_ATTR)
        self._rvs_roll_matrix_attr = '{0}.{1}'.format(self._output_node, self.RVS_ROLL_MATRIX_ATTR)
