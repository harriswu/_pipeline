# import python external library
import numpy
from scipy.interpolate import interp1d

# import maya python library
import maya.cmds as cmds

# import utils
import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils
import utils.common.duplicateUtils as duplicateUtils
import utils.common.nodeUtils as nodeUtils
import utils.modeling.curveUtils as curveUtils
import utils.rigging.jointUtils as jointUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils
import utils.rigging.deformerUtils as deformerUtils

import dev.rigging.rigNode.rigLimb.core.coreLimb as coreLimb


class CurveChain(coreLimb.CoreLimb):
    # constant attribute
    CURVE_ATTR = 'curve'
    UP_CURVE_ATTR = 'upCurve'

    def __init__(self, **kwargs):
        super(CurveChain, self).__init__(**kwargs)
        self._guide_curves = None
        self._joints_number = None
        self._guide_controls = None
        self._control_manip_orient = None
        self._curve_skin_cluster = None
        self._uniform = None

        self._twist_curve_data = None
        self._twist_curve_kind = None

        self._volume = None
        self._volume_curve_data = None
        self._volume_curve_kind = None

        self._aim_vector = None
        self._up_vector = None
        self._aim_type = None

        self._curve = None
        self._up_curve = None
        self._constraints = []

        # get twist weights and volume weights
        self._twist_weights = None
        self._volume_weights = None

    @property
    def curve(self):
        return self._curve

    @property
    def up_curve(self):
        return self._up_curve

    def get_build_kwargs(self, **kwargs):
        super(CurveChain, self).get_build_kwargs(**kwargs)
        self._guide_curves = kwargs.get('guide_curves', None)
        self._joints_number = kwargs.get('joints_number', 10)
        self._guide_controls = kwargs.get('guide_controls', [])
        self._additional_description = kwargs.get('additional_description', ['curveChain'])
        self._control_manip_orient = kwargs.get('control_manip_orient', None)
        self._curve_skin_cluster = kwargs.get('curve_skin_cluster', '')
        self._uniform = kwargs.get('uniform', True)
        self._aim_type = kwargs.get('aim_type', 'tangent')

        self._twist_curve_data = kwargs.get('twist_curve_data', [[0, 0], [1, 1]])
        self._twist_curve_kind = kwargs.get('twist_curve_kind', 'linear')

        self._volume = kwargs.get('volume', False)
        self._volume_curve_data = kwargs.get('volume_curve_data', [[0, 0], [0.5, 1], [1, 0]])
        self._volume_curve_kind = kwargs.get('volume_curve_kind', 'quadratic')

        self._aim_vector = [1, 0, 0]
        self._up_vector = [0, 1, 0]

        # get twist weights and volume weights
        self._twist_weights = self.get_curve_values(self._twist_curve_data, self._twist_curve_kind)
        self._volume_weights = self.get_curve_values(self._volume_curve_data, self._volume_curve_kind)

    def flip_build_kwargs(self):
        super(CurveChain, self).flip_build_kwargs()
        self._guide_curves = namingUtils.flip_names(self._guide_curves)
        self._guide_controls = namingUtils.flip_names(self._guide_controls)
        self._control_manip_orient = namingUtils.flip_names(self._control_manip_orient)

        self._aim_vector = [-1, 0, 0]
        self._up_vector = [0, -1, 0]

    def add_output_attributes(self):
        super(CurveChain, self).add_output_attributes()
        attributeUtils.add(self._output_node, [self.CURVE_ATTR, self.UP_CURVE_ATTR], attribute_type='message')
        attributeUtils.connect('{0}.{1}'.format(self._curve, attributeUtils.MESSAGE),
                               self.CURVE_ATTR, driven=self._output_node)
        if self._up_curve:
            attributeUtils.connect('{0}.{1}'.format(self._up_curve, attributeUtils.MESSAGE),
                                   self.UP_CURVE_ATTR, driven=self._output_node)

    def get_output_info(self):
        super(CurveChain, self).get_output_info()
        self._curve = self.get_single_attr_value(self.CURVE_ATTR, node=self._output_node)
        self._up_curve = self.get_single_attr_value(self.UP_CURVE_ATTR, node=self._output_node)
    
    def create_node(self):
        self.create_curves()
        super(CurveChain, self).create_node()
    
    def create_setup(self):
        super(CurveChain, self).create_setup()
        self.add_twist()
        if self._create_joints:
            self.connect_joints()
            self.add_volume()

    def create_curves(self):
        # create curve from guide
        curves = []
        for guide in self._guide_curves:
            # get curve info
            curve_info = curveUtils.get_shape_info(guide)
            # create curve
            curve, curve_shape = curveUtils.create(namingUtils.update(guide, type='curve'),
                                                   curve_info['control_vertices'], curve_info['knots'],
                                                   degree=curve_info['degree'], form=curve_info['form'],
                                                   parent=self._nodes_world_group)
            curves.append(curve)

        self._curve = curves[0]
        if len(curves) == 2:
            self._up_curve = curves[-1]

    def create_controls(self):
        if not isinstance(self._control_manip_orient, list):
            self._control_manip_orient = [self._control_manip_orient] * len(self._guide_controls)

        # create controllers and joints to control the curve
        curve_jnts = []
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
            curve_jnts.append(jnt)

        # bind with the curve
        if self._curve_skin_cluster:
            # load skin cluster
            deformerUtils.skinCluster.import_data(self._curve_skin_cluster, geo=self._curve, flip=self._flip)
            if self._up_curve:
                deformerUtils.skinCluster.import_data(self._curve_skin_cluster, geo=self._up_curve, flip=self._flip)
        else:
            # give it a default skin cluster
            cmds.skinCluster(curve_jnts, self._curve, toSelectedBones=True, dropoffRate=6, bindMethod=0,
                             name=namingUtils.update(self._curve, type='skinCluster'))
            if self._up_curve:
                cmds.skinCluster(curve_jnts, self._up_curve, toSelectedBones=True, dropoffRate=6, bindMethod=0,
                                 name=namingUtils.update(self._up_curve, type='skinCluster'))

        # rebuild curve if uniform
        if self._uniform:
            curve_shape = cmds.listRelatives(self._curve, shapes=True)[0]
            spans = cmds.getAttr(curve_shape + '.spans')
            cmds.rebuildCurve(self._curve, replaceOriginal=True, rebuildType=0, endKnots=1, keepRange=0,
                              keepControlPoints=0, keepEndPoints=1, keepTangents=0, spans=spans, degree=3)
            if self._up_curve:
                up_curve_shape = cmds.listRelatives(self._up_curve, shapes=True)[0]
                spans = cmds.getAttr(up_curve_shape + '.spans')
                cmds.rebuildCurve(self._up_curve, replaceOriginal=True, rebuildType=0, endKnots=1, keepRange=0,
                                  keepControlPoints=0, keepEndPoints=1, keepTangents=0, spans=spans, degree=3)

    def create_joints(self):
        self._joints = jointUtils.create_along_curve(self._curve, self._joints_number, additional_description=None,
                                                     aim_vector=self._aim_vector, up_vector=self._up_vector,
                                                     up_curve=self._up_curve, aim_type=self._aim_type, flip_check=True,
                                                     parent_node=self._joints_group, chain=True)

    def create_setup_nodes(self):
        self._setup_nodes = transformUtils.create_along_curve(self._curve, self._joints_number, node_type='group',
                                                              additional_description=self._additional_description,
                                                              aim_vector=self._aim_vector, up_vector=self._up_vector,
                                                              up_curve=self._up_curve, aim_type=self._aim_type,
                                                              flip_check=True, parent_node=self._setup_group)

        self._constraints = constraintUtils.curve_constraint(self._curve, self._setup_nodes, skip_rotate=False,
                                                             aim_vector=self._aim_vector,
                                                             up_vector=self._up_vector, aim_type=self._aim_type,
                                                             up_curve=self._up_curve,
                                                             parent_inverse_matrix=self.INPUT_INVERSE_MATRIX_ATTR,
                                                             force=True)

    def connect_joints(self):
        # connect first and second node to joint
        constraintUtils.position_constraint(self._setup_nodes[0] + '.matrix', self._joints[0])
        constraintUtils.position_constraint(self._setup_nodes[1] + '.matrix', self._joints[1],
                                            parent_inverse_matrices='{0}.{1}'.format(self._joints[0],
                                                                                     attributeUtils.INVERSE_MATRIX))
        # connect attach nodes with joint one by one,
        # need to generate parent inverse matrix because joints are chain hierarchy
        matrix_plug = self._joints[0] + '.matrix'
        for i, (attach_node, joint) in enumerate(zip(self._setup_nodes[2:], self._joints[2:])):
            mult_matrix = cmds.createNode('multMatrix',
                                          name=namingUtils.update(joint, type='multMatrix',
                                                                  additional_description='parentMatrix'))
            cmds.connectAttr(self._joints[i+1] + '.matrix', mult_matrix + '.matrixIn[0]')
            cmds.connectAttr(matrix_plug, mult_matrix + '.matrixIn[1]')
            # inverse matrix
            invs_matrix = cmds.createNode('inverseMatrix',
                                          name=namingUtils.update(mult_matrix, type='inverseMatrix'))
            cmds.connectAttr(mult_matrix + '.matrixSum', invs_matrix + '.inputMatrix')
            # connect joint with attach node
            constraintUtils.position_constraint(attach_node + '.matrix', joint,
                                                parent_inverse_matrices=invs_matrix + '.outputMatrix')
            # override matrix plug
            matrix_plug = mult_matrix + '.matrixSum'

    def add_twist(self):
        # add twist if no up curve
        if not self._up_curve:
            # create twist transform for start and end controller
            twist_plugs = []
            for ctrl, jnt in zip([self._controls[0], self._controls[-1]],
                                 [self._setup_nodes[0], self._setup_nodes[-1]]):
                grp = transformUtils.create(namingUtils.update(ctrl, type='group', additional_description='twist'),
                                            parent=self._nodes_hide_group, position=jnt)
                grp_zero = transformUtils.offset_group(grp, namingUtils.update(grp, type='zero'))
                # rotate constraint with controller
                constraintUtils.position_constraint('{0}.{1}'.format(ctrl, controlUtils.OUT_MATRIX_ATTR), grp,
                                                    parent_inverse_matrices=grp_zero + '.inverseMatrix',
                                                    maintain_offset=True,
                                                    skip=['translateX', 'translateY', 'translateZ'],
                                                    force=True)
                # extract twist
                twist_attr = transformUtils.twist_extraction('{0}.{1}'.format(grp, attributeUtils.MATRIX), axis='x')
                twist_plugs.append(twist_attr)

            # connect twist
            for aim_con, w in zip(self._constraints[1], self._twist_weights):
                if 0 < w < 1:
                    nodeUtils.arithmetic.equation('(1 - {0}) * {1} + {0} * {2}'.format(w, twist_plugs[0],
                                                                                       twist_plugs[1]),
                                                  namingUtils.update(aim_con, additional_description='twist'),
                                                  connect_attr=aim_con + '.offsetX')
                elif w == 0:
                    cmds.connectAttr(twist_plugs[0], aim_con + '.offsetX')
                else:
                    cmds.connectAttr(twist_plugs[1], aim_con + '.offsetX')

    def add_volume(self):
        # add volume preservation
        if self._volume:
            # duplicate curve as reference
            ref_curve = duplicateUtils.duplicate_clean(self._curve,
                                                       name=namingUtils.update(self._curve,
                                                                               additional_description='reference'),
                                                       parent=self._nodes_hide_group)
            # create curve info nodes
            curve_info_nodes = []
            for crv in [self._curve, ref_curve]:
                curve_info = cmds.createNode('curveInfo', name=namingUtils.update(crv, type='curveInfo',
                                                                                  additional_description='stretch'))
                # get curve shape node
                curve_shape = cmds.listRelatives(self._curve, shapes=True)[0]
                # connect to curve info
                cmds.connectAttr(curve_shape + '.worldSpace[0]', curve_info + '.inputCurve')

                curve_info_nodes.append(curve_info)

            # divide to get stretch weight
            name = namingUtils.update(self._curve, additional_description='stretchWeight')
            stretch_weight_attr = nodeUtils.arithmetic.equation('{0}.distance/{1}'.format(curve_info_nodes[0],
                                                                                          curve_info_nodes[1]), name)

            # add volume control attr
            cmds.addAttr(self._controls[0], longName='volume', attributeType='float', minValue=0, defaultValue=1,
                         keyable=True)

            # loop in each joint to set volume weight
            for joint, w in zip(self._joints, self._volume_weights):
                # add weight value attr for each joint
                weight_attr = attributeUtils.add(joint, 'volumeWeight', attribute_type='float', default_value=w,
                                                 keyable=False, channel_box=True)[0]
                # connect with stretch ratio to get volume preservation
                vol_attr = nodeUtils.arithmetic.equation('{0}**({1}*{2})'.format(stretch_weight_attr, weight_attr,
                                                                                 self._controls[0] + '.volume'),
                                                         namingUtils.update(joint, additional_description='volume'))
                # connect with scale attr
                attributeUtils.connect([vol_attr, vol_attr], [joint + '.scaleY', joint + '.scaleZ'])

    def get_curve_values(self, data_points, kind):
        # get x values and y values
        x, y = zip(*data_points)
        # convert to numpy array
        x = numpy.array(x)
        y = numpy.array(y)
        # get curve
        f = interp1d(x, y, kind=kind)
        # get curve values base on joints number
        weights = []
        for i in range(self._joints_number):
            val = float(i)/(self._joints_number - 1)
            weights.append(f(val).tolist())
        return weights
