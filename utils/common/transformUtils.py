# import maya python library
import maya.cmds as cmds

# import utils
import namingUtils
import apiUtils
import attributeUtils
import hierarchyUtils
import utils.modeling.curveUtils as curveUtils


# function
def create(name, lock_hide=None, parent=None, rotate_order=0, visibility=True, position=None, matrix=None,
           inherits_transform=True):
    """
    create transform node

    Args:
        name (str): transform node's name
        lock_hide (list): lock and hide transform attrs
        parent (str): where to parent the transform node
        rotate_order (int): transform node's rotate order, default is 0
        visibility (bool): transform node's visibility, default is True
        position (str/list): match transform node's transformation to given node/transform value
                             str: match translate,rotateto the given node
                             [str/None, str/None, str/None]: match translate/rotate/scale to the given node
                             [[x,y,z], [x,y,z], [x,y,z]]: match translate/rotate/scale to given values
        matrix (list): match transform node's transformation to the given matrix, it will override position
        inherits_transform (bool): set transform node's inheritance attr, default is True

    Returns:
        transform_node (str): transform node name
    """
    # create transform
    transform = cmds.createNode('transform', name=name)

    # set rotate order
    cmds.setAttr('{0}.{1}'.format(transform, attributeUtils.ROTATE_ORDER), rotate_order)

    # visibility
    cmds.setAttr('{0}.{1}'.format(transform, attributeUtils.VISIBILITY), visibility)

    # inheritance
    cmds.setAttr(transform + '.inheritsTransform', inherits_transform)

    # match position
    if position:
        set_position(transform, position, rotate_order=rotate_order, translate=True, rotate=True, scale=True,
                     method='snap')

    # match matrix
    if matrix:
        cmds.xform(transform, matrix=matrix, worldSpace=True)

    # parent
    hierarchyUtils.parent(transform, parent)

    # lock hide
    if lock_hide:
        attributeUtils.lock(lock_hide, node=transform, channel_box=False)

    return transform


def offset_group(node, name):
    """
    create offset group for given node

    Args:
        node (str): node name
        name (str): offset group's name

    Returns:
        name (str): offset group's name
    """
    # get node's parent
    parent = cmds.listRelatives(node, parent=True)
    if parent:
        parent = parent[0]
    offset_grp = create(name, parent=parent, position=node)
    cmds.parent(node, offset_grp)
    return offset_grp


def create_along_curve(curve, number, node_type='group', additional_description=None, aim_vector=None, up_vector=None,
                       up_curve=None, aim_type='tangent', flip_check=True, parent_node=None):
    """
    create transform nodes evenly along given curve
    Args:
        curve (str): curve name
        number (int): numbers of transforms need to be created
        node_type (str): transform node's type, it must be in namingUtils config list, default is 'group'
        additional_description (str/list): additional description need to be added when create transforms
        aim_vector (list): the vector aim to the next point, default is [1, 0, 0]
        up_vector (list): up vector for aiming
        up_curve (str): if need points up vectors to aim to a specific curve
        aim_type (str): tangent/next, aim type for each point,
                        will be either based on curve's tangent or aim to the next point, default is tangent
        flip_check (bool): will automatically fix flipping transform if set to True, default is True
        parent_node (str): parent transform nodes under the given node

    Returns:
        transform_nodes (list): transform nodes along given curve
    """
    # get matrices
    matrices = curveUtils.get_matrices(curve, number, aim_vector=aim_vector, up_vector=up_vector, up_curve=up_curve,
                                       aim_type=aim_type, flip_check=flip_check)

    # check naming convention
    name_check = namingUtils.check(curve)
    # loop in each matrix and create transform node
    transform_nodes = []
    for i, mtx in enumerate(matrices):
        transform = cmds.createNode('transform', parent=parent_node)
        if name_check:
            transform = cmds.rename(transform, namingUtils.update(curve, type=node_type,
                                                                  additional_description=additional_description,
                                                                  index=i+1))
        # set matrix position
        cmds.xform(transform, matrix=mtx, worldSpace=True)
        # append to list
        transform_nodes.append(transform)

    return transform_nodes


def bounding_box(nodes):
    """
    get given nodes/pos bounding box info

    Args:
        nodes(list)

    Returns:
        max(list): max X/Y/Z
        min(list): min X/Y/Z
        center(list): pos X/Y/Z
    """
    node_poses = []

    for n in nodes:
        if isinstance(n, basestring) and cmds.objExists(n):
            # get object's position
            pos = cmds.xform(n, query=True, translation=True, worldSpace=True)
            node_poses.append(pos)

        else:
            # it's a position list, add to list directly
            node_poses.append(n)

    # zip the list to get array for xyz
    xyz_array = zip(*node_poses)
    max_pos = [max(xyz_array[0]), max(xyz_array[1]), max(xyz_array[2])]
    min_pos = [min(xyz_array[0]), min(xyz_array[1]), min(xyz_array[2])]
    center_pos = [(max_pos[0] + min_pos[0]) * 0.5,
                  (max_pos[1] + min_pos[1]) * 0.5,
                  (max_pos[2] + min_pos[2]) * 0.5]

    return max_pos, min_pos, center_pos


