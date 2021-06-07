import maya.cmds as cmds

import utils.common.namingUtils as namingUtils


def create(driver, driven, rotation=False, drop_off=200, base_wire=None):
    """
    create wire deformer on driven object, using given driver

    Args:
        driver (str): driver node name
        driven (str): driven node name
        rotation (bool): driven object will rotate base on driver curve's normal and tangent changes, default is False
        drop_off (float): drop off distance for the driver wire, default is 200
        base_wire (str): use the given curve as base wire instead of auto create one, default is None

    Returns:
        wire_node (str): wire deformer node
        base_wire (str): base wire curve
    """
    if namingUtils.check(driven):
        wire_node = namingUtils.update(driven, type='wire')
    else:
        wire_node = 'wire_' + driven
    # create wire deformer
    cmds.wire(driven, wire=driver, name=wire_node, dropoffDistance=[(0, drop_off)])
    # get base curve
    base_node = cmds.listConnections(wire_node + '.baseWire[0]', source=True, destination=False, plugs=False)[0]
    if base_wire:
        # base wire shape given, override base wire connection
        # get base wire shape
        if cmds.objectType(base_wire) == 'transform':
            base_wire_shape = cmds.listRelatives(base_wire, shapes=True)[0]
        else:
            base_wire_shape = base_wire
            base_wire = cmds.listRelatives(base_wire_shape, parent=True)[0]
        cmds.connectAttr(base_wire_shape + '.worldSapce[0]', wire_node + '.baseWire[0]', force=True)
        # remove unused base wire node
        cmds.delete(base_node)
    else:
        # rename base wire
        if namingUtils.check(driver):
            base_wire = namingUtils.update(driver, type='wireBase')
        else:
            base_wire = 'wireBase_' + driver
        base_wire = cmds.rename(base_node, base_wire)
    # set rotation
    cmds.setAttr(wire_node + '.rotation', rotation)
    # return wire node and base wire
    return wire_node, base_wire
