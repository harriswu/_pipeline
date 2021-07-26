# import python library
import warnings

# import maya library
import maya.cmds as cmds

# import utils
import utils.common.namingUtils as namingUtils

# constant
ALL = ['translateX', 'translateY', 'translateZ',
       'rotateX', 'rotateY', 'rotateZ',
       'scaleX', 'scaleY', 'scaleZ', 'visibility']

TRANSFORM = ['translateX', 'translateY', 'translateZ',
             'rotateX', 'rotateY', 'rotateZ',
             'scaleX', 'scaleY', 'scaleZ']

TRANSLATE = ['translateX', 'translateY', 'translateZ']
ROTATE = ['rotateX', 'rotateY', 'rotateZ']
SCALE = ['scaleX', 'scaleY', 'scaleZ']
VISIBILITY = 'visibility'
ROTATE_ORDER = 'rotateOrder'
MATRIX = 'matrix'
INVERSE_MATRIX = 'inverseMatrix'
PARENT_MATRIX = 'parentMatrix[0]'
PARENT_INVERSE_MATRIX = 'parentInverseMatrix[0]'
WORLD_MATRIX = 'worldMatrix[0]'
WORLD_INVERSE_MATRIX = 'worldInverseMatrix[0]'

MESSAGE = 'message'


# function
def add(node, attrs, nice_name=None, attribute_type='float', value_range=None, default_value=None, keyable=True,
        channel_box=True, enum_name='', multi=False, lock_attr=False, parent=None):
    """
    add attributes on given node

    Args:
        node (str): node need to add attributes
        attrs (str/list): attribute names
        nice_name (str/list): attributes display names on channel box
        attribute_type(str): 'bool', 'long', 'enum', 'float', 'double',
                             'string', 'matrix', 'message', default is 'float'
        value_range(list):min/max value
        default_value(float/int/list/str): default value
        keyable(bool): set attr keyable, default is True
        channel_box(bool): show attr in channel box, default is True
        enum_name(str): enum attr name
        multi(m): add attr as a multi-attribute, default is False
        lock_attr (bool): lock attribute, default is False
        parent (str): parent attribute to given attribute name

    Returns:
        attr_paths (list): list of attributes full paths, like ['node.attr1', 'node.attr2']

    Examples:
        import maya.cmds as cmds
        import utils.common.attributeUtils as attributeUtils

        grp = cmds.createNode('transform', name='transform_node')
        attributeUtils.add(grp, ['test1', 'test2'], lock=False, attribute_type='float', value_range=[0, 1],
                           keyable=True)
        # ['transform_node.test1', 'transform_node.test2']
    """
    if isinstance(attrs, basestring):
        attrs = [attrs]

    if not isinstance(nice_name, list):
        nice_name = [nice_name] * len(attrs)

    # get default value
    if not isinstance(default_value, list):
        default_value = [default_value] * len(attrs)
    elif not isinstance(default_value[0], list) and attribute_type == 'matrix':
        default_value = [default_value] * len(attrs)

    # reset keyable
    if not channel_box or lock_attr:
        keyable = False

    # set attribute type key for cmds
    if attribute_type != 'string':
        attr_type_key = 'attributeType'
    else:
        attr_type_key = 'dataType'

    attr_paths = []
    for attr, val, n_name in zip(attrs, default_value, nice_name):
        attr_path = '{}.{}'.format(node, attr)

        attr_dict = {'longName': attr,
                     attr_type_key: attribute_type,
                     'keyable': keyable,
                     'multi': multi}

        if n_name:
            attr_dict.update({'niceName': n_name})

        # add default value
        if val is not None and not isinstance(val, basestring) and not isinstance(val, list):
            attr_dict.update({'defaultValue': val})

        # add min and max values
        if value_range:
            if value_range[0] is not None:
                attr_dict.update({'minValue': value_range[0]})
            if value_range[1] is not None:
                attr_dict.update({'maxValue': value_range[1]})

        if enum_name:
            attr_dict.update({'enumName': enum_name})

        # add parent
        if parent:
            attr_dict.update({'parent': parent})

        # add attr
        cmds.addAttr(node, **attr_dict)

        # set attribute data after creation
        if attribute_type != 'message':
            # set default value for string/matrix
            if attribute_type in ['string', 'matrix'] and val:
                cmds.setAttr(attr_path, val, type=attribute_type)
            # lock
            cmds.setAttr(attr_path, lock=lock_attr)
            # channelBox
            if attribute_type not in ['string', 'matrix'] and channel_box and not keyable:
                cmds.setAttr(attr_path, channelBox=channel_box)

        # append list
        attr_paths.append(attr_path)

    return attr_paths


