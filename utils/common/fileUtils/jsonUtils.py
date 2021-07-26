# import python library
import json


# function
def read(file_path):
    """
    read json file from given path

    Args:
        file_path (str): json file path

    Returns:
        file_data (list/dict): json file data

    Examples:
        import utils.common.fileUtils as fileUtils

        file_path = 'C:/_works/_pipeline/tests/json_test.json'
        file_data = fileUtils.jsonUtils.read(file_path)
    """

    infile = open(file_path, 'r')
    file_data = json.load(infile)
    infile.close()

    return file_data


def write(file_path, file_data):
    """
    write json data to the given path

    Args:
        file_path (str): json file path
        file_data (list/dict): json file data

    Examples:
        import utils.common.fileUtils as fileUtils

        file_path = 'C:/_works/_pipeline/tests/json_test.json'
        file_data = {'test': [1, 2, 3]}

        fileUtils.jsonUtils.write(file_path, file_data)
    """
    outfile = open(file_path, 'w')
    json.dump(file_data, outfile, indent=4, sort_keys=True)
    outfile.close()
