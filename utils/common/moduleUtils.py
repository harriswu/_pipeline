import importlib


def import_module(path, function=None):
    """
    import module from given path

    Args:
        path (str): import module path, path should be sth like 'dev.rigging.module'
        function (str): function name, if None will use the module name

    Returns:
        module, function
    """
    path = str(path)

    module_token = path.split('.')
    if not function:
        # get function name using module name, first letter in cap
        function = module_token[-1][0].upper() + module_token[-1][1:]

    # get module object
    module = importlib.import_module(path)

    return module, function
