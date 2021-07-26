# import maya python library
import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya2

# import utils
import utils.common.mathUtils as mathUtils
import utils.common.apiUtils as apiUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.hierarchyUtils as hierarchyUtils


# function
def create(name, control_vertices, knots, degree=1, form=1, parent=None):
    """
    create curve with given information

    Args:
        name (str): curve's name
        control_vertices (list): control vertices position list
        knots (list): curve shape's knots information
        degree (int): curve shape's degree, default is 1
        form (int): curve's form, default is 1
        parent (str): parent curve's transform to the given node

    Returns:
        name (str): curve's transform name
        shape_name (str): curve's shape name
    """
    # we need to create transform node first to attach the shape
    if not cmds.objExists(name):
        cmds.createNode('transform', name=name)

    hierarchyUtils.parent(name, parent)

    # create shape
    m_obj = apiUtils.MSelectionList.get_nodes_info(name, info_type='MObject')[0]
    mfn_crv = OpenMaya2.MFnNurbsCurve()
    m_obj = mfn_crv.create(control_vertices, knots, degree, form, False, True, m_obj)

    # rename shape
    dag_path = OpenMaya2.MDagPath.getAPathTo(m_obj)
    shape = dag_path.partialPathName()
    shape = cmds.rename(shape, name+'Shape')

    return name, shape


def get_info(curve):
    """
    get curve info, include transform node's world matrix and curve shape info

    Args:
        curve (str): curve's transform node name or shape name

    Returns:
        curve_info(dict): curve's info, include name, control_vertices, knots, degree, form and world_matrix
    """
    if cmds.objectType(curve) == 'nurbsCurve':
        curve = cmds.listRelatives(curve, parent=True)[0]

    curve_info = get_shape_info(curve)

    world_matrix = cmds.getAttr('{0}.{1}'.format(curve, attributeUtils.WORLD_MATRIX)[0])
    curve_info.update({'world_matrix': world_matrix})

    return curve_info


def get_shape_info(curve):
    """
    get curve's shape info

    Args:
        curve (str): curve's shape node or transform node

    Returns:
        curve_info (dict): curve shape information
                           include control_vertices, knots, degree, form
    """
    # get MFnNurbsCurve
    mfn_crv = get_MFnNurbsCurve(curve)

    cv_array = mfn_crv.cvPositions(OpenMaya2.MSpace.kObject)
    knots_array = mfn_crv.knots()

    degree = mfn_crv.degree
    form = mfn_crv.form

    control_vertices = apiUtils.MArray.to_list(cv_array)
    num_cvs = len(control_vertices)

    curve_info = {'num_cvs': num_cvs,
                  'control_vertices': control_vertices,
                  'knots': apiUtils.MArray.to_list(knots_array),
                  'degree': degree,
                  'form': form}

    return curve_info


def set_points(curve, points):
    """
    set curve shape points positions

    Args:
        curve(str): curve shape node or transform node
        points(list): curve cv positions
    """
    pnt_array = OpenMaya2.MPointArray(points)

    # get MFnNurbsCurve
    m_curve = get_MFnNurbsCurve(curve)

    # set pos
    m_curve.setCVPositions(pnt_array)


def set_display_setting(curve, display_type='normal', color=None):
    """
    set curve's display setting

    Args:
        curve (str): curve's shape name
        display_type (str): normal/template/reference
        color (list): rgb color
    """
    cmds.setAttr(curve + '.overrideEnabled', 1)
    cmds.setAttr(curve + '.overrideDisplayType', ['normal', 'template', 'reference'].index(display_type))
    if color:
        cmds.setAttr(curve + '.overrideRGBColors', 1)
        cmds.setAttr(curve + '.overrideColorRGB', *color)


def get_color(curve):
    """
    get curve's display color

    Args:
        curve (str): curve shape name

    Returns:
        color (list): rgb color
    """
    color = cmds.getAttr(curve + '.overrideColorRGB')[0]
    return color


def get_closest_point(curve, position):
    """
    get closest point position and parameter on given curve

    Args:
        curve (str): nurbs curve
        position (list): given position

    Returns:
        closest_point (list): closest point position on curve
        parameter (float): closest point's parameter on curve
    """
    m_point = OpenMaya2.MPoint(position)
    mfn_curve = get_MFnNurbsCurve(curve)

    # check if point on curve or not
    if not mfn_curve.isPointOnCurve(m_point):
        # get closest point and parameter
        m_point, parameter = mfn_curve.closestPoint(m_point, space=OpenMaya2.MSpace.kObject)
    else:
        parameter = mfn_curve.getParamAtPoint(m_point, space=OpenMaya2.MSpace.kObject)

    return [m_point.x, m_point.y, m_point.z], parameter


