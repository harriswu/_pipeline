import maya.cmds as cmds

import _creation
import arithmetic


def create(point1, point2, name='vector1'):
    """
    create vector node base on given point position values or attributes

    Args:
        point1 (str/list): first point's position, can be an attribute, list of values or list of attributes
        point2 (str/list): second point's position, can be an attribute, list of values or list of attributes
        name (str): node name

    Returns:
        output_attr (str): vector node's output attribute
    """
    # create plus minus average node as vector node
    output_attr = arithmetic.plus_minus_average(point2, point1, name=name, operation=2)
    return output_attr


def norm(vector, name='normVec1'):
    """
    normalize given vector

    Args:
        vector (str/list): vector need to be normalized, can be an attribute, list of values or list of attributes
        name (str): node name

    Returns:
        output_vector (str): normalized vector output attr
    """
    # create vector product node
    norm_node = _creation.create('vectorProduct', name, auto_suffix=False, normalizeOutput=1, operation=0)
    # connect vector with norm node
    if isinstance(vector, basestring):
        cmds.connectAttr(vector, norm_node + '.input1')
    else:
        for val, axis in zip(vector, ['X', 'Y', 'Z']):
            if isinstance(val, basestring):
                cmds.connectAttr(val, '{0}.input1{1}'.format(norm_node, axis))
            else:
                cmds.setAttr('{0}.input1{1}'.format(norm_node, axis), val)
    return norm_node + '.output'


def dot_product(vector1, vector2, name='dotProduct1'):
    """
    dot product two given vectors

    Args:
        vector1 (str/list): first vector, can be an attribute, list of values or list of attributes
        vector2 (str/list): second vector, can be an attribute, list of values or list of attributes
        name (str): node name

    Returns:
        output_attr (str): dot product output attr
    """
    # create vector product node
    dot_node = _creation.create('vectorProduct', name, auto_suffix=False, operation=1)
    # connect vectors with dot node
    for vec, attr in zip([vector1, vector2], ['input1', 'input2']):
        if isinstance(vec, basestring):
            cmds.connectAttr(vec, '{0}.{1}'.format(dot_node, attr))
        else:
            for val, axis in zip(vec, ['X', 'Y', 'Z']):
                if isinstance(val, basestring):
                    cmds.connectAttr(val, '{0}.{1}{2}'.format(dot_node, attr, axis))
                else:
                    cmds.setAttr('{0}.{1}{2}'.format(dot_node, attr, axis), val)
    return dot_node + '.outputX'


def cross_product(vector1, vector2, name='crossProduct1', normalize=True):
    """
    cross product two given vectors

    Args:
        vector1 (str/list): first vector, can be an attribute, list of values or list of attributes
        vector2 (str/list): second vector, can be an attribute, list of values or list of attributes
        name (str): node name
        normalize (bool): normalize the output vector, default is True

    Returns:
        output_vector (str): cross product output attr
    """
    # create vector product node
    cross_node = _creation.create('vectorProduct', name, auto_suffix=False, operation=2, normalizeOutput=normalize)
    # connect vectors with dot node
    for vec, attr in zip([vector1, vector2], ['input1', 'input2']):
        if isinstance(vec, basestring):
            cmds.connectAttr(vec, '{0}.{1}'.format(cross_node, attr))
        else:
            for val, axis in zip(vec, ['X', 'Y', 'Z']):
                if isinstance(val, basestring):
                    cmds.connectAttr(val, '{0}.{1}{2}'.format(cross_node, attr, axis))
                else:
                    cmds.setAttr('{0}.{1}{2}'.format(cross_node, attr, axis), val)
    return cross_node + '.output'
