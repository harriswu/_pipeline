import maya.cmds as cmds

import utils.common.hierarchyUtils as hierarchyUtils


def duplicate_clean(node, name, parent=None):
    cmds.duplicate(node, name=name)
    shapes = cmds.listRelatives(name, shapes=True)
    if len(shapes) > 1:
        cmds.delete(shapes[1:])
    hierarchyUtils.parent(name, parent)
    return name
