import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils
import utils.rigging.jointUtils as jointUtils
import coreLimb


class IkHandle(coreLimb.CoreLimb):
    # constant attributes
    IKS_ATTR = 'iks'
    IK_GROUPS_ATTR = 'ikGroups'

    def __init__(self, **kwargs):
        super(IkHandle, self).__init__(**kwargs)
        # naming kwargs
        self._additional_description = kwargs.get('additional_description', ['ik'])

        self._ik_type = 'ikSCsolver'

        self._iks = []
        self._ik_groups = []

    @property
    def iks(self):
        return self._iks

    @property
    def ik_groups(self):
        return self._ik_groups

    def register_outputs(self):
        super(IkHandle, self).register_outputs()
        attributeUtils.add(self._output_node, [self.IKS_ATTR, self.IK_GROUPS_ATTR], attribute_type='message',
                           multi=True)
        attributeUtils.connect_nodes_to_multi_attr(self._iks, self.IKS_ATTR, driver_attr=attributeUtils.MESSAGE,
                                                   driven=self._output_node)
        attributeUtils.connect_nodes_to_multi_attr(self._ik_groups, self.IK_GROUPS_ATTR,
                                                   driver_attr=attributeUtils.MESSAGE, driven=self._output_node)

    def create_setup(self):
        super(IkHandle, self).create_setup()
        self.create_ik()
        self.connect_ik()

    def create_setup_nodes(self):
        super(IkHandle, self).create_setup_nodes()
        if isinstance(self._additional_description, basestring):
            additional_description = [self._additional_description, 'setup']
        elif self._additional_description:
            additional_description = self._additional_description + ['setup']
        else:
            additional_description = 'setup'
        self._setup_nodes = namingUtils.update_sequence(self._guide_joints, type='joint',
                                                        additional_description=additional_description)

        self._setup_nodes = jointUtils.create_chain(self._guide_joints, self._setup_nodes,
                                                    parent_node=self._setup_group)

    def create_ik(self):
        # create ik handle
        ik_handle = namingUtils.compose(type='ikHandle', side=self._side, description=self._description,
                                        index=self._index, limb_index=self._limb_index,
                                        additional_description=self._additional_description)
        cmds.ikHandle(startJoint=self._setup_nodes[0], endEffector=self._setup_nodes[-1], solver=self._ik_type,
                      name=ik_handle)
        cmds.parent(ik_handle, self._nodes_hide_group)
        # append list
        self._iks.append(ik_handle)

    def connect_ik(self):
        # create transform group for ik handle
        zero = transformUtils.create(namingUtils.update(self._iks[0], type='zero'),
                                     parent=self._nodes_hide_group, rotate_order=0, visibility=False,
                                     position=self._setup_nodes[-1], inherits_transform=True)

        # parent ik under offset group
        cmds.parent(self._iks[0], zero)
        # append list
        self._ik_groups.append(zero)

    def connect_to_joints(self):
        super(IkHandle, self).connect_to_joints()
        for setup_jnt, jnt in zip(self._setup_nodes, self._joints):
            attributeUtils.connect(attributeUtils.TRANSFORM, attributeUtils.TRANSFORM,
                                   driver=setup_jnt, driven=jnt)

    def get_output_info(self):
        super(IkHandle, self).get_output_info()
        self._iks = self.get_multi_attr_value(self.IKS_ATTR, node=self._output_node)
        self._ik_groups = self.get_multi_attr_value(self.IK_GROUPS_ATTR, node=self._output_node)
