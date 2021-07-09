import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.core.ikHandle as ikHandleLimb


class SingleChainIk(ikHandleLimb.IkHandle):
    def __init__(self, **kwargs):
        super(SingleChainIk, self).__init__(**kwargs)

    def get_build_kwargs(self, **kwargs):
        super(SingleChainIk, self).get_build_kwargs(**kwargs)
        self._additional_description = kwargs.get('additional_description', ['scIk'])

    def create_controls(self):
        super(SingleChainIk, self).create_controls()
        for jnt, description, lock_attrs in zip([self._guide_joints[0], self._guide_joints[-1]], ['root', 'target'],
                                                [attributeUtils.ROTATE + attributeUtils.SCALE, attributeUtils.SCALE]):
            # decompose name
            name_info = namingUtils.decompose(jnt)
            ctrl = controlUtils.create(name_info['description'], side=name_info['side'], index=name_info['index'],
                                       limb_index=name_info['limb_index'], additional_description=description, sub=True,
                                       parent=self._controls_group, position=jnt, rotate_order=0, manip_orient=None,
                                       lock_hide=lock_attrs)
            self._controls.append(ctrl)

    def create_setup(self):
        super(SingleChainIk, self).create_setup()
        # connect root control with first joint's translation
        constraintUtils.position_constraint('{0}.{1}'.format(self._controls[0], controlUtils.OUT_MATRIX_ATTR),
                                            self._setup_nodes[0], maintain_offset=False, skip=attributeUtils.ROTATE)

        # connect ik group with controller
        constraintUtils.position_constraint('{0}.{1}'.format(self._controls[-1], controlUtils.OUT_MATRIX_ATTR),
                                            self._ik_groups[0], maintain_offset=True)
