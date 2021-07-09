# import python library
import os
import re

# import utils
import fileUtils

# config
import config
config_dir = os.path.dirname(config.__file__)
TYPE_CONVENTION = fileUtils.jsonUtils.read(os.path.join(config_dir, 'NAME_TYPE.cfg'))
SIDE_CONVENTION = fileUtils.jsonUtils.read(os.path.join(config_dir, 'NAME_SIDE.cfg'))
LOD_CONVENTION = fileUtils.jsonUtils.read(os.path.join(config_dir, 'NAME_LOD.cfg'))

# get inverse dictionary so we can check name in a reverse way
TYPE_INVERSE = {}
for key, item in TYPE_CONVENTION.iteritems():
    TYPE_INVERSE.update({key: {v: k for k, v in item.iteritems()}})

SIDE_INVERSE = {}
for key, item in SIDE_CONVENTION.iteritems():
    SIDE_INVERSE.update({key: {v: k for k, v in item.iteritems()}})

LOD_INVERSE = {}
for key, item in LOD_CONVENTION.iteritems():
    LOD_INVERSE.update({item: key})


# class
class Name(object):
    """
    wrapper for easier naming data access

    Args:
        name(str): decompose the given name

        type (str): name's type
        side (str/list): name's side, it can be a string, which only contains primary side token (left/right/center)
                         or it can be a list with two tokens, one for primary,
                         and one for secondary(front/back/top/bottom)
        lod (str): name's level of detail, normally used for meshes and morph targets, default is None
        description (str/list): name's description, it can be a string, which only contains the node's description
                                or it can be a list with two  tokens, [description, additional description],
                                additional description is optional
        index (int): name's index
        limb_index (int): limb's index, normally used for rigging related nodes, default is None
        additional_description (str/list): additional descriptions if need to be added

    Examples:
        import utils.common.namingUtils as namingUtils

        # decompose name in object by giving a valid name
        name_obj = namingUtils.Name('mesh__c__hig__body__001')
        name_obj.type  # 'mesh'
        name_obj.side  # ['center']
        name_obj.index  # 1

        # compose name in object by given tokens
        name_obj = namingUtils.Name(type='mesh', side='left', lod='low', description='body', index=1)
        name_obj.name  # 'mesh__l__low__body__001'

        # modify tokens to update the name
        name_obj = namingUtils.Name('mesh__c__hig__body__001')
        name_obj.type = 'group'
        name_obj.lod = None
        name_obj.name  # 'grp__c__body__001'

        # flip name to the other side
        name_obj = namingUtils.Name('grp__l__hand__001')
        name_obj.flip()
        name_obj.name  # 'grp__r__hand__001'

        # update name using in class method
        name_obj = namingUtils.Name('mesh__c__hig__body__001')
        name_obj.update(type='group', lod='low', index=3)
        name_obj.name  # 'grp__c__low__body__003'
    """
    def __init__(self, *args, **kwargs):
        self._name = None
        self._type = kwargs.get('type', None)
        self._side = kwargs.get('side', None)
        self._lod = kwargs.get('lod', None)
        self._description = kwargs.get('description', None)
        self._index = kwargs.get('index', None)
        self._limb_index = kwargs.get('limb_index', None)
        self._additional_description = kwargs.get('additional_description', None)

        if args:
            self._name = args[0]
            self.decompose()
        else:
            self.compose()

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def side(self):
        return self._side

    @property
    def lod(self):
        return self._lod

    @property
    def description(self):
        return self._description

    @property
    def index(self):
        return self._index

    @property
    def limb_index(self):
        return self._limb_index

    @type.setter
    def type(self, value):
        self.update(type=value)

    @side.setter
    def side(self, value):
        self.update(side=value)

    @lod.setter
    def lod(self, value):
        self.update(lod=value)

    @description.setter
    def description(self, value):
        self.update(description=value)

    @index.setter
    def index(self, value):
        self.update(index=value)

    @limb_index.setter
    def limb_index(self, value):
        self.update(limb_index=value)

    def compose(self):
        """
        compose tokens to a valid name
        """
        self._name = compose(type=self._type, side=self._side, description=self._description, index=self._index,
                             lod=self._lod, limb_index=self._limb_index,
                             additional_description=self._additional_description)

    def decompose(self):
        """
        decompose name to tokens
        """
        token_info = decompose(self._name)
        self._type = token_info['type']
        self._side = token_info['side']
        self._description = token_info['description']
        self._index = token_info['index']
        self._lod = token_info['lod']
        self._limb_index = token_info['limb_index']

    def update(self, type=None, side=None, description=None, index=None, lod=None, limb_index=None,
               primary_side=None, secondary_side=None, additional_description=None):
        """
        update name with given tokens

        Args:
            type (str): name's type
            side (str/list): name's side, it can be a string, which only contains primary side token (left/right/center)
                             or it can be a list with two tokens, one for primary,
                             and one for secondary(front/back/top/bottom)
            description (str/list): name's description, it can be a string, which only contains the node's description
                                    or it can be a list with two  tokens, [description, additional description],
                                    additional description is optional
            index (int): name's index
            lod (str): name's level of detail, normally used for meshes and morph targets, default is None
            limb_index (int): limb's index, normally used for rigging related nodes, default is None
            primary_side (str): primary side full name if need to be updated
            secondary_side (str): secondary side full name if need to be updated
            additional_description (str/list): additional descriptions if need to be added
        """
        self._name = update(self._name, type=type, side=side, lod=lod, description=description, index=index,
                            limb_index=limb_index, primary_side=primary_side,
                            secondary_side=secondary_side, additional_description=additional_description)
        self.decompose()

    def flip(self):
        """
        flip name from one side to the other
        """
        self._name = flip(self._name, keep=True)
        self.decompose()


