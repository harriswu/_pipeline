# import python library
import math
# import external library
import numpy


# function
def create(point_a, point_b, normalize=True):
    """
    create vector from two given points, the direction is from a to b

    Args:
        point_a (list): first point
        point_b (list): second point
        normalize (bool): normalize the output vector if True, default is True

    Returns:
        output_vector (list): output vector

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.vector.create([1, 0, 0], [5, 0, 0], normalize=True)
        # [1, 0, 0]

        mathUtils.vector.create([1, 0, 0], [5, 0, 0], normalize=False)
        # [4, 0, 0]
    """
    output_vector = [point_b[0] - point_a[0],
                     point_b[1] - point_a[1],
                     point_b[2] - point_a[2]]

    if normalize:
        output_vector = norm(output_vector)

    return output_vector


def length(vec):
    """
    get vector's length

    Args:
        vec (list): given vector

    Returns:
        length_value (float)

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.vector.length([5, 0, 0])
        # 5
    """
    length_value = math.sqrt(math.pow(vec[0], 2) + math.pow(vec[1], 2) + math.pow(vec[2], 2))
    return length_value


def norm(vector):
    """
    get normalized vector

    Args:
        vector (list/numpy.ndarray): vector need to be normalized

    Returns:
        norm_vector (list): normalized vector

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.vector.norm([5, 0, 0])
        # [1, 0, 0]
    """
    vector = numpy.array(vector)
    scalar = numpy.linalg.norm(vector)
    vector = vector / scalar

    return vector.tolist()


def reverse(vector, normalize=True):
    """
    reverse given vector's direction

    Args:
        vector (list): vector need to reverse direction
        normalize (bool): normalize the output vector if True, default is True

    Returns:
        rvs_vector (list): reversed vector

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.vector.reverse([5, 0, 0])
        # [-5, 0, 0]
    """
    if normalize:
        vector = norm(vector)
    return scale(vector, -1)


def add(*vectors):
    """
    add vectors together

    Args:
        *vectors (list): vectors need to add together

    Returns:
        sum_vector (list)

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.vector.scale([1, 0, 1], [2, 2, 2], [-1, -2, -3])
        # [2, 0, 0]
    """
    sum_list = zip(*vectors)
    return [sum(sum_list[0]), sum(sum_list[1]), sum(sum_list[2])]


def scale(vector, value):
    """
    scale the given vector

    Args:
        vector (list): vector need to be scaled
        value (float): scale factor

    Returns:
        scale_vector (list)

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.vector.scale([1, 0, 1], 2)
        # [2, 0, 2]
    """
    return [vector[0] * value, vector[1] * value, vector[2] * value]


def dot_product(vector_a, vector_b):
    """
    dot product between two given vectors

    Args:
        vector_a (list): first vector
        vector_b (list): second vector

    Returns:
        value (float)

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.vector.dot_product([1, 0, 0], [1, 2, 3])
        # 1
    """
    val = numpy.dot(vector_a, vector_b)
    return float(val)


def cross_product(vector_a, vector_b, normalize=True):
    """
    cross product for two given vectors

    Args:
        vector_a(list): first vector
        vector_b(list): second vector
        normalize(bool): normalize vector, default is True

    Returns:
        output_vector(list)

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.vector.cross_product([1, 0, 0], [1, 2, 3], normalize=True)
        # [0.0, -0.8320502943378437, 0.5547001962252291]

        mathUtils.vector.cross_product([1, 0, 0], [1, 2, 3], normalize=True)
        # [ 0, -3,  2]
    """
    output_vector = numpy.cross(vector_a, vector_b)
    if normalize:
        output_vector = norm(output_vector)
    else:
        output_vector = output_vector.tolist()
    return output_vector


def project_onto_plane(vector, normal, normalize=True):
    """
    project given vector onto a plane,
    vector - (vector.normal)*normal

    Args:
        vector (list): vector need to be projected
        normal (list): plane's normal vector, must be normalized
        normalize (bool): normalize vector, default is True

    Returns:
        project_vector (list): projected vector

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.vector.project_onto_plane([1, 0, 0], [2, 2, 3], normalize=True)
        # [-0.3841106397986879, -0.5121475197315839, -0.7682212795973759]

        mathUtils.vector.project_onto_plane([1, 0, 0], [2, 2, 3], normalize=True)
        # [-3, -4, -6]
    """
    dot_val = dot_product(vector, normal)
    vector = numpy.array(vector)
    normal = numpy.array(normal)
    project_vector = vector - dot_val * normal
    if normalize:
        project_vector = norm(project_vector)
    else:
        project_vector = project_vector.tolist()
    return project_vector


def coordinate_system(vector_x, vector_y, reference=None):
    """
    build object coordinate system base on the given two vectors

    Args:
        vector_x (list): primary vector
        vector_y (list): secondary vector
        reference (list): if reference coordinate system is given,
                          it will compare with the current one to avoid flipping,
                          it should be [vector_x, vector_y, vector_z]
                          default is None
    Returns:
        vector_x, vector_y, vector_z

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.vector.coordinate_system([1, 0, 0], [2, 2, 3], reference=None)
        # [1.0, 0.0, 0.0],
        # [-0.0, 0.5547001962252291, 0.8320502943378437],
        # [0.0, -0.8320502943378437, 0.5547001962252291]

        mathUtils.coordinate_system([1, 0, 0], [2, 2, 3], reference=[[1,0,0], [0,-1,0], [0,0,-1]])
        # [1.0, 0.0, 0.0],
        # [0.0, -0.5547001962252291, -0.8320502943378437],
        # [-0.0, 0.8320502943378437, -0.5547001962252291]
    """
    vector_x = norm(vector_x)
    vector_z = cross_product(vector_x, vector_y, normalize=True)

    if reference:
        # get z projected vector on reference plane (yz), so use x as normal
        project_vec = project_onto_plane(vector_z, reference[0], normalize=True)
        # dot product to check the angle between the project vector and reference z vector
        # if value lesser than 0, means the current system is flipping, reverse the z vector
        dot_val = dot_product(project_vec, reference[2])
        if dot_val < 0:
            vector_z = reverse(vector_z)

    vector_y = cross_product(vector_z, vector_x, normalize=True)

    return vector_x, vector_y, vector_z
