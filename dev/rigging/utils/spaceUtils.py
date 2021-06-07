import os
from collections import OrderedDict

import utils.common.fileUtils as fileUtils
import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils

# config
import config
config_dir = os.path.dirname(config.__file__)
SPACE_CONFIG = fileUtils.jsonUtils.read(os.path.join(config_dir, 'SPACE.cfg'))

CUSTOM_INDEX = 100


# functions
def sort_spaces(spaces, default_values=None, custom_index=CUSTOM_INDEX):
    """
    get spaces ordered based on config indexes

    Args:
        spaces (list): space names
        default_values (list): default spaces
        custom_index (int): if given space is not in the config file, it's a custom space,
                            will start count index from given number

    Returns:
        spaces (OrderedDict): space info, contains space name and space index, ordered base on config file
        default_indexes (list): default spaces indexes
    """
    # get space enum names
    custom_space_index = custom_index

    spaces_info = {}
    # loop into each space and put into the list
    for spc in spaces:
        # check if space key in config
        if spc in SPACE_CONFIG:
            # get index from config
            index = SPACE_CONFIG[spc]
        else:
            # it's a custom space
            index = custom_space_index
            custom_space_index += 1
        spaces_info.update({spc: index})

    # sort spaces by index, and compose enum name
    spaces = OrderedDict(sorted(spaces_info.items(), key=lambda t: t[1]))

    # get default indexes
    default_indexes = [spaces.values()[0], spaces.values()[0]]
    if default_values:
        if default_values[0]:
            default_indexes[0] = spaces[default_values[0]]
        if default_values[1]:
            default_indexes[1] = spaces[default_values[1]]

    return spaces, default_indexes


def add_blend_attr(spaces, node, default_indexes, name='space'):
    """
    add space blend attributes

    Args:
        spaces (OrderedDict): spaces info, keys are the spaces, and values are spaces indexes
                              it must be sorted, use sort_spaces function to get the spaces
        node (str): add attributes to the given node
        default_indexes (list): default space indexes
        name (str): attribute name, will use this name for three attributes
                    (name)A: first space
                    (name)B: second space
                    (name)Blend: blender between first and second spaces
                    default is space

    Returns:
        space_blend_attrs (list): blend attributes, [spaceA, spaceB, spaceBlend, spaceBlendReverse]
    """
    # get enum name
    enum_name = ''
    for space, index in spaces.iteritems():
        enum_name += '{0}={1}:'.format(space, index)
    enum_name = enum_name[:-1]

    # add enum attributes
    space_blend_attrs = attributeUtils.add(node, [name + 'A', name + 'B'], attribute_type='enum',
                                           enum_name=enum_name, default_value=default_indexes, keyable=True,
                                           channel_box=True)
    # add blend attribute
    space_blend_attrs += attributeUtils.add(node, [name + 'Blend', name + 'RvsBlend'], attribute_type='float',
                                            value_range=[0, 1], keyable=True, channel_box=True)
    # connect blend attr with reverse blend attr
    nodeUtils.arithmetic.equation('~' + space_blend_attrs[-2],
                                  namingUtils.update(node, additional_description=name + 'Blend'),
                                  connect_attr=space_blend_attrs[-1])
    # lock and hide reverse blend attr
    attributeUtils.lock(space_blend_attrs[-1], channel_box=False)

    return space_blend_attrs
