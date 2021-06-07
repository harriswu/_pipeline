import maya.cmds as cmds

import _creation


def distance(point1, point2, name='distance1'):
    """
    get distance between given two points

    Args:
        point1 (str/list): first point, can be an attribute, list of values or list of attributes
        point2 (str/list): second point, can be an attribute, list of values or list of attributes
        name (str): node name

    Returns:
        output_attr (str): distance node's output attr
    """
    # create distance in between node
    dis_node = cmds.createNode('distanceInBetween', name=name)
    # connect vectors with dot node
    for pnt, attr in zip([point1, point2], ['point1', 'point2']):
        if isinstance(pnt, basestring):
            cmds.connectAttr(pnt, '{0}.{1}'.format(dis_node, attr))
        else:
            for val, axis in zip(pnt, ['X', 'Y', 'Z']):
                if isinstance(val, basestring):
                    cmds.connectAttr(val, '{0}.{1}{2}'.format(dis_node, attr, axis))
                else:
                    cmds.setAttr('{0}.{1}{2}'.format(dis_node, attr, axis), val)
    return dis_node + '.distance'


def mult_matrix(input_point, input_matrix, name='pntMtxMult1'):
    """
    get point by multiply point with matrix

    Args:
        input_point (str/list): can be an attribute, list of values or list of attributes
        input_matrix (str/list): can be an attribute, or list of values
        name (str): node name

    Returns:
        point (str): point matrix mult node output point attr
    """
    # create point matrix mult node
    mult_node = cmds.createNode('pointMatrixMult', name=name)
    # connect point
    if isinstance(input_point, basestring):
        cmds.connectAttr(input_point, mult_node + '.inPoint')
    else:
        for val, axis in zip(input_point, ['X', 'Y', 'Z']):
            if isinstance(val, basestring):
                cmds.connectAttr(val, '{0}.inPoint{1}'.format(mult_node, axis))
            else:
                cmds.setAttr('{0}.inPoint{1}'.format(mult_node, axis), val)
    # connect matrix
    if isinstance(input_matrix, basestring):
        cmds.connectAttr(input_matrix, mult_node + '.inMatrix')
    else:
        cmds.setAttr(mult_node + '.inMatrix', input_matrix, type='matrix')
    return mult_node + '.output'
