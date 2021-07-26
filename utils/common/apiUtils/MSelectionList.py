# import maya python library
import maya.api.OpenMaya as OpenMaya2


# function
def create(*nodes):
    """
    create MSelectionList with given nodes added

    Args:
        *nodes (str): node names

    Returns:
        m_sel (MSelectionList)
    """
    # create empty MSelectionList
    m_sel = OpenMaya2.MSelectionList()
    for n in nodes:
        m_sel.add(n)
    return m_sel


def get_nodes_info(*nodes, **kwargs):
    """
    get given objects MObjects, MPlugs or MDagPaths

    Args:
        *nodes (str): node names
    Keyword Args:
        info_type (str): MObject, MPlug, MDagPath or component

    Returns:
        nodes_info (list): objects' MObjects, MPlugs or MDagPaths
    """
    info_type = kwargs.get('info_type', 'MObject')

    # get MSelectionList
    m_sel = create(*nodes)

    # get nodes info
    return get_nodes_info_from_list(m_sel, info_type=info_type)


def get_nodes_info_from_list(m_sel, index=None, info_type='MObject'):
    """
    get MObjects, MPlugs or MDagPaths information from given MSelectionList

    Args:
        m_sel (MSelectionList): given MSelection List
        index (int): get specific object's info, if None, will get all objects in the list
        info_type (str): MObject, MPlug, MDagPath or component

    Returns:
        nodes_info (list): objects' MObjects, MPlugs or MDagPaths
    """
    if info_type == 'MDagPath':
        return _get_MDagPath_from_list(m_sel, index=index)
    elif info_type == 'MObject':
        return _get_MObject_from_list(m_sel, index=index)
    elif info_type == 'MPlug':
        return _get_MPlug_from_list(m_sel, index=index)
    else:
        return _get_component_from_list(m_sel, index=index)


def _get_MDagPath_from_list(m_sel, index=None):
    """
    get objects MDagPaths from the given MSelectionList
    Args:
        m_sel (MSelectionList): given MSelection List
        index (int): get specific object's info, if None, will get all objects in the list

    Returns:
        dag_paths (list): a list of MDagPath objects
    """
    if index is not None:
        return [m_sel.getDagPath(index)]

    # get MSelectionList's length
    length = m_sel.length()

    dag_paths = []
    for i in range(length):
        dag_paths.append(m_sel.getDagPath(i))

    return dag_paths


def _get_MObject_from_list(m_sel, index=None):
    """
    get objects MObjects from the given MSelectionList
    Args:
        m_sel (MSelectionList): given MSelection List
        index (int): get specific object's info, if None, will get all objects in the list

    Returns:
        m_objs (list): a list of MObjects
    """
    if index is not None:
        return [m_sel.getDependNode(index)]

    # get MSelectionList's length
    length = m_sel.length()

    m_objs = []
    for i in range(length):
        m_objs.append(m_sel.getDependNode(i))

    return m_objs


def _get_MPlug_from_list(m_sel, index=None):
    """
    get objects MPlugs from the given MSelectionList
    Args:
        m_sel (MSelectionList): given MSelection List
        index (int): get specific object's info, if None, will get all objects in the list

    Returns:
        m_plugs (list): a list of MPlug objects
    """
    if index is not None:
        return [m_sel.getPlug(index)]

    # get MSelectionList's length
    length = m_sel.length()

    m_plugs = []
    for i in range(length):
        m_plugs.append(m_sel.getPlug(i))

    return m_plugs


def _get_component_from_list(m_sel, index=None):
    """
    get component MDagPath and MObject from the given MSelectionList
    Args:
        m_sel (MSelectionList): given MSelection List
        index (int): get specific object's info, if None, will get all objects in the list

    Returns:
        components (list): a list contains MDagPath and MObject, like [[MDagPath1, MObject1], [MDagPath2, MObject2]..]
    """
    if index is not None:
        return [m_sel.getComponent(index)]

    # get MSelectionList's length
    length = m_sel.length()

    components = []
    for i in range(length):
        components.append(m_sel.getComponent(i))

    return components
