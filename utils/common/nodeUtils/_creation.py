import maya.cmds as cmds

import utils.common.namingUtils as namingUtils


def create(node_type, node_name, auto_suffix=False, **kwargs):
    """
    create maya node, mainly for utility node

    Args:
        node_type (str): maya node's type
        node_name (str): node's name
        auto_suffix (bool): automatically add an additional description as suffix,
                            it will starts with 'n001', and if it's already exists,
                            will automatically index up to avoid name clashing, default is False
        **kwargs: set attrs when creating the node

    Returns:
        name (str): node's name
    """
    # update name if auto suffix
    if auto_suffix:
        # list all nodes
        node_exists = cmds.ls(namingUtils.update(node_name, additional_description='n???'))
        node_name = namingUtils.update(node_name, additional_description='n{:03d}'.format(len(node_exists) + 1))
    # create node
    node = cmds.createNode(node_type, name=node_name)
    # set attribute values
    for attr, val in kwargs.iteritems():
        attr = '{0}.{1}'.format(node, attr)
        if cmds.objExists(attr):
            if not isinstance(val, list):
                val = [val]
            cmds.setAttr(attr, *val)
    return node