# functions
def compose(type=None, side=None, lod=None, description=None, index=1, limb_index=None, additional_description=None):
    """
    compose name tokens to naming format

    Args:
        type (str): name's type
        side (str/list): name's side, it can be a string, which only contains primary side token (left/right/center)
                         or it can be a list with two tokens, one for primary,
                         and one for secondary(front/back/top/bottom)
        lod (str): name's level of detail, normally used for meshes and morph targets, default is None
        description (str/list): name's description, it can be a string, which only contains the node's description
                                or it can be a list of  tokens, [description1, description2, description3...],
                                additional description is optional
        index (int): name's index
        limb_index (int): limb's index, normally used for rigging related nodes, default is None
        additional_description (str/list): additional descriptions if need to be added

    Returns:
        name (str)

    Examples:
        import utils.common.namingUtils as namingUtils

        namingUtils.compose(type='group', side='center', description='test', index=1)
        # 'grp__c__test__001'

        namingUtils.compose(type='mesh', side=['left', 'front'], lod='high'. description='test', index=1)
        # 'mesh__l_fnt__high__test__001'

        namingUtils.compose(type='ctrl', side='right', description='hand', index=2, limb_index=1)
        # 'ctrl__r__hand__001_002'

        namingUtils.compose(type='target', side='center', description=['face', 'smile'], index=1)
        # 'trgt__c__face_smile__001'

        namingUtils.compose(type='master')
        # 'master'
    """
    # check if the given type is a top node
    name = TYPE_CONVENTION['top'].get(type, None)
    if name:
        return name

    # check if the given type is in config file
    name = TYPE_CONVENTION['general'].get(type, None)
    if name:
        # collect tokens
        name_tokens = [name, _compose_side(side), _compose_description(description,
                                                                       additional_description=additional_description),
                       _compose_index(index, limb_index=limb_index)]
        # check lod
        if lod and lod in LOD_CONVENTION:
            name_tokens.insert(2, LOD_CONVENTION[lod])

        return '__'.join(name_tokens)

    else:
        raise KeyError("The given type: '{0}' is not supported".format(type))


def decompose(name):
    """
    decompose name into separate tokens

    Args:
        name (str)

    Returns:
        token_info(dict)

    Examples:
        import utils.common.namingUtils as namingUtils

        namingUtils.decompose('grp__c__test__001')
        # {'type': 'group',
           'side': ['center'],
           'lod': None,
           'description': 'test',
           'index': 1,
           'limb_index': None}
    """
    token_info = {'type': None,
                  'side': None,
                  'lod': None,
                  'description': None,
                  'index': None,
                  'limb_index': None}

    # split base on double underscore
    name_tokens = name.split('__')

    # check how many tokens got collected
    if len(name_tokens) == 5:
        # decompose each token
        type_name = _get_type(name_tokens[0], section='general')
        side_name = _get_side(name_tokens[1].split('_'))
        lod_name = _get_lod(name_tokens[2])
        description_name = name_tokens[3].split('_')
        limb_index, index = _get_index(name_tokens[4].split('_'))

        token_info.update({'type': type_name,
                           'side': side_name,
                           'lod': lod_name,
                           'description': description_name,
                           'index': index,
                           'limb_index': limb_index})

    elif len(name_tokens) == 4:
        # no lod
        type_name = _get_type(name_tokens[0], section='general')
        side_name = _get_side(name_tokens[1].split('_'))
        description_name = name_tokens[2].split('_')
        limb_index, index = _get_index(name_tokens[3].split('_'))

        token_info.update({'type': type_name,
                           'side': side_name,
                           'description': description_name,
                           'index': index,
                           'limb_index': limb_index})

    elif len(name_tokens) == 1:
        # only node type
        type_name = _get_type(name_tokens[0], section='top')

        token_info.update({'type': type_name})

    else:
        raise ValueError("given name: '{0}' is not supported".format(name))

    return token_info


