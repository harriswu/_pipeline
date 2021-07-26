# import python library
import os


# function
def get_folders(path, full_path=True):
    """
    get folders from the given path

    Args:
        path(str): given path
        full_path(bool): return the full path if True, otherwise return the folders names only, default is True

    Returns:
        folders(list): all folders/all folders paths

    Examples:
        import utils.common.fileUtils as fileUtils

        fileUtils.pathUtils.get_folders('C:/_works/_pipeline/utils', full_path=False)
        # ['animation', 'common', 'modeling', 'rigging']

        fileUtils.pathUtils.get_folders('C:/_works/_pipeline/utils', full_path=True)
        # ['C:/_works/_pipeline/utils/animation', 'C:/_works/_pipeline/utils/common',
        #  'C:/_works/_pipeline/utils/modeling', 'C:/_works/_pipeline/utils/rigging']
    """

    all_files = os.listdir(path)

    folders = []

    for f in all_files:
        path_file = os.path.join(path, f)
        if os.path.isdir(path_file):
            # check if folder
            if full_path:
                folders.append(path_file)
            else:
                folders.append(f)
    return folders


def get_files_from_path(path, extension=None, exceptions=None, full_path=True):
    """
    get files from the given path

    Args:
        path(str): given path
        extension(list/str): specific extension
        exceptions(list/str): skip if worlds in exceptions
        full_path(bool): return full path if True, otherwise return just file names, default is True

    Returns:
        file_paths(list): all files path/names

    Examples:
        import utils.common.fileUtils as fileUtils

        fileUtils.pathUtils.get_files_from_path('C:/_works/_pipeline/utils/common', full_path=False)
        # ['attributeUtils.py', 'hierarchyUtils.py', 'namingUtils.py', 'namingUtils.pyc', 'transformUtils.py',
        #  '__init__.py', '__init__.pyc']

        fileUtils.pathUtils.get_files_from_path('C:/_works/_pipeline/utils/common', extension='.py', full_path=False)
        # ['attributeUtils.py', 'hierarchyUtils.py', 'namingUtils.py', 'transformUtils.py', '__init__.py']

        fileUtils.pathUtils.get_files_from_path('C:/_works/_pipeline/utils/common', extension='.py',
                                                exceptions='init', full_path=False)
        # ['attributeUtils.py', 'hierarchyUtils.py', 'namingUtils.py', 'transformUtils.py']

        fileUtils.pathUtils.get_files_from_path('C:/_works/_pipeline/utils/common', extension='.py',
                                                exceptions='init', full_path=True)
        # ['C:/_works/_pipeline/utils/common\\attributeUtils.py',
        #  'C:/_works/_pipeline/utils/common\\hierarchyUtils.py',
        #  'C:/_works/_pipeline/utils/common\\namingUtils.py',
        #  'C:/_works/_pipeline/utils/common\\transformUtils.py']
    """

    files = os.listdir(path)
    file_paths = []

    if isinstance(extension, basestring):
        extension = [extension]
    if isinstance(exceptions, basestring):
        exceptions = [exceptions]

    if files:
        for f in files:
            path_file = os.path.join(path, f)
            if os.path.isfile(path_file):
                ext = os.path.splitext(path_file)[-1]
                if not extension or ext in extension:
                    # check exceptions
                    add = True
                    if exceptions:
                        for exp in exceptions:
                            if exp in f:
                                add = False
                                break
                    if add:
                        if full_path:
                            file_paths.append(path_file)
                        else:
                            file_paths.append(f)
    return file_paths
