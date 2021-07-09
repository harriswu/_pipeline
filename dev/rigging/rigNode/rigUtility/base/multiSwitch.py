import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils

import dev.rigging.rigNode.rigUtility.core.coreUtility as coreUtility


class MultiSwitch(coreUtility.CoreUtility):
    ENUM1_ATTR = 'enum1'
    ENUM2_ATTR = 'enum2'
    ENUM_BLEND_ATTR = 'enumBlend'
    ENUM_SHOW_ALL_ATTR = 'enumShowAll'
    OUTPUT_ATTR = 'output'

    def __init__(self, **kwargs):
        super(MultiSwitch, self).__init__(**kwargs)
        self._input_enum1 = None
        self._input_enum2 = None
        self._input_blender = None
        self._input_show_all = None

        self._enum_attrs = None
        self._enum_blend_attr = None
        self._enum_show_all_attr = None
        self._enum_names = None
        self._enum_indexes = None

        self._condition_outputs = []

        self._output_attr = None

    @property
    def output_attr(self):
        return self._output_attr

    def get_build_kwargs(self, **kwargs):
        super(MultiSwitch, self).get_build_kwargs(**kwargs)
        self._additional_description = kwargs.get('additional_description', ['multiSwitch'])

    def get_connect_kwargs(self, **kwargs):
        super(MultiSwitch, self).get_connect_kwargs(**kwargs)
        self._input_enum1 = kwargs.get('input_enum1', None)
        self._input_enum2 = kwargs.get('input_enum2', None)
        self._input_blender = kwargs.get('input_blend', None)
        self._input_show_all = kwargs.get('input_show_all', None)

    def flip_connect_kwargs(self):
        super(MultiSwitch, self).flip_connect_kwargs()
        self._input_enum1 = namingUtils.flip_names(self._input_enum1)
        self._input_enum2 = namingUtils.flip_names(self._input_enum2)
        self._input_blender = namingUtils.flip_names(self._input_blender)
        self._input_show_all = namingUtils.flip_names(self._input_show_all)

    def add_input_attributes_post(self):
        super(MultiSwitch, self).add_input_attributes_post()
        # get enum info
        name, self._enum_names, self._enum_indexes = attributeUtils.get_enum_names(self._input_enum1)
        # add enum attr
        self._enum_attrs = attributeUtils.add(self._input_node, [self.ENUM1_ATTR, self.ENUM2_ATTR],
                                              attribute_type='enum', enum_name=name)
        self._enum_blend_attr = attributeUtils.add(self._input_node, self.ENUM_BLEND_ATTR, attribute_type='float',
                                                   value_range=[0, 1])[0]
        self._enum_show_all_attr = attributeUtils.add(self._input_node, self.ENUM_SHOW_ALL_ATTR,
                                                      attribute_type='bool')[0]

    def create_node_post(self):
        super(MultiSwitch, self).create_node_post()
        for name, index in zip(self._enum_names, self._enum_indexes):
            cond1_output = nodeUtils.utility.condition(self._enum_attrs[0], index, 1, 0,
                                                       name=namingUtils.update(self._node, type='condition',
                                                                               additional_description=['multiSwitch',
                                                                                                       name + 'A']),
                                                       operation='==')

            cond2_output = nodeUtils.utility.condition(self._enum_attrs[1], index, 1, 0,
                                                       name=namingUtils.update(self._node, type='condition',
                                                                               additional_description=['multiSwitch',
                                                                                                       name + 'B']),
                                                       operation='==')

            # add output together
            cond_sum = nodeUtils.arithmetic.equation('{0}+{1}'.format(cond1_output + 'R', cond2_output + 'R'),
                                                     namingUtils.update(self._node,
                                                                        additional_description=['multiSwitch',
                                                                                                name + 'ShowBoth']))

            # condition to blend between two attrs
            cond = namingUtils.update(self._node, type='condition',
                                      additional_description=['multiSwitch', name + 'Blend'])
            cond_blend_output = nodeUtils.utility.condition(self._enum_blend_attr, 0.5, cond1_output + 'R',
                                                            cond2_output + 'R', name=cond, operation='<')

            # condition to show both
            cond = namingUtils.update(self._node, type='condition',
                                      additional_description=['multiSwitch', name + 'showBoth'])
            output = nodeUtils.utility.condition(self._enum_show_all_attr, 0, cond_blend_output + 'R', cond_sum,
                                                 name=cond, operation='==')
            self._condition_outputs.append(output + 'R')

    def add_output_attributes_post(self):
        super(MultiSwitch, self).add_output_attributes_post()
        attributeUtils.add(self._output_node, self.OUTPUT_ATTR, attribute_type='bool', multi=True)

    def connect_input_attributes(self):
        super(MultiSwitch, self).connect_input_attributes()
        # connect with input enums
        attributeUtils.connect([self._input_enum1, self._input_enum2, self._input_blender, self._input_show_all],
                               [self._enum_attrs[0], self._enum_attrs[1], self._enum_blend_attr,
                                self._enum_show_all_attr])

    def connect_output_attributes(self):
        super(MultiSwitch, self).connect_output_attributes()
        attributeUtils.connect_nodes_to_multi_attr(self._condition_outputs, self.OUTPUT_ATTR, driven=self._output_node)
        self._output_attr = self.get_multi_attr_names(self.OUTPUT_ATTR, node=self._output_node)

    def get_input_info(self):
        super(MultiSwitch, self).get_input_info()
        self._enum_attrs = ['{0}.{1}'.format(self._input_node, self.ENUM1_ATTR),
                            '{0}.{1}'.format(self._input_node, self.ENUM2_ATTR)]
        self._enum_blend_attr = '{0}.{1}'.format(self._input_node, self.ENUM_BLEND_ATTR)
        self._enum_show_all_attr = '{0}.{1}'.format(self._input_node, self.ENUM_SHOW_ALL_ATTR)
        name, self._enum_names, self._enum_indexes = attributeUtils.get_enum_names(self._enum_attrs[0])

    def get_output_info(self):
        super(MultiSwitch, self).get_output_info()
        self._output_attr = self.get_multi_attr_names(self.OUTPUT_ATTR, node=self._output_node)
