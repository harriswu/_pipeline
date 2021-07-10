import maya.cmds as cmds

import _creation
import utils.common.attributeUtils as attributeUtils


def condition(first_term, second_term, if_true, if_false, name='condition1', operation=1, connect_attr=None,
              force=True):
    """
    connect attrs with condition node

    Args:
        first_term(str/float): first term
        second_term(str/float): secondTerm
        if_true(str/float/list): color if True
        if_false(str/float/list): color if False
        name (str): node name
        operation(int/str): condition node's operation
                            0['=='] equal
                            1['!='] not equal
                            2['>']  greater than
                            3['>='] greater or equal
                            4['<']  less than
                            5['<='] less or equal
                            default is 0
        connect_attr(str/list): connect the condition output to given attrs
        force(bool): force the connection, default is True

    Returns:
        output_attr(str): output attribute from the condition node
    """
    # get operation
    if isinstance(operation, basestring):
        op_list = ['==', '!=', '>', '>=', '<', '<=']
        operation = op_list.index(operation)

    cond = _creation.create('condition', name, operation=operation)

    # set or connect attrs
    attributeUtils.set_connect_single_attr(cond + '.firstTerm', first_term)
    attributeUtils.set_connect_single_attr(cond + '.secondTerm', second_term)

    attributeUtils.set_connect_3d_attr(cond + '.colorIfTrue', if_true, attr_suffix='RGB')
    attributeUtils.set_connect_3d_attr(cond + '.colorIfFalse', if_false, attr_suffix='RGB')

    # connect attrs
    if connect_attr:
        if isinstance(connect_attr, basestring):
            connect_attr = [connect_attr]
            for attr in connect_attr:
                # check output type
                attr_type = cmds.getAttr(attr, type=True)
                if attr_type.endswith('3'):
                    # 3d output, connect with outColor directly
                    attributeUtils.connect(cond + '.outColor', attr, force=force)
                else:
                    # connect using condition's first slot
                    attributeUtils.connect(cond + '.outColorR', attr, force=force)

    return cond + '.outColor'


def remap_value(input_value, input_range=None, output_range=None, name=None, connect_attr=None, force=True):
    """
    remap given value

    Args:
        input_value (str/float/int): input value needs to be remapped
        input_range (list): input min and max values, can be attributes or values
        output_range (list): output min and max values, can be attributes or values
        name (str): node's name
        connect_attr (str/list): connect remap output to given attributes
        force (bool): force connection, default is True

    Returns:
        output_attr (str): remap value output value attr
    """
    if not input_range:
        input_range = [0, 1]
    if not output_range:
        output_range = [0, 1]

    remap_node = cmds.createNode('remapValue', name=name)
    # connect attributes for each input
    for in_val, attr in zip([input_value, input_range[0], input_range[1], output_range[0], output_range[1]],
                            ['inputValue', 'inputMin', 'inputMax', 'outputMin', 'outputMax']):
        if isinstance(in_val, basestring):
            cmds.connectAttr(in_val, '{0}.{1}'.format(remap_node, attr))
        else:
            cmds.setAttr('{0}.{1}'.format(remap_node, attr), in_val)

    output_attr = remap_node + '.outValue'

    if connect_attr:
        attributeUtils.connect(output_attr, connect_attr, force=force)

    return output_attr


def blend_colors(blender, color1, color2, name='blendColors1', connect_attr=None, force=True):
    """
    connect attrs with blendColor node

    Args:
        blender(str/float): blendColor's blender
        color1(str/float/list): blendColor's color1
        color2(str/float/list): blendColor's color2
        name (str): node name
        connect_attr(str/list): connect the condition output to given attrs
        force(bool): force the connection, default is True

    Returns:
        output_attr (str): blend colors output attr
    """
    blend_node = cmds.createNode('blendColors', name=name)
    # connect attributes for inputs
    attributeUtils.set_connect_single_attr(blend_node + '.blender', blender)

    attributeUtils.set_connect_3d_attr(blend_node + '.color1', color1, attr_suffix='RGB')
    attributeUtils.set_connect_3d_attr(blend_node + '.color2', color2, attr_suffix='RGB')
    # connect attrs
    if connect_attr:
        if isinstance(connect_attr, basestring):
            connect_attr = [connect_attr]
            for attr in connect_attr:
                # check output type
                attr_type = cmds.getAttr(attr, type=True)
                if attr_type.endswith('3'):
                    # 3d output, connect with outColor directly
                    attributeUtils.connect(blend_node + '.output', attr, force=force)
                else:
                    # connect using condition's first slot
                    attributeUtils.connect(blend_node + '.outputR', attr, force=force)

    return blend_node + '.output'
