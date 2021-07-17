import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.mathUtils as mathUtils
import utils.common.nodeUtils as nodeUtils
import utils.common.attributeUtils as attributeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.jointUtils as jointUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.core.coreLimb as coreLimb


class Twist(coreLimb.CoreLimb):
    START_MATRIX_ATTR = 'startMatrix'
    END_MATRIX_ATTR = 'endMatrix'
    REVERSE_START_ATTR = 'reverseStart'
    REVERSE_END_ATTR = 'reverseEnd'
    TWIST_START_ATTR = 'twistStart'
    TWIST_END_ATTR = 'twistEnd'
    TWIST_WEIGHT_ATTR = 'twistWeight'

    def __init__(self, **kwargs):
        super(Twist, self).__init__(**kwargs)
        self._joints_number = None
        self._reverse_start = None
        self._reverse_end = None

        self._start_matrix = None
        self._end_matrix = None

        self._twist_start_attr = None
        self._twist_end_attr = None

        self._start_matrix_attr = None
        self._end_matrix_attr = None
        self._reverse_start_attr = None
        self._reverse_end_attr = None

    def get_build_kwargs(self, **kwargs):
        super(Twist, self).get_build_kwargs(**kwargs)
        self._additional_description = kwargs.get('additional_description', ['twist'])
        self._joints_number = kwargs.get('joints_number', 5)
        self._reverse_start = kwargs.get('reverse_start', True)
        self._reverse_end = kwargs.get('reverse_end', False)

    def get_connect_kwargs(self, **kwargs):
        super(Twist, self).get_connect_kwargs(**kwargs)
        self._start_matrix = kwargs.get('start_matrix', None)
        self._end_matrix = kwargs.get('end_matrix', None)

    def flip_connect_kwargs(self):
        super(Twist, self).flip_connect_kwargs()
        self._start_matrix = namingUtils.flip_names(self._start_matrix)
        self._end_matrix = namingUtils.flip_names(self._end_matrix)

    def add_input_attributes(self):
        super(Twist, self).add_input_attributes()
        self._start_matrix_attr, self._end_matrix_attr = attributeUtils.add(self._input_node,
                                                                            [self.START_MATRIX_ATTR,
                                                                             self.END_MATRIX_ATTR],
                                                                            attribute_type='matrix')

        self._reverse_start_attr, self._reverse_end_attr = attributeUtils.add(self._input_node,
                                                                              [self.REVERSE_START_ATTR,
                                                                               self.REVERSE_END_ATTR],
                                                                              attribute_type='bool',
                                                                              default_value=[self._reverse_start,
                                                                                             self._reverse_end])

        self._twist_start_attr, self._twist_end_attr = attributeUtils.add(self._input_node,
                                                                          [self.TWIST_START_ATTR, self.TWIST_END_ATTR],
                                                                          attribute_type='float')

    def create_controls(self):
        # create controllers from start position to the end
        # get guide joints positions
        start_pos = cmds.xform(self._guide_joints[0], query=True, translation=True, worldSpace=True)
        end_pos = cmds.xform(self._guide_joints[-1], query=True, translation=True, worldSpace=True)
        # get controllers positions
        ctrl_pos = mathUtils.point.linear_space(start_pos, end_pos, number=self._joints_number)

        for i, pos in enumerate(ctrl_pos):
            ctrl = controlUtils.create(self._description, side=self._side, index=i + 1,
                                       additional_description=self._additional_description,
                                       limb_index=self._limb_index, sub=True, parent=self._controls_group,
                                       position=[pos, self._guide_joints[0]],
                                       lock_hide=attributeUtils.TRANSLATE + attributeUtils.SCALE)
            # add twist weight attr
            attributeUtils.add(ctrl, self.TWIST_WEIGHT_ATTR, attribute_type='float', value_range=[0, 1],
                               default_value=float(i)/(self._joints_number - 1))

            # add to control list
            self._controls.append(ctrl)
        # override setup nodes
        self._setup_nodes = self._controls

    def create_setup(self):
        super(Twist, self).create_setup()
        # extract twist value from start and end matrix
        start_twist = nodeUtils.matrix.twist_extraction(self._start_matrix_attr, axis='x',
                                                        additional_description=self._additional_description)
        end_twist = nodeUtils.matrix.twist_extraction(self._end_matrix_attr, axis='x',
                                                      additional_description=self._additional_description)

        # use condition to remap reverse from [0, 1] to [1, -1]
        reverse_start_val = nodeUtils.utility.condition(self._reverse_start_attr, 0, 1, -1,
                                                        name=namingUtils.update(self._node, type='condition',
                                                                                additional_description='reverseStart'),
                                                        operation='==') + 'R'
        reverse_end_val = nodeUtils.utility.condition(self._reverse_end_attr, 0, 1, -1,
                                                      name=namingUtils.update(self._node, type='condition',
                                                                              additional_description='reverseEnd'),
                                                      operation='==') + 'R'

        # multiple together to get twist values
        nodeUtils.arithmetic.equation('{0}*{1}'.format(start_twist, reverse_start_val),
                                      namingUtils.update(self._node, additional_description='startTwistVal'),
                                      connect_attr=self._twist_start_attr)
        nodeUtils.arithmetic.equation('{0}*{1}'.format(end_twist, reverse_end_val),
                                      namingUtils.update(self._node, additional_description='endTwistVal'),
                                      connect_attr=self._twist_end_attr)

        # loop into each controller and connect with connect group
        for ctrl in self._controls:
            # get connect node
            connect = controlUtils.get_hierarchy_node(ctrl, 'connect')
            # connect twist values with weight
            nodeUtils.arithmetic.equation('{0}*(1 - {1}) + {2}*{1}'.format(self._twist_start_attr,
                                                                           '{0}.{1}'.format(ctrl,
                                                                                            self.TWIST_WEIGHT_ATTR),
                                                                           self._twist_end_attr),
                                          namingUtils.update(ctrl, additional_description='twistVal'),
                                          connect_attr=connect + '.rotateX')

        # position constraint to make the in-between positions follow
        for i, ctrl in enumerate(self._controls[1:self._joints_number-1]):
            weight = float(i+1)/(self._joints_number - 1)
            constraintUtils.position_constraint(['{0}.{1}'.format(self._controls[0], controlUtils.LOCAL_MATRIX_ATTR),
                                                 '{0}.{1}'.format(self._controls[-1], controlUtils.LOCAL_MATRIX_ATTR)],
                                                controlUtils.get_hierarchy_node(ctrl, 'driven'),
                                                weights=[1 - weight, weight], skip=attributeUtils.ROTATE,
                                                maintain_offset=False)

    def create_joints(self):
        # create joints base on setup nodes
        self._joints = namingUtils.update_sequence(self._setup_nodes, type='joint')
        self._joints = jointUtils.create_chain(self._setup_nodes, self._joints, parent_node=self._joints_group)

    def connect_to_joints(self):
        # connect first and second node to joint
        constraintUtils.position_constraint(self._setup_nodes[0] + '.matrix', self._joints[0])
        constraintUtils.position_constraint(self._setup_nodes[1] + '.matrix', self._joints[1],
                                            parent_inverse_matrices='{0}.{1}'.format(self._joints[0],
                                                                                     attributeUtils.INVERSE_MATRIX))

        if self._joints_number > 2:
            # connect setup nodes with joint one by one,
            # need to generate parent inverse matrix because joints are chain hierarchy
            matrix_plug = self._joints[0] + '.matrix'
            for i, (attach_node, joint) in enumerate(zip(self._setup_nodes[2:], self._joints[2:])):
                mult_matrix = cmds.createNode('multMatrix',
                                              name=namingUtils.update(joint, type='multMatrix',
                                                                      additional_description='parentMatrix'))
                cmds.connectAttr(self._joints[i + 1] + '.matrix', mult_matrix + '.matrixIn[0]')
                cmds.connectAttr(matrix_plug, mult_matrix + '.matrixIn[1]')
                # inverse matrix
                invs_matrix = cmds.createNode('inverseMatrix',
                                              name=namingUtils.update(mult_matrix, type='inverseMatrix'))
                cmds.connectAttr(mult_matrix + '.matrixSum', invs_matrix + '.inputMatrix')
                # connect joint with attach node
                constraintUtils.position_constraint(attach_node + '.matrix', joint,
                                                    parent_inverse_matrices=invs_matrix + '.outputMatrix')
                # override matrix plug
                matrix_plug = mult_matrix + '.matrixSum'

    def connect_input_attributes(self):
        super(Twist, self).connect_input_attributes()
        attributeUtils.connect([self._start_matrix, self._end_matrix], [self._start_matrix_attr, self._end_matrix_attr])
        # position constraint end matrix with end controller
        zero = controlUtils.get_hierarchy_node(self._controls[-1], 'zero')
        ivs_matrix = cmds.getAttr('{0}.{1}'.format(zero, attributeUtils.INVERSE_MATRIX))
        constraintUtils.position_constraint(self._end_matrix_attr,
                                            controlUtils.get_hierarchy_node(self._controls[-1], 'driven'),
                                            parent_inverse_matrices=ivs_matrix, maintain_offset=False)