def add_multi_dimension_attribute(node, name, compound_type='double3', attribute_type='doubleLinear', suffix='XYZ',
                                  keyable=True, multi=False, default_value=None):
    """
    add multi dimension attribute on given node

    Args:
        node (str): node name
        name (str): attribute name
        compound_type (str): the multi dimension attribute type
        attribute_type (str): the single attribute type
        suffix (str): suffix on each dimension
        keyable(bool): set attr keyable, default is True
        multi (bool): add attr as a multi-attribute, default is False
        default_value(list): default value

    Returns:
        attr_path (str): attribute path
    """
    attr_path = '{0}.{1}'.format(node, name)
    cmds.addAttr(node, longName=name, attributeType=compound_type, multi=multi, keyable=keyable)

    if not isinstance(default_value, list):
        default_value = [default_value] * len(suffix)

    suffix = list(suffix)

    for s, v in zip(suffix, default_value):
        kwargs = {'longName': name + s,
                  'attributeType': attribute_type,
                  'keyable': keyable,
                  'parent': name}
        if v is not None:
            kwargs.update({'defaultValue': v})

        cmds.addAttr(node, **kwargs)

    return attr_path


def add_divider(node, name):
    """
    add divider attribute for given node

    Args:
        node (str): maya node name
        name (str): divider name
    """
    name_upper = namingUtils.to_snake_case(name).upper()
    add(node, name + 'Divider', nice_name=name_upper + ' ---------------', attribute_type='enum',
        enum_name='----------', lock_attr=True, channel_box=True, keyable=False)


def connect(driver_attrs, driven_attrs, driver=None, driven=None, force=True):
    """
    Connect driver attrs to driven attrs

    Args:
        driver_attrs(str/list): source attrs
        driven_attrs(str/list): target attrs
        driver(str): override the node in driver_attrs
        driven(str): override the node in driven_attrs
        force(bool): override the connection/lock status, default is True
    """
    # check if driver_attrs/driven_attrs is string/list
    if isinstance(driver_attrs, basestring):
        driver_attrs = [driver_attrs]
    if isinstance(driven_attrs, basestring):
        driven_attrs = [driven_attrs]

    # connect each attr
    for attrs in zip(driver_attrs, driven_attrs):
        _connect_single_attr(attrs[0], attrs[1], driver=driver, driven=driven, force=force)

    if len(driver_attrs) == 1 and len(driven_attrs) > 1:
        # connect driver attr with all driven
        for attr in driven_attrs[1:]:
            _connect_single_attr(driver_attrs[0], attr, driver=driver, driven=driven, force=force)


def connect_nodes_to_multi_attr(driver_nodes, driven_attr, driver_attr=None, driven=None, skip_indexes=None,
                                force=True):
    """
    connect multiple nodes attributes to given multi type attribute

    Args:
        driver_nodes (str/list): driver nodes name
        driven_attr (str): driven multi type attribute name
        driver_attr (str): driver node's attribute name
        driven (str): driven node name
        skip_indexes (int/list): if need to skip specific slot, put the index here, default is None
        force (bool): force the connection
    """
    # get input attrs
    if isinstance(driver_nodes, basestring):
        driver_nodes = [driver_nodes]

    if driver_attr:
        driver_attrs = []
        for n in driver_nodes:
            driver_attrs.append(compose_attr(driver_attr, node=n)[0])
    else:
        driver_attrs = driver_nodes
    # get driven attr
    driven_attr = compose_attr(driven_attr, node=driven)[0]
    # get skip indexes as a list
    if skip_indexes is None:
        skip_indexes = []
    elif isinstance(skip_indexes, int):
        skip_indexes = [skip_indexes]
    # loop in each driver and connect with driven
    # get driver number
    driver_num = len(driver_attrs)
    # start counting
    driven_index = 0
    count = 0
    while driven_index < driver_num:
        if count not in skip_indexes:
            _connect_single_attr(driver_attrs[driven_index], '{0}[{1}]'.format(driven_attr, count), force=force)
            driven_index += 1
        count += 1


