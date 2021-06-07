import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya2

import utils.common.apiUtils as apiUtils


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
