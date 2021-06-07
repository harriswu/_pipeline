import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils
import utils.common.hierarchyUtils as hierarchyUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.core.ikHandle as ikHandle


class MultiScIk(ikHandle.IkHandle):
    def __init__(self, **kwargs):
        super(MultiScIk, self).__init__(**kwargs)
        self._additional_description = kwargs.get('additional_description', 'multiScIk')

        self._ik_type = 'ikSCsolver'

    def create_ik(self):
        for i, jnt in enumerate(self._setup_nodes[:-1]):
            # create ik handle
            ik_handle = namingUtils.update(jnt, type='ikHandle')
            cmds.ikHandle(startJoint=jnt, endEffector=self._setup_nodes[i + 1], solver=self._ik_type, name=ik_handle)
            hierarchyUtils.parent(ik_handle, self._nodes_hide_group)
            self._iks.append(ik_handle)

    def connect_ik(self):
        # create transform group to control root position
        zero = transformUtils.create(namingUtils.update(self._setup_nodes[0], type='zero',
                                                        additional_description='root'),
                                     parent=self._nodes_hide_group, rotate_order=0, visibility=False,
                                     position=self._setup_nodes[0], inherits_transform=True)
        constraintUtils.position_constraint('{0}.{1}'.format(zero, attributeUtils.MATRIX), self._setup_nodes[0],
                                            maintain_offset=False, skip=attributeUtils.ROTATE)
        self._ik_groups.append(zero)

        # create transform group for each ik handle
        for ik_hnd, jnt in zip(self._iks, self._setup_nodes[1:]):
            zero = transformUtils.create(namingUtils.update(ik_hnd, type='zero', additional_description='ik'),
                                         parent=self._nodes_hide_group, rotate_order=0, visibility=False,
                                         position=jnt, inherits_transform=True)

            # parent ik under offset group
            cmds.parent(ik_hnd, zero)
            # append list
            self._ik_groups.append(zero)
