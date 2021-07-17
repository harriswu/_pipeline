import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.hierarchyUtils as hierarchyUtils
import utils.rigging.controlUtils as controlUtils

import dev.rigging.rigNode.rigLimb.core.coreLimb as coreLimb
import dev.rigging.utils.limbUtils as limbUtils


class RigGroup(coreLimb.CoreLimb):
    LIMB_KEYS_ATTR = 'limbKeys'
    LIMB_NODES_ATTR = 'limbNodes'

    def __init__(self, **kwargs):
        super(RigGroup, self).__init__(**kwargs)
        self._node_type = 'rigGroup'

        self._guide_controls = None
        self._input_limbs = None

        self._extra_attributes = None

        self._limb_keys = None
        self._limb_keys_attr = None
        self._limb_nodes_attr = None

    @property
    def limb_keys(self):
        return self._limb_keys

    def get_build_kwargs(self, **kwargs):
        super(RigGroup, self).get_build_kwargs(**kwargs)
        self._guide_controls = kwargs.get('guide_controls', [])

    def flip_build_kwargs(self):
        super(RigGroup, self).flip_build_kwargs()
        self._guide_controls = namingUtils.flip_names(self._guide_controls)

    def get_connect_kwargs(self, **kwargs):
        super(RigGroup, self).get_connect_kwargs(**kwargs)
        self._input_limbs = kwargs.get('input_limbs', {})
        self._limb_keys = self._input_limbs.keys()
        self._extra_attributes = kwargs.get('extra_attributes', {})

    def flip_connect_kwargs(self):
        super(RigGroup, self).flip_connect_kwargs()
        self._input_limbs = namingUtils.flip_names(self._input_limbs)

    def register_steps(self):
        super(RigGroup, self).register_steps()
        self.add_build_step('pack limbs', self.pack_limbs, 'connect')

    def create_controls(self):
        super(RigGroup, self).create_controls()
        if self._guide_controls:
            name_info = namingUtils.decompose(self._guide_controls[0])
            ctrl = controlUtils.create(name_info['description'], side=name_info['side'], index=name_info['index'],
                                       limb_index=name_info['limb_index'], sub=False, parent=self._controls_group,
                                       position=self._guide_controls[0], rotate_order=0, manip_orient=None,
                                       lock_hide=attributeUtils.ALL)
            self._controls.append(ctrl)

    def add_input_attributes_post(self):
        super(RigGroup, self).add_input_attributes_post()
        self._limb_keys_attr = attributeUtils.add(self._input_node, self.LIMB_KEYS_ATTR, attribute_type='string')[0]
        self._limb_nodes_attr = attributeUtils.add(self._input_node, self.LIMB_NODES_ATTR, attribute_type='message',
                                                   multi=True)[0]

        for attr, input_plug in self._extra_attributes.iteritems():
            attr_path = attributeUtils.transfer_attribute(input_plug, self._input_node,
                                                          name_override=namingUtils.to_camel_case(attr), link=True)
            # add back to class as attribute
            # check if it's multi attr
            multi = cmds.attributeQuery(namingUtils.to_camel_case(attr), node=self._input_node, multi=True)
            if multi:
                attr_path = self.get_multi_attr_names(attr_path)
            self.add_object_attribute(attr + '_attr', attr_path)

    def create_node_post(self):
        super(RigGroup, self).create_node_post()
        # connect extra attributes
        for attr in self._extra_attributes.keys():
            for limb_node in self._input_limbs.values():
                # get limb object
                limb_object = limbUtils.get_limb_object(limb_node)
                # check if limb has the attribute
                if hasattr(limb_object, attr + '_attr'):
                    # connect together
                    attributeUtils.connect(namingUtils.to_camel_case(attr), getattr(limb_object, attr + '_attr'),
                                           driver=self._input_node)

    def connect_input_attributes(self):
        super(RigGroup, self).connect_input_attributes()
        cmds.setAttr(self._limb_keys_attr, str(self._limb_keys), type='string', lock=True)
        for i, key in enumerate(self._limb_keys):
            limb_node = self._input_limbs[key]
            cmds.connectAttr('{0}.{1}'.format(limb_node, attributeUtils.MESSAGE),
                             '{0}[{1}]'.format(self._limb_nodes_attr, i))

    def pack_limbs(self):
        # re-parent limb node to sub node group
        for key, node in self._input_limbs.iteritems():
            hierarchyUtils.parent(node, self._sub_nodes_group)
            # get limb object
            limb_object = limbUtils.get_limb_object(node)
            # add to class as attribute
            self.add_object_attribute(key, limb_object)

    def get_input_info(self):
        super(RigGroup, self).get_input_info()
        # get limb keys
        self._limb_keys = self.get_single_attr_value(self.LIMB_KEYS_ATTR, node=self._input_node)
        # get limb nodes
        limb_nodes = self.get_multi_attr_value(self.LIMB_NODES_ATTR, node=self._input_node)
        # loop into each limb node and add as attribute to class
        for key, node in zip(self._limb_keys, limb_nodes):
            # get limb object
            limb_obj = limbUtils.get_limb_object(node)
            # add to class
            self.add_object_attribute(key, limb_obj)
