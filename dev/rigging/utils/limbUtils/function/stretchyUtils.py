import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.nodeUtils as nodeUtils


def add_stretchy(nodes, name_template, stretch, stretch_dis, orig_length, stretch_max, stretch_min,
                 max_clamp, min_clamp):
    """
    add stretch setup for given nodes

    Args:
        nodes (list): nodes need to add stretchy setup, normally is a list of joints
        name_template (str): use given name as a reference to name all the utility nodes
        stretch (str/bool): the attribute/value turn stretchy effect on and off
        stretch_dis (str): the distance attribute between root position and ik handle
        orig_length (str/float): the original chain length attribute/value
        stretch_max (str/float): stretchy maximum attribute/value
        stretch_min (str/float): stretchy minimum attribute/value
        max_clamp (str/bool): the attribute/value decide if clamp the stretchy effect with maximum limitation
        min_clamp (str/bool): the attribute/value decide if clamp the stretchy effect with minimum limitation
    """
    # divide to get stretch weight
    stretch_weight_attr = nodeUtils.arithmetic.equation('{0}/{1}'.format(stretch_dis, orig_length),
                                                        namingUtils.update(name_template,
                                                                           additional_description='stretchWeight'))

    # use blender node to blend min and max values
    name = namingUtils.update(name_template, type='blendColors', additional_description='stretchMaxClamp')
    blend_max = nodeUtils.utility.blend_colors(max_clamp, stretch_max, stretch_weight_attr, name=name) + 'R'

    name = namingUtils.update(name_template, type='blendColors', additional_description='stretchMinClamp')
    blend_min = nodeUtils.utility.blend_colors(min_clamp, stretch_min, stretch_weight_attr, name=name) + 'R'

    # use condition to clamp min and max weights
    max_weight_attr = nodeUtils.utility.condition(stretch_weight_attr, stretch_max, blend_max, stretch_weight_attr,
                                                  name=namingUtils.update(name_template, type='condition',
                                                                          additional_description='stretchMax'),
                                                  operation='>') + 'R'
    min_weight_attr = nodeUtils.utility.condition(stretch_weight_attr, stretch_min, blend_min, max_weight_attr,
                                                  name=namingUtils.update(name_template, type='condition',
                                                                          additional_description='stretchMin'),
                                                  operation='<') + 'R'

    # blend with original weight value to turn it on and off
    name = namingUtils.update(name_template, type='blendColors', additional_description='stretchWeight')
    blend_stretch = nodeUtils.utility.blend_colors(stretch, min_weight_attr, 1, name=name) + 'R'

    # loop into each setup node and multiply translate X to do stretch
    for n in nodes[1:]:
        tx_val = cmds.getAttr(n + '.translateX')
        nodeUtils.arithmetic.equation('{0}*{1}'.format(tx_val, blend_stretch),
                                      namingUtils.update(n, additional_description='stretch'),
                                      connect_attr=n + '.translateX')
