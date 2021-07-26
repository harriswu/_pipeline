import inspect

import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils
import utils.rigging.controlUtils as controlUtils

import dev.rigging.rigNode.core.coreNode as coreNode


class Master(coreNode.CoreNode):
    GEOMETRY_VIS_ATTR = 'geometryVis'
    CONTROLS_VIS_ATTR = 'controlsVis'
    SKELETON_VIS_ATTR = 'skeletonVis'
    JOINTS_VIS_ATTR = 'jointsVis'
    NODES_VIS_ATTR = 'nodesVis'
    GEOMETRY_DISPLAY_TYPE_ATTR = 'geometryDisplayType'
    OUT_MATRIX_ATTR = 'outMatrix'
    NODE_PATH_ATTR = 'nodePath'
    CONTROLS_ATTR = 'controls'

    LAYOUT_CONTROL_VIS_ATTR = 'layoutCtrlVis'
    LOCAL_CONTROL_VIS_ATTR = 'localCtrlVis'

    GEOMETRY_GROUP_ATTR = 'geometryGroup'
    CONTROLS_GROUP_ATTR = 'controlsGroup'
    SKELETON_GROUP_ATTR = 'skeletonGroup'
    LIMBS_GROUP_ATTR = 'limbsGroup'
    SPACES_GROUP_ATTR = 'spacesGroup'

    def __init__(self):
        super(Master, self).__init__()

        self._node_path = inspect.getmodule(self.__class__).__name__

        self._master_group = None
        self._geometry_group = None
        self._controls_group = None
        self._skeleton_group = None
        self._limbs_group = None
        self._spaces_group = None

        self._world_control = None
        self._layout_control = None
        self._local_control = None

        self._geometry_vis_attr = None
        self._geometry_display_type_attr = None
        self._controls_vis_attr = None
        self._skeleton_vis_attr = None
        self._joints_vis_attr = None
        self._nodes_vis_attr = None

        self._node_path_attr = None

        self._controls_attr = None

        self._out_matrix_attr = None

        self._geometry_group_attr = None
        self._controls_group_attr = None
        self._skeleton_group_attr = None
        self._limbs_group_attr = None
        self._spaces_group_attr = None

    @property
    def node(self):
        return self._master_group

    @node.setter
    def node(self, value):
        self._master_group = value

    @property
    def geometry_group(self):
        return self._geometry_group

    @property
    def controls_group(self):
        return self._controls_group

    @property
    def skeleton_group(self):
        return self._skeleton_group

    @property
    def space_group(self):
        return self._spaces_group

    @property
    def limbs_group(self):
        return self._limbs_group

    @property
    def world_control(self):
        return self._world_control

    @property
    def layout_control(self):
        return self._layout_control

    @property
    def local_control(self):
        return self._local_control

    @property
    def geometry_vis_attr(self):
        return self._geometry_vis_attr

    @property
    def geometry_display_type_attr(self):
        return self._geometry_display_type_attr

    @property
    def controls_vis_attr(self):
        return self._controls_vis_attr

    @property
    def skeleton_vis_attr(self):
        return self._skeleton_vis_attr

    @property
    def joints_vis_attr(self):
        return self._joints_vis_attr

    @property
    def nodes_vis_attr(self):
        return self._nodes_vis_attr

    @property
    def out_matrix_attr(self):
        return self._out_matrix_attr

    def create_hierarchy(self):
        """
        create master node's hierarchy
        """
        self._master_group = transformUtils.create(namingUtils.compose(type='master'),
                                                   lock_hide=attributeUtils.ALL)
        self._geometry_group = transformUtils.create(namingUtils.compose(type='geometry'),
                                                     lock_hide=attributeUtils.ALL, parent=self._master_group)
        self._controls_group = transformUtils.create(namingUtils.compose(type='controls'),
                                                     lock_hide=attributeUtils.ALL, parent=self._master_group)
        self._skeleton_group = transformUtils.create(namingUtils.compose(type='skeleton'),
                                                     lock_hide=attributeUtils.ALL, parent=self._master_group)
        self._limbs_group = transformUtils.create(namingUtils.compose(type='limbs'),
                                                  lock_hide=attributeUtils.ALL, parent=self._master_group)
        self._spaces_group = transformUtils.create(namingUtils.compose(type='spaces'),
                                                   lock_hide=attributeUtils.ALL, parent=self._master_group)

        self._node = self._master_group
        # register node path
        attributeUtils.add(self._master_group, self.NODE_PATH_ATTR, attribute_type='string',
                           default_value=self._node_path, lock_attr=True)

    def add_input_attributes(self):
        self._geometry_display_type_attr = attributeUtils.add(self._master_group, self.GEOMETRY_DISPLAY_TYPE_ATTR,
                                                              attribute_type='enum',
                                                              enum_name='Normal:Template:Reference',
                                                              default_value=2, keyable=False, channel_box=True)[0]
        vis_attrs = attributeUtils.add(self._master_group,
                                       [self.GEOMETRY_VIS_ATTR, self.CONTROLS_VIS_ATTR, self.SKELETON_VIS_ATTR,
                                        self.JOINTS_VIS_ATTR, self.NODES_VIS_ATTR],
                                       attribute_type='bool', default_value=[True, True, False, False, False],
                                       keyable=False, channel_box=True)

        self._geometry_vis_attr = vis_attrs[0]
        self._controls_vis_attr = vis_attrs[1]
        self._skeleton_vis_attr = vis_attrs[2]
        self._joints_vis_attr = vis_attrs[3]
        self._nodes_vis_attr = vis_attrs[4]

        # connect with each group
        attributeUtils.connect([self._geometry_vis_attr,
                                self._geometry_display_type_attr,
                                self._controls_vis_attr,
                                self._skeleton_vis_attr],
                               ['{0}.{1}'.format(self._geometry_group, attributeUtils.VISIBILITY),
                                self._geometry_group + '.overrideDisplayType',
                                '{0}.{1}'.format(self._controls_group, attributeUtils.VISIBILITY),
                                '{0}.{1}'.format(self._skeleton_group, attributeUtils.VISIBILITY)])

        cmds.setAttr(self._geometry_group + '.overrideEnabled', 1)

    def create_node(self):
        self._world_control = controlUtils.create('world', side='center', index=1, lock_hide=attributeUtils.SCALE,
                                                  tag=True, parent=self._controls_group)
        self._layout_control = controlUtils.create('layout', side='center', index=1, lock_hide=attributeUtils.SCALE,
                                                   parent=self._world_control,
                                                   input_matrix='{0}.{1}'.format(self._world_control,
                                                                                 controlUtils.HIERARCHY_MATRIX_ATTR),
                                                   tag=True, tag_parent=self._world_control)
        self._local_control = controlUtils.create('local', side='center', index=1, lock_hide=attributeUtils.SCALE,
                                                  parent=self._layout_control,
                                                  input_matrix='{0}.{1}'.format(self._layout_control,
                                                                                controlUtils.HIERARCHY_MATRIX_ATTR),
                                                  tag=True, tag_parent=self._layout_control)

        # add rig scale attribute
        for ctrl in [self._world_control, self._layout_control, self._local_control]:
            scale_attr = attributeUtils.add(ctrl, 'rigScale', attribute_type='float', value_range=[0, None],
                                            default_value=1)[0]
            attributeUtils.connect(scale_attr, attributeUtils.SCALE, driven=ctrl)

        # add vis switch for layout and local control
        attributeUtils.add(self._world_control, [self.LAYOUT_CONTROL_VIS_ATTR, self.LOCAL_CONTROL_VIS_ATTR],
                           attribute_type='bool', keyable=False, channel_box=True)
        attributeUtils.connect([self.LAYOUT_CONTROL_VIS_ATTR, self.LOCAL_CONTROL_VIS_ATTR],
                               ['{0}.{1}'.format(controlUtils.get_hierarchy_node(self._layout_control, 'zero'),
                                                 attributeUtils.VISIBILITY),
                                '{0}.{1}'.format(controlUtils.get_hierarchy_node(self._local_control, 'zero'),
                                                 attributeUtils.VISIBILITY)], driver=self._world_control)

    def add_output_attributes(self):
        self._out_matrix_attr = attributeUtils.add(self._master_group, self.OUT_MATRIX_ATTR, attribute_type='matrix')[0]

        message_attrs = attributeUtils.add(self._master_group,
                                           [self.GEOMETRY_GROUP_ATTR, self.CONTROLS_GROUP_ATTR,
                                            self.SKELETON_GROUP_ATTR, self.LIMBS_GROUP_ATTR,
                                            self.SPACES_GROUP_ATTR],
                                           attribute_type='message')

        self._controls_attr = attributeUtils.add(self._master_group, self.CONTROLS_ATTR, attribute_type='message',
                                                 multi=True)[0]

        self._geometry_group_attr = message_attrs[0]
        self._controls_group_attr = message_attrs[1]
        self._skeleton_group_attr = message_attrs[2]
        self._limbs_group_attr = message_attrs[3]
        self._spaces_group_attr = message_attrs[4]

        # connect with each group
        attributeUtils.connect(['{0}.{1}'.format(self._geometry_group, attributeUtils.MESSAGE),
                                '{0}.{1}'.format(self._skeleton_group, attributeUtils.MESSAGE),
                                '{0}.{1}'.format(self._limbs_group, attributeUtils.MESSAGE),
                                '{0}.{1}'.format(self._spaces_group, attributeUtils.MESSAGE)],
                               [self._geometry_group_attr, self._skeleton_group_attr, self._limbs_group_attr,
                                self._spaces_group_attr])

        # connect to out matrix
        attributeUtils.connect('{0}.{1}'.format(self._local_control, controlUtils.HIERARCHY_MATRIX_ATTR),
                               self._out_matrix_attr)
        # connect controller message
        attributeUtils.connect_nodes_to_multi_attr([self._world_control, self._layout_control, self._local_control],
                                                   self.CONTROLS_ATTR, driver_attr=attributeUtils.MESSAGE,
                                                   driven=self._master_group)

    def get_rig_node_info(self):
        self._geometry_group = self.get_single_attr_value(self.GEOMETRY_GROUP_ATTR, node=self._master_group)
        self._controls_group = self.get_single_attr_value(self.CONTROLS_GROUP_ATTR, node=self._master_group)
        self._skeleton_group = self.get_single_attr_value(self.SKELETON_GROUP_ATTR, node=self._master_group)
        self._limbs_group = self.get_single_attr_value(self.LIMBS_GROUP_ATTR, node=self._master_group)

        controls = self.get_multi_attr_value(self.CONTROLS_ATTR, node=self._master_group)
        self._world_control = controls[0]
        self._layout_control = controls[1]
        self._local_control = controls[2]

        self._geometry_vis_attr = '{0}.{1}'.format(self._master_group, self.GEOMETRY_VIS_ATTR)
        self._geometry_display_type_attr = '{0}.{1}'.format(self._master_group, self.GEOMETRY_DISPLAY_TYPE_ATTR)
        self._controls_vis_attr = '{0}.{1}'.format(self._master_group, self.CONTROLS_VIS_ATTR)
        self._skeleton_vis_attr = '{0}.{1}'.format(self._master_group, self.SKELETON_VIS_ATTR)
        self._joints_vis_attr = '{0}.{1}'.format(self._master_group, self.JOINTS_VIS_ATTR)
        self._nodes_vis_attr = '{0}.{1}'.format(self._master_group, self.NODES_VIS_ATTR)

        self._node_path = self.get_single_attr_value(self.NODE_PATH_ATTR, node=self._master_group)

        self._out_matrix_attr = '{0}.{1}'.format(self._master_group, self.OUT_MATRIX_ATTR)
