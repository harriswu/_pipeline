import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya2

import utils.common.apiUtils as apiUtils
import utils.common.mathUtils as mathUtils


def get_shape_info(mesh):
    """
    get mesh's shape info

    Args:
        mesh (str): mesh's shape node or transform node

    Returns:
        mesh_info (dict): mesh shape information
                          include control_vertices, knots, degree, form
    """
    # get MFnMesh
    mfn_mesh = get_MFnMesh(mesh)

    num_vertices = mfn_mesh.numVertices
    num_polygons = mfn_mesh.numPolygons
    points_array = mfn_mesh.getPoints(space=OpenMaya2.MSpace.kObject)
    poly_count_array, poly_connects = mfn_mesh.getVertices()

    mesh_info = {'num_vertices': num_vertices,
                 'num_polygons': num_polygons,
                 'points_array': apiUtils.MArray.to_list(points_array),
                 'poly_count_array': apiUtils.MArray.to_list(poly_count_array),
                 'poly_connects': apiUtils.MArray.to_list(poly_connects)}

    return mesh_info


def ray_casting_intersection_closest(mesh, point, direction, radius=1, both_direction=False):
    """
    ray casting from given point and direction to get the closest intersection point on mesh

    Args:
        mesh (str): mesh name
        point (list): start point position
        direction (list): ray direction vector
        radius (float): radius to calculate the intersection, any point outside the radius won't be calculated,
                        default is 1
        both_direction (bool): calculate intersection points on both direction if set to True, default is False

    Returns:
        hit_point (list): point position intersected with the ray
        hit_ray_param (float): parametric distance along the ray to the point hit
        hit_face (str): faces name intersected with the ray
    """
    # get mfn mesh
    mfn_mesh = get_MFnMesh(mesh)

    # get start point as MPoint
    m_point = OpenMaya2.MFloatPoint(point)

    # normalize direction and convert to MVector
    m_vec = OpenMaya2.MVector(mathUtils.vector.norm(direction))

    intersection_info = mfn_mesh.closestIntersection(m_point, m_vec, OpenMaya2.MSpace.kWorld, radius, both_direction)

    hit_point = intersection_info[0]
    hit_ray_param = intersection_info[1]
    hit_face = intersection_info[2]

    if hit_point:
        hit_point = [hit_point.x, hit_point.y, hit_point.z]

    return hit_point, hit_ray_param, hit_face


def ray_casting_intersection_all(mesh, point, direction, radius=1, both_direction=False):
    """
    ray casting from given point and direction to get intersection points on mesh

    Args:
        mesh (str): mesh name
        point (list): start point position
        direction (list): ray direction vector
        radius (float): radius to calculate the intersection, any point outside the radius won't be calculated,
                        default is 1
        both_direction (bool): calculate intersection points on both direction if set to True, default is False

    Returns:
        hit_points (list): list of point position intersected with the ray
        hit_ray_params (list): list of parametric distances along the ray to the points hit
        hit_faces (list): list of faces names intersected with the ray
    """
    # get mfn mesh
    mfn_mesh = get_MFnMesh(mesh)

    # get start point as MPoint
    m_point = OpenMaya2.MFloatPoint(point)

    # normalize direction and convert to MVector
    m_vec = OpenMaya2.MVector(mathUtils.vector.norm(direction))

    intersection_info = mfn_mesh.allIntersections(m_point, m_vec, OpenMaya2.MSpace.kWorld, radius, both_direction,
                                                  sortHits=True)

    hit_points = intersection_info[0]
    hit_ray_params = intersection_info[1]
    hit_faces = intersection_info[2]

    # convert data to lists
    hit_points = apiUtils.MArray.to_list(hit_points)
    hit_ray_params = apiUtils.MArray.to_list(hit_ray_params)
    hit_faces = apiUtils.MArray.to_list(hit_faces)
    # convert to faces name instead of just index
    hit_faces = ['{0}.f[{1}]'.format(mesh, i) for i in hit_faces]

    return hit_points, hit_ray_params, hit_faces


def get_MFnMesh(mesh):
    """
    get MFnMesh object from given mesh

    Args:
        mesh (str): mesh's shape node or transform node

    Returns:
        m_mesh (MFnMesh)
    """
    # get curve shape
    if cmds.objectType(mesh) == 'transform':
        mesh = cmds.listRelatives(mesh, shapes=True)[0]

    # get dag path
    dag_path = apiUtils.MSelectionList.get_nodes_info(mesh, info_type='MDagPath')[0]
    # get MFnMesh
    mfn_mesh = OpenMaya2.MFnMesh(dag_path)

    return mfn_mesh
