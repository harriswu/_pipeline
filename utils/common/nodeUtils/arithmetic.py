import maya.cmds as cmds

import _creation
from _equation import equation
import utils.common.attributeUtils as attributeUtils


def plus_minus_average(*input_attrs, **kwargs):
    """
    create plusMinusAverage node

    Args:
        *input_attrs (str/float/int/list): input attribute/value
    Keyword Args:
        name (str): node name
        operation (int): plusMinusAverage node's operation
        connect_attr(str/list): connect the plusMinusAverage output to given attrs
        force(bool): force the connection, default is True

    Returns:
        output_attr(str): output attribute from the plusMinusAverage node
    """
    name = kwargs.get('name', 'plusMinusAverage1')
    operation = kwargs.get('operation', 1)
    connect_attr = kwargs.get('connect_attr', None)
    force = kwargs.get('force', True)

    pmav = _creation.create('plusMinusAverage', name, operation=operation)

    # check input attr's type to define input and output type
    if isinstance(input_attrs[0], list):
        # it's a list of values/attributes
        if len(input_attrs[0]) == 2:
            plug_type = '2D'
        else:
            plug_type = '3D'
    elif not isinstance(input_attrs[0], basestring):
        # it's not an attribute, which means it's a number
        plug_type = '1D'
    else:
        # it's an attribute, check the attribute type
        attr_type = cmds.getAttr(input_attrs[0], type=True)
        if attr_type.endswith('2'):
            plug_type = '2D'
        elif attr_type.endswith('3'):
            plug_type = '3D'
        else:
            plug_type = '1D'

    # loop in each input attr and connect with plusMinusAverage node
    for i, attr in enumerate(input_attrs):
        if isinstance(attr, basestring):
            # it's an attribute, plug to the node directly
            cmds.connectAttr(attr, '{0}.input{1}[{2}]'.format(pmav, plug_type, i))
        elif isinstance(attr, list):
            for val, axis in zip(attr, ['x', 'y', 'z']):
                if isinstance(val, basestring):
                    # connect attribute directly
                    cmds.connectAttr(val, '{0}.input{1}[{2}].input{1}{3}'.format(pmav, plug_type, i, axis))
                else:
                    # it's a value, set value
                    cmds.setAttr('{0}.input{1}[{2}].input{1}{3}'.format(pmav, plug_type, i, axis), val)
        else:
            # it's a single value
            cmds.setAttr('{0}.input{1}[{2}]'.format(pmav, plug_type, i), attr)

    # get output attr
    output_attr = '{0}.output{1}'.format(pmav, plug_type)

    # connect output
    if connect_attr:
        attributeUtils.connect(output_attr, connect_attr, force=force)

    return output_attr


def multiply_divide(input1, input2, **kwargs):
    """
    create multiplyDivide node

    Args:
        input1 (str/list): first input attribute/value
        input2 (str/list): second input attribute/value
    Keyword Args:
        name (str): node name
        operation (int): multiply divide node's operation
        connect_attr(str/list): connect the multiplyDivide output to given attrs
        force(bool): force the connection, default is True

    Returns:
        output_attr(str): output attribute from the multiplyDivide node
    """
    name = kwargs.get('name', 'mutliplyDivide1')
    operation = kwargs.get('operation', 1)
    connect_attr = kwargs.get('connect_attr', None)
    force = kwargs.get('force', True)

    mult = _creation.create('multiplyDivide', name, operation=operation)
    for i, input_attr in enumerate([input1, input2]):
        if isinstance(input_attr, basestring):
            cmds.connectAttr(input_attr, '{0}.input{1}'.format(mult, i+1))
        else:
            for val, axis in zip(input_attr, ['X', 'Y', 'Z']):
                if isinstance(val, basestring):
                    cmds.connectAttr(val, '{0}.input{1}{2}'.format(mult, i+1, axis))
                else:
                    cmds.setAttr('{0}.input{1}{2}'.format(mult, i+1, axis), val)

    # get output attr
    output_attr = mult + '.output'

    # connect output
    if connect_attr:
        attributeUtils.connect(output_attr, connect_attr, force=force)

    return output_attr
