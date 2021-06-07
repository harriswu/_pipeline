import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.controlUtils as controlUtils

import dev.rigging.rigNode.rigLimb.base.rotatePlaneIk as rotatePlaneIk


class BipedArmIk(rotatePlaneIk.RotatePlaneIk):
    # constant attribute
    AUTO_CLAV_MATRIX_ATTR = 'autoClavMatrix'

    def __init__(self, **kwargs):
        super(BipedArmIk, self).__init__(**kwargs)
        self._auto_clav_matrix_attr = None
        self._local_ik_node = None

    @property
    def auto_clav_matrix(self):
        return cmds.getAttr(self._auto_clav_matrix_attr)

    @property
    def auto_clav_matrix_attr(self):
        return self._auto_clav_matrix_attr

    def create_setup(self):
        super(BipedArmIk, self).create_setup()
        self.create_local_ik()

    def create_local_ik(self):
        # create rotate plane ik
        name_info = namingUtils.decompose(self._node)
        self._local_ik_node = rotatePlaneIk.RotatePlaneIk(side=name_info['side'], description=name_info['description'],
                                                          index=name_info['index'], limb_index=name_info['limb_index'],
                                                          additional_description='local',
                                                          create_joints=False,
                                                          guide_joints=self._guide_joints,
                                                          input_matrix=self._input_matrix,
                                                          tag_control=False,
                                                          parent_node=self._rig_nodes_group)

        self._local_ik_node.build()
        self._local_ik_node.connect()

        # connect root joint translation
        cmds.connectAttr(self._setup_nodes[0] + '.translate', self._local_ik_node.setup_nodes[0] + '.translate')

        # loop into each ik group and ik and connect with auto clav ik chain
        for node_source, node_target in zip(self._ik_groups + self._iks,
                                            self._local_ik_node.ik_groups + self._local_ik_node.iks):
            attributeUtils.link_attrs(node_source, node_target, force=False)

    def register_outputs(self):
        super(BipedArmIk, self).register_outputs()
        self._auto_clav_matrix_attr = attributeUtils.add(self._output_node, self.AUTO_CLAV_MATRIX_ATTR,
                                                         attribute_type='matrix')

        nodeUtils.matrix.compose_matrix(namingUtils.update(self._local_ik_node.setup_nodes[0], type='composeMatrix',
                                                           additional_description='localMatrix'),
                                        rotate=['{0}.{1}'.format(self._local_ik_node.setup_nodes[0],
                                                                 attributeUtils.ROTATE[0]),
                                                '{0}.{1}'.format(self._local_ik_node.setup_nodes[0],
                                                                 attributeUtils.ROTATE[1]),
                                                '{0}.{1}'.format(self._local_ik_node.setup_nodes[0],
                                                                 attributeUtils.ROTATE[2])],
                                        rotate_order='{0}.{1}'.format(self._local_ik_node.setup_nodes[0],
                                                                      attributeUtils.ROTATE_ORDER),
                                        connect_attr=self._auto_clav_matrix_attr)

    def get_output_info(self):
        super(BipedArmIk, self).get_output_info()
        self._auto_clav_matrix_attr = '{0}.{1}'.format(self._output_node, self.AUTO_CLAV_MATRIX_ATTR)
