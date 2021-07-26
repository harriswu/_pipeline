# import external library
import numpy

# import utils
import utils.common.apiUtils as apiUtils

# constant
# maya transform default matrix
IDENTITY = [1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0]


# function
def list_to_matrix(array, column=4, row=4):
    """
    convert list to numpy matrix

    Args:
        array (list/numpy.ndarray): list of float values, normally contains 16 values
        column (int): matrix's column number, default is 4
        row (int): matrix's row number, default is 4

    Returns:
        matrix (numpy.ndarray)

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.matrix.list_to_matrix([1.0, 0.0, 0.0, 0.0,
                                         0.0, 1.0, 0.0, 0.0,
                                         0.0, 0.0, 1.0, 0.0,
                                         0.0, 0.0, 0.0, 1.0], column=4, row=4)
        # matrix([[ 1.,  0.,  0.,  0.],
        #         [ 0.,  1.,  0.,  0.],
        #         [ 0.,  0.,  1.,  0.],
        #         [ 0.,  0.,  0.,  1.]]
    """
    np_array = numpy.reshape(array, (column, row))

    return numpy.asmatrix(np_array)


def matrix_to_list(matrix):
    """
    convert numpy matrix to list

    Args:
        matrix(numpy.ndarray): numpy matrix

    Returns:
        array(list)

    Examples:
        import numpy
        import utils.common.mathUtils as mathUtils

        matrix_numpy = mathUtils.matrix.list_to_matrix([1.0, 0.0, 0.0, 0.0,
                                                        0.0, 1.0, 0.0, 0.0,
                                                        0.0, 0.0, 1.0, 0.0,
                                                        0.0, 0.0, 0.0, 1.0])
        mathUtils.matrix.matrix_to_list(matrix_numpy)
        # [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    """

    array = numpy.reshape(matrix, matrix.size)
    array = numpy.array(array)[0]
    array = array.tolist()
    return array


def inverse(matrix, output_type='list'):
    """
    inverse numpy matrix

    Args:
        matrix(list/numpy.ndarray): given matrix
        output_type(str): output data type, can be 'list'/'numpy', default is list

    Returns:
        matrix_inverse(list/numpy.ndarray)

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.matrix.inverse([1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 2.0, 3.0, 1.0])
        # [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, -2.0, -3.0, 1.0]
    """

    if isinstance(matrix, list):
        matrix = list_to_matrix(matrix)
    matrix_inverse = numpy.linalg.inv(matrix)
    if output_type == 'list':
        matrix_inverse = matrix_to_list(matrix_inverse)

    return matrix_inverse


def multiply(*matrices, **kwargs):
    """
    multiply given matrices

    Args:
        matrices(list/numpy.ndarray): list of list/numpy matrix
    Keyword Args:
        output_type(str): output data type, can be 'list'/'numpy', default is list

    Returns:
        matrix(list/numpy.ndarray)

    Examples:
        import utils.common.mathUtils as mathUtils

        matrix_01 = [0.9396926207859084, 0.3420201433256687, 0.0, 0.0,
                     -0.3368240888334652, 0.9254165783983234, -0.17364817766693036, 0.0,
                     -0.059391174613884705, 0.16317591116653485, 0.984807753012208, 0.0,
                     1.0, 2.0, 3.0, 1.0]
        matrix_02 = [0.9396926207859084, 0.3420201433256687, 0.0, 0.0,
                     -0.3368240888334652, 0.9254165783983234, 0.17364817766693036, 0.0,
                     0.059391174613884705, -0.16317591116653485, 0.984807753012208, 0.0,
                     2.0, 2.0, 2.0, 1.0]

        mathUtils.matrix.multiply(matrix_01, matrix_02)

        # [0.7678215984211295, 0.6379049156230141, 0.059391174613884705, 0.0,
        #  -0.6385268758313423, 0.7695304200493104, -0.010313169241199516, 0.0,
        #  -0.0522821369024579, -0.030004187086592082, 0.9981815100061638, 0.0,
        #  2.444217966960632, 3.7033255666227105, 5.301719614370485, 1.0]
    """
    output_type = kwargs.get('output_type', 'list')

    # check the first argument type
    if isinstance(matrices[0], list):
        # convert to numpy array
        matrix_mult = list_to_matrix(matrices[0])
    else:
        matrix_mult = matrices[0]

    # loop in each matrix in list, multiply to get the final matrix
    for matrix in matrices[1:]:
        if isinstance(matrix, list):
            matrix = list_to_matrix(matrix)
        matrix_mult = numpy.dot(matrix_mult, matrix)

    if output_type == 'list':
        matrix_mult = matrix_to_list(matrix_mult)

    return matrix_mult


