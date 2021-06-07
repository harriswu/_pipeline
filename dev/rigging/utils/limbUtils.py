import maya.cmds as cmds

import utils.common.moduleUtils as moduleUtils


def get_limb_object(limb_node):
    """
    get limb object wrapper to easier access limb related information

    Args:
        limb_node (str): limb node's name

    Returns:
        limb_object (object): limb object wrapper
    """
    # get limb path
    path = cmds.getAttr(limb_node + '.nodePath')
    # get limb object
    limb_module, limb_class = moduleUtils.import_module(path)
    limb_object = getattr(limb_module, limb_class)()
    # get limb info from limb node
    limb_object.node = limb_node
    limb_object.get_info()

    return limb_object
