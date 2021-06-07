import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.mathUtils as mathUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.jointUtils as jointUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.core.coreNode as coreNode


class CoreLimb(coreNode.CoreNode):
    # input attributes
    CONTROLS_VIS_ATTR = 'controlsVis'
    JOINTS_VIS_ATTR = 'jointsVis'
    NODES_LOCAL_VIS_ATTR = 'nodesLocalVis'
    NODES_WORLD_VIS_ATTR = 'nodesWorldVis'
    CONTROLS_VIS_OFFSET_ATTR = 'controlsVisOffset'
    JOINTS_VIS_OFFSET_ATTR = 'jointsVisOffset'
    NODES_LOCAL_VIS_OFFSET_ATTR = 'nodesLocalVisOffset'
    NODES_WORLD_VIS_OFFSET_ATTR = 'nodesWorldVisOffset'
    CONTROLS_VIS_OUTPUT_ATTR = 'controlsVisOutput'
    JOINTS_VIS_OUTPUT_ATTR = 'jointsVisOutput'
    NODES_LOCAL_VIS_OUTPUT_ATTR = 'nodesLocalVisOutput'
    NODES_WORLD_VIS_OUTPUT_ATTR = 'nodesWorldVisOutput'
    INPUT_MATRIX_ATTR = 'inputMatrix'
    OFFSET_MATRIX_ATTR = 'offsetMatrix'
    INPUT_INVERSE_MATRIX_ATTR = 'inputInverseMatrix'
    # output attributes
    CONTROLS_ATTR = 'controls'
    JOINTS_ATTR = 'joints'
    SETUP_NODES_ATTR = 'setupNodes'
    OUTPUT_MATRIX_ATTR = 'outputMatrix'
    CONTROL_MATRIX_ATTR = 'controlMatrix'

    def __init__(self, **kwargs):
        super(CoreLimb, self).__init__(**kwargs)
        # limb kwargs
        self._guide_joints = kwargs.get('guide_joints', [])
        self._create_joints = kwargs.get('create_joints', True)
        # control kwargs
        self._control_size = kwargs.get('control_size', 1)
        self._control_color = kwargs.get('control_color', None)
        self._control_shape = kwargs.get('control_shape', 'cube')
        self._tag_control = kwargs.get('tag_control', True)
        self._control_additional_description = kwargs.get('control_additional_description', None)

        # override node type
        self._node_type = 'rigLimb'

        # group nodes
        self._local_group = None
        self._controls_group = None
        self._joints_group = None
        self._setup_group = None
        self._nodes_show_group = None
        self._nodes_hide_group = None
        self._nodes_world_group = None
        self._rig_nodes_group = None

        # variables
        self._joints = []
        self._controls = []
        self._setup_nodes = []
        self._input_matrix_attr = None
        self._offset_matrix_attr = None
        self._input_inverse_matrix_attr = None
        self._output_matrix_attr = None
        self._setup_matrix_attr = None
        self._control_matrix_attr = None

        self._controls_vis_attr = None
        self._joints_vis_attr = None
        self._nodes_local_vis_attr = None
        self._nodes_world_vis_attr = None

        self._controls_vis_offset_attr = None
        self._joints_vis_offset_attr = None
        self._nodes_local_vis_offset_attr = None
        self._nodes_world_vis_offset_attr = None

        self._controls_vis_output_attr = None
        self._joints_vis_output_attr = None
        self._nodes_local_vis_output_attr = None
        self._nodes_world_vis_output_attr = None

        # connection
        self._input_matrix = None
        self._offset_matrix = None
        self._tag_parent = None

    @property
    def joints(self):
        return self._joints

    @property
    def controls(self):
        return self._controls

    @property
    def setup_nodes(self):
        return self._setup_nodes

    @property
    def input_matrix_attr(self):
        return self._input_matrix_attr

    @property
    def offset_matrix_attr(self):
        return self._offset_matrix_attr

    @property
    def input_inverse_matrix_attr(self):
        return self._input_inverse_matrix_attr

    @property
    def output_matrix_attr(self):
        return self._output_matrix_attr

    @property
    def control_matrix_attr(self):
        return self._control_matrix_attr

    @property
    def controls_vis_attr(self):
        return self._controls_vis_attr

    @property
    def joints_vis_attr(self):
        return self._joints_vis_attr

    @property
    def nodes_local_vis_attr(self):
        return self._nodes_local_vis_attr

    @property
    def nodes_world_vis_attr(self):
        return self._nodes_world_vis_attr

    @property
    def controls_vis_offset_attr(self):
        return self._controls_vis_offset_attr

    @property
    def joints_vis_offset_attr(self):
        return self._joints_vis_offset_attr

    @property
    def nodes_local_vis_offset_attr(self):
        return self._nodes_local_vis_offset_attr

    @property
    def nodes_world_vis_offset_attr(self):
        return self._nodes_world_vis_offset_attr

    def create_hierarchy(self):
        super(CoreLimb, self).create_hierarchy()
        # create node groups
        # local group
        self._local_group = transformUtils.create(namingUtils.update(self._node, type='localGroup'),
                                                  lock_hide=attributeUtils.ALL, parent=self._node)
        # controls group
        self._controls_group = transformUtils.create(namingUtils.update(self._node, type='controlsGroup'),
                                                     lock_hide=attributeUtils.ALL, parent=self._local_group)
        # joints group
        self._joints_group = transformUtils.create(namingUtils.update(self._node, type='jointsGroup'),
                                                   lock_hide=attributeUtils.ALL, parent=self._local_group,
                                                   visibility=False)

        # setup group
        self._setup_group = transformUtils.create(namingUtils.update(self._node, type='setupGroup'),
                                                  lock_hide=attributeUtils.ALL, parent=self._local_group,
                                                  visibility=False)

        # nodes show group
        self._nodes_show_group = transformUtils.create(namingUtils.update(self._node, type='nodesShowGroup'),
                                                       lock_hide=attributeUtils.ALL, parent=self._local_group)
        # nodes hide group
        self._nodes_hide_group = transformUtils.create(namingUtils.update(self._node, type='nodesHideGroup'),
                                                       lock_hide=attributeUtils.ALL, parent=self._local_group,
                                                       visibility=False)

        # nodes world group
        self._nodes_world_group = transformUtils.create(namingUtils.update(self._node, type='nodesWorldGroup'),
                                                        lock_hide=attributeUtils.ALL, parent=self._node,
                                                        visibility=False)

        # rig nodes group
        self._rig_nodes_group = transformUtils.create(namingUtils.update(self._node, type='rigNodesGroup'),
                                                      lock_hide=attributeUtils.ALL, parent=self._node,
                                                      visibility=True)

    def register_inputs(self):
        super(CoreLimb, self).register_inputs()
        # visibility switch for controls, joints, rig nodes local, rig nodes world
        vis_attrs = attributeUtils.add(self._input_node,
                                       [self.CONTROLS_VIS_ATTR, self.JOINTS_VIS_ATTR, self.NODES_LOCAL_VIS_ATTR,
                                        self.NODES_WORLD_VIS_ATTR],
                                       attribute_type='bool', default_value=[True, False, False, False], keyable=False,
                                       channel_box=True)
        # add offset visibility control so it can be plugged with master node
        vis_offset_attrs = attributeUtils.add(self._input_node,
                                              [self.CONTROLS_VIS_OFFSET_ATTR, self.JOINTS_VIS_OFFSET_ATTR,
                                               self.NODES_LOCAL_VIS_OFFSET_ATTR, self.NODES_WORLD_VIS_OFFSET_ATTR],
                                              attribute_type='bool', default_value=[True, True, True, True],
                                              keyable=False, channel_box=False)
        # add output visibility attrs
        vis_output_attrs = attributeUtils.add(self._input_node,
                                              [self.CONTROLS_VIS_OUTPUT_ATTR, self.JOINTS_VIS_OUTPUT_ATTR,
                                               self.NODES_LOCAL_VIS_OUTPUT_ATTR, self.NODES_WORLD_VIS_OUTPUT_ATTR],
                                              attribute_type='bool', default_value=[True, True, True, True],
                                              keyable=False, channel_box=False)
        # input matrix, offset matrix, input inverse matrix
        matrix_attrs = attributeUtils.add(self._input_node,
                                          [self.INPUT_MATRIX_ATTR, self.OFFSET_MATRIX_ATTR,
                                           self.INPUT_INVERSE_MATRIX_ATTR],
                                          attribute_type='matrix')

        # connect attributes
        # connect visibility attrs
        for vis_attr, offset_attr, output_attr, description, node in zip(vis_attrs, vis_offset_attrs, vis_output_attrs,
                                                                         [self.CONTROLS_VIS_ATTR, self.JOINTS_VIS_ATTR,
                                                                          self.NODES_LOCAL_VIS_ATTR,
                                                                          self.NODES_WORLD_VIS_ATTR],
                                                                         [self._controls_group, self._joints_group,
                                                                          self._nodes_hide_group,
                                                                          self._nodes_world_group]):
            nodeUtils.arithmetic.equation('{0}*{1}'.format(vis_attr, offset_attr),
                                          namingUtils.update(self._input_node, additional_description=description),
                                          connect_attr=output_attr)
            attributeUtils.connect(output_attr, '{0}.{1}'.format(node, attributeUtils.VISIBILITY))

        # connect vis switch to setup group
        attributeUtils.connect(vis_output_attrs[-2], attributeUtils.VISIBILITY, driven=self._setup_group)

        # connect input matrix to local group
        mult_matrix = namingUtils.update(self._input_node, type='multMatrix',
                                         additional_description=self.INPUT_MATRIX_ATTR)
        mult_matrix_attr = nodeUtils.matrix.mult_matrix(matrix_attrs[1], matrix_attrs[0], name=mult_matrix)
        constraintUtils.matrix_connect(mult_matrix_attr, self._local_group)

        # get inverse matrix attr
        nodeUtils.matrix.inverse_matrix(mult_matrix_attr,
                                        name=namingUtils.update(self._input_node,
                                                                additional_description=self.INPUT_INVERSE_MATRIX_ATTR),
                                        connect_attr=matrix_attrs[2])

        self._input_matrix_attr = matrix_attrs[0]
        self._offset_matrix_attr = matrix_attrs[1]
        self._input_inverse_matrix_attr = matrix_attrs[2]

        self._controls_vis_attr = vis_attrs[0]
        self._joints_vis_attr = vis_attrs[1]
        self._nodes_local_vis_attr = vis_attrs[2]
        self._nodes_world_vis_attr = vis_attrs[3]

        self._controls_vis_offset_attr = vis_offset_attrs[0]
        self._joints_vis_offset_attr = vis_offset_attrs[1]
        self._nodes_local_vis_offset_attr = vis_offset_attrs[2]
        self._nodes_world_vis_offset_attr = vis_offset_attrs[3]

        self._controls_vis_output_attr = vis_output_attrs[0]
        self._joints_vis_output_attr = vis_output_attrs[1]
        self._nodes_local_vis_output_attr = vis_output_attrs[2]
        self._nodes_world_vis_output_attr = vis_output_attrs[3]

    def register_outputs(self):
        super(CoreLimb, self).register_outputs()
        # controls list and joints list
        attributeUtils.add(self._output_node, [self.CONTROLS_ATTR, self.JOINTS_ATTR, self.SETUP_NODES_ATTR],
                           attribute_type='message', multi=True)
        # output matrices amd control matrices
        attributeUtils.add(self._output_node, [self.OUTPUT_MATRIX_ATTR, self.CONTROL_MATRIX_ATTR],
                           attribute_type='matrix', multi=True)
        # control message
        attributeUtils.connect_nodes_to_multi_attr(self._controls, self.CONTROLS_ATTR,
                                                   driver_attr=attributeUtils.MESSAGE, driven=self._output_node)
        # setup nodes messages
        attributeUtils.connect_nodes_to_multi_attr(self._setup_nodes, self.SETUP_NODES_ATTR,
                                                   driver_attr=attributeUtils.MESSAGE, driven=self._output_node)
        # joints message and output matrix
        attributeUtils.connect_nodes_to_multi_attr(self._joints, self.JOINTS_ATTR, driver_attr=attributeUtils.MESSAGE,
                                                   driven=self._output_node)
        attributeUtils.connect_nodes_to_multi_attr(self._joints, self.OUTPUT_MATRIX_ATTR,
                                                   driver_attr=attributeUtils.WORLD_MATRIX, driven=self._output_node)

        self._output_matrix_attr = self.get_multi_attr_names(self.OUTPUT_MATRIX_ATTR, node=self._output_node)

        # control world matrix
        attributeUtils.connect_nodes_to_multi_attr(self._controls, self.CONTROL_MATRIX_ATTR,
                                                   driver_attr=controlUtils.WORLD_MATRIX_ATTR,
                                                   driven=self._output_node)
        self._control_matrix_attr = self.get_multi_attr_names(self.CONTROL_MATRIX_ATTR, node=self._output_node)

    def get_input_info(self):
        super(CoreLimb, self).get_input_info()
        self._input_matrix_attr = '{0}.{1}'.format(self._input_node, self.INPUT_MATRIX_ATTR)
        self._offset_matrix_attr = '{0}.{1}'.format(self._input_node, self.OFFSET_MATRIX_ATTR)
        self._input_inverse_matrix_attr = '{0}.{1}'.format(self._input_node, self.INPUT_INVERSE_MATRIX_ATTR)

        self._controls_vis_attr = '{0}.{1}'.format(self._input_node, self.CONTROLS_VIS_ATTR)
        self._joints_vis_attr = '{0}.{1}'.format(self._input_node, self.JOINTS_VIS_ATTR)
        self._nodes_local_vis_attr = '{0}.{1}'.format(self._input_node, self.NODES_LOCAL_VIS_ATTR)
        self._nodes_world_vis_attr = '{0}.{1}'.format(self._input_node, self.NODES_WORLD_VIS_ATTR)

        self._controls_vis_offset_attr = '{0}.{1}'.format(self._input_node, self.CONTROLS_VIS_OFFSET_ATTR)
        self._joints_vis_offset_attr = '{0}.{1}'.format(self._input_node, self.JOINTS_VIS_OFFSET_ATTR)
        self._nodes_local_vis_offset_attr = '{0}.{1}'.format(self._input_node, self.NODES_LOCAL_VIS_OFFSET_ATTR)
        self._nodes_world_vis_offset_attr = '{0}.{1}'.format(self._input_node, self.NODES_WORLD_VIS_OFFSET_ATTR)

        self._controls_vis_output_attr = '{0}.{1}'.format(self._input_node, self.CONTROLS_VIS_OUTPUT_ATTR)
        self._joints_vis_output_attr = '{0}.{1}'.format(self._input_node, self.JOINTS_VIS_OUTPUT_ATTR)
        self._nodes_local_vis_output_attr = '{0}.{1}'.format(self._input_node, self.NODES_LOCAL_VIS_OUTPUT_ATTR)
        self._nodes_world_vis_output_attr = '{0}.{1}'.format(self._input_node, self.NODES_WORLD_VIS_OUTPUT_ATTR)

    def get_output_info(self):
        super(CoreLimb, self).get_output_info()
        self._joints = self.get_multi_attr_value(self.JOINTS_ATTR, node=self._output_node)
        self._controls = self.get_multi_attr_value(self.CONTROLS_ATTR, node=self._output_node)
        self._setup_nodes = self.get_multi_attr_value(self.SETUP_NODES_ATTR, node=self._output_node)
        self._output_matrix_attr = self.get_multi_attr_names(self.OUTPUT_MATRIX_ATTR, node=self._output_node)
        self._control_matrix_attr = self.get_multi_attr_names(self.CONTROL_MATRIX_ATTR, node=self._output_node)

    def connect_inputs(self):
        super(CoreLimb, self).connect_inputs()
        if self._input_matrix:
            # get matrix
            input_matrix = cmds.getAttr(self._input_matrix)
            # compute offset matrix
            offset_matrix = mathUtils.matrix.localize(mathUtils.matrix.IDENTITY, input_matrix, output_type='list')
            # set offset matrix
            cmds.setAttr(self._offset_matrix_attr, offset_matrix, type='matrix')
            # connect input matrix
            attributeUtils.connect(self._input_matrix, self._input_matrix_attr)

        if self._offset_matrix:
            if isinstance(self._offset_matrix, basestring):
                attributeUtils.connect(self._offset_matrix, self._offset_matrix_attr)
            else:
                cmds.setAttr(self._offset_matrix_attr, self._offset_matrix, type='matrix')

        if self._tag_control:
            self.tag_controllers()
        
    def get_connection_kwargs(self, **kwargs):
        super(CoreLimb, self).get_connection_kwargs(**kwargs)
        # connection kwargs
        self._input_matrix = kwargs.get('input_matrix', None)
        self._offset_matrix = kwargs.get('offset_matrix', None)
        self._tag_parent = kwargs.get('tag_parent', None)

    def tag_controllers(self):
        tag_parent = self._tag_parent
        for ctrl in self._controls:
            controlUtils.set_tag_parent(ctrl, tag_parent)
            tag_parent = ctrl

    def create_node(self):
        super(CoreLimb, self).create_node()
        if self._create_joints:
            self.create_joints()
        self.create_controls()
        self.create_setup()
        if self._create_joints:
            self.connect_to_joints()

    def create_joints(self):
        self._joints = namingUtils.update_sequence(self._guide_joints, type='joint',
                                                   additional_description=self._additional_description)
        self._joints = jointUtils.create_chain(self._guide_joints, self._joints, parent_node=self._joints_group)

    def create_controls(self):
        pass

    def create_setup(self):
        self.create_setup_nodes()

    def create_setup_nodes(self):
        pass

    def connect_to_joints(self):
        pass

    def _add_obj_attr(self, attr, attr_dict):
        attr_split = attr.split('.')
        attr_parent = self
        if len(attr_split) > 1:
            for a in attr_split[:-1]:
                attr_parent = getattr(attr_parent, a)
        setattr(attr_parent, attr_split[-1], ObjectView(attr_dict))


class ObjectView(object):
    def __init__(self, kwargs):
        self.__dict__ = kwargs
