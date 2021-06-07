import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.base.rotatePlaneIk as rotatePlaneIk


class Rib(rotatePlaneIk.RotatePlaneIk):
    DRIVER_VALUE_ATTR = 'driverValue'
    TWIST_MULT_ATTR = 'twistMult'
    ATTACH_MATRIX_ATTR = 'attachMatrix'

    def __init__(self, **kwargs):
        super(Rib, self).__init__(**kwargs)
        self._driver_value = None
        self._twist_multiplier = kwargs.get('twist_multiplier', 0.2)
        self._attach_matrix = None

        self._driver_value_attr = None
        self._twist_mult_attr = None
        self._attach_matrix_attr = None

    @property
    def driver_value_attr(self):
        return self._driver_value_attr

    @property
    def twist_mult_attr(self):
        return self._twist_mult_attr

    @property
    def attach_matrix_attr(self):
        return self._attach_matrix_attr
        
    def register_inputs(self):
        super(Rib, self).register_inputs()
        self._driver_value_attr = attributeUtils.add(self._input_node, self.DRIVER_VALUE_ATTR,
                                                     attribute_type='float')[0]
        self._twist_mult_attr = attributeUtils.add(self._input_node, self.TWIST_MULT_ATTR, attribute_type='float',
                                                   default_value=self._twist_multiplier)[0]
        self._attach_matrix_attr = attributeUtils.add(self._input_node, self.ATTACH_MATRIX_ATTR,
                                                      attribute_type='matrix')[0]

    def connect_control(self):
        super(Rib, self).connect_control()
        # connect twist
        nodeUtils.arithmetic.equation('{0}*{1}'.format(self._driver_value_attr, self._twist_mult_attr),
                                      namingUtils.update(self._node, additional_description='bucketHandle'),
                                      connect_attr='{0}.{1}'.format(self._controls[-1], self.TWIST_ATTR))
        # remove end ik controller's sub control
        controlUtils.remove_sub(self._controls[-1])
        # lock hide all
        attributeUtils.lock(attributeUtils.TRANSFORM + [self.TWIST_ATTR], node=self._controls[-1])

        # hide controller
        cmds.setAttr('{0}.{1}'.format(controlUtils.get_hierarchy_node(self._controls[-1], 'zero'),
                                      attributeUtils.VISIBILITY), 0)

    def get_connection_kwargs(self, **kwargs):
        super(Rib, self).get_connection_kwargs(**kwargs)
        self._driver_value = kwargs.get('driver_value', None)
        self._attach_matrix = kwargs.get('attach_matrix', None)
        
    def connect_inputs(self):
        super(Rib, self).connect_inputs()
        attributeUtils.connect(self._driver_value, self._driver_value_attr)
        # attach end controller with given matrix
        attributeUtils.connect(self._attach_matrix, self._attach_matrix_attr)
        driven = controlUtils.get_hierarchy_node(self._controls[-1], 'driven')
        ivs_matrix_attr = '{0}.{1}'.format(driven, attributeUtils.PARENT_INVERSE_MATRIX)
        constraintUtils.position_constraint(self._attach_matrix_attr, driven,
                                            parent_inverse_matrices=ivs_matrix_attr, maintain_offset=True)

    def get_input_info(self):
        super(Rib, self).get_input_info()
        self._driver_value_attr = '{0}.{1}'.format(self._input_node, self.DRIVER_VALUE_ATTR)
        self._twist_mult_attr = '{0}.{1}'.format(self._input_node, self.TWIST_MULT_ATTR)
        self._attach_matrix_attr = '{0}.{1}'.format(self._input_node, self.ATTACH_MATRIX_ATTR)
