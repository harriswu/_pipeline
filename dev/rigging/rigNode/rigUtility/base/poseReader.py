import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils

import dev.rigging.rigNode.rigUtility.core.coreUtility as coreUtility


class PoseReader(coreUtility.CoreUtility):
    # TODO: add RBF type pose reader option
    INPUT_MATRIX_ATTR = 'inputMatrix'
    DRIVER_VECTOR_ATTR = 'driverVector'
    REFERENCE_POINTS_ATTR = 'referencePoints'
    OUTPUTS_ATTR = 'outputs'

    def __init__(self, **kwargs):
        super(PoseReader, self).__init__(**kwargs)
        self._driver_vector = kwargs.get('driver_vector', [1, 0, 0])
        self._reference_points = kwargs.get('reference_points', [])
        self._input_matrix = None

        self._input_matrix_attr = None
        self._driver_vector_attr = None
        self._reference_points_attr = None

        self._weights = []
        self._outputs_attr = None

    @property
    def input_matrix_attr(self):
        return self._input_matrix_attr

    @property
    def driver_vector_attr(self):
        return self._driver_vector_attr

    @property
    def reference_points_attr(self):
        return self._reference_points_attr

    @property
    def outputs_attr(self):
        return self._outputs_attr

    def register_inputs(self):
        super(PoseReader, self).register_inputs()
        self._input_matrix_attr = attributeUtils.add(self._input_node, self.INPUT_MATRIX_ATTR,
                                                     attribute_type='matrix')[0]

        self._driver_vector_attr = attributeUtils.add_multi_dimension_attribute(self._input_node,
                                                                                self.DRIVER_VECTOR_ATTR,
                                                                                compound_type='double3',
                                                                                attribute_type='doubleLinear',
                                                                                suffix='XYZ')
        self._reference_points_attr = attributeUtils.add_multi_dimension_attribute(self._input_node,
                                                                                   self.REFERENCE_POINTS_ATTR,
                                                                                   compound_type='double3',
                                                                                   attribute_type='doubleLinear',
                                                                                   suffix='XYZ',
                                                                                   multi=True)

        cmds.setAttr(self._driver_vector_attr, *self._driver_vector)
        for i, pnt in enumerate(self._reference_points):
            cmds.setAttr('{0}[{1}]'.format(self._reference_points_attr, i), *pnt)

    def create_node(self):
        super(PoseReader, self).create_node()
        # get pose driver vector by multiply driver vector with input matrix
        pnt_matrix_node = namingUtils.update(self._node, type='pointMatrixMult', additional_description='driver')
        pose_vec = nodeUtils.point.mult_matrix(self._driver_vector, self._input_matrix_attr, name=pnt_matrix_node)

        # loop in each pose and get output values
        for i in range(len(self._reference_points)):
            # use dot product to check the angle
            dot_node = namingUtils.update(self._node, type='dotProduct',
                                          additional_description='pose{:03d}'.format(i+1))
            dot_attr = nodeUtils.vector.dot_product(pose_vec, '{0}[{1}]'.format(self._reference_points_attr, i),
                                                    name=dot_node)
            # get current dot value
            dot_val = cmds.getAttr(dot_attr)
            # use remap to get output weight
            remap_node = namingUtils.update(dot_node, type='remapValue')
            weight_attr = nodeUtils.utility.remap_value(dot_attr, input_range=[dot_val, 1], output_range=[0, 1],
                                                        name=remap_node)
            self._weights.append(weight_attr)

    def register_outputs(self):
        super(PoseReader, self).register_outputs()
        attributeUtils.add(self._output_node, self.OUTPUTS_ATTR, attribute_type='float', multi=True)
        attributeUtils.connect_nodes_to_multi_attr(self._weights, self.OUTPUTS_ATTR, driven=self._output_node)
        self._outputs_attr = self.get_multi_attr_names(self.OUTPUTS_ATTR, node=self._output_node)

    def get_connection_kwargs(self, **kwargs):
        super(PoseReader, self).get_connection_kwargs(**kwargs)
        self._input_matrix = kwargs.get('input_matrix', None)

    def get_input_info(self):
        super(PoseReader, self).get_input_info()
        self._input_matrix_attr = '{0}.{1}'.format(self._input_node, self.INPUT_MATRIX_ATTR)
        self._driver_vector_attr = '{0}.{1}'.format(self._input_node, self.DRIVER_VECTOR_ATTR)
        self._reference_points_attr = '{0}.{1}'.format(self._input_node, self.REFERENCE_POINTS_ATTR)

    def get_output_info(self):
        super(PoseReader, self).get_output_info()
        self._outputs_attr = self.get_multi_attr_names(self.OUTPUTS_ATTR, node=self._output_node)

    def connect_inputs(self):
        super(PoseReader, self).connect_inputs()
        attributeUtils.connect(self._input_matrix, self._input_matrix_attr)
