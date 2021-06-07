import maya.cmds as cmds

import utils.common.attributeUtils as attributeUtils
import utils.rigging.controlUtils as controlUtils

import dev.rigging.rigNode.rigLimb.base.fkChain as fkChain


class BipedArmFk(fkChain.FkChain):
    # constant attribute
    AUTO_CLAV_MATRIX_ATTR = 'autoClavMatrix'

    def __init__(self, **kwargs):
        super(BipedArmFk, self).__init__(**kwargs)
        self._lock_hide = kwargs.get('lock_hide', attributeUtils.TRANSLATE + attributeUtils.SCALE)
        self._unlock_elbow = kwargs.get('unlock_elbow', False)

        self._auto_clav_matrix_attr = None

    @property
    def auto_clav_matrix(self):
        return cmds.getAttr(self._auto_clav_matrix_attr)

    @property
    def auto_clav_matrix_attr(self):
        return self._auto_clav_matrix_attr

    def register_outputs(self):
        super(BipedArmFk, self).register_outputs()
        self._auto_clav_matrix_attr = attributeUtils.add(self._output_node, self.AUTO_CLAV_MATRIX_ATTR,
                                                         attribute_type='matrix')
        attributeUtils.connect('{0}.{1}'.format(self._controls[0], controlUtils.PARTIAL_MATRIX_ATTR),
                               self._auto_clav_matrix_attr)

    def create_controls(self):
        super(BipedArmFk, self).create_controls()
        if not self._unlock_elbow:
            attributeUtils.lock([attributeUtils.ROTATE[0], attributeUtils.ROTATE[2]], node=self._controls[1])

    def get_output_info(self):
        super(BipedArmFk, self).get_output_info()
        self._auto_clav_matrix_attr = '{0}.{1}'.format(self._output_node, self.AUTO_CLAV_MATRIX_ATTR)
