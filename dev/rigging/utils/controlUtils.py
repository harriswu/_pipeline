import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.rigging.controlUtils as controlUtils

import spaceUtils
import dev.rigging.rigNode.rigUtility.base.spaceBlend as spaceBlend

# constant
CUSTOM_INDEX = 100
SPACE_NAME = 'space'
LOCAL_NODE = 'LOCAL'
DIVIDER_NAME = 'spaceBlend'


def add_spaces(ctrl, space_info, translate=True, rotate=True, scale=False, default_translate=None,
               default_rotate=None, default_scale=None, maintain_offset=True, parent=None, flip=False):
    """
    add space switch to given controller

    Args:
        ctrl (str): controller's name
        space_info (dict): space information, the keys are spaces names, and values are driver objects names
        translate (bool): blend translation
        rotate (bool): blend rotation
        scale (bool): blend scale
        default_translate (list): default translation spaces
        default_rotate (list): default rotation spaces
        default_scale (list): default scale spaces
        maintain_offset (bool): maintain offset for blend node
        parent (str): parent space blend node to the given node
        flip (bool): flip to do the opposite side
    """
    if flip:
        ctrl = namingUtils.flip_names(ctrl)
        space_info = namingUtils.flip_names(space_info)
        parent = namingUtils.flip_names(parent)

    # get driven node
    driven_node = controlUtils.get_hierarchy_node(ctrl, 'driven')

    input_matrices = {}
    # loop in each space and get world matrix attr as value
    for key, val in space_info.iteritems():
        # check if it's local node, local node is the controller's driven node
        if val == LOCAL_NODE:
            # get driven node as input node
            input_node = driven_node
        else:
            input_node = val

        # use world matrix as input matrix and add to space info
        input_matrices.update({key: '{0}.{1}'.format(input_node, attributeUtils.WORLD_MATRIX)})

    # get space sorted
    space_sort, _ = spaceUtils.sort_spaces(input_matrices.keys(), custom_index=CUSTOM_INDEX)

    # get control name info
    name_info = namingUtils.decompose(ctrl)

    # loop into translate, rotation and scale to add space blend
    for name_full, name_short, check, defaults in zip(['translate', 'rotate', 'scale'], ['trn', 'rot', 'scl'],
                                                      [translate, rotate, scale],
                                                      [default_translate, default_rotate, default_scale]):
        if check:
            # add separator
            attributeUtils.add_divider(ctrl, DIVIDER_NAME + name_short.title())

            # get default indexes
            default_indexes = [space_sort.values()[0], space_sort.values()[0]]
            # get defaults
            if defaults:
                if defaults[0]:
                    default_indexes[0] = space_sort[defaults[0]]
                if defaults[1]:
                    default_indexes[1] = space_sort[defaults[1]]

            # add blend attrs
            space_blend_attrs = spaceUtils.add_blend_attr(space_sort, ctrl, default_indexes,
                                                          name=SPACE_NAME + name_short.title())

            # add space blend node
            space_node = spaceBlend.SpaceBlend(flip=flip)
            build_kwargs = {'side': name_info['side'],
                            'description': name_info['description'],
                            'index': name_info['index'],
                            'limb_index': name_info['limb_index'],
                            'additional_description': SPACE_NAME + name_short.title(),
                            'parent_node': parent}
            space_node.build(**build_kwargs)
            connect_kwargs = {'input_matrices': input_matrices,
                              'translate': False,
                              'rotate': False,
                              'scale': False,
                              'parent_inverse_matrices': '{0}.{1}'.format(driven_node,
                                                                          attributeUtils.WORLD_INVERSE_MATRIX),
                              'maintain_offset': maintain_offset,
                              'defaults': defaults,
                              'input_space_attrs': space_blend_attrs[:2],
                              'input_blend_attr': space_blend_attrs[2],
                              'custom_space_index': CUSTOM_INDEX}
            connect_kwargs.update({name_full: True})
            space_node.connect(**connect_kwargs)