def get_point(curve, parameter, space='world'):
    """
    get point information (position, tangent) on given parameter

    Args:
        curve (str): nurbs curve
        parameter (float): parameter on curve
        space (str): world/object

    Returns:
        position (list): point's position
        tangent (list): point's tangent
    """
    if space == 'world':
        space = OpenMaya2.MSpace.kWorld
    else:
        space = OpenMaya2.MSpace.kObject

    mfn_curve = get_MFnNurbsCurve(curve)
    m_point = mfn_curve.getPointAtParam(parameter, space=space)
    tangent = mfn_curve.tangent(parameter)
    return [m_point.x, m_point.y, m_point.z], tangent


def get_points(curve, number, space='world'):
    """
    get points positions evenly on curve

    Args:
        curve (str): curve name
        number (int): points number
        space (str): world/object

    Returns:
        positions (list): points positions list
        parameters (list): parameters on curve
        tangents (list): points tangent vectors list
    """
    mfn_curve = get_MFnNurbsCurve(curve)
    # get curve length
    length = mfn_curve.length()
    # get length per section
    length_section = float(length) / (number - 1)

    # loop in each point
    positions = []
    parameters = []
    tangents = []
    for i in range(number):
        parameter = mfn_curve.findParamFromLength(i * length_section)
        # get point on parameter
        point, tangent = get_point(curve, parameter, space=space)
        # add to list
        positions.append(point)
        parameters.append(parameter)
        tangents.append(tangent)

    return positions, parameters, tangents


def get_matrices(curve, number, aim_vector=None, up_vector=None, up_curve=None, aim_type='tangent', flip_check=True):
    """
    get matrices along the given curve uniformly

    Args:
        curve (str): curve name
        number (int): matrices number
        aim_vector (list): the vector aim to the next point, default is [1, 0, 0]
        up_vector (list): up vector for aiming
        up_curve (str): if need points up vectors to aim to a specific curve
        aim_type (str): tangent/next, aim type for each point,
                        will be either based on curve's tangent or aim to the next point, default is tangent
        flip_check (bool): will automatically fix flipping transform if set to True, default is True

    Returns:
        matrices (list): list of output matrices
    """
    # get aim vector
    if not aim_vector:
        aim_vector = [1, 0, 0]
    # get up vector
    if not up_vector:
        up_vector = [0, 1, 0]

    # get points info on curve
    positions, parameters, tangents = get_points(curve, number)
    # loop in each position, and get matrix, skip the last one for now
    matrices = []
    reference_vectors = None
    for i, pos in enumerate(positions):
        # get target vector
        if aim_type == 'tangent':
            target_vector = tangents[i]
        elif i < number - 1:
            target_vector = mathUtils.vector.create(pos, positions[i + 1])
        else:
            target_vector = mathUtils.vector.create(positions[i - 1], pos)

        # get rotation vectors
        if not up_curve:
            # use quaternion rotation match the target vector
            # get target vector and aim vector as MVector
            m_aim = OpenMaya2.MVector(aim_vector)
            m_target = OpenMaya2.MVector(target_vector)
            # rotate to match target vector
            m_quaternion = m_aim.rotateTo(m_target)
            # convert to MMatrix
            m_matrix = m_quaternion.asMatrix()
            # update translation
            m_matrix.setElement(3, 0, pos[0])
            m_matrix.setElement(3, 1, pos[1])
            m_matrix.setElement(3, 2, pos[2])
            # convert to list
            matrix = apiUtils.MMatrix.to_list(m_matrix)
        else:
            # get point on up curve
            up_pos, up_tangent = get_point(up_curve, parameters[i])
            # get up vector
            aim_up_vector = mathUtils.vector.create(pos, up_pos)
            # get coordinate vectors
            vectors = mathUtils.vector.coordinate_system(target_vector, aim_up_vector, reference=reference_vectors)

            if flip_check:
                # override reference vectors with current ones for flip check
                reference_vectors = vectors
            # compose matrix
            matrix_aim = mathUtils.matrix.four_by_four_matrix(vectors[0], vectors[1], vectors[2], pos,
                                                              output_type='numpy')
            # get aim vector's matrix
            vectors_local = mathUtils.vector.coordinate_system(aim_vector, up_vector)
            matrix_local = mathUtils.matrix.four_by_four_matrix(vectors_local[0], vectors_local[1], vectors_local[2],
                                                                [0, 0, 0], output_type='numpy')
            # get inverse local matrix
            matrix_local_inverse = mathUtils.matrix.inverse(matrix_local, output_type='numpy')
            # multiply to get output matrix
            matrix = mathUtils.matrix.multiply(matrix_local_inverse, matrix_aim, output_type='list')
        # append matrix to list
        matrices.append(matrix)
    return matrices


def get_MFnNurbsCurve(curve):
    """
    get MFnNurbsCurve object from given curve

    Args:
        curve (str): curve's shape node or transform node

    Returns:
        mfn_crv (MFnNurbsCurve)
    """
    # get curve shape
    if cmds.objectType(curve) == 'transform':
        curve = cmds.listRelatives(curve, shapes=True)[0]

    # get dag path
    dag_path = apiUtils.MSelectionList.get_nodes_info(curve, info_type='MDagPath')[0]
    # get MFnNurbsCurve
    mfn_crv = OpenMaya2.MFnNurbsCurve(dag_path)

    return mfn_crv