def set_position(nodes, position, rotate_order=0, translate=True, rotate=True, scale=False, method='snap'):
    """
    set nodes to match given transform node or position value

    Args:
        nodes (str/list): nodes need to be set position
        position (str/list): match transform node's transformation to given node/transform value
                             str: match translate,rotate and scale to the given node
                             [str/None, str/None, str/None]: match translate/rotate/scale to the given node,
                                                             scale is optional
                             [[x,y,z], [x,y,z], [x,y,z]: match translate/rotate/scale to given values,
                                                         scale is optional
        rotate_order (int): rotate order for the input position
        translate (bool): set translation
        rotate (bool): set rotation
        scale (bool): set scale
        method (str): 'snap' or 'copy',
                      snap will try to match the world position with the given position
                      copy is a direct copy/paste value process from source position to the node
    """
    if isinstance(nodes, basestring):
        nodes = [nodes]
    for n in nodes:
        if method == 'snap':
            _snap_node_position(n, position, rotate_order=rotate_order, translate=translate, rotate=rotate,
                                scale=scale)
        else:
            _copy_node_position(n, position, rotate_order=rotate_order, translate=translate, rotate=rotate,
                                scale=scale)


# sub function
def _snap_node_position(node, position, rotate_order=0, translate=True, rotate=True, scale=False):
    """
    snap node to given transform or position

    Args:
        node (str): node need to be snapped
        position (str/list): match transform node's transformation to given node/transform value
                             str: match translate,rotate and scale to the given node
                             [str/None, str/None, str/None]: match translate/rotate/scale to the given node,
                                                             scale is optional
                             [[x,y,z], [x,y,z], [x,y,z]: match translate/rotate/scale to given values,
                                                         scale is optional
        rotate_order (int): rotate order for the input position
        translate (bool): snap translation
        rotate (bool): snap rotation
        scale (bool): snap scale
    """
    # xform rotate order only accept string
    ro = ['xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx']

    if isinstance(position, basestring):
        # snap to given object
        cmds.matchTransform(node, position, position=translate, rotation=rotate, scale=scale)
    else:
        if position[0] and translate:
            if isinstance(position[0], basestring):
                # snap node position to given object only
                cmds.matchTransform(node, position[0], position=True, rotation=False, scale=False)
            else:
                # set translation values using xform
                cmds.xform(node, translation=position[0], worldSpace=True)

        if position[1] and rotate:
            if isinstance(position[1], basestring):
                # snap node rotation to given object only
                cmds.matchTransform(node, position[1], position=False, rotation=True, scale=False)
            else:
                # get node's rotate order first
                ro_node = cmds.getAttr(node + '.rotateOrder')
                # set rotation with given rotate order
                cmds.xform(node, rotation=position[1], worldSpace=True, rotateOrder=ro[rotate_order])
                # set back node's rotate order, and preserve overall rotation
                cmds.xform(node, rotateOrder=ro[ro_node])

        if len(position) > 2 and position[2] and scale:
            if isinstance(position[2], basestring):
                # snap node scale to given object only
                cmds.matchTransform(node, position[1], position=False, rotation=False, scale=True)
            else:
                # set node scale values using xform
                cmds.xform(node, scale=position[2])


def _copy_node_position(node, position, rotate_order=0, translate=True, rotate=True, scale=False):
    """
    copy given transform or position values to node

    Args:
        node (str): node need to transfer position values
        position (str/list): match transform node's transformation to given node/transform value
                             str: match translate,rotate and scale to the given node
                             [str/None, str/None, str/None]: match translate/rotate/scale to the given node
                             [[x,y,z], [x,y,z], [x,y,z]: match translate/rotate/scale to given values
                             NOTE: it will reset the node's rotate order if the position's rotation set to a transform
        rotate_order (int): input position's rotate order, it only works if rotation are values,
                            and node's rotate order will be set to this given value
        translate (bool): transfer translation
        rotate (bool): transfer rotation
        scale (bool): transfer scale
    """
    if isinstance(position, basestring):
        position = [position, position, position]

    if position[0] and translate:
        if isinstance(position[0], basestring):
            position[0] = cmds.getAttr(node + '.translate')[0]
        cmds.setAttr(node + '.translate', *position[0])

    if position[1] and rotate:
        if isinstance(position[1], basestring):
            rotate_order = cmds.getAttr(node + '.rotateOrder')
            position[1] = cmds.getAttr(node + '.rotate')[0]
        cmds.setAttr(node + '.rotate', *position[1])
        cmds.setAttr(node + '.rotateOrder', rotate_order)

    if position[2] and scale:
        if isinstance(position[2], basestring):
            position[2] = cmds.getAttr(node + '.scale')[0]
        cmds.setAttr(node + '.scale', *position[2])