def update(name, type=None, side=None, lod=None, description=None, index=None, limb_index=None, primary_side=None,
           secondary_side=None, additional_description=None):
    """
    update given name with tokens

    Args:
        name (str): the name need to be updated
        type (str): name's type
        side (str/list): name's side, it can be a string, which only contains primary side token (left/right/center)
                         or it can be a list with two tokens, one for primary,
                         and one for secondary(front/back/top/bottom)
        lod (str): name's level of detail, normally used for meshes and morph targets, default is None
        description (str/list): name's description, it can be a string, which only contains the node's description
                                or it can be a list with tokens, [description1, description2, description3 ...],
                                additional description is optional
        index (int): name's index
        limb_index (int): limb's index, normally used for rigging related nodes, default is None
        primary_side (str): primary side full name if need to be updated
        secondary_side (str): secondary side full name if need to be updated
        additional_description (str/list): additional descriptions if need to be added

    Returns:
        update_name (str): updated name

    Examples:
        import utils.common.namingUtils as namingUtils

        namingUtils.update('grp__c__test__001', type='mesh', lod='high', secondary_side='front',
                    additional_description='Suffix')
        # 'mesh__c_fnt__hig_test_suffix__001'
    """
    # decompose the name
    token_info = decompose(name)

    name_tokens = [token_info['type'], token_info['side'], token_info['lod'], token_info['description'],
                   token_info['index'], token_info['limb_index']]

    # update tokens
    for i, token in enumerate([type, side, lod, description, index, limb_index]):
        if token is not None:
            name_tokens[i] = token

    if primary_side:
        if isinstance(name_tokens[1], basestring) or not name_tokens[1]:
            # side token is either string or None, set it to primary side directly
            name_tokens[1] = primary_side
        else:
            # side tokens contain primary and secondary side, update the first one
            name_tokens[1][0] = primary_side

    if name_tokens[1] and secondary_side:
        if isinstance(name_tokens[1], basestring):
            # side token is a string, which means it only has primary side, convert to list to add the second
            name_tokens[1] = [name_tokens[1], secondary_side]
        elif len(name_tokens[1]) == 1:
            # side token is a list, but only contains primary side, append the list to add the second
            name_tokens[1].append(secondary_side)
        else:
            # side tokens have both primary and secondary, swap the secondary side directly
            name_tokens[1][2] = secondary_side

    if additional_description:
        if not name_tokens[3]:
            name_tokens[3] = additional_description
        else:
            if isinstance(additional_description, basestring):
                additional_description = [additional_description]
            name_tokens[3] += additional_description

    # update the token info to re-compose the name
    token_info.update({'type': name_tokens[0],
                       'side': name_tokens[1],
                       'lod': name_tokens[2],
                       'description': name_tokens[3],
                       'index': name_tokens[4],
                       'limb_index': name_tokens[5]})

    return compose(**token_info)


def check(name):
    """
    check if the given name is followed naming convention

    Args:
        name (str): name need to be checked

    Returns:
        True/False

    Examples:
        import utils.common.namingUtils as namingUtils

        namingUtils.check('mesh__c__hig_body__001')
        # True
        namingUtils.check('locator1')
        # False
    """
    try:
        decompose(name)
        return True
    except ValueError:
        return False


def flip_side(side, keep=True):
    if isinstance(side, basestring):
        if side == 'left':
            side_flip = 'right'
        elif side == 'right':
            side_flip = 'left'
        elif not keep:
            side_flip = None
        else:
            side_flip = side
    else:
        if side[0] == 'left':
            side_flip = ['right'] + side[1:]
        elif side[0] == 'right':
            side_flip = ['left'] + side[1:]
        elif not keep:
            side_flip = None
        else:
            side_flip = side
    return side_flip