def remove_connections(node, source=True, destination=True):
    """
    remove node's source/destination connections

    Args:
        node (str): node name
        source (bool): remove all source connections if True
        destination (bool): remove all destination connections if True
    """
    # list all source connections
    if source:
        connect_plugs = cmds.listConnections(node, connections=True, source=True, destination=False, plugs=True,
                                             shapes=True, skipConversionNodes=True)
        node_attrs = connect_plugs[::2]
        connect_attrs = connect_plugs[1::2]
        for n_attr, c_attr in zip(node_attrs, connect_attrs):
            cmds.disconnectAttr(c_attr, n_attr)

    if destination:
        connect_plugs = cmds.listConnections(node, connections=True, source=False, destination=True, plugs=True,
                                             shapes=True, skipConversionNodes=True)
        node_attrs = connect_plugs[::2]
        connect_attrs = connect_plugs[1::2]
        for n_attr, c_attr in zip(node_attrs, connect_attrs):
            cmds.disconnectAttr(n_attr, c_attr)


def set_value(attr, value, node=None, force=True, **kwargs):
    """
    set values for attributes

    Args:
        attr (str/list): attribute's need to set values, can be full path or attribute name
                         if only attribute names are given, then node can't be empty
        value: attributes values
        node (str): if attr is given with attributes names,
                    it will need to compose with given node name to get full path
                    default is None
        force (bool): force to set value even it's locked
    Keyword Args:
        type(str): if need to be specific, normally for string/matrix

    Examples:
        import maya.cmds as cmds
        import utils.common.attributeUtils as attributeUtils

        grp = cmds.createNode('transform', name='transform_node')
        attributeUtils.set_value([grp + '.translateX', grp + '.translateY'], [1, 2])
        attributeUtils.set_value(['translateX', 'translateY'], [1, 2], node=grp)
    """
    attr_type = kwargs.get('type', None)

    if isinstance(attr, basestring):
        attr = [attr]
    # get how many attributes need to be set
    attrs_num = len(attr)

    if not isinstance(value, list):
        # if it's a single value, multiply the attrs_num to feed in each attr
        value = [value] * attrs_num
    elif attr_type == 'matrix' and not isinstance(value[0], list):
        # input value is a matrix list
        value = [value] * attrs_num

    for attr, val in zip(attr, value):
        # compose attr path
        attr_path = compose_attr(attr, node=node)[0]
        # get lock states
        lock_attr = cmds.getAttr(attr_path, lock=True)
        # get input connection
        input_plug = cmds.listConnections(attr_path, source=True, destination=False)

        # skip if has input connection
        if input_plug:
            warnings.warn("the attribute: {0} has input connection, can't set value, skipped".format(attr_path))
            continue
        elif lock_attr and not force:
            warnings.warn("the attribute: {0} is locked, can't set value, skipped".format(attr_path))
            continue
        else:
            # unlock attr
            cmds.setAttr(attr_path, lock=False)

        # set value
        cmds.setAttr(attr_path, val, **kwargs)

        # restore lock states
        cmds.setAttr(attr_path, lock=lock_attr)


def lock(attrs, node=None, channel_box=False):
    """
    lock and hide attrs

    Args:
        attrs(str/list): lock and hide given attrs
        node(str/list): the node to lock hide attrs
        channel_box(bool): show the attr on channel box, default is False

    Examples:
        import utils.common.attributeUtils as attributeUtils

        attributeUtils.lock_hide(['pCube1.translateX', 'pCube2.translateY'])

        attributeUtils.lock_hide(['translateX', 'translateY'], node='pCube1')
    """
    if not isinstance(node, list):
        node = [node]
    if not isinstance(attrs, list):
        attrs = [attrs]

    for attr in attrs:
        for n in node:
            attr_path = compose_attr(attr, node=n)[0]
            cmds.setAttr(attr_path, keyable=False, lock=True)
            cmds.setAttr(attr_path, channelBox=channel_box)


def unlock(attrs, node=None, keyable=True, channel_box=True):
    """
    unlock attrs

    Args:
        attrs(str/list): unlock and show given attrs
        node(str/list): the node to unlock attrs
        keyable(bool): set attr keyable, default is True
        channel_box(bool): show attr in channel box (none keyable if False), default is True

    Examples:
        import utils.common.attributeUtils as attributeUtils

        attributeUtils.unlock(['pCube1.translateX', 'pCube2.translateY'])

        attributeUtils.unlock(['translateX', 'translateY'], node='pCube1')
    """
    if isinstance(node, basestring):
        node = [node]
    if isinstance(attrs, basestring):
        attrs = [attrs]

    for attr in attrs:
        for n in node:
            attr_path = compose_attr(attr, node=n)[0]
            cmds.setAttr(attr_path, lock=False)
            cmds.setAttr(attr_path, channelBox=channel_box)
            if not channel_box:
                keyable = False
            cmds.setAttr(attr_path, keyable=keyable)


