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
    """
    limb template class, all rig limbs should sub-class from this class
    """
    # vis switch attributes
    CONTROLS_VIS_ATTR = 'controlsVis'
    JOINTS_VIS_ATTR = 'jointsVis'
    NODES_VIS_ATTR = 'nodesVis'
    # vis switch offsets
    CONTROLS_VIS_OFFSET_ATTR = 'controlsVisOffset'
    JOINTS_VIS_OFFSET_ATTR = 'jointsVisOffset'
    NODES_VIS_OFFSET_ATTR = 'nodesVisOffset'
    # vis switch outputs
    CONTROLS_VIS_OUTPUT_ATTR = 'controlsVisOutput'
    JOINTS_VIS_OUTPUT_ATTR = 'jointsVisOutput'
    NODES_VIS_OUTPUT_ATTR = 'nodesVisOutput'
    # input attributes
    INPUT_MATRIX_ATTR = 'inputMatrix'
    OFFSET_MATRIX_ATTR = 'offsetMatrix'
    INPUT_INVERSE_MATRIX_ATTR = 'inputInverseMatrix'
    # output attributes
    CONTROLS_ATTR = 'controls'
    JOINTS_ATTR = 'joints'
    SETUP_NODES_ATTR = 'setupNodes'
    OUTPUT_WORLD_MATRIX_ATTR = 'outputWorldMatrix'
    OUTPUT_LOCAL_MATRIX_ATTR = 'outputLocalMatrix'

    def __init__(self, **kwargs):
        super(CoreLimb, self).__init__(**kwargs)
        # override node type
        self._node_type = 'rigLimb'

        # hierarchy groups
        self._local_group = None
        self._controls_group = None
        self._joints_group = None
        self._setup_group = None
        self._nodes_show_group = None
        self._nodes_hide_group = None
        self._nodes_world_group = None
        self._sub_nodes_group = None

        # limb info
        self._joints = []
        self._controls = []
        self._setup_nodes = []

        # place holders for attributes
        # vis switch attributes
        self._controls_vis_attr = None
        self._joints_vis_attr = None
        self._nodes_vis_attr = None
        # vis offset attributes
        self._controls_vis_offset_attr = None
        self._joints_vis_offset_attr = None
        self._nodes_vis_offset_attr = None
        # vis output attributes
        self._controls_vis_output_attr = None
        self._joints_vis_output_attr = None
        self._nodes_vis_output_attr = None
        # input attributes
        self._input_matrix_attr = None
        self._offset_matrix_attr = None
        self._input_inverse_matrix_attr = None
        # output attributes
        self._output_world_matrix_attrs = None
        self._output_local_matrix_attrs = None

        # place holder for kwargs
        # build kwargs
        self._guide_joints = None
        self._create_joints = None
        self._tag_controls = None
        # connection kwargs
        self._input_matrix = None
        self._offset_matrix = None
        self._tag_parent = None

    # property
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
    def controls_vis_attr(self):
        return self._controls_vis_attr

    @property
    def joints_vis_attr(self):
        return self._joints_vis_attr

    @property
    def nodes_vis_attr(self):
        return self._nodes_vis_attr

    @property
    def controls_vis_offset_attr(self):
        return self._controls_vis_offset_attr

    @property
    def joints_vis_offset_attr(self):
        return self._joints_vis_offset_attr

    @property
    def nodes_vis_offset_attr(self):
        return self._nodes_vis_offset_attr

    @property
    def controls_vis_output_attr(self):
        return self._controls_vis_output_attr

    @property
    def joints_vis_output_attr(self):
        return self._joints_vis_output_attr

    @property
    def nodes_vis_output_attr(self):
        return self._nodes_vis_output_attr

    @property
    def input_matrix_attr(self):
        return self._input_matrix_attr

    @property
    def offset_matrix_attr(self):
        return self._offset_matrix_attr

    @property
    def output_world_matrix_attrs(self):
        return self._output_world_matrix_attrs

    @property
    def output_local_matrix_attrs(self):
        return self._output_local_matrix_attrs

    # get kwargs
    def get_build_kwargs(self, **kwargs):
        super(CoreLimb, self).get_build_kwargs(**kwargs)
        # limb kwargs
        self._guide_joints = kwargs.get('guide_joints', [])
        self._create_joints = kwargs.get('create_joints', True)
        # control kwargs
        self._tag_controls = kwargs.get('tag_controls', True)

    def flip_build_kwargs(self):
        super(CoreLimb, self).flip_build_kwargs()
        self._create_joints = namingUtils.flip_names(self._guide_joints)

    def get_connect_kwargs(self, **kwargs):
        super(CoreLimb, self).get_connect_kwargs(**kwargs)
        self._input_matrix = kwargs.get('input_matrix', None)
        self._offset_matrix = kwargs.get('offset_matrix', None)
        self._tag_parent = kwargs.get('tag_parent', None)

    def flip_connect_kwargs(self):
        super(CoreLimb, self).flip_connect_kwargs()
        self._input_matrix = namingUtils.flip_names(self._input_matrix)
        self._offset_matrix = namingUtils.flip_names(self._offset_matrix)
        self._tag_parent = namingUtils.flip_names(self._tag_parent)

    # register steps to sections
    def register_steps(self):
        super(CoreLimb, self).register_steps()
        self.add_build_step('tag controllers', self.tag_controllers, 'connect')

    # build functions
    def create_hierarchy(self):
        super(CoreLimb, self).create_hierarchy()
        # local group
        self._local_group = transformUtils.create(namingUtils.update(self._node, type='localGroup'),
                                                  lock_hide=attributeUtils.ALL, parent=self._compute_node)
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
                                                        lock_hide=attributeUtils.ALL, parent=self._compute_node,
                                                        visibility=False)

        # rig nodes group
        self._sub_nodes_group = transformUtils.create(namingUtils.update(self._node, type='subNodesGroup'),
                                                      lock_hide=attributeUtils.ALL, parent=self._compute_node,
                                                      visibility=True)

    def add_input_attributes(self):
        super(CoreLimb, self).add_input_attributes()
        # add vis attrs
        vis_attrs = attributeUtils.add(self._input_node,
                                       [self.CONTROLS_VIS_ATTR, self.JOINTS_VIS_ATTR, self.NODES_VIS_ATTR],
                                       attribute_type='bool', default_value=[True, False, False],
                                       keyable=False, channel_box=True)

        offset_attrs = attributeUtils.add(self._input_node,
                                          [self.CONTROLS_VIS_OFFSET_ATTR, self.JOINTS_VIS_OFFSET_ATTR,
                                           self.NODES_VIS_OFFSET_ATTR],
                                          attribute_type='bool', default_value=True, keyable=False, channel_box=False)

        output_attrs = attributeUtils.add(self._input_node,
                                          [self.CONTROLS_VIS_OUTPUT_ATTR, self.JOINTS_VIS_OUTPUT_ATTR,
                                           self.NODES_VIS_OUTPUT_ATTR],
                                          attribute_type='bool', default_value=True, keyable=False, channel_box=False)

        # input matrices
        matrix_attrs = attributeUtils.add(self._input_node,
                                          [self.INPUT_MATRIX_ATTR, self.OFFSET_MATRIX_ATTR,
                                           self.INPUT_INVERSE_MATRIX_ATTR],
                                          attribute_type='matrix')

        # connect vis attr, offset attr to output attr
        for vis_attr, offset_attr, output_attr, description in zip(vis_attrs, offset_attrs, output_attrs,
                                                                   ['controlsVis', 'jointsVis', 'nodesVis']):
            nodeUtils.arithmetic.equation('{0}*{1}'.format(vis_attr, offset_attr),
                                          namingUtils.update(self._input_node, additional_description=description),
                                          connect_attr=output_attr)

        # connect output attr to groups vis attribute
        attributeUtils.connect(output_attrs[0], attributeUtils.VISIBILITY, driven=self._controls_group)
        attributeUtils.connect(output_attrs[1], attributeUtils.VISIBILITY, driven=self._joints_group)
        attributeUtils.connect(output_attrs[2], ['{0}.{1}'.format(self._nodes_hide_group, attributeUtils.VISIBILITY),
                                                 '{0}.{1}'.format(self._nodes_world_group, attributeUtils.VISIBILITY),
                                                 '{0}.{1}'.format(self._sub_nodes_group, attributeUtils.VISIBILITY)])

        # connect input matrix to local group
        mult_matrix_node = namingUtils.update(self._input_node, type='multMatrix', additional_description='inputMatrix')
        mult_matrix_attr = nodeUtils.matrix.mult_matrix(matrix_attrs[1], matrix_attrs[0], name=mult_matrix_node)
        constraintUtils.matrix_connect(mult_matrix_attr, self._local_group)

        # connect input inverse matrix
        nodeUtils.matrix.inverse_matrix(mult_matrix_attr,
                                        name=namingUtils.update(self._input_node,
                                                                additional_description=self.INPUT_INVERSE_MATRIX_ATTR),
                                        connect_attr=matrix_attrs[2])

        # store attributes
        # vis switch attributes
        self._controls_vis_attr = vis_attrs[0]
        self._joints_vis_attr = vis_attrs[1]
        self._nodes_vis_attr = vis_attrs[2]
        # vis offset attributes
        self._controls_vis_offset_attr = offset_attrs[0]
        self._joints_vis_offset_attr = offset_attrs[1]
        self._nodes_vis_offset_attr = offset_attrs[2]
        # vis output attributes
        self._controls_vis_output_attr = output_attrs[0]
        self._joints_vis_output_attr = output_attrs[1]
        self._nodes_vis_output_attr = output_attrs[2]
        # input matrix attributes
        self._input_matrix_attr = matrix_attrs[0]
        self._offset_matrix_attr = matrix_attrs[1]
        self._input_inverse_matrix_attr = matrix_attrs[2]

    def create_node(self):
        super(CoreLimb, self).create_node()
        self.create_controls()
        self.create_setup()
        if self.create_joints():
            self.create_joints()
            self.connect_to_joints()

    def create_controls(self):
        pass

    def create_setup(self):
        self.create_setup_nodes()

    def create_setup_nodes(self):
        pass

    def create_joints(self):
        self._joints = namingUtils.update_sequence(self._guide_joints, type='joint',
                                                   additional_description=self._additional_description)
        self._joints = jointUtils.create_chain(self._guide_joints, self._joints, parent_node=self._joints_group)

    def connect_to_joints(self):
        pass

    def add_output_attributes(self):
        super(CoreLimb, self).add_output_attributes()
        # controls list and joints list
        attributeUtils.add(self._output_node, [self.CONTROLS_ATTR, self.JOINTS_ATTR, self.SETUP_NODES_ATTR],
                           attribute_type='message', multi=True)
        # output matrices
        attributeUtils.add(self._output_node, [self.OUTPUT_WORLD_MATRIX_ATTR, self.OUTPUT_LOCAL_MATRIX_ATTR],
                           attribute_type='matrix', multi=True)

        # add limb info to output attributes
        # control message
        attributeUtils.connect_nodes_to_multi_attr(self._controls, self.CONTROLS_ATTR,
                                                   driver_attr=attributeUtils.MESSAGE, driven=self._output_node)
        # setup nodes messages
        attributeUtils.connect_nodes_to_multi_attr(self._setup_nodes, self.SETUP_NODES_ATTR,
                                                   driver_attr=attributeUtils.MESSAGE, driven=self._output_node)
        # joints message
        attributeUtils.connect_nodes_to_multi_attr(self._joints, self.JOINTS_ATTR, driver_attr=attributeUtils.MESSAGE,
                                                   driven=self._output_node)
        # output world matrix
        attributeUtils.connect_nodes_to_multi_attr(self._joints, self.OUTPUT_WORLD_MATRIX_ATTR,
                                                   driver_attr=attributeUtils.WORLD_MATRIX, driven=self._output_node)
        # output local matrix
        if self._joints:
            cmds.connectAttr('{0}.{1}'.format(self._joints[0], attributeUtils.MATRIX),
                             '{0}.{1}[0]'.format(self._output_node, self.OUTPUT_LOCAL_MATRIX_ATTR))
            if len(self._joints) > 1:
                parent_matrix_attr = '{0}.{1}'.format(self._joints[0], attributeUtils.MATRIX)
                for i, jnt in enumerate(self._joints[1:]):
                    mult_matrix = namingUtils.update(jnt, type='multMatirx', additional_description='localMatrix')
                    matrix_attr = nodeUtils.matrix.mult_matrix('{0}.{1}'.format(jnt, attributeUtils.MATRIX),
                                                               parent_matrix_attr, name=mult_matrix)
                    cmds.connectAttr(matrix_attr, '{0}{1}[{2}]'.format(self._output_node, self.OUTPUT_LOCAL_MATRIX_ATTR,
                                                                       i + 1))
                    parent_matrix_attr = matrix_attr

        self._output_world_matrix_attrs = self.get_multi_attr_names(self.OUTPUT_WORLD_MATRIX_ATTR,
                                                                    node=self._output_node)
        self._output_local_matrix_attrs = self.get_multi_attr_names(self.OUTPUT_LOCAL_MATRIX_ATTR,
                                                                    node=self._output_node)

    # connect functions
    def connect_input_attributes(self):
        super(CoreLimb, self).connect_input_attributes()
        if self._input_matrix:
            # get input matrix value
            input_matrix_val = cmds.getAttr(self._input_matrix)
            # compute offset matrix
            offset_matrix_val = mathUtils.matrix.localize(mathUtils.matrix.IDENTITY, input_matrix_val,
                                                          output_type='list')
            # set offset matrix
            cmds.setAttr(self._offset_matrix_attr, offset_matrix_val, type='matrix')
            # connect input matrix
            attributeUtils.connect(self._input_matrix, self._input_matrix_attr)

        if self._offset_matrix and isinstance(self._offset_matrix, basestring):
            attributeUtils.connect(self._offset_matrix, self._offset_matrix_attr)

    def tag_controllers(self):
        if self._tag_controls:
            tag_parent = self._tag_parent
            for ctrl in self._controls:
                controlUtils.add_tag(ctrl, tag_parent)
                tag_parent = ctrl

    # get node info
    def get_input_info(self):
        super(CoreLimb, self).get_input_info()
        # vis switch attributes
        self._controls_vis_attr = '{0}.{1}'.format(self._input_node, self.CONTROLS_VIS_ATTR)
        self._joints_vis_attr = '{0}.{1}'.format(self._input_node, self.JOINTS_VIS_ATTR)
        self._nodes_vis_attr = '{0}.{1}'.format(self._input_node, self.NODES_VIS_ATTR)
        # vis offset attributes
        self._controls_vis_offset_attr = '{0}.{1}'.format(self._input_node, self.CONTROLS_VIS_OFFSET_ATTR)
        self._joints_vis_offset_attr = '{0}.{1}'.format(self._input_node, self.JOINTS_VIS_OFFSET_ATTR)
        self._nodes_vis_offset_attr = '{0}.{1}'.format(self._input_node, self.NODES_VIS_OFFSET_ATTR)
        # vis output attributes
        self._controls_vis_output_attr = '{0}.{1}'.format(self._input_node, self.CONTROLS_VIS_OUTPUT_ATTR)
        self._joints_vis_output_attr = '{0}.{1}'.format(self._input_node, self.JOINTS_VIS_OUTPUT_ATTR)
        self._nodes_vis_output_attr = '{0}.{1}'.format(self._input_node, self.NODES_VIS_OUTPUT_ATTR)
        # input attributes
        self._input_matrix_attr = '{0}.{1}'.format(self._input_node, self.INPUT_MATRIX_ATTR)
        self._offset_matrix_attr = '{0}.{1}'.format(self._input_node, self.OFFSET_MATRIX_ATTR)
        self._input_inverse_matrix_attr = '{0}.{1}'.format(self._input_node, self.INPUT_INVERSE_MATRIX_ATTR)

    def get_output_info(self):
        super(CoreLimb, self).get_output_info()
        self._joints = self.get_multi_attr_value(self.JOINTS_ATTR, node=self._output_node)
        self._controls = self.get_multi_attr_value(self.CONTROLS_ATTR, node=self._output_node)
        self._setup_nodes = self.get_multi_attr_value(self.SETUP_NODES_ATTR, node=self._output_node)
        self._output_world_matrix_attrs = self.get_multi_attr_names(self.OUTPUT_WORLD_MATRIX_ATTR,
                                                                    node=self._output_node)
        self._output_local_matrix_attrs = self.get_multi_attr_names(self.OUTPUT_LOCAL_MATRIX_ATTR,
                                                                    node=self._output_node)