def flip(name, keep=True):
    """
    flip the given name from one side to the other

    Args:
        name (str): name need to be flipped
        keep (bool): set to True if need to return the original name when the name is not flippable, default is True

    Returns:
        name (str)

    Examples:
        import utils.common.namingUtils as namingUtils

        name = namingUtils.flip('mesh__l__hig__hand__001')
        print(name)  # 'mesh__r__hig__hand__001'

        name = namingUtils.flip('mesh__r__hig__hand__001')
        print(name)  # 'mesh__l_hig__hand__001'

        name = namingUtils.flip('mesh__c__hig__hand__001', keep=True)
        print(name)  # 'mesh__c__hig__hand__001'

        name = namingUtils.flip('mesh__c__hig__hand__001', keep=False)
        print(name)  # None

        name = namingUtils.flip('locator1', keep=True)
        print(name)  # 'locator1'

        name = namingUtils.flip('locator1', keep=False)
        print(name)  # None
    """
    # check if name is an attribute name
    attr_names = []
    if isinstance(name, basestring):
        name_split = name.split('.')
        name = name_split[0]
        if len(name_split) > 1:
            attr_names = name_split[1:]

    # check if name is valid
    name_valid = check(name)

    if name_valid:
        # decompose name to get side
        tokens_info = decompose(name)
        # check side
        if tokens_info['side']:
            side = flip_side(tokens_info['side'], keep=keep)
            if side:
                tokens_info['side'] = side
                name = compose(**tokens_info)
            else:
                name = None

        elif not keep:
            # set name to None to return
            name = None

    elif not keep:
        # set name to None to return
        name = None

    # add attributes name back
    if name and attr_names:
        name = '.'.join([name] + attr_names)

    return name


def flip_names(names):
    if names:
        if isinstance(names, basestring):
            name_flip = flip(names, keep=True)
        elif isinstance(names, list):
            name_flip = [flip(n, keep=True) for n in names]
        elif isinstance(names, dict):
            name_flip = {k: flip(n, keep=True) for k, n in names.iteritems()}
        else:
            name_flip = names
    else:
        name_flip = names
    return name_flip


def compose_sequence(number, type=None, side=None, lod=None, description=None, start_index=1, limb_index=None):
    """
    compose multiple names using same pattern, with consecutive indexes

    Args:
        number (int): how many names need to be generated
        type (str): name's type
        side (str/list): name's side, it can be a string, which only contains primary side token (left/right/center)
                         or it can be a list with two tokens, one for primary,
                         and one for secondary(front/back/top/bottom)
        lod (str): name's level of detail, normally used for meshes and morph targets, default is None
        description (str/list): name's description, it can be a string, which only contains the node's description
                                or it can be a list of  tokens, [description1, description2, description3...],
                                additional description is optional
        start_index (int): names' start index, default is 1
        limb_index (int): limb's index, normally used for rigging related nodes, default is None

    Returns:
        names (list)
    """
    names = []
    for i in range(number):
        names.append(compose(type=type, side=side, lod=lod, description=description, index=start_index + i,
                             limb_index=limb_index))
    return names


def update_sequence(names, type=None, side=None, lod=None, description=None, index=None, limb_index=None,
                    primary_side=None, secondary_side=None, additional_description=None, search=None, replace=None):
    """
    update given names

    Args:
        names (list): names need to updater
        type (str): name's type
        side (str/list): name's side, it can be a string, which only contains primary side token (left/right/center)
                         or it can be a list with two tokens, one for primary,
                         and one for secondary(front/back/top/bottom)
        lod (str): name's level of detail, normally used for meshes and morph targets, default is None
        description (str/list): name's description, it can be a string, which only contains the node's description
                                or it can be a list with tokens, [description1, description2, description3 ...],
                                additional description is optional
        index (int): name's index
        limb_index (int): limb's index, normally used for rigging related nodes, default is None
        primary_side (str): primary side full name if need to be updated
        secondary_side (str): secondary side full name if need to be updated
        additional_description (str/list): additional descriptions if need to be added
        search (str/list): name parts need to be replaced
        replace (str/list): replaced parts with given names

    Returns:
        names (list)
    """
    if isinstance(search, basestring):
        search = [search]
    elif not search:
        search = []
    if isinstance(replace, basestring):
        replace = [replace]
    elif not replace:
        replace = []

    # loop in each name and update
    names_update = []
    for n in names:
        # update name
        n = update(n, type=type, side=side, lod=lod, description=description, index=index, limb_index=limb_index,
                   primary_side=primary_side, secondary_side=secondary_side,
                   additional_description=additional_description)

        # search and replace name parts
        for s, r in zip(search, replace):
            n = n.replace(s, r)

        names_update.append(n)

    return names_update


