# import maya python library
import maya.api.OpenMaya as OpenMaya2


def to_list(array):
    """
    convert input MPointArray/MDoubleArray object to list

    Args:
        array (MPointArray/MDoubleArray): MPointArray, MDagPathArray or MDoubleArray

    Returns:
        array_list (list)
    """
    if isinstance(array, OpenMaya2.MPointArray):
        return _point_array_to_list(array)
    elif isinstance(array, OpenMaya2.MDagPathArray):
        return _dag_path_array_to_list(array)
    else:
        return _double_array_to_list(array)


def to_MPointArray(points):
    """
    convert points list to MPointArray

    Args:
        points (list): list of points positions

    Returns:
        point_array(MPointArray)
    """
    return OpenMaya2.MPointArray(points)


def _point_array_to_list(point_array):
    """
    convert MPointArray to list

    Args:
        point_array (MPointArray): input MPointArray

    Returns:
        point_list (list)
    """
    point_list = []
    for i in range(len(point_array)):
        point_list.append([point_array[i].x,
                           point_array[i].y,
                           point_array[i].z])
    return point_list


def _double_array_to_list(double_array):
    """
    Args:
        double_array (MDoubleArray): input MDoubleArray

    Returns:
        array_list(list)
    """

    array_list = []
    for i in range(len(double_array)):
        array_list.append(double_array[i])
    return array_list


def _dag_path_array_to_list(dag_path_array):
    """
    convert MDagPathArray to list of string

    Args:
        dag_path_array (MDagPathArray): input MDagPathArray

    Returns:
        string_list (list)
    """
    string_list = []
    for i in range(len(dag_path_array)):
        string_list.append(dag_path_array[i].partialPathName())
    return string_list
