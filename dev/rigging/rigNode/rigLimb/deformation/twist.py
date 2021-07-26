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
    START_OFFSET_MATRIX_ATTR = 'startOffsetMatrix'
    START_PARENT_MATRIX_ATTR = 'startParentMatrix'
    START_INVERSE_MATRIX_ATTR = 'startInverseMatrix'
    END_MATRIX_ATTR = 'endMatrix'
    END_OFFSET_MATRIX_ATTR = 'endOffsetMatrix'
    END_PARENT_MATRIX_ATTR = 'endParentMatrix'
    END_INVERSE_MATRIX_ATTR = 'endInverseMatrix'
    END_POSITION_MATRIX_ATTR = 'endPositionMatrix'
    REVERSE_START_ATTR = 'reverseStart'
    TWIST_START_ATTR = 'twistStart'
    TWIST_END_ATTR = 'twistEnd'
    TWIST_WEIGHT_ATTR = 'twistWeight'

    def __init__(self, **kwargs):
        super(Twist, self).__init__(**kwargs)
        self._joints_number = None
        self._reverse_start = None

        self._start_matrix = None
        self._end_matrix = None
        self._end_position_matrix = None

        self._twist_start_attr = None
        self._twist_end_attr = None

        self._start_matrix_attr = None
        self._end_matrix_attr = None
        self._end_position_matrix_attr = None
        self._reverse_start_attr = None

        self._start_offset_matrix_attr = None
        self._start_parent_matrix_attr = None
        self._start_inverse_matrix_attr = None
        self._end_offset_matrix_attr = None
        self._end_parent_matrix_attr = None
        self._end_inverse_matrix_attr = None

    def get_build_kwargs(self, **kwargs):
        super(Twist, self).get_build_kwargs(**kwargs)
        self._additional_description = kwargs.get('additional_description', ['twist'])
        self._joints_number = kwargs.get('joints_number', 5)
        self._reverse_start = kwargs.get('reverse_start', False)

    def get_connect_kwargs(self, **kwargs):
        super(Twist, self).get_connect_kwargs(**kwargs)
        self._start_matrix = kwargs.get('start_matrix', None)
        self._end_matrix = kwargs.get('end_matrix', None)
        self._end_position_matrix = kwargs.get('end_position_matrix', None)

        if isinstance(self._start_matrix, basestring):
            self._start_matrix = [self._start_matrix]
        if isinstance(self._end_matrix, basestring):
            self._end_matrix = [self._end_matrix]

    def flip_connect_kwargs(self):
        super(Twist, self).flip_connect_kwargs()
        self._start_matrix = namingUtils.flip_names(self._start_matrix)
        self._end_matrix = namingUtils.flip_names(self._end_matrix)
        self._end_position_matrix = namingUtils.flip_names(self._end_position_matrix)

    def add_input_attributes(self):
        super(Twist, self).add_input_attributes()
        self._start_matrix_attr, self._end_matrix_attr = attributeUtils.add(self._input_node,
                                                                            [self.START_MATRIX_ATTR,
                                                                             self.END_MATRIX_ATTR],
                                                                            attribute_type='matrix', multi=True)

        (self._start_offset_matrix_attr, self._end_offset_matrix_attr, self._start_parent_matrix_attr,
         self._end_parent_matrix_attr, self._start_inverse_matrix_attr,
         self._end_inverse_matrix_attr) = attributeUtils.add(self._input_node,
                                                             [self.START_OFFSET_MATRIX_ATTR,
                                                              self.END_OFFSET_MATRIX_ATTR,
                                                              self.START_PARENT_MATRIX_ATTR,
                                                              self.END_PARENT_MATRIX_ATTR,
                                                              self.START_INVERSE_MATRIX_ATTR,
                                                              self.END_INVERSE_MATRIX_ATTR], attribute_type='matrix',
                                                             multi=True)

        self._end_position_matrix_attr = attributeUtils.add(self._input_node, self.END_POSITION_MATRIX_ATTR,
                                                            attribute_type='matrix')[0]

        self._reverse_start_attr = attributeUtils.add(self._input_node, self.REVERSE_START_ATTR, attribute_type='bool',
                                                      default_value=self._reverse_start)[0]

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

    def create_node_post(self):
        super(Twist, self).create_node_post()
        # get start and end matrix, use joint orient as inverse matrix
        start_end_twist = []
        for (mtx, mtx_attr, offset_attr, parent_attr, ivs_attr, name,
             guide) in zip([self._start_matrix, self._end_matrix], [self._start_matrix_attr, self._end_matrix_attr],
                           [self._start_offset_matrix_attr, self._end_offset_matrix_attr],
                           [self._start_parent_matrix_attr, self._end_parent_matrix_attr],
                           [self._start_inverse_matrix_attr, self._end_inverse_matrix_attr], ['start', 'end'],
                           [self._guide_joints[0], self._guide_joints[-1]]):

            twist_sum_attrs = []

            for i, value in enumerate(mtx):
                mult_matrix_node = namingUtils.update(self._node, type='multMatrix',
                                                      additional_description=[name, 'twistMatrix'], index=i + 1)
                twist_matrix_attr = self.connect_twist_matrix(value, '{0}[{1}]'.format(mtx_attr, i), guide,
                                                              '{0}[{1}]'.format(offset_attr, i),
                                                              '{0}[{1}]'.format(parent_attr, i),
                                                              '{0}[{1}]'.format(ivs_attr, i), mult_matrix_node)
                # extract twist value
                twist_attr = nodeUtils.matrix.twist_extraction(twist_matrix_attr, axis='x',
                                                               additional_description=self._additional_description)
                # add to twist sum list
                twist_sum_attrs.append(twist_attr)

            # use plus minus average node to get the twist value
            plus_node = namingUtils.update(self._node, type='plusMinusAverage',
                                           additional_description=['twistSum', name])
            twist_sum = nodeUtils.arithmetic.plus_minus_average(*twist_sum_attrs, name=plus_node)

            # add to start end twist list
            start_end_twist.append(twist_sum)

        # connect extract twist values to twist attrs
        # because the whole limb is driven by input matrix,
        # so start joint has to be twisted in a counter direction to avoid double transformation
        nodeUtils.arithmetic.equation('-' + start_end_twist[0],
                                      namingUtils.update(self._node, additional_description='startTwistVal'),
                                      connect_attr=self._twist_start_attr)
        attributeUtils.connect(start_end_twist[1], self._twist_end_attr)

        # loop into each controller and connect with connect group
        for ctrl in self._controls:
            # get start weight
            # use condition to setup start reverse
            # if reverse set to False, it will counter from the bottom joints, otherwise will counter from the top
            weight_attr = '{0}.{1}'.format(ctrl, self.TWIST_WEIGHT_ATTR)
            rvs_weight_val = nodeUtils.arithmetic.equation('1 - ' + weight_attr,
                                                           namingUtils.update(ctrl,
                                                                              additional_description='startWeightRvs'))
            start_weight = nodeUtils.utility.condition(self._reverse_start_attr, 0, weight_attr, rvs_weight_val,
                                                       operation='==',
                                                       name=namingUtils.update(ctrl, type='condition',
                                                                               additional_description='startWeight')
                                                       ) + 'R'
            # get connect node
            connect = controlUtils.get_hierarchy_node(ctrl, 'connect')
            # connect twist values with weight
            nodeUtils.arithmetic.equation('{0}*{1} + {2}*{3}'.format(self._twist_start_attr, start_weight,
                                                                     self._twist_end_attr, weight_attr),
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
        constraintUtils.position_constraint('{0}.{1}'.format(self._setup_nodes[0],
                                                             controlUtils.OUT_MATRIX_ATTR), self._joints[0])
        constraintUtils.position_constraint('{0}.{1}'.format(self._setup_nodes[1],
                                                             controlUtils.OUT_MATRIX_ATTR), self._joints[1],
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
                constraintUtils.position_constraint('{0}.{1}'.format(attach_node,
                                                                     controlUtils.OUT_MATRIX_ATTR), joint,
                                                    parent_inverse_matrices=invs_matrix + '.outputMatrix')
                # override matrix plug
                matrix_plug = mult_matrix + '.matrixSum'

    def connect_input_attributes(self):
        super(Twist, self).connect_input_attributes()

        if self._end_position_matrix:
            attributeUtils.connect(self._end_position_matrix, self._end_position_matrix_attr)
            # position constraint end matrix with end controller
            zero = controlUtils.get_hierarchy_node(self._controls[-1], 'zero')
            ivs_matrix = '{0}.{1}'.format(zero, attributeUtils.WORLD_INVERSE_MATRIX)
            constraintUtils.position_constraint(self._end_position_matrix_attr,
                                                controlUtils.get_hierarchy_node(self._controls[-1], 'driven'),
                                                parent_inverse_matrices=ivs_matrix, maintain_offset=False,
                                                skip=attributeUtils.ROTATE)

    def connect_twist_matrix(self, twist_matrix, twist_matrix_attr, guide, offset_matrix_attr, parent_matrix_attr,
                             inverse_matrix_attr, mult_matrix_node):
        # connect twist matrix
        attributeUtils.connect(twist_matrix, twist_matrix_attr)
        # get driver matrix attr's object name
        driver = attributeUtils.compose_attr(twist_matrix)[1]
        # get inverse world matrix
        ivs_world_matrix_driver = cmds.getAttr('{0}.{1}'.format(driver, attributeUtils.WORLD_INVERSE_MATRIX))
        # get root joint's world matrix
        world_matrix_joint = cmds.getAttr('{0}.{1}'.format(self._guide_joints[0], attributeUtils.WORLD_MATRIX))
        # get guide joint position
        guide_pos = cmds.xform(guide, query=True, translation=True, worldSpace=True)
        # update matrix
        world_matrix_joint = mathUtils.matrix.update(world_matrix_joint, translate=guide_pos)
        # compute offset matrix
        offset_matrix = mathUtils.matrix.multiply(world_matrix_joint, ivs_world_matrix_driver, output_type='list')
        # set value
        attributeUtils.set_value(offset_matrix_attr, offset_matrix, type='matrix')
        # get driver parent node
        driver_parent = cmds.listRelatives(driver, parent=True)
        # get parent world matrix and set value
        if driver_parent:
            attributeUtils.set_value(parent_matrix_attr,
                                     cmds.getAttr('{0}.{1}'.format(driver_parent[0], attributeUtils.WORLD_MATRIX)),
                                     type='matrix')
        # set inverse matrix value
        attributeUtils.set_value(inverse_matrix_attr, mathUtils.matrix.inverse(world_matrix_joint, output_type='list'),
                                 type='matrix')

        # mult matrix to get output matrix
        mult_matrix_attr = nodeUtils.matrix.mult_matrix(offset_matrix_attr, twist_matrix_attr, parent_matrix_attr,
                                                        inverse_matrix_attr, name=mult_matrix_node)

        return mult_matrix_attr
