import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya2

import utils.common.apiUtils as apiUtils


def get_shape_info(surface):
    """
    get surface's shape info

    Args:
        surface (str): surface's shape node or transform node

    Returns:
        surface_info (dict): surface shape information
                          include control_vertices, knots, degree, form
    """
    # get MFnNurbsSurface
    mfn_surface = get_MFnNurbsSurface(surface)

    control_vertices = mfn_surface.cvPositions(space=OpenMaya2.MSpace.kObject)
    u_knots = mfn_surface.knotsInU()
    v_knots = mfn_surface.knotsInV()

    u_degree = mfn_surface.degreeInU
    v_degree = mfn_surface.degreeInV

    u_form = mfn_surface.formInU
    v_form = mfn_surface.formInV

    control_vertices = apiUtils.MArray.to_list(control_vertices)
    num_cvs = len(control_vertices)

    surface_info = {'num_cvs': num_cvs,
                    'control_vertices': apiUtils.MArray.to_list(control_vertices),
                    'u_knots': apiUtils.MArray.to_list(u_knots),
                    'v_knots': apiUtils.MArray.to_list(v_knots),
                    'u_degree': u_degree,
                    'v_degree': v_degree,
                    'u_form': u_form,
                    'v_form': v_form}

    return surface_info


def get_MFnNurbsSurface(surface):
    """
    get MFnNurbsSurface object from given surface

    Args:
        surface (str): surface's shape node or transform node

    Returns:
        mfn_surface (MFnNurbsSurface)
    """
    # get curve shape
    if cmds.objectType(surface) == 'transform':
        surface = cmds.listRelatives(surface, shapes=True)[0]

    # get dag path
    dag_path = apiUtils.MSelectionList.get_nodes_info(surface, info_type='MDagPath')[0]
    # get MFnMesh
    mfn_surface = OpenMaya2.MFnNurbsSurface(dag_path)

    return mfn_surface
