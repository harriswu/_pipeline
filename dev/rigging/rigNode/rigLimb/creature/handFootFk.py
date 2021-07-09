import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils

import dev.rigging.rigNode.rigLimb.base.fkChain as fkChain


class HandFootFk(fkChain.FkChain):
    ROLL_MATRIX_ATTR = 'rollMatrix'

    def __init__(self, **kwargs):
        super(HandFootFk, self).__init__(**kwargs)
        self._create_joints = True
        self._roll_matrix_attr = None

    @property
    def roll_matrix_attr(self):
        return self._roll_matrix_attr

    def add_output_attributes(self):
        super(HandFootFk, self).add_output_attributes()
        self._roll_matrix_attr = attributeUtils.add(self._output_node, self.ROLL_MATRIX_ATTR,
                                                    attribute_type='matrix')[0]

        if self._create_joints:
            nodeUtils.matrix.compose_matrix(namingUtils.update(self._node, type='composeMatrix',
                                                               additional_description='rollMatrix'),
                                            rotate=['{0}.{1}'.format(self._joints[1], attributeUtils.ROTATE[0]),
                                                    '{0}.{1}'.format(self._joints[1], attributeUtils.ROTATE[1]),
                                                    '{0}.{1}'.format(self._joints[1], attributeUtils.ROTATE[2])],
                                            rotate_order='{0}.{1}'.format(self._joints[1], attributeUtils.ROTATE_ORDER),
                                            connect_attr=self._roll_matrix_attr)

    def get_output_info(self):
        super(HandFootFk, self).get_output_info()
        self._roll_matrix_attr = '{0}.{1}'.format(self._output_node, self.ROLL_MATRIX_ATTR)
