# import python library
import math
import numpy
import matrix
import numeric


def get_distance(point_a, point_b):
    """
    distance between two given points

    Args:
        point_a(list): first point
        point_b(list): second point

    Returns:
        distance(float): distance between two points

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.point.get_distance([1, 0, 0], [2, 0, 0])
        # 1
    """

    dis = math.sqrt(math.pow(point_b[0] - point_a[0], 2) +
                    math.pow(point_b[1] - point_a[1], 2) +
                    math.pow(point_b[2] - point_a[2], 2))
    return dis


def get_point_from_vector(vector, start_pos, distance=1):
    """
    get point from vector and given position, vector can be scaled by distance

    Args:
        vector (list): vector to shoot from the initial position
        start_pos (list): initial position
        distance (float): scale factor for the given vector, default is 1

    Returns:
        output_point (list): output point position

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.point.get_point_from_vector([1, 2, 3], [1, 0, 0], distance=2)
        # [3, 4, 6]
    """
    vector = [vector[0] * distance, vector[1] * distance, vector[2] * distance]
    output_point = [start_pos[0] + vector[0], start_pos[1] + vector[1], start_pos[2] + vector[2]]
    return output_point


def linear_space(start_point, end_point, number=5):
    """
    evenly spaced points, calculated over the interval [start, stop]

    Args:
        start_point (list): start point position
        end_point (list): end point position
        number (int): number of points need to be evenly spaced, start and end point included

    Returns:
        output_points (list): output points positions
    """
    output_x = numeric.linear_space(start_point[0], end_point[0], number=number)
    output_y = numeric.linear_space(start_point[1], end_point[1], number=number)
    output_z = numeric.linear_space(start_point[2], end_point[2], number=number)
    output_points = zip(output_x, output_y, output_z)
    return output_points


def mult_matrix(point, input_matrix, output_type='list'):
    """
    multipy point position with a given matrix

    Args:
        point (list/numpy.ndarray): point position
        input_matrix (list/numpy.ndarray): matrix need to multiply
        output_type(str): output data type, can be 'list'/'numpy', default is list

    Returns:
        point (list/numpy.ndarray)
    """
    if isinstance(point, list):
        # convert to numpy
        point = numpy.array(point)

    # add the last column for calculation
    point = numpy.append(point, 1)

    if isinstance(input_matrix, list):
        input_matrix = matrix.list_to_matrix(input_matrix)

    # get output point, and remove the last column
    point = point.dot(input_matrix).A1[:-1]
    if output_type == 'list':
        point = point.tolist()

    return point


def array_mult_matrix(point_array, input_matrix, output_type='list'):
    """
    multiply points array with a given matrix

    Args:
        point_array (list/numpy.ndarray): points array
        input_matrix (list/numpy.ndarray): matrix need to multiply
        output_type(str): output data type, can be 'list'/'numpy', default is list

    Returns:
        point_array (list/numpy.ndarray)
    """
    if isinstance(point_array, list):
        point_array = numpy.array(point_array)

    # add one column for calculation
    point_array = numpy.c_[point_array, numpy.ones(point_array.shape[0])]

    if isinstance(input_matrix, list):
        # convert to numpy
        input_matrix = matrix.list_to_matrix(input_matrix)

    # get output points array
    point_array = point_array.dot(input_matrix)

    # remove last column
    point_array = numpy.delete(point_array, (-1), axis=1)

    if output_type == 'list':
        point_array = point_array.tolist()

    return point_array