def transfer_attribute(source_attr, target_node, source_node=None, name_override=None, link=False):

    source_attr_path, source_node, source_attr = compose_attr(source_attr, node=source_node)

    # get target attr name
    if not name_override:
        # make sure to remove index
        target_attr = source_attr.split('[')[0]
    else:
        target_attr = name_override

    # get attribute information
    attr_kwargs = {'attribute_type': None,
                   'multi': False}

    # get attribute type
    attr_type = cmds.getAttr('{0}.{1}'.format(source_node, source_attr), type=True)
    attr_kwargs.update({'attribute_type': attr_type})
    # check multi
    if 'Compound' in attr_type:
        attr_kwargs.update({'multi': True})
        # check child attr type
        attr_type = cmds.getAttr(source_attr_path + '[0]', type=True)
        attr_kwargs.update({'attribute_type': attr_type})

    # check max and min value
    # remove index if exists, attributeQuery doesn't support index
    source_attr = source_attr.split('[')[0]
    value_range = [None, None]
    max_exists = cmds.attributeQuery(source_attr, node=source_node, maxExists=True)
    min_exists = cmds.attributeQuery(source_attr, node=source_node, minExists=True)
    if max_exists:
        max_val = cmds.attributeQuery(source_attr, node=source_node, maximum=True)[0]
        value_range[1] = max_val
    if min_exists:
        min_val = cmds.attributeQuery(source_attr, node=source_node, minimum=True)[0]
        value_range[0] = min_val
    if value_range != [None, None]:
        attr_kwargs.update({'value_range': value_range})

    # get default value
    default_val = cmds.attributeQuery(source_attr, node=source_node, listDefault=True)
    if default_val:
        attr_kwargs.update({'default_value': default_val[0]})

    # get keyable and channelBox
    keyable = cmds.attributeQuery(source_attr, node=source_node, keyable=True)
    channel_box = cmds.attributeQuery(source_attr, node=source_node, channelBox=True)
    if keyable:
        channel_box = True
    attr_kwargs.update({'keyable': keyable,
                        'channel_box': channel_box})

    # get enum name
    if attr_type == 'enum':
        enum_name = cmds.attributeQuery(source_attr, node=source_node, listEnum=True)[0]
        attr_kwargs.update({'enum_name': enum_name})

    # get children
    child_attrs = cmds.attributeQuery(source_attr, node=source_node, listChildren=True)
    if child_attrs:
        # get attr type
        child_attr_type = cmds.getAttr(child_attrs[0], type=True)
        # get suffix
        suffix = ''
        for attr in child_attrs:
            suffix += attr[-1]
        # add attribute
        add_multi_dimension_attribute(target_node, target_attr, compound_type=attr_type,
                                      attribute_type=child_attr_type, suffix=suffix, keyable=keyable, multi=False)
    else:
        add(target_node, target_attr, **attr_kwargs)

    target_attr_path = '{0}.{1}'.format(target_node, target_attr)

    if link:
        if not attr_kwargs.get('multi', False):
            connect(source_attr_path, target_attr_path)
        else:
            # get indexes in use
            indices = cmds.getAttr(source_attr_path, multiIndices=True)
            if indices:
                for i in indices:
                    connect('{0}[{1}]'.format(source_attr_path, i),
                            '{0}[{1}]'.format(target_attr_path, i))

    return target_attr_path


def transfer_default_attrs_status(source_node, target_nodes):
    """
    check source node's default attributes (translate/rotate/scale/visibility/rotateOrder),
    transfer the status (lock/unlock/channelBox/keyable/nonkeyable) to target nodes

    Args:
        source_node (str): source transform node
        target_nodes (str/list): target transform nodes
    """
    if isinstance(target_nodes, basestring):
        target_nodes = [target_nodes]

    # check each attribute status
    attr_info = {}
    for attr in ALL + [ROTATE_ORDER]:
        # check status
        keyable_status = cmds.getAttr('{0}.{1}'.format(source_node, attr), keyable=True)
        lock_staus = cmds.getAttr('{0}.{1}'.format(source_node, attr), lock=True)
        channel_box_status = cmds.getAttr('{0}.{1}'.format(source_node, attr), channelBox=True)
        attr_info.update({attr: {'keyable': keyable_status,
                                 'lock': lock_staus,
                                 'channel_box': channel_box_status}})

    # transfer to targets
    for target in target_nodes:
        for attr, status in attr_info.iteritems():
            if status['keyable']:
                unlock(attr, node=target, keyable=True, channel_box=True)
            else:
                lock_staus = status['lock']
                channel_box_status = status['channel_box']
                if lock_staus:
                    lock(attr, node=target, channel_box=channel_box_status)
                else:
                    unlock(attr, node=target, keyable=False, channel_box=channel_box_status)


