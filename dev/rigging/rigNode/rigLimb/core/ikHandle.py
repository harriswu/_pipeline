import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils
import utils.rigging.jointUtils as jointUtils
import coreLimb as coreLimb


class IkHandle(coreLimb.CoreLimb):
    """
    ik limb template class, all ik limbs should sub-class from this class
    """
    # ik attributes
    IKS_ATTR = 'iks'
    IK_GROUPS_ATTR = 'ikGroups'
    
    def __init__(self, **kwargs):
        super(IkHandle, self).__init__(**kwargs)
        # set ik type
        self._ik_type = 'ikSCsolver'

        # ik info
        self._iks = []
        self._ik_groups = []

    # build functions
    def create_setup(self):
        super(IkHandle, self).create_setup()
        self.create_ik()
        self.connect_ik()

    def create_setup_nodes(self):
        super(IkHandle, self).create_setup_nodes()
        self._setup_nodes = namingUtils.update_sequence(self._guide_joints, type='joint',
                                                        additional_description=self._additional_description + ['setup'])
        jointUtils.create_chain(self._guide_joints, self._setup_nodes, parent_node=self._setup_group)

    def create_ik(self):
        # create ik handle
        ik_handle = cmds.ikHandle(startJoint=self._setup_nodes[0], endEffector=self._setup_nodes[-1],
                                  solver=self._ik_type, name=namingUtils.update(self._node, type='ikHandle'))[0]
        cmds.parent(ik_handle, self._nodes_hide_group)
        # append list
        self._iks.append(ik_handle)

    def connect_ik(self):
        # add offset group for ik handles
        for ik in self._iks:
            zero = transformUtils.offset_group(ik, name=namingUtils.update(ik, type='zero'))
            self._ik_groups.append(zero)

    def connect_to_joints(self):
        super(IkHandle, self).connect_to_joints()
        for setup_jnt, jnt in zip(self._setup_nodes, self._joints):
            attributeUtils.connect(attributeUtils.TRANSFORM, attributeUtils.TRANSFORM,
                                   driver=setup_jnt, driven=jnt)

    def add_output_attributes(self):
        super(IkHandle, self).add_output_attributes()
        attributeUtils.add(self._output_node, [self.IKS_ATTR, self.IK_GROUPS_ATTR], attribute_type='message',
                           multi=True)

        # connect ik info to attributes
        attributeUtils.connect_nodes_to_multi_attr(self._iks, self.IKS_ATTR, driver_attr=attributeUtils.MESSAGE,
                                                   driven=self._output_node)
        attributeUtils.connect_nodes_to_multi_attr(self._ik_groups, self.IK_GROUPS_ATTR,
                                                   driver_attr=attributeUtils.MESSAGE, driven=self._output_node)