def localize(matrix_a, matrix_b, output_type='list'):
    """
    get matrix_a's local matrix on matrix_b

    Args:
        matrix_a(list/numpy.ndarray): matrix need to be localized
        matrix_b(list/numpy.ndarray): parent matrix
        output_type(str): output data type, can be 'list'/'numpy', default is list

    Returns:
        matrix_local(list/numpy.ndarray): local matrix as list

    Examples:
        import utils.common.mathUtils as mathUtils

        matrix_01 = [0.9396926207859084, 0.3420201433256687, 0.0, 0.0,
                     -0.3368240888334652, 0.9254165783983234, -0.17364817766693036, 0.0,
                     -0.059391174613884705, 0.16317591116653485, 0.984807753012208, 0.0,
                     1.0, 2.0, 3.0, 1.0]
        matrix_02 = [0.9396926207859084, 0.3420201433256687, 0.0, 0.0,
                     -0.3368240888334652, 0.9254165783983234, 0.17364817766693036, 0.0,
                     0.059391174613884705, -0.16317591116653485, 0.984807753012208, 0.0,
                     2.0, 2.0, 2.0, 1.0]

        mathUtils.matrix.localize(matrix_01, matrix_02)
        # [1.0, 1.1102230246251565e-16, 4.163336342344337e-17, 0.0,
        #  5.551115123125783e-17, 0.9396926207859085, -0.3420201433256687, 0.0,
        #  4.163336342344337e-17, 0.34202014332566877, 0.9396926207859082, 0.0,
        #  -0.9396926207859083, 0.5104722665003956, 0.9254165783983233, 1.0]
    """

    matrix_b_inverse = inverse(matrix_b)
    matrix_local = multiply(matrix_a, matrix_b_inverse, output_type=output_type)

    return matrix_local


def four_by_four_matrix(vector_x, vector_y, vector_z, position, output_type='list'):
    """
    create four by four matrix

    Args:
        vector_x(list/numpy.ndarray)
        vector_y(list/numpy.ndarray)
        vector_z(list/numpy.ndarray)
        position(list/numpy.ndarray)
        output_type(str): output data type, can be 'list'/'numpy', default is list
    Returns:
        matrix(list/numpy.ndarray)

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.matrix.four_by_four_matrix([1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 2, 3])
        # [1, 0, 0, 0,
        #  0, 1, 0, 0,
        #  0, 0, 1, 0,
        #  1, 2, 3, 1]
    """
    matrix = [vector_x[0], vector_x[1], vector_x[2], 0,
              vector_y[0], vector_y[1], vector_y[2], 0,
              vector_z[0], vector_z[1], vector_z[2], 0,
              position[0], position[1], position[2], 1]

    if output_type == 'numpy':
        matrix = list_to_matrix(matrix)

    return matrix


def compose(translate=None, rotate=None, scale=None, rotate_order=0):
    """
    compose matrix as a list with given transformation values

    Args:
        translate (list): translation values, default is [0, 0, 0]
        rotate (list): rotation values, default is [0, 0, 0]
        scale (list): scale values, default is [1, 1, 1]
        rotate_order (int): current transformation values' rotate order, default is 0

    Returns:
        matrix (list)
    """
    # get MMatrix
    m_matrix = apiUtils.MMatrix.compose(translate=translate, rotate=rotate, scale=scale, rotate_order=rotate_order)

    matrix = apiUtils.MMatrix.to_list(m_matrix)

    return matrix


def decompose(matrix, rotate_order=0):
    """
    decompose given matrix list to transformation info

    Args:
        matrix (list): matrix list need to be decomposed
        rotate_order (int): input rotate order, default is 0

    Returns:
        [translate, rotate, scale](list)
    """
    # get MMatrix
    m_matrix = apiUtils.MMatrix.compose(matrix=matrix)
    # decompose to transform values
    return apiUtils.MMatrix.decompose(m_matrix, rotate_order=rotate_order)


def update(matrix, translate=None, rotate=None, scale=None, rotate_order=0):
    """
    update given matrix with transformation values

    Args:
        matrix (list): the matrix need to be updated
        translate (list): translation values to override the current matrix
        rotate (list): rotation values to override the current matrix
        scale (list): scale values to override the current matrix
        rotate_order (int): transform values' rotate order

    Returns:
        matrix (list)
    """
    # decompose matrix
    decompose_info = decompose(matrix)
    # collect kwargs
    kwargs = {'translate': decompose_info[0],
              'rotate': decompose_info[1],
              'scale': decompose_info[2],
              'rotate_order': 0}
    if translate:
        kwargs.update({'translate': translate})
    if rotate:
        kwargs.update({'rotate': rotate,
                       'rotate_order': rotate_order})
    if scale:
        kwargs.update({'scale': scale})
    # recompose the matrix and return it
    return compose(**kwargs)
