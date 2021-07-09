import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils
import utils.common.nodeUtils as nodeUtils
import utils.modeling.curveUtils as curveUtils
import utils.rigging.jointUtils as jointUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils
import utils.rigging.deformerUtils as deformerUtils

import dev.rigging.rigNode.rigLimb.core.ikHandle as ikHandleLimb


class SplineIk(ikHandleLimb.IkHandle):
    # constant attribute
    CURVES_ATTR = 'curves'
    ROOT_LOCAL_CONTROL_ATTR = 'rootLocalControl'
    ROOT_LOCAL_CONTROL_VIS_ATTR = 'localCtrlVis'

    def __init__(self, **kwargs):
        super(SplineIk, self).__init__(**kwargs)
        self._guide_curve = None
        self._guide_controls = None
        self._additional_description = None
        self._control_manip_orient = None
        self._curve_skin_cluster = None
        self._root_local_control = None

        self._iks = []
        self._curves = None
        self._curve_joints = []
        self._root_control = None

    @property
    def curves(self):
        return self._curves

    def get_build_kwargs(self, **kwargs):
        super(SplineIk, self).get_build_kwargs(**kwargs)
        self._guide_curve = kwargs.get('guide_curve', '')
        self._guide_controls = kwargs.get('guide_controls', [])
        self._additional_description = kwargs.get('additional_description', ['splineIk'])
        self._control_manip_orient = kwargs.get('control_manip_orient', None)
        self._curve_skin_cluster = kwargs.get('curve_skin_cluster', '')
        self._root_local_control = kwargs.get('root_local_control', True)

    def flip_connect_kwargs(self):
        super(SplineIk, self).flip_connect_kwargs()
        self._guide_curve = namingUtils.flip(self._guide_curve)
        self._guide_controls = namingUtils.flip(self._guide_controls)
        self._control_manip_orient = namingUtils.flip(self._control_manip_orient)

    def create_setup(self):
        super(SplineIk, self).create_setup()
        self.add_twist()

    def create_controls(self):
        if not isinstance(self._control_manip_orient, list):
            self._control_manip_orient = [self._control_manip_orient] * len(self._guide_controls)

        # create controllers and joints to control the curve
        for guide, manip_orient in zip(self._guide_controls, self._control_manip_orient):
            name_info = namingUtils.decompose(guide)
            # create controller
            ctrl = controlUtils.create(name_info['description'], side=name_info['side'], index=name_info['index'],
                                       limb_index=name_info['limb_index'], additional_description=None, sub=True,
                                       parent=self._controls_group, position=guide, rotate_order=0,
                                       manip_orient=manip_orient, lock_hide=attributeUtils.SCALE)
            self._controls.append(ctrl)

            # create joint
            zero_jnt = transformUtils.create(namingUtils.update(ctrl, type='zero', additional_description='curve'),
                                             parent=self._nodes_hide_group, rotate_order=0, visibility=True,
                                             position=ctrl, inherits_transform=True)
            jnt = jointUtils.create(namingUtils.update(zero_jnt, type='joint'), position=zero_jnt,
                                    parent_node=zero_jnt)

            # connect zero group with controller
            constraintUtils.position_constraint('{0}.{1}'.format(ctrl, controlUtils.OUT_MATRIX_ATTR), zero_jnt,
                                                maintain_offset=False)
            self._curve_joints.append(jnt)

        # create root control
        if self._root_local_control:
            name_info = namingUtils.decompose(self._controls[0])
            self._root_control = controlUtils.create(name_info['description'], side=name_info['side'],
                                                     index=name_info['index'], limb_index=name_info['limb_index'],
                                                     additional_description='local', sub=True,
                                                     parent=self._controls[0], position=self._joints[0],
                                                     rotate_order=0,
                                                     lock_hide=attributeUtils.TRANSLATE + attributeUtils.SCALE,
                                                     input_matrix='{0}.{1}'.format(self._controls[0],
                                                                                   controlUtils.OUT_MATRIX_ATTR))
            # add vis switch on ik controller
            vis_attr = attributeUtils.add(self._controls[0], self.ROOT_LOCAL_CONTROL_VIS_ATTR,
                                          attribute_type='bool', keyable=False, channel_box=True)[0]
            zero = controlUtils.get_hierarchy_node(self._root_control, 'zero')
            cmds.connectAttr(vis_attr, '{0}.{1}'.format(zero, attributeUtils.VISIBILITY))

    def create_ik(self):
        # create curve from guide
        # get curve info
        curve_info = curveUtils.get_shape_info(self._guide_curve)
        # create drive curve
        drive_curve, curve_shape = curveUtils.create(namingUtils.update(self._guide_curve, type='curve',
                                                                        additional_description='drive'),
                                                     curve_info['control_vertices'], curve_info['knots'],
                                                     degree=curve_info['degree'], form=curve_info['form'],
                                                     parent=self._nodes_world_group)

        # create ik handle, let maya auto generate the curve, otherwise will get offset values on joints
        ik_handle = namingUtils.compose(type='ikHandle', side=self._side, description=self._description,
                                        index=self._index, limb_index=self._limb_index,
                                        additional_description=self._additional_description)
        ik_nodes = cmds.ikHandle(startJoint=self._setup_nodes[0], endEffector=self._setup_nodes[-1],
                                 solver='ikSplineSolver', simplifyCurve=False, parentCurve=False, name=ik_handle)

        # rename the auto generate curve
        driven_curve = cmds.rename(ik_nodes[-1], namingUtils.update(self._guide_curve, type='curve',
                                                                    additional_description='driven'))
        # parent ik handle and driven curve to hide group
        cmds.parent(ik_handle, driven_curve, self._nodes_hide_group)

        # append list
        self._iks.append(ik_handle)
        # store curves
        self._curves = [drive_curve, driven_curve]

    def connect_ik(self):
        # bind with the curve
        if self._curve_skin_cluster:
            # load skin cluster
            deformerUtils.skinCluster.import_data(self._curve_skin_cluster, geo=self._curves[0], flip=self._flip)
        else:
            # give it a default skin cluster
            skin = namingUtils.update(self._curves[0], type='skinCluster')
            cmds.skinCluster(self._curve_joints, self._curves[0], toSelectedBones=True, dropoffRate=6, bindMethod=0,
                             name=skin)

        # connect with driven curve using wire deformer
        wire_node, base_wire = deformerUtils.wire.create(self._curves[0], self._curves[1])
        # parent base wire under hide group
        cmds.parent(base_wire, self._nodes_hide_group)

    def add_twist(self):
        # create twist transform for start and end controller
        twist_plugs = []
        for ctrl, jnt in zip([self._controls[0], self._controls[-1]], [self._setup_nodes[0], self._setup_nodes[-1]]):
            grp = transformUtils.create(namingUtils.update(ctrl, type='group', additional_description='twist'),
                                        parent=self._nodes_hide_group, position=jnt)
            grp_zero = transformUtils.offset_group(grp, namingUtils.update(grp, type='zero'))
            # rotate constraint with controller
            constraintUtils.position_constraint('{0}.{1}'.format(ctrl, controlUtils.OUT_MATRIX_ATTR), grp,
                                                parent_inverse_matrices='{0}.{1}'.format(grp_zero,
                                                                                         attributeUtils.INVERSE_MATRIX),
                                                maintain_offset=True, skip=['translateX', 'translateY', 'translateZ'],
                                                force=True)
            # extract twist
            twist_attr = transformUtils.twist_extraction('{0}.{1}'.format(grp, attributeUtils.MATRIX), axis='x')
            twist_plugs.append(twist_attr)

        # ik handle's advance twist only works with world matrix,
        # it is kind against the current limb structure, which require all connections localized to the limb itself
        # so use roll and twist attrs to do the spline twist
        cmds.connectAttr(twist_plugs[0], self._iks[0] + '.roll')
        # twist value = top control twist - bot control twist
        # TODO: auto create utility nodes using pyparsing
        nodeUtils.arithmetic.equation('{0} - {1}'.format(twist_plugs[1], twist_plugs[0]),
                                      namingUtils.update(self._iks[0], additional_description='twist'),
                                      connect_attr=self._iks[0] + '.twist')

    def connect_to_joints(self):
        if self._root_local_control:
            # connect root joint with local controller
            constraintUtils.position_constraint('{0}.{1}'.format(self._root_control,
                                                                 controlUtils.HIERARCHY_MATRIX_ATTR),
                                                self._joints[0], maintain_offset=False)
            # connect the rest with ik joints
            # connect the second one with root joint's inverse matrix
            mult_matrix = nodeUtils.matrix.mult_matrix('{0}.{1}'.format(self._setup_nodes[1], attributeUtils.MATRIX),
                                                       '{0}.{1}'.format(self._setup_nodes[0], attributeUtils.MATRIX),
                                                       name=namingUtils.update(self._setup_nodes[1], type='multMatrix',
                                                                               additional_description='outMatrix'))
            constraintUtils.position_constraint(mult_matrix, self._joints[1],
                                                parent_inverse_matrices='{0}.{1}'.format(self._joints[0],
                                                                                         attributeUtils.INVERSE_MATRIX),
                                                maintain_offset=False)
            setup_nodes = self._setup_nodes[2:]
            joints = self._joints[2:]
        else:
            setup_nodes = self._setup_nodes
            joints = self._joints
        # loop in each setup node and joint and connect attributes
        for setup_jnt, jnt in zip(setup_nodes, joints):
            attributeUtils.connect(attributeUtils.TRANSFORM, attributeUtils.TRANSFORM,
                                   driver=setup_jnt, driven=jnt)

    def add_output_attributes(self):
        super(SplineIk, self).add_output_attributes()
        attributeUtils.add(self._output_node, self.CURVES_ATTR, attribute_type='message', multi=True)
        attributeUtils.connect_nodes_to_multi_attr(self._curves, self.CURVES_ATTR, driver_attr=attributeUtils.MESSAGE,
                                                   driven=self._output_node)

        root_control_attr = attributeUtils.add(self._output_node, self.ROOT_LOCAL_CONTROL_ATTR,
                                               attribute_type='message')
        if self._root_local_control:
            attributeUtils.connect(attributeUtils.MESSAGE, root_control_attr, driver=self._root_control)

    def get_output_info(self):
        super(SplineIk, self).get_output_info()
        self._curves = self.get_multi_attr_value(self.CURVES_ATTR, node=self._output_node)
        self._root_local_control = self.get_single_attr_value(self.ROOT_LOCAL_CONTROL_ATTR, node=self._output_node)
