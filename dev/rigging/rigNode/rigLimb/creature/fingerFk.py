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

    def __init__(self, **kwargs):
        super(FingerFk, self).__init__(**kwargs)
        self._follow_metacarpal = kwargs.get('follow_metacarpal', False)
        self._driver_matrix = None

        self._control_end_joint = False

        self._driver_matrix_attr = None

    @property
    def driver_matrix_attr(self):
        return self._driver_matrix_attr

    def register_inputs(self):
        super(FingerFk, self).register_inputs()
        self._driver_matrix_attr = attributeUtils.add(self._input_node, self.DRIVER_MATRIX_ATTR,
                                                      attribute_type='matrix')

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
        connect = controlUtils.get_hierarchy_node(self._controls[1], 'connect')
        constraintUtils.position_constraint(self._driver_matrix_attr, connect, weights=1, maintain_offset=True,
                                            skip=attributeUtils.TRANSLATE)

    def get_connection_kwargs(self, **kwargs):
        super(FingerFk, self).get_connection_kwargs(**kwargs)
        self._driver_matrix = kwargs.get('driver_matrix', None)

    def connect_inputs(self):
        super(FingerFk, self).connect_inputs()
        if self._driver_matrix:
            attributeUtils.connect(self._driver_matrix, self._driver_matrix_attr)

    def get_input_info(self):
        super(FingerFk, self).get_input_info()
        self._driver_matrix_attr = '{0}.{1}'.format(self._input_node, self.DRIVER_MATRIX_ATTR)
