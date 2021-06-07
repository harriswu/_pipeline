import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.base.splineIk as splineIk
import dev.rigging.rigNode.rigLimb.base.fkChain as fkChain


class SplineIkOnFk(splineIk.SplineIk):
    FK_CONTROLS_ATTR = 'fkControls'

    def __init__(self, **kwargs):
        super(SplineIkOnFk, self).__init__(**kwargs)
        self._guide_fk = kwargs.get('guide_fk', [])
        self._fk_lock_hide = kwargs.get('fk_lock_hide', attributeUtils.TRANSLATE + attributeUtils.SCALE)

        self._fk_limb = None
        self._fk_controls = []

    def create_controls(self):
        super(SplineIkOnFk, self).create_controls()
        name_info = namingUtils.decompose(self._node)
        self._fk_limb = fkChain.FkChain(side=name_info['side'], description=name_info['description'],
                                        index=name_info['index'], limb_index=name_info['limb_index'],
                                        additional_description='fk', parent_node=self._rig_nodes_group,
                                        guide_joints=self._guide_fk, control_size=self._control_size,
                                        control_color=self._control_color, control_shape=self._control_shape,
                                        tag_control=self._tag_control,
                                        control_additional_description=self._control_additional_description,
                                        lock_hide=self._fk_lock_hide, control_end_joint=True, create_joint=False)
        self._fk_limb.build()
        self._fk_limb.connect(input_matrix=self._input_matrix_attr, offset_matrix=self._offset_matrix_attr)
        attributeUtils.connect([self._controls_vis_output_attr, self._joints_vis_output_attr,
                                self._nodes_local_vis_output_attr, self._nodes_world_vis_output_attr],
                               [self._fk_limb.controls_vis_offset_attr, self._fk_limb.joints_vis_offset_attr,
                                self._fk_limb.nodes_local_vis_offset_attr,
                                self._fk_limb.nodes_world_vis_offset_attr])

        self._fk_controls = self._fk_limb.controls

        # connect vis attrs to limb group
        attributeUtils.connect(self._controls_vis_attr, self._fk_limb.controls_vis_offset_attr)

        # connect with ik tip controller
        driven = controlUtils.get_hierarchy_node(self._controls[-1], 'driven')
        zero = controlUtils.get_hierarchy_node(self._controls[-1], 'zero')
        zero_ivs_matrix = cmds.getAttr('{0}.{1}'.format(zero, attributeUtils.INVERSE_MATRIX))
        constraintUtils.position_constraint('{0}.{1}'.format(self._fk_limb.controls[-1],
                                                             controlUtils.HIERARCHY_MATRIX_ATTR),
                                            driven, parent_inverse_matrices=zero_ivs_matrix, maintain_offset=True)

    def register_outputs(self):
        super(SplineIkOnFk, self).register_outputs()
        fk_attr = attributeUtils.add(self._output_node, self.FK_CONTROLS_ATTR, attribute_type='message', multi=True)[0]
        attributeUtils.connect_nodes_to_multi_attr(self._fk_controls, fk_attr, driver_attr=attributeUtils.MESSAGE)

    def get_output_info(self):
        super(SplineIkOnFk, self).get_output_info()
        self._fk_controls = self.get_multi_attr_value(self.FK_CONTROLS_ATTR, node=self._output_node)

    def tag_controllers(self):
        super(SplineIkOnFk, self).tag_controllers()
        tag_parent = self._tag_parent
        for ctrl in self._fk_controls:
            controlUtils.set_tag_parent(ctrl, tag_parent)
            tag_parent = ctrl
