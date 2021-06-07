import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.base.fkChain as fkChain
import dev.rigging.rigNode.rigLimb.base.pistonAim as pistonAim


class AimFk(fkChain.FkChain):
    def __init__(self, **kwargs):
        super(AimFk, self).__init__(**kwargs)
        self._aim_distance_multiplier = kwargs.get('aim_distance_multiplier', 10)

        self._piston_limb = None

    def create_controls(self):
        super(AimFk, self).create_controls()
        # create piston setup
        name_info = namingUtils.decompose(self._node)
        self._piston_limb = pistonAim.PistonAim(side=name_info['side'], description=name_info['description'],
                                                index=name_info['index'], limb_index=name_info['limb_index'],
                                                additional_description='aim', parent_node=self._rig_nodes_group,
                                                guide_joints=self._guide_joints,
                                                control_size=self._control_size, control_color=self._control_color,
                                                control_shape=self._control_shape, tag_control=False,
                                                control_additional_description=self._control_additional_description,
                                                aim_distance_multiplier=self._aim_distance_multiplier,
                                                up_type='none', create_joint=False)

        self._piston_limb.build()
        self._piston_limb.connect(input_matrix=self._input_matrix_attr, offset_matrix=self._offset_matrix_attr)

        # connect vis attrs to limb group
        attributeUtils.connect([self._controls_vis_output_attr, self._joints_vis_output_attr,
                                self._nodes_local_vis_output_attr, self._nodes_world_vis_output_attr],
                               [self._piston_limb.controls_vis_offset_attr, self._piston_limb.joints_vis_offset_attr,
                                self._piston_limb.nodes_local_vis_offset_attr,
                                self._piston_limb.nodes_world_vis_offset_attr])

        # remove root sub control
        controlUtils.remove_sub(self._piston_limb.controls[0])
        # lock hide root control attributes
        attributeUtils.lock(attributeUtils.TRANSFORM, node=self._piston_limb.controls[0], channel_box=False)
        # hide root control
        zero = controlUtils.get_hierarchy_node(self._piston_limb.controls[0], 'zero')
        cmds.setAttr('{}.{}'.format(zero, attributeUtils.VISIBILITY), 0)

        # add to control list
        self._controls.append(self._piston_limb.controls[-1])

    def create_setup(self):
        super(AimFk, self).create_setup()
        # connect aim node with controller
        attributeUtils.connect(attributeUtils.ROTATE, attributeUtils.ROTATE, driver=self._piston_limb.setup_nodes[0],
                               driven=controlUtils.get_hierarchy_node(self._controls[0], 'driven'))

    def connect_to_joints(self):
        constraintUtils.position_constraint('{0}.{1}'.format(self._controls[0], controlUtils.OUT_MATRIX_ATTR),
                                            self._joints[0], maintain_offset=False)