def link_attrs(source_node, target_nodes, lock_attr=True, exception=None, force=True):
    """
    connect all source node's attributes to target nodes, it will skip the attributes not matching
    Args:
        source_node (str): source node name
        target_nodes (str/list): target node names
        lock_attr (bool): lock target's attributes after connection, default is True
        exception (str/list): skip given attributes
        force (bool): force the connection, default is True
    """
    if isinstance(target_nodes, basestring):
        target_nodes = [target_nodes]

    # get source node's attributes
    # get all custom attributes
    custom_attrs = cmds.listAttr(source_node, userDefined=True)
    if not custom_attrs:
        custom_attrs = []
    # get all keyable attributes
    keyable_attrs = cmds.listAttr(source_node, keyable=True)
    if not keyable_attrs:
        keyable_attrs = []
    # get all non-keyable but on channel box attributes
    channel_box_attrs = cmds.listAttr(source_node, channelBox=True)
    if not channel_box_attrs:
        channel_box_attrs = []
    # put together, and remove overlap ones
    attrs = list(set(custom_attrs + keyable_attrs + channel_box_attrs))
    # remove attrs in exception list
    if exception:
        if isinstance(exception, basestring):
            exception = [exception]
            for exp in exception:
                if exp in attrs:
                    attrs.remove(exp)

    # connect attrs
    for trgt_node in target_nodes:
        for at in attrs:
            # check if attribute on target node
            if check_exists(at, node=trgt_node):
                _connect_single_attr(at, at, driver=source_node, driven=trgt_node, force=force)
                # lock attribute
                if lock_attr:
                    lock(at, node=trgt_node)


def list_channel_box_attrs(node):
    # get all keyable attributes
    keyable_attrs = cmds.listAttr(node, keyable=True)
    if not keyable_attrs:
        keyable_attrs = []
    # get all non-keyable but on channel box attributes
    channel_box_attrs = cmds.listAttr(node, channelBox=True)
    if not channel_box_attrs:
        channel_box_attrs = []
    return keyable_attrs + channel_box_attrs


# enum
def get_enum_names(attr, node=None):
    """
    return the list of enum strings for the given attribute

    Args:
        attr (str): enum attribute name
        node (str): node name

    Returns:
        enum_name (str): enum name
        name_list (list): list of names
        index_list (list): list of indexes
    """
    attr_path, node, attr = compose_attr(attr, node=node)
    enum_name = cmds.attributeQuery(attr, node=node, listEnum=True)[0]
    # split by :
    enum_name_split = enum_name.split(':')

    enum_name_list = []
    enum_index_list = []

    index_current = 0
    for part in enum_name_split:
        # maya saving enum format is name=index, so we split = to get index
        part_split = part.split('=')
        name = part_split[0]
        # because maya only save the index if it's not continuously, like 'attr1=1:attr2=5',
        # otherwise will be 'attr1=1:attr2', so we need to check if it has index or not, if not, use current one
        if len(part_split) > 1:
            index = int(part_split[1])
        else:
            index = index_current
        enum_name_list.append(name)
        enum_index_list.append(index)

        index_current = index + 1  # add 1 for the current index, so the next enum attr will use if next to it

    return enum_name, enum_name_list, enum_index_list


def compose_attr(attr, node=None):
    """
    get attribute's full path

    Args:
        attr (str): given attribute, can be full name like 'node.attr' or only attribute name
        node (str): given node, default is None

    Returns:
        attr_path (str): attribute's full path
        node (str): node name
        attr_name (str): attribute's name

    Examples:
        import utils.common.attributeUtils as attributeUtils

        attributeUtils.compose_attr('pCube1.translateX', node=None)
        # ('pCube1.translateX', 'pCube1', 'translateX')

        attributeUtils.compose_attr('translateX', node='pCube1')
        # ('pCube1.translateX', 'pCube1', 'translateX')
    """
    attr_split = attr.split('.')
    if not node:
        # get node from attribute path
        node = attr_split[0]
        attr_name = attr.replace(node + '.', '')
        attr_path = attr
    else:
        # compose attr path
        attr_path = '{0}.{1}'.format(node, attr)
        attr_name = attr

    return attr_path, node, attr_name


