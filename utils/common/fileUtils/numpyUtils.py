# import external library
import numpy


# functions
def read(file_path):
    """
    read data from the given numpy file path

    Args:
        file_path(str): given numpy file path

    Returns:
        data(numpy.ndarray): numpy array from the numpy file

    Examples:
        import utils.common.fileUtils as fileUtils

        file_path = 'C:/_works/_pipeline/tests/numpy_test.npy'
        file_data = fileUtils.numpyUtils.read(file_path)
    """

    data = numpy.load(file_path)
    return data


def write(file_path, file_data):
    """
    write data to the given path as numpy file

    Args:
        file_path(str): given numpy file path
        file_data(dict/list): given data

    Examples:
        import utils.common.fileUtils as fileUtils

        file_path = 'C:/_works/_pipeline/tests/numpy_test.npy'
        file_data = {'test': [1, 2, 3]}

        fileUtils.numpyUtils.write(file_path, file_data)
    """

    numpy.save(file_path, file_data)
