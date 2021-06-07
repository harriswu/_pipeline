import ast
import inspect

import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils


class CoreNode(object):
    # constant attributes
    INPUT_NODE_ATTR = 'inputNode'
    OUTPUT_NODE_ATTR = 'outputNode'

    NODE_PATH_ATTR = 'nodePath'

    def __init__(self, **kwargs):
        # naming kwargs
        self._side = kwargs.get('side', 'center')
        self._description = kwargs.get('description', '')
        self._index = kwargs.get('index', 1)
        self._limb_index = kwargs.get('limb_index', 1)
        self._additional_description = kwargs.get('additional_description', None)

        # hierarchy kwargs
        self._parent_node = kwargs.get('parent_node', None)
        # get rig node's python path
        self._node_path = inspect.getmodule(self.__class__).__name__

        # hierarchy nodes
        self._node = None
        self._input_node = None
        self._output_node = None

        # node type for different naming
        self._node_type = 'rigNode'

    @property
    def node(self):
        return self._node

    @node.setter
    def node(self, value):
        self._node = value

    @property
    def node_path(self):
        return self._node_path

    def build(self):
        """
        build rig node
        """
        self.create_hierarchy()
        self.register_inputs()
        self.create_node()
        self.register_outputs()

    def create_hierarchy(self):
        """
        create node's hierarchy
        """
        # create rig node
        self._node = namingUtils.compose(type=self._node_type, side=self._side, description=self._description,
                                         index=self._index, limb_index=self._limb_index,
                                         additional_description=self._additional_description)
        transformUtils.create(self._node, lock_hide=attributeUtils.ALL, parent=self._parent_node)

        # create input, output and default value node
        self._input_node = transformUtils.create(namingUtils.update(self._node, type='inputNode'),
                                                 lock_hide=attributeUtils.ALL, parent=self._node)
        self._output_node = transformUtils.create(namingUtils.update(self._node, type='outputNode'),
                                                  lock_hide=attributeUtils.ALL, parent=self._node)

        # register node path
        attributeUtils.add(self._node, self.NODE_PATH_ATTR, attribute_type='string', default_value=self._node_path,
                           lock_attr=True)

    def create_node(self):
        """
        create rig node
        """
        pass

    def get_info(self):
        """
        get rig node information
        """
        # get name tokens
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
        # get parent node
        parent_node = cmds.listRelatives(self._node, parent=True)
        if parent_node:
            self._parent_node = parent_node[0]
        else:
            self._parent_node = None

        self.get_input_info()
        self.get_output_info()

    def connect(self, **kwargs):
        self.get_connection_kwargs(**kwargs)
        self.post_register_inputs()
        self.post_build()
        self.post_register_outputs()
        self.connect_inputs()
        self.connect_outputs()

    def get_connection_kwargs(self, **kwargs):
        pass

    def remove(self):
        # delete node
        cmds.delete(self._node)

    def register_inputs(self):
        pass

    def register_outputs(self):
        pass

    def post_register_inputs(self):
        pass

    def post_build(self):
        pass

    def post_register_outputs(self):
        pass

    def connect_inputs(self):
        pass

    def connect_outputs(self):
        pass

    def get_input_info(self):
        pass

    def get_output_info(self):
        pass

    def add_object_attribute(self, attr_name, value):
        setattr(self, attr_name, value)

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
            else:
                # it's a data compound, get values from available indices
                values = []
                for i in indices:
                    values.append(cmds.getAttr('{}[{}]'.format(attr_path, i)))
        else:
            values = []
        return values

    @staticmethod
    def set_multi_attr_values(attr, values, node=None):
        attr_path, node, attr_name = attributeUtils.compose_attr(attr, node=node)
        for i, val in enumerate(values):
            attr_type = cmds.getAttr('{}[{}]'.format(attr_path, i), type=True)
            attributeUtils.set_value('{}[{}]'.format(attr_path, i), val, type=attr_type)

    @staticmethod
    def get_multi_attr_names(attr, node=None):
        attr_path, node, attr_name = attributeUtils.compose_attr(attr, node=node)
        # get indexes in use
        indices = cmds.getAttr(attr_path, multiIndices=True)
        if indices:
            attrs = []
            for i in indices:
                attrs.append('{}[{}]'.format(attr_path, i))
        else:
            attrs = []
        return attrs
