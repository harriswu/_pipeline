import maya.cmds as cmds

import utils.common.attributeUtils as attributeUtils


def sine(input_attr, name='sine1', connect_attr=None, force=True):
    """
    create sine node using given input attr

    Args:
        input_attr (str): input attribute
        name (str): node name
        connect_attr (str): connect attribute
        force (bool): force connection
    """
    # create quat node
    sine_node = cmds.createNode('eulerToQuat', name=name)
    cmds.connectAttr(input_attr, sine_node + '.inputRotateX')
    output_attr = sine_node + '.outputQuatX'
    if connect_attr:
        attributeUtils.connect(output_attr, connect_attr, force=force)
    return output_attr
