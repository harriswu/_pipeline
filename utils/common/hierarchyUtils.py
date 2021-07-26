# import python library
import warnings

# import maya python library
import maya.cmds as cmds


# function
def parent(child_nodes, parent_node):
    """
    parent nodes under given parent node,
    it will skip instead of error out if given nodes are already children for the parent

    Args:
        child_nodes(str/list): given nodes
        parent_node(str): given parent node

    Examples:
        import utils.common.hierarchyUtils as hierarchyUtils

        hierarchyUtils.parent('group1', 'group2')
        hierarchyUtils.parent(['group1', 'group2'], 'group3')
    """
    if not parent_node:
        warnings.warn("no parent node given, skipped")
        return

    if isinstance(child_nodes, basestring):
        child_nodes = [child_nodes]

    for n in child_nodes:
        p = cmds.listRelatives(n, p=True)
        if not p or p[0] != parent_node:
            # parent if given node has no parent or not the same has given parent
            cmds.parent(n, parent_node)


def parent_chain(nodes, parent_node=None, reverse=False):
    """
    parent given nodes as a hierarchy chain
    by default, the hierarchy order is from end to root

    Args:
        nodes (list): nodes need to be parented as a chain
        parent_node (str): parent hierarchy chain to the given node
        reverse (bool): reverse parent order, default is False

    Returns:
        nodes (list): chain nodes, from the top node to the bottom child node
    """
    # copy node list so it won't affect the original list
    chain_nodes = nodes[:]

    # the given list is from the bottom to the top, so we need to reverse the order
    # but if reverse set to True, then we don't need to reverse again
    if not reverse:
        chain_nodes.reverse()

    # add parent node to the start of the list
    chain_nodes.insert(0, parent_node)

    # loop in each node and parent the chain, parent each one to the previous one on the list
    for i, n in enumerate(chain_nodes[1:]):
        parent(n, chain_nodes[i])

    # skip the parent node, don't need to return it
    nodes_return = chain_nodes[1:]

    return nodes_return


def get_parent(node):
    """
    get node's parent node

    Args:
        node (str): node's name

    Returns:
        parent_node (str): parent node's name
    """
    parent_node = cmds.listRelatives(node, parent=True)
    if parent_node:
        parent_node = parent_node[0]
    else:
        parent_node = None
    return parent_node


def get_all_parents(node, root=None):
    """
    get all parent nodes from the given root node, the order is from the top to the bottom
    Args:
        node (str): transform node
        root (str): get all parent nodes starting from the given node, None will start from world, default is None

    Returns:
        parent_nodes (list): given transform's parent nodes
    """
    # check if given node is under world or node
    if not cmds.listRelatives(node, parent=True):
        return []

    # get node's full path
    node_long = cmds.ls(node, long=True)[0]
    # split to get each node name, first is empty, and the last is node's name, remove those
    parent_nodes = node_long.split('|')[1:-1]
    if root:
        if root in parent_nodes:
            if len(parent_nodes) == 1:
                # check if the hierarchy only has root node
                return []
            else:
                # get root index
                root_index = parent_nodes.index(root)
                parent_nodes = parent_nodes[root_index + 1:]
        else:
            raise ValueError('given node: {0} is not part of the hierarchy of {1}'.format(root, node))

    return parent_nodes
