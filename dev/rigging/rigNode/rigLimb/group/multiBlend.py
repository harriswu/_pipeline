import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.mathUtils as mathUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.constraintUtils as constraintUtils

import rigGroup
import dev.rigging.utils.spaceUtils as spaceUtils
import dev.rigging.utils.limbUtils as limbUtils


class MultiBlend(rigGroup.RigGroup):
    CUSTOM_SPACE_INDEX = 100
    MODE_NAME = 'mode'
    SHOW_ALL_ATTR = 'showAll'
    MULTI_SWITCH_OUTPUT_ATTR = 'multiSwitchOutput'
    EXTRA_BLEND_ATTR = 'extraBlends'

    def __init__(self, **kwargs):
        super(MultiBlend, self).__init__(**kwargs)

        self._translate = False
        self._rotate = True
        self._scale = False
        self._defaults = None
        self._blend_input_matrix = False
        self._blend_input_matrix_translate = False
        self._blend_input_matrix_rotate = False
        self._blend_input_matrix_scale = False

        self._input_mode_attrs = None
        self._input_blend_attr = None
        self._input_show_all_attr = None

        self._create_joints = True

        self._extra_inputs = None

        self._modes_sort = None
        self._default_indexes = None

        self._mode_attrs = []
        self._blend_attrs = []
        self._show_all_attr = None

        self._blend_matrices = {'joints': {},
                                'input_matrix': {}}

        self._space_blend_node = None
        self._extra_blend_nodes = []
        self._multi_switch_node = None
        self._multi_switch_output_attr = None

    @property
    def modes(self):
        return self._limb_keys

    @property
    def mode_attrs(self):
        return self._mode_attrs

    @property
    def blend_attr(self):
        return self._blend_attrs[0]

    @property
    def show_all_attr(self):
        return self._show_all_attr

    def get_connect_kwargs(self, **kwargs):
        super(MultiBlend, self).get_connect_kwargs(**kwargs)
        self._translate = kwargs.get('translate', False)
        self._rotate = kwargs.get('rotate', True)
        self._scale = kwargs.get('scale', False)
        self._defaults = kwargs.get('defaults', [])
        self._blend_input_matrix_translate = kwargs.get('blend_input_matrix_translate', False)
        self._blend_input_matrix_rotate = kwargs.get('blend_input_matrix_rotate', False)
        self._blend_input_matrix_scale = kwargs.get('blend_input_matrix_scale', False)

        self._input_mode_attrs = kwargs.get('input_mode_attrs', None)
        self._input_blend_attr = kwargs.get('input_blend_attr', None)
        self._input_show_all_attr = kwargs.get('input_show_all_attr', None)

        self._extra_inputs = kwargs.get('extra_inputs', [])

        if self._blend_input_matrix_translate or self._blend_input_matrix_rotate or self._blend_input_matrix_scale:
            self._blend_input_matrix = True

    def flip_connect_kwargs(self):
        super(MultiBlend, self).flip_connect_kwargs()
        self._input_mode_attrs = namingUtils.flip_names(self._input_mode_attrs)
        self._input_blend_attr = namingUtils.flip_names(self._input_blend_attr)
        self._input_show_all_attr = namingUtils.flip_names(self._input_show_all_attr)

    def add_input_attributes_post(self):
        super(MultiBlend, self).add_input_attributes_post()
        self.add_blend_inputs()
        if self._controls:
            self.add_control_attributes()
        self.add_input_matrices()

    def add_blend_inputs(self):
        # sort modes
        self._modes_sort, self._default_indexes = spaceUtils.sort_spaces(self._input_limbs.keys(),
                                                                         default_values=self._defaults,
                                                                         custom_index=self.CUSTOM_SPACE_INDEX)

        # add blend attributes
        mode_blend_attrs = spaceUtils.add_blend_attr(self._modes_sort, self._input_node, self._default_indexes,
                                                     name=self.MODE_NAME)
        self._mode_attrs = mode_blend_attrs[:2]
        self._blend_attrs = mode_blend_attrs[2:]

        # add show all attr
        self._show_all_attr = attributeUtils.add(self._input_node, self.SHOW_ALL_ATTR, attribute_type='bool',
                                                 keyable=False, channel_box=True)[0]

        # connect if has input blend attrs
        if self._input_mode_attrs:
            attributeUtils.connect(self._input_mode_attrs, self._mode_attrs)

        if self._input_blend_attr:
            attributeUtils.connect(self._input_blend_attr, self._blend_attrs[0])

        if self._input_show_all_attr:
            attributeUtils.connect(self._input_show_all_attr, self._show_all_attr)

        # override limb keys
        self._limb_keys = self._modes_sort.keys()

    def add_control_attributes(self):
        # add blend attr
        mode_blend_attrs = spaceUtils.add_blend_attr(self._modes_sort, self._controls[0], self._default_indexes,
                                                     name=self.MODE_NAME)
        show_all_attr = attributeUtils.add(self._controls[0], self.SHOW_ALL_ATTR, attribute_type='bool',
                                           keyable=False, channel_box=True)[0]
        # connect with input attrs
        attributeUtils.connect(mode_blend_attrs + [show_all_attr],
                               self._mode_attrs + self._blend_attrs + [self._show_all_attr])

    def add_input_matrices(self):
        for mode, limb_node in self._input_limbs.iteritems():
            # add output matrix list attribute per mode
            matrix_attr = attributeUtils.add(self._input_node, mode, attribute_type='matrix', multi=True)[0]

            # get limb object
            limb_obj = limbUtils.info.get_limb_object(limb_node)
            # connect matrices
            attributeUtils.connect_nodes_to_multi_attr(limb_obj.joints, matrix_attr, driver_attr=attributeUtils.MATRIX)
            # update joints matrices dictionary
            self._blend_matrices['joints'].update({mode: self.get_multi_attr_names(mode, node=self._input_node)})

            # input matrix blend
            if self._blend_input_matrix:
                # add input matrix attr per mode
                input_matrix_attr = attributeUtils.add(self._input_node,
                                                       namingUtils.to_camel_case(mode + 'InputMatrix'),
                                                       attribute_type='matrix', multi=False)[0]
                # connect with limb's input matrix
                attributeUtils.connect(limb_obj.connect_matrix_attr, input_matrix_attr)
                # update input matrices dictionary
                self._blend_matrices['input_matrix'].update({mode: input_matrix_attr})

            # extra matrices blend
            for extra_attr in self._extra_inputs:
                input_attr = getattr(limb_obj, extra_attr + '_attr')
                # add attribute
                extra_matrix_attr = attributeUtils.add(self._input_node,
                                                       namingUtils.to_camel_case('{0}_{1}'.format(mode, extra_attr)),
                                                       attribute_type='matrix', multi=True)[0]
                # connect with input attr
                attributeUtils.connect_nodes_to_multi_attr(input_attr, extra_matrix_attr)
                # update input matrices
                if extra_attr in self._blend_matrices:
                    self._blend_matrices[extra_attr].update({mode: self.get_multi_attr_names(extra_matrix_attr)})
                else:
                    self._blend_matrices[extra_attr] = {mode: self.get_multi_attr_names(extra_matrix_attr)}

    def create_node_post(self):
        super(MultiBlend, self).create_node_post()
        # get all joints joint orient attribute
        joint_orient_attrs = attributeUtils.compose_attrs(self._joints, 'jointOrient')
        # create blend node for joint matrices
        build_kwargs = ({'additional_description': ['modeBlend'],
                         'parent_node': self._sub_nodes_group})
        connect_kwargs = {'input_matrices': self._blend_matrices['joints'],
                          'joint_orients': joint_orient_attrs,
                          'translate': self._translate,
                          'rotate': self._rotate,
                          'scale': self._scale,
                          'input_space_attrs': self._mode_attrs,
                          'input_blend_attr': self._blend_attrs[0]}

        space_blend_node = self.create_rig_node('dev.rigging.rigNode.rigUtility.base.spaceBlend',
                                                name_template=self._node,
                                                build=True, build_kwargs=build_kwargs,
                                                connect=True, connect_kwargs=connect_kwargs, flip=self._flip)

        # connect blend node's output matrices to joints
        for output_matrix_attr, joint in zip(space_blend_node.blend_matrix_attr, self._joints):
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
            build_kwargs = ({'additional_description': ['inputMatrixBlend'],
                             'parent_node': self._sub_nodes_group})
            connect_kwargs = {'input_matrices': self._blend_matrices['input_matrix'],
                              'translate': self._blend_input_matrix_translate,
                              'rotate': self._blend_input_matrix_rotate,
                              'scale': self._blend_input_matrix_scale,
                              'input_space_attrs': self._mode_attrs,
                              'input_blend_attr': self._blend_attrs[0]}
            blend_node = self.create_rig_node('dev.rigging.rigNode.rigUtility.base.spaceBlend',
                                              name_template=self._node,
                                              build=True, build_kwargs=build_kwargs,
                                              connect=True, connect_kwargs=connect_kwargs, flip=self._flip)
            # override connections with related nodes
            if self._blend_input_matrix_translate or self._blend_input_matrix_rotate:
                if self._blend_input_matrix_translate:
                    skip = attributeUtils.ROTATE
                else:
                    skip = attributeUtils.TRANSLATE
                constraintUtils.position_constraint(blend_node.blend_matrix_attr, self._local_group,
                                                    maintain_offset=False, skip=skip, force=True)
            if self._blend_input_matrix_scale:
                constraintUtils.scale_constraint(blend_node.blend_matrix_attr, self._local_group, force=True)

        # create blend node for extra inputs
        for attr, input_matrices in self._blend_matrices.iteritems():
            if attr not in ['joints', 'input_matrix'] and input_matrices:
                build_kwargs = ({'additional_description': [namingUtils.to_camel_case(attr + 'Blend')],
                                 'parent_node': self._sub_nodes_group})
                connect_kwargs = {'input_matrices': input_matrices,
                                  'translate': True,
                                  'rotate': True,
                                  'scale': False,
                                  'input_space_attrs': self._mode_attrs,
                                  'input_blend_attr': self._blend_attrs[0]}
                blend_node = self.create_rig_node('dev.rigging.rigNode.rigUtility.base.spaceBlend',
                                                  name_template=self._node,
                                                  build=True, build_kwargs=build_kwargs,
                                                  connect=True, connect_kwargs=connect_kwargs, flip=self._flip)
                self._blend_matrices[attr].update({'blend_node': blend_node})

        # create multi switch node
        build_kwargs = ({'additional_description': ['visSwitch'],
                         'parent_node': self._sub_nodes_group})
        connect_kwargs = {'input_enum1': self._mode_attrs[0],
                          'input_enum2': self._mode_attrs[1],
                          'input_blend': self._blend_attrs[0],
                          'input_show_all': self._show_all_attr}
        self._multi_switch_node = self.create_rig_node('dev.rigging.rigNode.rigUtility.base.multiSwitch',
                                                       name_template=self._node,
                                                       build=True, build_kwargs=build_kwargs,
                                                       connect=True, connect_kwargs=connect_kwargs, flip=self._flip)

        # override mode attrs
        if self._controls:
            node = self._controls[0]
        else:
            node = self._input_node
        self._mode_attrs = ['{0}.{1}A'.format(node, self.MODE_NAME), '{0}.{1}B'.format(node, self.MODE_NAME)]
        self._blend_attrs = ['{0}.{1}Blend'.format(node, self.MODE_NAME),
                             '{0}.{1}BlendRvs'.format(node, self.MODE_NAME)]
        self._show_all_attr = '{0}.{1}'.format(node, self.SHOW_ALL_ATTR)

    def add_output_attributes_post(self):
        super(MultiBlend, self).add_output_attributes_post()
        # compose extra attrs as a string to get the info in query
        extra_blend_attr = attributeUtils.add(self._output_node, self.EXTRA_BLEND_ATTR, attribute_type='string')[0]
        extra_attr_list = []
        for attr in self._blend_matrices:
            if attr not in ['joints', 'input_matrix']:
                # get blend node
                blend_node = self._blend_matrices[attr]['blend_node']
                # add attribute to output node
                attr_plug = attributeUtils.add(self._output_node, namingUtils.to_camel_case(attr),
                                               attribute_type='matrix', multi=True)[0]
                # connect with blend node
                attributeUtils.connect_nodes_to_multi_attr(blend_node.blend_matrix_attr, attr_plug)
                # add attr to list
                extra_attr_list.append(attr)
                # add attribute to class
                self.add_object_attribute(attr + '_attr', self.get_multi_attr_names(attr_plug))
        # convert extra attr list as string and set to the attribute
        cmds.setAttr(extra_blend_attr, str(extra_attr_list), type='string', lock=True)

        # add multi switch attributes
        attributeUtils.add(self._output_node, self.MULTI_SWITCH_OUTPUT_ATTR, attribute_type='bool', multi=True)
        attributeUtils.connect_nodes_to_multi_attr(self._multi_switch_node.output_attr,
                                                   self.MULTI_SWITCH_OUTPUT_ATTR, driven=self._output_node)
        self._multi_switch_output_attr = self.get_multi_attr_names(self.MULTI_SWITCH_OUTPUT_ATTR,
                                                                   node=self._output_node)

    def connect_output_attributes(self):
        super(MultiBlend, self).connect_output_attributes()
        # connect vis switch to limb's vis offset attr
        vis_attrs = []
        for mode in self._modes_sort.keys():
            # get limb node
            limb_node = self._input_limbs[mode]
            # get limb object
            limb_obj = limbUtils.info.get_limb_object(limb_node)
            # add control vis offset to list
            vis_attrs.append(limb_obj.controls_vis_attr)

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
