import utils.common.attributeUtils as attributeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.base.fkChain as fkChain


class AimFk(fkChain.FkChain):
    def __init__(self, **kwargs):
        super(AimFk, self).__init__(**kwargs)
        self._aim_distance_multiplier = None

        self._piston_limb = None

    def get_build_kwargs(self, **kwargs):
        super(AimFk, self).get_build_kwargs(**kwargs)
        self._aim_distance_multiplier = kwargs.get('aim_distance_multiplier', 10)

    def create_controls(self):
        super(AimFk, self).create_controls()
        print self._side
        print self._node
        # create piston setup
        build_kwargs = ({'additional_description': ['aim'],
                         'parent_node': self._sub_nodes_group,
                         'guide_joints': self._guide_joints,
                         'aim_distance_multiplier': self._aim_distance_multiplier,
                         'up_type': 'none',
                         'create_joint': False})
        connect_kwargs = {'input_matrix': self._input_matrix_attr,
                          'offset_matrix': self._offset_matrix_attr}

        self._piston_limb = self.create_rig_node('dev.rigging.rigNode.rigLimb.base.pistonAim',
                                                 name_template=self._node,
                                                 build=True, build_kwargs=build_kwargs,
                                                 connect=True, connect_kwargs=connect_kwargs, flip=self._flip)

        # connect vis attrs to limb group
        attributeUtils.connect([self._controls_vis_output_attr, self._joints_vis_output_attr,
                                self._nodes_vis_output_attr],
                               [self._piston_limb.controls_vis_offset_attr, self._piston_limb.joints_vis_offset_attr,
                                self._piston_limb.nodes_vis_offset_attr])

        # remove root sub control
        controlUtils.remove_sub(self._piston_limb.controls[0])
        # lock hide root control attributes
        attributeUtils.lock(attributeUtils.TRANSFORM, node=self._piston_limb.controls[0], channel_box=False)
        # hide root control
        controlUtils.hide_controller(self._piston_limb.controls[0])

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
