# import python library
import cPickle


# function
def read(file_path):
    """
    read data from the given cPickle file path

    Args:
        file_path(str): given cPickle file path

    Returns:
        data(dict/list): data from cPickle file

    Examples:
        import utils.common.fileUtils as fileUtils

        file_path = 'C:/_works/_pipeline/tests/pickle_test.pickle'
        file_data = fileUtils.pickleUtils.read(file_path)
    """

    infile = open(file_path, 'rb')
    file_data = cPickle.load(infile)
    infile.close()
    return file_data


def write(file_path, file_data):
    """
    write data to the given path as cPickle file

    Args:
        file_path(str): given cPickle file path
        file_data(dict/list): given cPickle data

    Examples:
        import utils.common.fileUtils as fileUtils

        file_path = 'C:/_works/_pipeline/tests/pickle_test.pickle'
        file_data = {'test': [1, 2, 3]}

        fileUtils.pickleUtils.write(file_path, file_data)
    """

    outfile = open(file_path, 'wb')
    cPickle.dump(file_data, outfile, cPickle.HIGHEST_PROTOCOL)
    outfile.close()
