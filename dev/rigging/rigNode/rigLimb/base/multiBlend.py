import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.mathUtils as mathUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.controlUtils as controlUtils

import dev.rigging.rigNode.rigLimb.core.coreLimb as coreLimb
import dev.rigging.rigNode.rigUtility.base.spaceBlend as spaceBlend
import dev.rigging.rigNode.rigUtility.base.multiSwitch as multiSwitch
import dev.rigging.utils.spaceUtils as spaceUtils
import dev.rigging.utils.limbUtils as limbUtils


class MultiBlend(coreLimb.CoreLimb):
    # constant attribute
    CUSTOM_SPACE_INDEX = 100
    MODE_NAME = 'mode'
    SHOW_ALL_ATTR = 'showAll'
    MULTI_SWITCH_OUTPUT_ATTR = 'multiSwitchOutput'
    EXTRA_BLEND_ATTR = 'extraBlends'

    def __init__(self, **kwargs):
        super(MultiBlend, self).__init__(**kwargs)
        self._guide_controls = kwargs.get('guide_controls', [])

        # connection
        self._input_limbs = None
        self._translate = None
        self._rotate = None
        self._scale = None
        self._defaults = None
        self._blend_input_matrix = None

        self._input_mode_attrs = None
        self._input_blend_attr = None
        self._input_show_all_attr = None

        self._extra_inputs = kwargs.get('extra_inputs', [])

        self._create_joints = True

        self._modes_sort = None
        self._default_indexes = None

        self._mode_attrs = []
        self._blend_attrs = []
        self._input_joints_matrices = {}
        self._input_matrices = {}
        self._extra_input_matrices = {}
        self._space_blend_node = None
        self._extra_blend_nodes = []
        self._multi_switch_node = None
        self._show_all_attr = None
        self._multi_switch_output_attr = None

    @property
    def mode_attrs(self):
        return self._mode_attrs

    @property
    def blend_attr(self):
        return self._blend_attrs[0]

    @property
    def show_all_attr(self):
        return self._show_all_attr

    def post_register_inputs(self):
        super(MultiBlend, self).post_register_inputs()
        self.register_blend_inputs()
        if not self._input_blend_attr:
            self.add_control_attr()
        self.register_input_matrices()

    def register_blend_inputs(self):
        # sort modes
        self._modes_sort, self._default_indexes = spaceUtils.sort_spaces(self._input_limbs.keys(),
                                                                         default_values=self._defaults,
                                                                         custom_index=self.CUSTOM_SPACE_INDEX)

        # add blend attr
        mode_blend_attrs = spaceUtils.add_blend_attr(self._modes_sort, self._input_node, self._default_indexes,
                                                     name=self.MODE_NAME)
        self._mode_attrs = mode_blend_attrs[:2]
        self._blend_attrs = mode_blend_attrs[2:]

        # add show all attr
        self._show_all_attr = attributeUtils.add(self._input_node, self.SHOW_ALL_ATTR, attribute_type='bool',
                                                 keyable=False, channel_box=True)[0]
        
    def get_connection_kwargs(self, **kwargs):
        super(MultiBlend, self).get_connection_kwargs(**kwargs)
        self._input_limbs = kwargs.get('input_limbs', {})
        self._translate = kwargs.get('translate', False)
        self._rotate = kwargs.get('rotate', True)
        self._scale = kwargs.get('scale', False)
        self._defaults = kwargs.get('defaults', [])
        self._blend_input_matrix = kwargs.get('blend_input_matrix', False)

        self._input_mode_attrs = kwargs.get('input_mode_attrs', None)
        self._input_blend_attr = kwargs.get('input_blend_attr', None)
        self._input_show_all_attr = kwargs.get('input_show_all_attr', None)

        self._extra_inputs = kwargs.get('extra_inputs', [])

    def register_input_matrices(self):
        for mode, limb_node in self._input_limbs.iteritems():
            # add matrix list attribute
            matrix_attr = attributeUtils.add(self._input_node, mode, attribute_type='matrix', multi=True)[0]

            # add input matrix attribute per mode
            input_matrix_attr = attributeUtils.add(self._input_node,
                                                   namingUtils.to_camel_case('{0}_{1}'.format(mode,
                                                                                              self.INPUT_MATRIX_ATTR)),
                                                   attribute_type='matrix', multi=False)[0]

            # get limb object
            limb_obj = limbUtils.get_limb_object(limb_node)
            # connect matrices
            attributeUtils.connect_nodes_to_multi_attr(limb_obj.joints, matrix_attr, driver_attr=attributeUtils.MATRIX)
            # connect each limb's input matrix
            if self._blend_input_matrix:
                attributeUtils.connect(limb_obj.input_matrix_attr, input_matrix_attr)
                self._input_matrices.update({mode: input_matrix_attr})
            # update input matrices
            self._input_joints_matrices.update({mode: self.get_multi_attr_names(mode, node=self._input_node)})

            # add extra inputs
            for extra_attr in self._extra_inputs:
                input_attr = getattr(limb_obj, extra_attr + '_attr')
                # add attribute
                extra_matrix_attr = attributeUtils.add(self._input_node,
                                                       namingUtils.to_camel_case('{0}_{1}'.format(mode, extra_attr)),
                                                       attribute_type='matrix', multi=True)[0]
                # connect with input attr
                attributeUtils.connect_nodes_to_multi_attr(input_attr, extra_matrix_attr)
                # update input matrices
                if extra_attr in self._extra_input_matrices:
                    self._extra_input_matrices[extra_attr].update({mode: self.get_multi_attr_names(extra_matrix_attr)})
                else:
                    self._extra_input_matrices[extra_attr] = {mode: self.get_multi_attr_names(extra_matrix_attr)}

        # connect if have input
        if self._input_mode_attrs:
            attributeUtils.connect(self._input_mode_attrs, self._mode_attrs)

        if self._input_blend_attr:
            attributeUtils.connect(self._input_blend_attr, self._blend_attrs[0])

        if self._input_show_all_attr:
            attributeUtils.connect(self._input_show_all_attr, self._show_all_attr)

    def create_controls(self):
        super(MultiBlend, self).create_controls()
        if self._guide_controls:
            name_info = namingUtils.decompose(self._guide_controls[0])
            ctrl = controlUtils.create(name_info['description'], side=name_info['side'], index=name_info['index'],
                                       limb_index=name_info['limb_index'], sub=False, parent=self._controls_group,
                                       position=self._guide_controls[0], rotate_order=0, manip_orient=None,
                                       lock_hide=attributeUtils.ALL, shape=self._control_shape,
                                       color=self._control_color, size=self._control_size,
                                       tag=self._tag_control)
            self._controls.append(ctrl)

    def add_control_attr(self):
        # add blend attr
        mode_blend_attrs = spaceUtils.add_blend_attr(self._modes_sort, self._controls[0], self._default_indexes,
                                                     name=self.MODE_NAME)
        show_all_attr = attributeUtils.add(self._controls[0], self.SHOW_ALL_ATTR, attribute_type='bool',
                                           keyable=False, channel_box=True)[0]

        # connect with input attrs
        attributeUtils.connect(mode_blend_attrs + [show_all_attr],
                               self._mode_attrs + self._blend_attrs + [self._show_all_attr])

    def post_build(self):
        super(MultiBlend, self).post_build()
        # get all joints joint orient attrs
        joint_orient_attrs = attributeUtils.compose_attrs(self._joints, 'jointOrient')

        # create blend node for input matrices
        name_info = namingUtils.decompose(self._node)
        self._space_blend_node = spaceBlend.SpaceBlend(side=name_info['side'], description=name_info['description'],
                                                       index=name_info['index'], limb_index=name_info['limb_index'],
                                                       additional_description='modeBlend',
                                                       parent_node=self._rig_nodes_group)
        self._space_blend_node.build()
        self._space_blend_node.connect(input_matrices=self._input_joints_matrices, joint_orients=joint_orient_attrs,
                                       translate=self._translate, rotate=self._rotate, scale=self._scale,
                                       input_space_attrs=self._mode_attrs, input_blend_attr=self._blend_attrs[0])

        # connect with joints
        for output_matrix_attr, joint in zip(self._space_blend_node.blend_matrix_attr, self._joints):
            # decompose matrix and connect with joint
            decompose = nodeUtils.create('decomposeMatrix', namingUtils.update(joint, type='decomposeMatrix'))
            cmds.connectAttr(output_matrix_attr, decompose + '.inputMatrix')
            if self._translate:
                cmds.connectAttr(decompose + '.outputTranslate', joint + '.translate')
            if self._rotate:
                cmds.connectAttr(decompose + '.outputRotate', joint + '.rotate')
            if self._scale:
                cmds.connectAttr(decompose + '.outputScale', joint + '.scale')

        # create blend node for input matrix
        if self._blend_input_matrix:
            blend_node = spaceBlend.SpaceBlend(side=name_info['side'], description=name_info['description'],
                                               index=name_info['index'], limb_index=name_info['limb_index'],
                                               additional_description='inputMatrixBlend',
                                               parent_node=self._rig_nodes_group)
            blend_node.build()
            blend_node.connect(input_matrices=self._input_matrices, translate=True, rotate=True, scale=True,
                               input_space_attrs=self._mode_attrs, input_blend_attr=self._blend_attrs[0])

            # get blend matrix value
            blend_matrix = cmds.getAttr(blend_node.blend_matrix_attr)
            # compute offset matrix
            offset_matrix = mathUtils.matrix.localize(mathUtils.matrix.IDENTITY, blend_matrix, output_type='list')
            # set offset matrix
            cmds.setAttr(self._offset_matrix_attr, offset_matrix, type='matrix')
            # connect input matrix
            attributeUtils.connect(blend_node.blend_matrix_attr, self._input_matrix_attr, force=True)

        # create blend node for extra inputs
        for extra_attr, extra_inputs_matrices in self._extra_input_matrices.iteritems():
            blend_node = spaceBlend.SpaceBlend(side=name_info['side'], description=name_info['description'],
                                               index=name_info['index'], limb_index=name_info['limb_index'],
                                               additional_description=namingUtils.to_camel_case(extra_attr + '_blend'),
                                               parent_node=self._rig_nodes_group)
            blend_node.build()
            blend_node.connect(input_matrices=extra_inputs_matrices, translate=True, rotate=True, scale=False,
                               input_space_attrs=self._mode_attrs, input_blend_attr=self._blend_attrs[0])

            self._extra_blend_nodes.append(blend_node)

        # create multi switch node
        self._multi_switch_node = multiSwitch.MultiSwitch(side=name_info['side'], description=name_info['description'],
                                                          index=name_info['index'], limb_index=name_info['limb_index'],
                                                          additional_description='visSwitch',
                                                          parent_node=self._rig_nodes_group)
        self._multi_switch_node.build()
        self._multi_switch_node.connect(input_enum1=self._mode_attrs[0], input_enum2=self._mode_attrs[1],
                                        input_blend=self._blend_attrs[0], input_show_all=self._show_all_attr)

        if self._controls:
            node = self._controls[0]
        else:
            node = self._input_node
        self._mode_attrs = ['{0}.{1}A'.format(node, self.MODE_NAME), '{0}.{1}B'.format(node, self.MODE_NAME)]
        self._blend_attrs = ['{0}.{1}Blend'.format(node, self.MODE_NAME),
                             '{0}.{1}BlendRvs'.format(node, self.MODE_NAME)]
        self._show_all_attr = '{0}.{1}'.format(node, self.SHOW_ALL_ATTR)

    def post_register_outputs(self):
        super(MultiBlend, self).post_register_outputs()
        # add extra output and connect with extra blend node
        # add attr to store all extra attribute names
        extra_blend_attr = attributeUtils.add(self._output_node, self.EXTRA_BLEND_ATTR, attribute_type='string')[0]
        extra_attr_list = []
        for attr, blend_node in zip(self._extra_input_matrices.keys(), self._extra_blend_nodes):
            # add matrix attr
            attr_plug = attributeUtils.add(self._output_node, namingUtils.to_camel_case(attr), attribute_type='matrix',
                                           multi=True)[0]
            # connect with blend node
            attributeUtils.connect_nodes_to_multi_attr(blend_node.blend_matrix_attr, attr_plug)
            # add attr to list
            extra_attr_list.append(attr)
            # add attribute to class
            self.add_object_attribute(attr + '_attr', self.get_multi_attr_names(attr_plug))
        # add extra attr list to extra blend attr
        cmds.setAttr(extra_blend_attr, str(extra_attr_list), type='string', lock=True)

        # connect multi switch output
        attributeUtils.add(self._output_node, self.MULTI_SWITCH_OUTPUT_ATTR, attribute_type='bool', multi=True)
        attributeUtils.connect_nodes_to_multi_attr(self._multi_switch_node.output_attr,
                                                   self.MULTI_SWITCH_OUTPUT_ATTR, driven=self._output_node)
        self._multi_switch_output_attr = self.get_multi_attr_names(self.MULTI_SWITCH_OUTPUT_ATTR,
                                                                   node=self._output_node)

        # connect with limb's control vis offset attr
        vis_attrs = []
        for mode in self._modes_sort.keys():
            # get limb node
            limb_node = self._input_limbs[mode]
            # get limb object
            limb_obj = limbUtils.get_limb_object(limb_node)
            # add control vis offset to list
            vis_attrs.append(limb_obj.controls_vis_offset_attr)

        # connect multi switch output to attributes
        attributeUtils.connect(self._multi_switch_output_attr, vis_attrs)

    def get_input_info(self):
        super(MultiBlend, self).get_input_info()
        if self._controls:
            node = self._controls[0]
        else:
            node = self._input_node
        self._mode_attrs = ['{0}.{1}A'.format(node, self.MODE_NAME), '{0}.{1}B'.format(node, self.MODE_NAME)]
        self._blend_attrs = ['{0}.{1}Blend'.format(node, self.MODE_NAME),
                             '{0}.{1}BlendRvs'.format(node, self.MODE_NAME)]
        self._show_all_attr = '{0}.{1}'.format(node, self.SHOW_ALL_ATTR)

    def get_output_info(self):
        super(MultiBlend, self).get_output_info()
        # get extra attrs
        extra_attrs = self.get_single_attr_value(self.EXTRA_BLEND_ATTR, node=self._output_node)
        # get each attr's output and add as attribute on current object
        for attr in extra_attrs:
            self.add_object_attribute(attr + '_attr', self.get_multi_attr_names(namingUtils.to_camel_case(attr),
                                                                                node=self._output_node))
