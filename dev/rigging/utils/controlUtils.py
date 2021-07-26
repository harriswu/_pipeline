import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.mathUtils as mathUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import spaceUtils
import dev.rigging.rigNode.rigUtility.base.spaceBlend as spaceBlend

# constant
CUSTOM_INDEX = 100
SPACE_NAME = 'space'
LOCAL_NODE = 'LOCAL'
DIVIDER_NAME = 'space'


def add_spaces(ctrl, space_info, **kwargs):
    """
    add space switch to given controller

    Args:
        ctrl (str): controller's name
        space_info (dict): space information, the keys are spaces names, and values are driver objects names
    Keyword Args:
        translate (bool): blend translation
        rotate (bool): blend rotation
        scale (bool): blend scale
        default_translate (list): default translation spaces
        default_rotate (list): default rotation spaces
        default_scale (list): default scale spaces
        blend_translate (float): default blend value for translation
        blend_rotate (float): default blend value for rotation
        blend_scale (float): default blend value for scale
        maintain_offset (bool): maintain offset for blend node
        parent (str): parent space blend node to the given node
        flip (bool): flip to do the opposite side
    """
    translate = kwargs.get('translate', True)
    rotate = kwargs.get('rotate', True)
    scale = kwargs.get('scale', False)
    default_translate = kwargs.get('default_translate', None)
    default_rotate = kwargs.get('default_rotate', None)
    default_scale = kwargs.get('default_scale', None)
    blend_translate = kwargs.get('blend_translate', 0)
    blend_rotate = kwargs.get('blend_rotate', 0)
    blend_scale = kwargs.get('blend_scale', 0)
    maintain_offset = kwargs.get('maintain_offset', True)
    parent = kwargs.get('parent', None)
    flip = kwargs.get('flip', False)

    if flip:
        ctrl = namingUtils.flip_names(ctrl)
        space_info = namingUtils.flip_names(space_info)
        parent = namingUtils.flip_names(parent)

    # get driven node
    driven_node = controlUtils.get_hierarchy_node(ctrl, 'driven')

    # get driven node world matrix
    world_matrix_ctrl = cmds.getAttr('{0}.{1}'.format(driven_node, attributeUtils.WORLD_MATRIX))

    input_matrices = {}
    # loop in each space and get world matrix attr as value
    for key, val in space_info.iteritems():
        # check if it's local node, local node is the controller's driven node
        if val == LOCAL_NODE:
            # get driven node as input node
            input_node = driven_node
        elif controlUtils.is_control(val):
            input_node = controlUtils.get_hierarchy_node(val, 'output')
        else:
            input_node = val

        # get input matrix attr
        input_matrix_attr = '{0}.{1}'.format(input_node, attributeUtils.WORLD_MATRIX)
        if maintain_offset:
            # get offset value and multiply with input matrix
            offset_matrix = mathUtils.matrix.localize(world_matrix_ctrl, cmds.getAttr(input_matrix_attr),
                                                      output_type='list')
            driver_matrix = nodeUtils.matrix.mult_matrix(offset_matrix,  input_matrix_attr,
                                                         name=namingUtils.update(ctrl, type='multMatrix',
                                                                                 additional_description=['offset',
                                                                                                         key]))
            # use world matrix as input matrix and add to space info
            input_matrices.update({key: driver_matrix})
        else:
            input_matrices.update({key: input_matrix_attr})

    # get space sorted
    space_sort, _ = spaceUtils.sort_spaces(input_matrices.keys(), custom_index=CUSTOM_INDEX)

    # loop into translate, rotation and scale to add space blend
    for name_full, name_short, check, defaults, blend, attrs in zip(['translate', 'rotate', 'scale'],
                                                                    ['trn', 'rot', 'scl'],
                                                                    [translate, rotate, scale],
                                                                    [default_translate, default_rotate, default_scale],
                                                                    [blend_translate, blend_rotate, blend_scale],
                                                                    [attributeUtils.TRANSLATE, attributeUtils.ROTATE,
                                                                     attributeUtils.SCALE]):
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
            space_blend_attrs = spaceUtils.add_blend_attr(space_sort, ctrl, default_indexes, blend_value=blend,
                                                          name=SPACE_NAME + name_short.title())

            # add space blend node
            # get control name info
            name_info = namingUtils.decompose(ctrl)

            space_node = spaceBlend.SpaceBlend()
            space_node.register_steps()
            build_kwargs = {'side': name_info.get('side', 'center'),
                            'description': name_info.get('description', None),
                            'index': name_info.get('index', 1),
                            'limb_index': name_info.get('limb_index', 1),
                            'additional_description': [SPACE_NAME + name_short.title()],
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

            # connect to control's space group
            space_group = controlUtils.get_hierarchy_node(ctrl, 'space')
            skip_attrs = []
            for atr in attributeUtils.TRANSFORM:
                if atr not in attrs:
                    skip_attrs.append(atr)
            constraintUtils.matrix_connect(space_node.blend_matrix_attr[0], space_group, skip=skip_attrs)