def check_exists(attr, node=None):
    """
    check if attr exists or not, return None if not exist

    Args:
        attr (str): given attribute, can be full name like 'node.attr' or only attribute name
        node (str): given node, default is None

    Returns:
        attr_path (str): attribute's full path
        node (str): node name
        attr_name (str): attribute's name

    Examples:
        import maya.cmds as cmds
        import utils.common.attributeUtils as attributeUtils

        cmds.polyCube()
        attributeUtils.check_exists('pCube1.translateX', node=None)
        # ('pCube1.translateX', 'pCube1', 'translateX')

        attributeUtils.check_exists('pCube1.test', node=None)
        # None

        attributeUtils.compose_attr('test', node='pCube1')
        # None
    """
    attr_path, node, attr_name = compose_attr(attr, node=node)
    if cmds.objExists(attr_path):
        return attr_path, node, attr_name
    else:
        return None


def compose_attrs(nodes, attr_name):
    """
    compose attr path for list of nodes

    Args:
        nodes (list): nodes names
        attr_name (str): attribute name

    Returns:
        attr_paths (list): attribute paths
    """
    attr_paths = []
    for n in nodes:
        attr_paths.append('{}.{}'.format(n, attr_name))
    return attr_paths


def set_connect_single_attr(attr, value, force=True):
    """
    set/connect value to given single input attr

    Args:
        attr (str): attribute name
        value (str/float): attribute name, can be name or value
        force (bool): force connection
    """
    if isinstance(value, basestring):
        connect(value, attr, force=force)
    else:
        set_value(attr, value, force=force)


def set_connect_3d_attr(attr, value, attr_suffix='XYZ', force=True):
    """
    set/connect values to given 3d type input, like translate, rotate, scale or color

    if only one value/attribute given, it will use the first slot

    Args:
        attr (str): attribute name
        value (str/float/list): attribute value, can be float value, attribute name, or list of value/attr names
        attr_suffix (str): 3d attr's suffix, translate is XYZ, color is RGB, default is XYZ
        force: force connection
    """
    if isinstance(value, basestring):
        # input value is an attribute
        # check input value's type
        value_type = cmds.getAttr(value, type=True)
        if value_type.endswith('3'):
            # it's a 3D attr, connect directly
            connect(value, attr, force=force)
        else:
            # it's a 1D attr, connect the first slot
            connect(value, attr + attr_suffix[0], force=force)
    elif not isinstance(value, list):
        # input value is a number, set to the first slot
        set_value(attr + attr_suffix[0], value, force=force)
    else:
        # input value is a list, set/connect one by one
        for i, v in enumerate(value):
            set_connect_single_attr(attr + attr_suffix[i], v, force=force)


# sub function
def _connect_single_attr(driver_attr, driven_attr, driver=None, driven=None, force=True):
    """
    Args:
        driver_attr(str): source attr
        driven_attr(str): target attr
        driver(str): override the node in driver_attr
        driven(str): override the node in driven_attr
        force(bool): override the connection/lock status, default is True
    """

    driver_attr = compose_attr(driver_attr, node=driver)[0]
    driven_attr = compose_attr(driven_attr, node=driven)[0]

    # check if driven attr has connection
    input_plug = cmds.listConnections(driven_attr, source=True, destination=False, plugs=True, skipConversionNodes=True)
    # check if driven attr is locked
    lock_attr = cmds.getAttr(driven_attr, lock=True)

    # connect attr
    if not input_plug and not lock_attr:
        # just connect attr
        cmds.connectAttr(driver_attr, driven_attr)
    else:
        if force:
            if not input_plug or driver_attr not in input_plug:
                cmds.setAttr(driven_attr, lock=False)  # unlock the attr anyway
                cmds.connectAttr(driver_attr, driven_attr, force=True)  # force connection
                cmds.setAttr(driven_attr, lock=lock_attr)  # restore lock state
        else:
            if input_plug:
                if input_plug[0] != driver_attr:
                    warnings.warn("the attribute: {0} already has input connection from {1}, "
                                  "skipped".format(driven_attr, input_plug[0]))
                else:
                    warnings.warn("the attribute: {0} is already connected with {1}, "
                                  "skipped".format(driven_attr, driver_attr))
            elif lock_attr:
                warnings.warn("the attribute: {0} is locked, skipped".format(driven_attr))