def to_snake_case(name):
    """
    convert camel case name to snake case

    get function from stackoverflow
    https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name_convert = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    return name_convert


def to_camel_case(name):
    """
    convert snake case name to camel case

    get function from stackoverflow
    https://stackoverflow.com/questions/4303492/how-can-i-simplify-this-conversion-from-underscore-to-camelcase-in-python
    """
    def camelcase():
        yield str.lower
        while True:
            yield str.capitalize

    c = camelcase()
    name = to_snake_case(name)
    return "".join(c.next()(x) if x else '_' for x in name.split("_"))


# sub functions
def _compose_side(side_token):
    """
    compose side tokens into naming format

    Args:
        side_token (str/list): name's side tokens need to be filled in,
                               it can be a string, which only contains primary side token (left/right/center)
                               or it can be a list with two tokens, one for primary,
                               and one for secondary(front/back/top/bottom)

    Returns:
        side_name (str): side name in required format
    """
    if not side_token:
        raise ValueError("no side value is given")

    if isinstance(side_token, basestring):
        side_token = [side_token]

    side_name = ''
    for token, section in zip(side_token[:2], ['primary', 'secondary']):
        token_val = SIDE_CONVENTION[section].get(token, None)
        if not token_val:
            raise KeyError("The given side: '{0}' is not supported".format(token))
        side_name += '{0}_'.format(token_val)

    return side_name[:-1]


def _compose_description(description_token, additional_description=None):
    """
    compose description tokens into naming format

    Args:
        description_token (str/list): name's description tokens need to be filled in,
                                      it can be a string, which only contains the node's description
                                      or it can be a list with two  tokens,
                                      [description, additional description],
                                      additional description is optional
        additional_description (str/list): additional descriptions if need to be added

    Returns:
        description_name (str): description name in required format
    """
    if not description_token:
        raise ValueError("no description is given")

    if isinstance(description_token, basestring):
        description_token = [description_token]

    if isinstance(additional_description, basestring):
        description_token.append(additional_description)
    elif isinstance(additional_description, list):
        description_token += additional_description

    return '_'.join(description_token)


def _compose_index(index, limb_index=None):
    """
    compose index tokens into naming format

    Args:
        index (int): name index tokens need to be filled in
        limb_index(int): limb's index, normally used for rigging related nodes, default is None

    Returns:
        index_name (str): index name in required format
    """
    if index is None:
        raise ValueError("no index value is given")

    index_name = ''

    if limb_index is not None:
        index_name += '{:03d}_'.format(limb_index)

    index_name += '{:03d}_'.format(index)

    return index_name[:-1]


def _get_type(value, section='general'):
    """
    get type full name from given value

    Args:
        value (str): naming type's short name
        section (str): 'top' or 'general', will look into the given section to get the full name

    Returns:
        type_name (str): naming type's full name
    """
    type_name = TYPE_INVERSE[section].get(value, None)
    if not type_name:
        raise ValueError("given type name: '{0}' is not supported".format(value))

    return type_name


def _get_side(value):
    """
    get side full name from given value

    Args:
        value (str/list): naming side's short name

    Returns:
        side_name (list): naming side's full name
    """
    if isinstance(value, basestring):
        value = [value]

    side_name = []
    for v, section in zip(value[:2], ['primary', 'secondary']):
        side_token = SIDE_INVERSE[section].get(v, None)
        if not side_token:
            raise ValueError("given side name: '{0}' is not supported".format(v))
        side_name.append(side_token)

    return side_name


def _get_lod(value):
    """
    get lod full name from given value

    Args:
        value (str): naming lod's short name

    Returns:
        lod_name (str): naming lod's full name
    """
    lod_name = LOD_INVERSE.get(value, None)
    if not lod_name:
        raise ValueError("given lod name: '{0}' is not supported".format(value))

    return lod_name


def _get_index(value):
    """
    get index from given value, will get limb index as well if in the value

    Args:
        value (str/list): naming's index in naming format

    Returns:
        limb_index (int): limb's index, return None if not in the given value
        index (int): naming's index
    """
    limb_index = None

    if isinstance(value, basestring):
        index = int(value)
    elif len(value) == 1:
        index = int(value[0])
    else:
        limb_index = int(value[0])
        index = int(value[1])

    return limb_index, index
