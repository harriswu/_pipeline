import ast

import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.moduleUtils as moduleUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.hierarchyUtils as hierarchyUtils
import utils.common.transformUtils as transformUtils

import dev.rigging.rigFunction.core.coreFunction as coreFunction


class CoreNode(coreFunction.CoreFunction):
    """
    node template class, all rig nodes should sub-class from this class

    it has 3 build sections, build, connect and get_info
    build: create the rig node in the scene
    connect: connect the inputs to this rig node
    get_info: get rig node information from the top node
    """
    # constant attributes
    INPUT_NODE_ATTR = 'inputNode'
    OUTPUT_NODE_ATTR = 'outputNode'
    NODE_PATH_ATTR = 'nodePath'

    def __init__(self, **kwargs):
        super(CoreNode, self).__init__(**kwargs)
        self._flip = kwargs.get('flip', False)
        self._skip_name_flip = kwargs.get('skip_name_flip', False)
        # node type for different naming
        self._node_type = 'rigNode'

        # build sections
        self._build_list.update({'get_info': {'functions': {},
                                              'keys': []}})

        # hierarchy nodes
        self._node = None
        self._input_node = None
        self._output_node = None
        self._compute_node = None

        # place holder for kwargs
        self._side = None
        self._description = None
        self._index = None
        self._limb_index = None
        self._additional_description = []
        self._parent_node = None

    # properties
    @property
    def node(self):
        return self._node

    @property
    def input_node(self):
        return self._input_node

    @property
    def output_node(self):
        return self._output_node

    @property
    def compute_node(self):
        return self._compute_node

    @property
    def parent_node(self):
        return self._parent_node

    # get kwargs
    def get_build_kwargs(self, **kwargs):
        super(CoreNode, self).get_build_kwargs(**kwargs)
        # naming kwargs
        self._side = kwargs.get('side', 'center')
        self._description = kwargs.get('description', '')
        self._index = kwargs.get('index', 1)
        self._limb_index = kwargs.get('limb_index', 1)
        self._additional_description = kwargs.get('additional_description', [])

        # hierarchy kwargs
        self._parent_node = kwargs.get('parent_node', None)

    def flip_build_kwargs(self):
        self._side = namingUtils.flip_side(self._side, keep=True)
        self._parent_node = namingUtils.flip_names(self._parent_node)

    def register_build_kwargs(self, **kwargs):
        super(CoreNode, self).register_build_kwargs(**kwargs)
        if self._flip and not self._skip_name_flip:
            self.flip_build_kwargs()

    def get_build_setting(self):
        super(CoreNode, self).get_build_setting()
        if self._side != 'right' and 'right' not in self._side:
            self.get_left_build_setting()
        else:
            self.get_right_build_setting()

    def get_left_build_setting(self):
        pass

    def get_right_build_setting(self):
        pass

    def get_connect_kwargs(self, **kwargs):
        super(CoreNode, self).get_connect_kwargs(**kwargs)
        pass

    def flip_connect_kwargs(self):
        pass

    def register_connect_kwargs(self, **kwargs):
        super(CoreNode, self).register_connect_kwargs(**kwargs)
        if self._flip and not self._skip_name_flip:
            self.flip_connect_kwargs()

    def get_connect_setting(self):
        super(CoreNode, self).get_connect_setting()
        if self._side != 'right' and 'right' not in self._side:
            self.get_left_connect_setting()
        else:
            self.get_right_connect_setting()

    def get_left_connect_setting(self):
        pass

    def get_right_connect_setting(self):
        pass

    # execute functions
    def get_info(self, node):
        self._node = node

        for key in self._build_list['get_info']['keys']:
            self._build_list['get_info']['functions'][key]()

    # register steps to sections
    def register_steps(self):
        super(CoreNode, self).register_steps()
        # build steps
        self.add_build_step('create hierarchy', self.create_hierarchy, 'build')
        self.add_build_step('add input attributes', self.add_input_attributes, 'build')
        self.add_build_step('create node', self.create_node, 'build')
        self.add_build_step('add output attributes', self.add_output_attributes, 'build')

        # connect steps
        self.add_build_step('add input attributes post', self.add_input_attributes_post, 'connect')
        self.add_build_step('create node post', self.create_node_post, 'connect')
        self.add_build_step('add output attributes post', self.add_output_attributes_post, 'connect')
        self.add_build_step('connect input attributes', self.connect_input_attributes, 'connect')
        self.add_build_step('connect output attributes', self.connect_output_attributes, 'connect')

        # get info steps
        self.add_build_step('get rig node info', self.get_rig_node_info, 'get_info')
        self.add_build_step('get input info', self.get_input_info, 'get_info')
        self.add_build_step('get output info', self.get_output_info, 'get_info')

    # build functions
    def create_hierarchy(self):
        """
        create node's hierarchy
        """
        # create rig node
        self._node = namingUtils.compose(type=self._node_type, side=self._side, description=self._description,
                                         index=self._index, limb_index=self._limb_index,
                                         additional_description=self._additional_description)
        transformUtils.create(self._node, lock_hide=attributeUtils.ALL, parent=self._parent_node)

        # create input, output and compute node
        self._input_node = transformUtils.create(namingUtils.update(self._node, type='inputNode'),
                                                 lock_hide=attributeUtils.ALL, parent=self._node)
        self._output_node = transformUtils.create(namingUtils.update(self._node, type='outputNode'),
                                                  lock_hide=attributeUtils.ALL, parent=self._node)
        self._compute_node = transformUtils.create(namingUtils.update(self._node, type='computeNode'),
                                                   lock_hide=attributeUtils.ALL, parent=self._node)

        # register node path
        attributeUtils.add(self._node, self.NODE_PATH_ATTR, attribute_type='string', default_value=self._node_path,
                           lock_attr=True)

    def add_input_attributes(self):
        pass

    def create_node(self):
        pass

    def add_output_attributes(self):
        pass

    # connect functions
    def add_input_attributes_post(self):
        pass

    def create_node_post(self):
        pass

    def add_output_attributes_post(self):
        pass

    def connect_input_attributes(self):
        pass

    def connect_output_attributes(self):
        pass

    # get node info
    def get_rig_node_info(self):
        name_info = namingUtils.decompose(self._node)
        self._side = name_info.get('side', 'center')
        self._description = name_info.get('description', None)
        self._index = name_info.get('index', 1)
        self._limb_index = name_info.get('limb_index', 1)
        self._additional_description = name_info.get('additional_description', [])
        self._node_path = cmds.getAttr('{0}.{1}'.format(self._node, self.NODE_PATH_ATTR))
        # get input, output node
        self._input_node = namingUtils.update(self._node, type='inputNode')
        self._output_node = namingUtils.update(self._node, type='outputNode')
        self._compute_node = namingUtils.update(self._node, type='computeNode')
        # get parent node
        self._parent_node = hierarchyUtils.get_parent(self._node)

    def get_input_info(self):
        pass

    def get_output_info(self):
        pass

    def add_object_attribute(self, attr_name, value):
        setattr(self, attr_name, value)

    # static method functions
    # set attrs
    @staticmethod
    def set_multi_attr_values(attr, values, node=None):
        attr_path, node, attr_name = attributeUtils.compose_attr(attr, node=node)
        for i, val in enumerate(values):
            attr_type = cmds.getAttr('{0}[{1}]'.format(attr_path, i), type=True)
            attributeUtils.set_value('{0}[{1}]'.format(attr_path, i), val, type=attr_type)

    # get attrs
    @staticmethod
    def get_single_attr_value(attr, node=None):
        attr_path, node, attr_name = attributeUtils.compose_attr(attr, node=node)
        # check if attribute exist
        if attributeUtils.check_exists(attr_path):
            # check attribute type
            attr_type = cmds.getAttr(attr_path, type=True)
            if attr_type == 'message':
                val = cmds.listConnections(attr_path, source=True, destination=False, plugs=False, shapes=True)
                if val:
                    val = val[0]
                else:
                    val = None
            elif attr_type == 'string':
                val = cmds.getAttr(attr_path)
                if val:
                    try:
                        # try to convert it to other data type
                        val = ast.literal_eval(val)
                    except ValueError:
                        # otherwise it's a string
                        pass
                else:
                    val = None
            else:
                val = cmds.getAttr(attr_path)
        else:
            val = None
        return val

    @staticmethod
    def get_multi_attr_value(attr, node=None):
        attr_path, node, attr_name = attributeUtils.compose_attr(attr, node=node)
        # check if attribute exist
        if attributeUtils.check_exists(attr_path):
            # get indexes in use
            indices = cmds.getAttr(attr_path, multiIndices=True)
            # check attribute type
            attr_type = cmds.getAttr(attr_path, type=True)
            if attr_type == 'message':
                # it's a message compound, get message attrs connect with the attr
                values = cmds.listConnections(attr_path, source=True, destination=False, plugs=False, shapes=True)
                if not values:
                    values = []
            else:
                # it's a data compound, get values from available indices
                values = []
                for i in indices:
                    values.append(cmds.getAttr('{0}[{1}]'.format(attr_path, i)))
        else:
            values = []
        return values

    @staticmethod
    def get_multi_attr_names(attr, node=None):
        attr_path, node, attr_name = attributeUtils.compose_attr(attr, node=node)
        # get indexes in use
        indices = cmds.getAttr(attr_path, multiIndices=True)
        if indices:
            attrs = []
            for i in indices:
                attrs.append('{0}[{1}]'.format(attr_path, i))
        else:
            attrs = []
        return attrs

    @staticmethod
    def create_rig_node(node_path, name_template=None, build=True, build_kwargs=None, connect=True, connect_kwargs=None,
                        flip=False):
        """
        create rig node using given module path

        Args:
            node_path (str): rig node's path
            name_template (str): get name information from given node
            build (bool): execute build process if set to True
            build_kwargs (dict): build arguments
            connect (bool): execute connect process if set to True
            connect_kwargs (dict): connect arguments
            flip (bool): instead building the given side, it will build the opposite side

        Returns:
            rig_node_object: rig node instance
        """
        if name_template:
            name_info = namingUtils.decompose(name_template)
        else:
            name_info = {}

        rig_node_module, rig_node_class = moduleUtils.import_module(node_path)
        rig_node_object = getattr(rig_node_module, rig_node_class)(flip=flip, skip_name_flip=True)
        rig_node_object.register_steps()
        if build:
            if build_kwargs:
                name_info.update(build_kwargs)
            build_kwargs = name_info

            rig_node_object.build(**build_kwargs)

            # connect process need to happens after build, so put it under build if statement
            if connect:
                if not connect_kwargs:
                    connect_kwargs = {}
                rig_node_object.connect(**connect_kwargs)

        return rig_node_object
