import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.mathUtils as mathUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.controlUtils as controlUtils

import aimFk
import dev.rigging.rigNode.rigUtility.base.poseReader as poseReader
import dev.rigging.rigNode.rigUtility.base.poseBlend as poseBlend


class Clavicle(aimFk.AimFk):
    DRIVER_MATRIX_ATTR = 'driverMatrix'

    def __init__(self, **kwargs):
        super(Clavicle, self).__init__(**kwargs)
        self._driver_matrix = None
        self._driver_vector = kwargs.get('driver_vector', [1, 0, 0])
        self._reference_points = kwargs.get('reference_points', [[0, 1, 0], [0, 0, 1], [0, -1, 0], [0, 0, -1]])
        self._poses = kwargs.get('poses', [])
        self._aim_distance_multiplier = kwargs.get('aim_distance_multiplier', 1)

        self._driver_matrix_attr = None
        self._piston_limb = None
        self._pose_reader_node = None
        self._pose_blend_node = None

    @property
    def driver_matrix_attr(self):
        return self._driver_matrix_attr

    def register_inputs(self):
        super(Clavicle, self).register_inputs()
        self._driver_matrix_attr = attributeUtils.add(self._input_node, self.DRIVER_MATRIX_ATTR,
                                                      attribute_type='matrix')

    def create_setup(self):
        super(Clavicle, self).create_setup()
        # create pose reader for auto clavicle
        name_info = namingUtils.decompose(self._node)
        self._pose_reader_node = poseReader.PoseReader(side=name_info['side'], description=name_info['description'],
                                                       index=name_info['index'], limb_index=name_info['limb_index'],
                                                       additional_description='autoClavDriver',
                                                       parent_node=self._rig_nodes_group,
                                                       driver_vector=self._driver_vector,
                                                       reference_points=self._reference_points)
        self._pose_reader_node.build()
        self._pose_reader_node.connect(input_matrix=self._driver_matrix_attr)

        # create pose blend node
        mult_matrix = namingUtils.update(self._node, type='multMatrix', additional_description='autoClavMtx')
        mult_matrix_attr = nodeUtils.matrix.mult_matrix('{0}.{1}'.format(self._piston_limb.setup_nodes[0],
                                                                         attributeUtils.MATRIX),
                                                        cmds.getAttr('{0}.{1}'.format(self._guide_joints[0],
                                                                                      attributeUtils.MATRIX)),
                                                        name=mult_matrix)

        self._pose_blend_node = poseBlend.PoseBlend(side=name_info['side'], description=name_info['description'],
                                                    index=name_info['index'], limb_index=name_info['limb_index'],
                                                    additional_description='autoClavPose',
                                                    parent_node=self._rig_nodes_group)
        self._pose_blend_node.build()

        self._pose_blend_node.connect(input_matrix=mult_matrix_attr, poses=self._poses,
                                      pose_weights=self._pose_reader_node.outputs_attr, translate=True, rotate=True,
                                      scale=False)

        # get connect node
        connect_node = controlUtils.get_hierarchy_node(self._controls[0], 'connect')
        # connect pose blend node's output to connect node
        attributeUtils.connect([self._pose_blend_node.output_translate, self._pose_blend_node.output_rotate],
                               [connect_node + '.translate', connect_node + '.rotate'])

    def get_connection_kwargs(self, **kwargs):
        super(Clavicle, self).get_connection_kwargs(**kwargs)
        self._driver_matrix = kwargs.get('driver_matrix', None)

    def connect_inputs(self):
        super(Clavicle, self).connect_inputs()
        if self._driver_matrix:
            attributeUtils.connect(self._driver_matrix, self._driver_matrix_attr)

        # get pose blend reference matrix
        driver_world_matrix = cmds.getAttr('{0}.{1}'.format(self._guide_joints[0], attributeUtils.WORLD_MATRIX))
        input_matrix = cmds.getAttr(self._input_matrix_attr)
        # get local matrix
        driver_local_matrix = mathUtils.matrix.localize(driver_world_matrix, input_matrix)
        # mult with input matrix to get reference matrix
        nodeUtils.matrix.mult_matrix(driver_local_matrix, self._input_matrix_attr,
                                     name=namingUtils.update(self._node, type='multMatrix',
                                                             additional_description='poseReferenceMatrix'),
                                     connect_attr=self._pose_blend_node.reference_matrix_attr)

    def get_input_info(self):
        super(Clavicle, self).get_input_info()
        self._driver_matrix_attr = '{0}.{1}'.format(self._input_node, self.DRIVER_MATRIX_ATTR)
