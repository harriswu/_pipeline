# import maya python library
import maya.cmds as cmds

# import utils
import utils.common.namingUtils as namingUtils
import utils.common.transformUtils as transformUtils
import utils.common.hierarchyUtils as hierarchyUtils
import utils.modeling.curveUtils as curveUtils


# functions
def create(name, rotate_order=0, parent_node=None, position=None, matrix=None, visibility=True):
    """
    create single joint

    Args:
        name(str): joint's name
        rotate_order(int): joint's rotate order, default is 0
        parent_node(str): parent joint
        position(str/list): match joint's position to given node/transform value
                           str: match translate and rotate to the given node
                           [str/None, str/None]: match translate/rotate to the given node
                           [[x,y,z], [x,y,z]]: match translate/rotate to given values
        matrix(list): if need the joint to match a specific matrix, it will override position
        visibility(bool): visibility, default is True

    Returns:
        joint(str)
    """
    # create joint
    jnt = cmds.createNode('joint', name=name, parent=parent_node)
    cmds.setAttr(jnt+'.rotateOrder', rotate_order)
    cmds.setAttr(jnt+'.visibility', visibility)

    # match position
    if position:
        transformUtils.set_position(jnt, position, translate=True, rotate=True, scale=False, method='snap')
        # freeze transformation
        cmds.makeIdentity(jnt, apply=True, translate=True, rotate=True, scale=True)

    # match matrix
    if matrix:
        cmds.xform(jnt, matrix=matrix, worldSpace=True)
        # freeze transformation
        cmds.makeIdentity(jnt, apply=True, translate=True, rotate=True, scale=True)

    return jnt


def create_chain(positions, names, rotate_order=0, visibility=True, reverse=False, parent_node=None):
    """
    create joint chain base on given positions/nodes,
    by default the parent order is from the root to the end

    Args:
        positions (list): list of positions or node names
        names (str): create joint chain with given names
        rotate_order(int): joint's rotate order, default is 0
        visibility (bool): joints visibility, default is True
        reverse (bool): reverse parent order, default is False.
        parent_node (str): parent joint chain to the given node

    Returns:
        joints (list): list of joints
    """
    # create joints
    jnts = []
    for pos, nm in zip(positions, names):
        jnt = create(nm, rotate_order=rotate_order, position=pos, visibility=visibility)
        jnts.append(jnt)

    # parent chain function has opposite reverse order
    reverse = not reverse

    # parent hierarchy
    jnts = hierarchyUtils.parent_chain(jnts, parent_node=parent_node, reverse=reverse)

    return jnts


def create_along_curve(curve, number, additional_description=None, aim_vector=None, up_vector=None, up_curve=None,
                       aim_type='tangent', flip_check=True, parent_node=None, chain=True):
    """
    create joints evenly along given curve
    Args:
        curve (str): curve name
        number (int): numbers of joints need to be created
        additional_description (str/list): additional description need to be added when create transforms
        aim_vector (list): the vector aim to the next point, default is [1, 0, 0]
        up_vector (list): up vector for aiming
        up_curve (str): if need points up vectors to aim to a specific curve
        aim_type (str): tangent/next, aim type for each point,
                        will be either based on curve's tangent or aim to the next point, default is tangent
        flip_check (bool): will automatically fix flipping transform if set to True, default is True
        parent_node (str): parent transform nodes under the given node
        chain (bool): if need to parent joints as a joint chain, default is True

    Returns:
        joints (list): joints along given curve
    """
    # get matrices
    matrices = curveUtils.get_matrices(curve, number, aim_vector=aim_vector, up_vector=up_vector, up_curve=up_curve,
                                       aim_type=aim_type, flip_check=flip_check)

    # check naming convention
    name_check = namingUtils.check(curve)
    # loop in each matrix and create joint
    joints = []
    for i, mtx in enumerate(matrices):
        jnt = cmds.createNode('joint', parent=parent_node)
        if name_check:
            jnt = cmds.rename(jnt, namingUtils.update(curve, type='joint',
                                                      additional_description=additional_description, index=i + 1))
        # set matrix position
        cmds.xform(jnt, matrix=mtx, worldSpace=True)
        # freeze transformation
        cmds.makeIdentity(jnt, apply=True, translate=True, rotate=True, scale=True)
        # append to list
        joints.append(jnt)

    # connect as chain
    if chain:
        hierarchyUtils.parent_chain(joints, reverse=True)

    return joints
