import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.mathUtils as mathUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.base.fkChain as fkChain


class FingerFk(fkChain.FkChain):
    # constant attribute
    DRIVER_MATRIX_ATTR = 'driverMatrix'
    DRIVER_WEIGHT_ATTR = 'driverWeight'

    def __init__(self, **kwargs):
        super(FingerFk, self).__init__(**kwargs)
        self._follow_metacarpal = None
        self._driver_matrix = None
        self._driver_weight = 1

        self._control_end_joint = False

        self._driver_matrix_attr = None
        self._driver_weight_attr = None

    @property
    def driver_matrix_attr(self):
        return self._driver_matrix_attr

    def get_build_kwargs(self, **kwargs):
        super(FingerFk, self).get_build_kwargs(**kwargs)
        self._follow_metacarpal = kwargs.get('follow_metacarpal', False)

    def get_connect_kwargs(self, **kwargs):
        super(FingerFk, self).get_connect_kwargs(**kwargs)
        self._driver_matrix = kwargs.get('driver_matrix', None)
        self._driver_weight = kwargs.get('driver_weight', 1)

    def flip_connect_kwargs(self):
        super(FingerFk, self).flip_connect_kwargs()
        self._driver_matrix = namingUtils.flip_names(self._driver_matrix)

    def add_input_attributes(self):
        super(FingerFk, self).add_input_attributes()
        self._driver_matrix_attr = attributeUtils.add(self._input_node, self.DRIVER_MATRIX_ATTR,
                                                      attribute_type='matrix')
        self._driver_weight_attr = attributeUtils.add(self._input_node, self.DRIVER_WEIGHT_ATTR,
                                                      attribute_type='float', value_range=[0, 1],
                                                      default_value=self._driver_weight)

    def create_setup(self):
        super(FingerFk, self).create_setup()
        # check if follow metacarpal rotation
        if not self._follow_metacarpal:
            # override base controller's rotation
            # get base controller's zero group's inverse matrix
            zero = controlUtils.get_hierarchy_node(self._controls[1], 'zero')
            ivs_matrix_zero = cmds.getAttr('{}.{}'.format(zero, attributeUtils.INVERSE_MATRIX))
            # multiply inverse matrix
            mult_matrix = namingUtils.update(self._guide_joints[0], type='multMatrix',
                                             additional_description='inverseMatrix')
            ivs_matrix_ctrl = nodeUtils.matrix.mult_matrix(ivs_matrix_zero,
                                                           '{0}.{1}'.format(self._controls[0],
                                                                            controlUtils.OUT_INVERSE_MATRIX_ATTR),
                                                           name=mult_matrix)
            # plug with base controller's driven node
            driven = controlUtils.get_hierarchy_node(self._controls[1], 'driven')
            constraintUtils.position_constraint(mathUtils.matrix.IDENTITY, driven, weights=1,
                                                parent_inverse_matrices=ivs_matrix_ctrl, maintain_offset=True,
                                                skip=attributeUtils.TRANSLATE)

        # get connect node and connect the rotation
        driven = controlUtils.get_hierarchy_node(self._controls[1], 'driven')
        connect = controlUtils.get_hierarchy_node(self._controls[1], 'connect')
        constraintUtils.position_constraint([self._driver_matrix_attr, '{0}.{1}'.format(driven, attributeUtils.MATRIX)],
                                            connect, weights=self._driver_weight_attr, maintain_offset=True,
                                            skip=attributeUtils.TRANSLATE)

    def connect_input_attributes(self):
        super(FingerFk, self).connect_input_attributes()
        if self._driver_matrix:
            attributeUtils.connect(self._driver_matrix, self._driver_matrix_attr)

    def get_input_info(self):
        super(FingerFk, self).get_input_info()
        self._driver_matrix_attr = '{0}.{1}'.format(self._input_node, self.DRIVER_MATRIX_ATTR)
        self._driver_weight_attr = '{0}.{1}'.format(self._input_node, self.DRIVER_WEIGHT_ATTR)
