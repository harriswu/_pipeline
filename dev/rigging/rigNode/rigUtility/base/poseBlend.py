import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigUtility.core.coreUtility as coreUtility


class PoseBlend(coreUtility.CoreUtility):
    INPUT_MATRIX_ATTR = 'inputMatrix'
    POSE_WEIGHTS_ATTR = 'poseWeights'
    POSE_HANDLES_ATTR = 'poseHandles'
    JOINT_ORIENT_ATTR = 'jointOrient'
    REFERENCE_MATRIX_ATTR = 'referenceMatrix'
    OUTPUT_TRANSLATE_ATTR = 'outputTranslate'
    OUTPUT_ROTATE_ATTR = 'outputRotate'
    OUTPUT_SCALE_ATTR = 'outputScale'

    def __init__(self, **kwargs):
        super(PoseBlend, self).__init__(**kwargs)
        self._input_matrix = None
        self._reference_matrix = None
        self._input_joint_orient = None
        self._poses = None
        self._pose_weights = None
        self._translate = None
        self._rotate = None
        self._scale = None

        self._input_matrix_attr = None
        self._pose_weights_attr = None
        self._joint_orient_attr = None
        self._reference_matrix_attr = None
        self._pose_handles = []
        self._pose_handle_group = None
        self._constraints_group = None
        self._translate_blend = None
        self._rotate_blend = None
        self._scale_blend = None

        self._output_translate = None
        self._output_rotate = None
        self._output_scale = None

    @property
    def input_matrix_attr(self):
        return self._input_matrix_attr

    @property
    def reference_matrix_attr(self):
        return self._reference_matrix_attr

    @property
    def pose_weights_attr(self):
        return self._pose_weights_attr

    @property
    def pose_handles(self):
        return self._pose_handles

    @property
    def output_translate(self):
        return self._output_translate

    @property
    def output_rotate(self):
        return self._output_rotate

    @property
    def output_scale(self):
        return self._output_scale

    def get_connection_kwargs(self, **kwargs):
        super(PoseBlend, self).get_connection_kwargs(**kwargs)
        self._input_matrix = kwargs.get('input_matrix', None)
        self._reference_matrix = kwargs.get('reference_matrix', None)
        self._input_joint_orient = kwargs.get('input_joint_orient', None)
        self._poses = kwargs.get('poses', [])
        self._pose_weights = kwargs.get('pose_weights', [])
        self._translate = kwargs.get('translate', True)
        self._rotate = kwargs.get('rotate', True)
        self._scale = kwargs.get('scale', True)

        # get pose weights list
        self._pose_weights_attr = ['{0}.{1}[{2}]'.format(self._input_node, self.POSE_WEIGHTS_ATTR, i)
                                   for i in range(len(self._pose_weights))]

    def register_inputs(self):
        super(PoseBlend, self).register_inputs()
        self._input_matrix_attr = attributeUtils.add(self._input_node, self.INPUT_MATRIX_ATTR, attribute_type='matrix')
        # add pose weights attributes
        attributeUtils.add(self._input_node, self.POSE_WEIGHTS_ATTR, attribute_type='float', multi=True)

        # add joint orient attr
        self._joint_orient_attr = attributeUtils.add_multi_dimension_attribute(self._input_node, self.JOINT_ORIENT_ATTR,
                                                                               compound_type='double3',
                                                                               attribute_type='doubleAngle',
                                                                               suffix='XYZ')

        # reference matrix attr
        self._reference_matrix_attr = attributeUtils.add(self._input_node, self.REFERENCE_MATRIX_ATTR,
                                                         attribute_type='matrix')[0]

    def connect_inputs(self):
        super(PoseBlend, self).connect_inputs()
        # connect with input joint orient
        if self._input_joint_orient:
            attributeUtils.connect(self._input_joint_orient, self._joint_orient_attr)

        attributeUtils.connect(self._input_matrix, self._input_matrix_attr)
        if self._reference_matrix:
            attributeUtils.connect(self._reference_matrix, self._reference_matrix_attr)
        # connect with input pose weights
        attributeUtils.connect_nodes_to_multi_attr(self._pose_weights, self.POSE_WEIGHTS_ATTR, driven=self._input_node)
        # get pose weights list
        self._pose_weights_attr = self.get_multi_attr_names(self.POSE_WEIGHTS_ATTR, node=self._input_node)

    def create_hierarchy(self):
        super(PoseBlend, self).create_hierarchy()
        self._pose_handle_group = transformUtils.create(namingUtils.update(self._node, type='group',
                                                                           additional_description='poseHandles'),
                                                        lock_hide=attributeUtils.ALL, parent=self._node)

        self._constraints_group = transformUtils.create(namingUtils.update(self._node, type='group',
                                                                           additional_description='constraintNodes'),
                                                        lock_hide=attributeUtils.ALL, parent=self._node)
        
    def post_build(self):
        super(PoseBlend, self).post_build()
        # connect with reference matrix
        constraintUtils.position_constraint(self._reference_matrix_attr, self._pose_handle_group)
        # create transform nodes as pose handles, and connect with weights,
        # sum together as translation, rotation and scale
        pose_inputs = [[], [], []]
        for i, pose in enumerate(self._poses):
            # check pose type
            if isinstance(pose, list) and len(pose) == 16:
                # pose is a matrix
                matrix = pose
                position = None
            else:
                matrix = None
                position = pose
            # create transform node
            pose_handle = transformUtils.create(namingUtils.update(self._node, type='poseHandle',
                                                                   additional_description='pose{:03d}'.format(i+1)),
                                                parent=self._pose_handle_group, position=position, matrix=matrix)
            self._pose_handles.append(pose_handle)

            # create multiply node to get pose input
            for j, (attr, check) in enumerate(zip(['translate', 'rotate', 'scale'],
                                                  [self._translate, self._rotate, self._scale])):
                if check:
                    mult_node = namingUtils.update(pose_handle, type='multiplyDivide', additional_description=attr)
                    pose_attr = nodeUtils.arithmetic.multiply_divide('{0}.{1}'.format(pose_handle, attr),
                                                                     [self._pose_weights_attr[i],
                                                                      self._pose_weights_attr[i],
                                                                      self._pose_weights_attr[i]],
                                                                     name=mult_node)
                    pose_inputs[j].append(pose_attr)

        # get plus minus average nodes to sum the values
        plus_outputs = []
        for i, (pose_attrs, attr) in enumerate(zip(pose_inputs, ['translate', 'rotate', 'scale'])):
            if pose_attrs:
                plus_node = namingUtils.update(self._node, type='plusMinusAverage',
                                               additional_description=['positionBlend', attr])
                plus_attr = nodeUtils.arithmetic.plus_minus_average(*pose_attrs, name=plus_node)
                plus_outputs.append(plus_attr)
            else:
                plus_outputs.append(None)

        self._translate_blend = plus_outputs[0]
        self._rotate_blend = plus_outputs[1]
        self._scale_blend = plus_outputs[2]

    def register_outputs(self):
        super(PoseBlend, self).register_outputs()
        # add pose handle messages
        attributeUtils.add(self._output_node, self.POSE_HANDLES_ATTR, attribute_type='message', multi=True)

        # add output translation rotation and scale
        self._output_translate = attributeUtils.add_multi_dimension_attribute(self._output_node,
                                                                              self.OUTPUT_TRANSLATE_ATTR,
                                                                              compound_type='double3',
                                                                              attribute_type='doubleLinear',
                                                                              suffix='XYZ')
        self._output_rotate = attributeUtils.add_multi_dimension_attribute(self._output_node, self.OUTPUT_ROTATE_ATTR,
                                                                           compound_type='double3',
                                                                           attribute_type='doubleAngle', suffix='XYZ')
        self._output_scale = attributeUtils.add_multi_dimension_attribute(self._output_node, self.OUTPUT_SCALE_ATTR,
                                                                          compound_type='double3',
                                                                          attribute_type='doubleLinear', suffix='XYZ',
                                                                          default_value=[1, 1, 1])

    def connect_outputs(self):
        super(PoseBlend, self).connect_outputs()
        attributeUtils.connect_nodes_to_multi_attr(self._pose_handles, self.POSE_HANDLES_ATTR,
                                                   driver_attr=attributeUtils.MESSAGE, driven=self._output_node)
        # connect with constraint
        if self._translate:
            attributeUtils.connect(self._translate_blend, self.OUTPUT_TRANSLATE_ATTR, driven=self._output_node)

        if self._rotate:
            attributeUtils.connect(self._rotate_blend, self.OUTPUT_ROTATE_ATTR, driven=self._output_node)

        if self._scale:
            attributeUtils.connect(self._scale_blend, self.OUTPUT_SCALE_ATTR, driven=self._output_node)

    def get_input_info(self):
        super(PoseBlend, self).get_input_info()
        self._input_matrix_attr = '{0}.{1}'.format(self._input_node, self.INPUT_MATRIX_ATTR)
        self._pose_weights_attr = self.get_multi_attr_names(self.POSE_WEIGHTS_ATTR, node=self._input_node)
        self._joint_orient_attr = '{0}.{1}'.format(self._input_node, self.JOINT_ORIENT_ATTR)

    def get_output_info(self):
        super(PoseBlend, self).get_output_info()
        self._pose_handles = self.get_multi_attr_value(self.POSE_HANDLES_ATTR, node=self._output_node)
        self._output_translate = '{0}.{1}'.format(self._output_node, self.OUTPUT_TRANSLATE_ATTR)
        self._output_rotate = '{0}.{1}'.format(self._output_node, self.OUTPUT_ROTATE_ATTR)
        self._output_scale = '{0}.{1}'.format(self._output_node, self.OUTPUT_SCALE_ATTR)
