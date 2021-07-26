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
    limb_object.register_steps()
    # get limb info from limb node
    limb_object.get_info(limb_node)

    return limb_object


def is_limb(limb_node):
    if cmds.objExists(limb_node + '.nodePath'):
        node_path = cmds.getAttr(limb_node + '.nodePath')
        # check if it's a rig limb or master
        if 'rigLimb' in node_path or 'rigMaster' in node_path:
            # get limb object
            limb_object = get_limb_object(limb_node)
        else:
            limb_object = None
    else:
        limb_object = None
    return limb_object
