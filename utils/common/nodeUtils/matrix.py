import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils


def compose_matrix(name='composeMatrix1', translate=None, rotate=None, scale=None, rotate_order=0, connect_attr=None,
                   force=True):
    """
    connect attrs with compose matrix node

    Args:
        name (str): compose matrix name
        translate(list): input translate
                         each can be attribute/float, default is [0, 0, 0]
        rotate(list): input rotate
                      each can be attribute/float, default is [0, 0, 0]
        scale(list): input scale
                     each can be attribute/float, default is [1,1,1]
        rotate_order(int/str): input rotate order, default is 0
        connect_attr(str/list): connect the composeMatrix output to given attrs
        force(bool): force the connection, default is True

    Returns:
        output_attr(str): output attribute from the node
    """
    if not translate:
        translate = [0, 0, 0]
    if not rotate:
        rotate = [0, 0, 0]
    if not scale:
        scale = [1, 1, 1]

    # create node
    matrix_node = cmds.createNode('composeMatrix', name=name)

    for input_attr_info in zip([translate, rotate, scale], ['translate', 'rotate', 'scale']):
        for input_val in zip(input_attr_info[0], ['X', 'Y', 'Z']):
            if isinstance(input_val[0], basestring):
                cmds.connectAttr(input_val[0],
                                 '{0}.input{1}{2}'.format(matrix_node, input_attr_info[1].title(), input_val[1]))
            else:
                cmds.setAttr('{0}.input{1}{2}'.format(matrix_node, input_attr_info[1].title(), input_val[1]),
                             input_val[0])

    if isinstance(rotate_order, basestring):
        cmds.connectAttr(rotate_order, matrix_node + '.inputRotateOrder')
    else:
        cmds.setAttr(matrix_node + '.inputRotateOrder', rotate_order)

    output_attr = matrix_node + '.outputMatrix'

    # connect output
    if connect_attr:
        attributeUtils.connect(output_attr, connect_attr, force=force)

    # return output_attr
    return output_attr


def mult_matrix(*input_matrices, **kwargs):
    """
    connect attrs with mult matrix node

    Args:
        *input_matrices(str/list): input matrix attribute/value

    Keyword Args:
        name (str): mult matrix node's name
        connect_attr(str/list): connect the plusMinusAverage output to given attrs
        force(bool): force the connection, default is True

    Returns:
        output_attr(str): output attribute from the multMatrix node
    """
    name = kwargs.get('name', 'multMatrix1')
    connect_attr = kwargs.get('connect_attr', None)
    force = kwargs.get('force', True)

    matrix_node = cmds.createNode('multMatrix', name=name)
    # input attrs
    for i, matrix in enumerate(input_matrices):
        if isinstance(matrix, basestring):
            cmds.connectAttr(matrix, '{0}.matrixIn[{1}]'.format(matrix_node, i))
        elif matrix is not None:
            cmds.setAttr('{0}.matrixIn[{1}]'.format(matrix_node, i), matrix, type='matrix')

    # get output attr
    output_attr = matrix_node + '.matrixSum'

    # connect output
    if connect_attr:
        attributeUtils.connect(output_attr, connect_attr, force=force)

    return output_attr


def inverse_matrix(input_matrix, **kwargs):
    """
    connect attrs with inverse matrix node

    Args:
        input_matrix(str): input matrix attr

    Keyword Args:
        name (str): mult matrix node's name
        connect_attr(str/list): connect the plusMinusAverage output to given attrs
        force(bool): force the connection, default is True

    Returns:
        output_attr(str): output attribute from the node
    """

    # get vars
    name = kwargs.get('name', 'inverseMatrix1')
    connect_attr = kwargs.get('connect_attr', None)
    force = kwargs.get('force', True)

    # create node
    matrix_node = cmds.createNode('inverseMatrix', name=name)

    # input attrs
    cmds.connectAttr(input_matrix, matrix_node + '.inputMatrix')

    output_attr = matrix_node + '.outputMatrix'

    # connect output
    if connect_attr:
        attributeUtils.connect(output_attr, connect_attr, force=force)

    return output_attr


def twist_extraction(input_matrix, axis='x', additional_description=None, connect_attr=None, force=None):
    """
    extract twist value from input matrix

    Args:
        input_matrix (str): input matrix attribute
        axis (str/list): axis need to extracted, default is x
        additional_description (str): additional description add to utility nodes
        connect_attr(str/list): connect the plusMinusAverage output to given attrs
        force(bool): force the connection, default is True

    Returns:
        output_attr (str): twist attribute path
    """
    if not additional_description:
        additional_description = 'twistExtract'
    elif isinstance(additional_description, list):
        additional_description = ''.join(additional_description)

    # create decompose matrix and quat to euler node
    decompose = cmds.createNode('decomposeMatrix')
    quat_euler = cmds.createNode('quatToEuler')

    twist_nodes = [decompose, quat_euler]

    # rename nodes if follow naming convention
    # get node name
    attr_path, node, attr_name = attributeUtils.check_exists(input_matrix)
    # check if node's name is following naming convention, if so, store nodes name in a list for further usage
    if namingUtils.check(node):
        twist_nodes[0] = cmds.rename(twist_nodes[0],
                                     namingUtils.update(node, type='decomposeMatrix',
                                                        additional_description=additional_description + axis.upper()))
        twist_nodes[1] = cmds.rename(twist_nodes[1],
                                     namingUtils.update(node, type='quatToEuler',
                                                        additional_description=additional_description + axis.upper()))

    # connect input matrix with decompose matrix
    cmds.connectAttr(input_matrix, twist_nodes[0] + '.inputMatrix')
    # connect quat values to quat to euler
    cmds.connectAttr('{0}.outputQuat{1}'.format(twist_nodes[0], axis.upper()),
                     '{0}.inputQuat{1}'.format(twist_nodes[1], axis.upper()))
    cmds.connectAttr(twist_nodes[0] + '.outputQuatW', twist_nodes[1] + '.inputQuatW')

    # get twist attr as output attr
    output_attr = '{0}.outputRotate{1}'.format(twist_nodes[1], axis.upper())

    # connect output
    if connect_attr:
        attributeUtils.connect(output_attr, connect_attr, force=force)

    return output_attr
