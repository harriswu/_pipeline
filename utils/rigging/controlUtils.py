# import python library
import os
import warnings

# import maya python library
import maya.cmds as cmds

# import utils
import utils.common.fileUtils as fileUtils
import utils.common.mathUtils as mathUtils
import utils.common.namingUtils as namingUtils
import utils.common.nodeUtils as nodeUtils
import utils.common.transformUtils as transformUtils
import utils.common.hierarchyUtils as hierarchyUtils
import utils.common.attributeUtils as attributeUtils
import utils.modeling.curveUtils as curveUtils
import jointUtils

# config
import config

config_dir = os.path.dirname(config.__file__)
SHAPE_CONFIG = fileUtils.jsonUtils.read(os.path.join(config_dir, 'CONTROL_SHAPE.cfg'))
SIDE_CONFIG = fileUtils.jsonUtils.read(os.path.join(config_dir, 'CONTROL_SIDE_COLOR.cfg'))
COLOR_CONFIG = fileUtils.jsonUtils.read(os.path.join(config_dir, 'CONTROL_COLOR.cfg'))

# controller's attributes
HIERARCHY_ATTR = 'hierarchy'
INPUT_MATRIX_ATTR = 'inputMatrix'
WORLD_MATRIX_ATTR = 'controlWorldMatrix'
HIERARCHY_MATRIX_ATTR = 'controlHierarchyMatrix'
OUT_MATRIX_ATTR = 'controlOutMatrix'
LOCAL_MATRIX_ATTR = 'controlLocalMatrix'
PARTIAL_MATRIX_ATTR = 'controlPartialMatrix'
WORLD_INVERSE_MATRIX_ATTR = 'controlWorldInverseMatrix'
HIERARCHY_INVERSE_MATRIX_ATTR = 'controlHierarchyInverseMatrix'
OUT_INVERSE_MATRIX_ATTR = 'controlOutInverseMatrix'
LOCAL_INVERSE_MATRIX_ATTR = 'controlLocalInverseMatrix'
PARTIAL_INVERSE_MATRIX_ATTR = 'controlPartialInverseMatrix'


# class
class Control(object):
    def __init__(self, *args, **kwargs):
        self._side = None
        self._description = None
        self._index = None
        self._limb_index = None

        self._zero = None
        self._driven = None
        self._space = None
        self._connect = None
        self._offset = None
        self._control = None
        self._sub = None
        self._output = None

        self._world_matrix_attr = None
        self._hierarchy_matrix_attr = None
        self._out_matrix_attr = None
        self._local_matrix_attr = None
        self._partial_matrix_attr = None
        self._world_inverse_matrix_attr = None
        self._hierarchy_inverse_matrix_attr = None
        self._out_inverse_matrix_attr = None
        self._local_inverse_matrix_attr = None
        self._partial_inverse_matrix_attr = None

        self._tag = None

        self._ctrls = None  # put controllers to a list in case we need to do sth for both ctrl and sub ctrl

        if args:
            self._control = args[0]
        else:
            self._control = create(**kwargs)

        self.get_control_info()

    @property
    def side(self):
        return self._side

    @property
    def description(self):
        return self._description

    @property
    def index(self):
        return self._index

    @property
    def limb_index(self):
        return self._limb_index

    @side.setter
    def side(self, value):
        self.update_name(side=value)

    @description.setter
    def description(self, value):
        self.update_name(description=value)

    @index.setter
    def index(self, value):
        self.update_name(index=value)

    @limb_index.setter
    def limb_index(self, value):
        self.update_name(limb_index=value)

    @property
    def zero(self):
        return self._zero

    @property
    def driven(self):
        return self._driven

    @property
    def space(self):
        return self._space

    @property
    def connect(self):
        return self._connect

    @property
    def offset(self):
        return self._offset

    @property
    def name(self):
        return self._control

    @property
    def sub(self):
        return self._sub

    @sub.setter
    def sub(self, value):
        if value:
            self.add_sub()
        else:
            self.remove_sub()

    @property
    def output(self):
        return self._output

    @property
    def world_matrix(self):
        return cmds.getAttr(self._world_matrix_attr)

    @property
    def hierarchy_matrix(self):
        return cmds.getAttr(self._hierarchy_matrix_attr)

    @property
    def out_matrix(self):
        return cmds.getAttr(self._out_matrix_attr)

    @property
    def local_matrix(self):
        return cmds.getAttr(self._local_matrix_attr)

    @property
    def partial_matrix(self):
        return cmds.getAttr(self._partial_matrix_attr)

    @property
    def world_inverse_matrix(self):
        return cmds.getAttr(self._world_inverse_matrix_attr)

    @property
    def hierarchy_inverse_matrix(self):
        return cmds.getAttr(self._hierarchy_inverse_matrix_attr)

    @property
    def out_inverse_matrix(self):
        return cmds.getAttr(self._out_inverse_matrix_attr)

    @property
    def local_inverse_matrix(self):
        return cmds.getAttr(self._local_inverse_matrix_attr)

    @property
    def partial_inverse_matrix(self):
        return cmds.getAttr(self._partial_inverse_matrix_attr)

    @property
    def world_matrix_attr(self):
        return self._world_matrix_attr

    @property
    def hierarchy_matrix_attr(self):
        return self._hierarchy_matrix_attr

    @property
    def out_matrix_attr(self):
        return self._out_matrix_attr

    @property
    def local_matrix_attr(self):
        return self._local_matrix_attr

    @property
    def partial_matrix_attr(self):
        return self._partial_matrix_attr

    @property
    def world_inverse_matrix_attr(self):
        return self._world_inverse_matrix_attr

    @property
    def hierarchy_inverse_matrix_attr(self):
        return self._hierarchy_inverse_matrix_attr

    @property
    def out_inverse_matrix_attr(self):
        return self._out_inverse_matrix_attr

    @property
    def local_inverse_matrix_attr(self):
        return self._local_inverse_matrix_attr

    @property
    def partial_inverse_matrix_attr(self):
        return self._partial_inverse_matrix_attr

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, value):
        if value:
            self.add_tag()
        else:
            self.remove_tag()

    def get_control_info(self):
        self._ctrls = [self._control]
        # get name token
        token_info = namingUtils.decompose(self._control)
        self._side = token_info['side']
        self._description = token_info['description']
        self._index = token_info['index']
        self._limb_index = token_info['limb_index']

        # get controller's hierarchy nodes
        ctrl_nodes = get_hierarchy(self._control)
        self._zero = ctrl_nodes[0]
        self._driven = ctrl_nodes[1]
        self._space = ctrl_nodes[2]
        self._connect = ctrl_nodes[3]
        self._offset = ctrl_nodes[4]
        self._output = ctrl_nodes[-1]

        # get matrix attrs
        self._world_matrix_attr = '{0}.{1}'.format(self._control, WORLD_MATRIX_ATTR)
        self._out_matrix_attr = '{0}.{1}'.format(self._control, OUT_MATRIX_ATTR)
        self._local_matrix_attr = '{0}.{1}'.format(self._control, LOCAL_MATRIX_ATTR)
        self._partial_matrix_attr = '{0}.{1}'.format(self._control, PARTIAL_MATRIX_ATTR)
        self._world_inverse_matrix_attr = '{0}.{1}'.format(self._control, WORLD_INVERSE_MATRIX_ATTR)
        self._out_inverse_matrix_attr = '{0}.{1}'.format(self._control, OUT_INVERSE_MATRIX_ATTR)
        self._local_inverse_matrix_attr = '{0}.{1}'.format(self._control, LOCAL_INVERSE_MATRIX_ATTR)
        self._partial_inverse_matrix_attr = '{0}.{1}'.format(self._control, PARTIAL_INVERSE_MATRIX_ATTR)

        # check if controller has sub or not
        if len(ctrl_nodes) == 9:
            # it has sub controller
            self._sub = ctrl_nodes[-2]
            self._ctrls.append(self._sub)
        else:
            self._sub = None

        # get tagged nodes
        if is_tagged(self._control):
            self._tag = get_tag(self._ctrls)
        else:
            self._tag = None

    def update_name(self, side=None, description=None, index=None, limb_index=None, primary_side=None,
                    secondary_side=None, additional_description=None):
        """
        update controller's name, it will update all controller nodes as well

        Args:
            side (str/list): controller's side, it can be a string,
                             which only contains primary side token (left/right/center)
                             or it can be a list with two tokens, one for primary,
                             and one for secondary(front/back/top/bottom)
            description (str/list): controller's description,
                                    it can be a string, which only contains the node's description
                                    or it can be a list with two  tokens, [description, additional description],
                                    additional description is optional
            index (int): controller's index
            limb_index (int): limb's index, normally used for rigging related controller, default is None
            primary_side (str): primary side full name if need to be updated
            secondary_side (str): secondary side full name if need to be updated
            additional_description (str/list): additional descriptions if need to be added
        """
        self._control = update_name(self._control, side=side, description=description, index=index,
                                    limb_index=limb_index, primary_side=primary_side, secondary_side=secondary_side,
                                    additional_description=additional_description)
        self.get_control_info()

    def add_tag(self, parent_node=None):
        """
        tag controller using maya control tag node

        Args:
            parent_node (str): pick walk parent node for controller
        """
        self._tag = add_tag(self._ctrls)
        if parent_node:
            set_tag_parent(self._control, parent_node=parent_node)

    def remove_tag(self):
        """
        remove control tag node from controller
        """
        remove_tag(self._ctrls)
        self._tag = None

    def add_sub(self):
        """
        add sub controller
        """
        add_sub(self._control)
        self.get_control_info()

    def remove_sub(self):
        """
        remove sub controller
        """
        remove_sub(self._control)
        self.get_control_info()

    def transform_shape(self, translate=None, rotate=None, scale=None, pivot='shape'):
        """
        adjust control shapes by transforming the cv points

        Args:
            translate (list): translation values need to be offset
            rotate (list): rotation values need to be offset
            scale (list): scale values need to be offset
            pivot (str): transform/shape, define the offset pivot, default is shape
        """
        for c in self._ctrls:
            shape = cmds.listRelatives(c, shapes=True)[0]
            transform_shape(shape, translate=translate, rotate=rotate, scale=scale, pivot=pivot)

    def replace_shape(self, shape_name, size=1):
        """
        replace given controls shapes to the given shape
        Args:
            shape_name(str): control shape name, like 'cube', 'circle' ect.. base on config's CONTROL_SHAPE.cfg
            size(float): uniformly scale the control shape, default is 1
        """
        for c, s in zip(self._ctrls, [size, size * 0.95]):
            replace_shape(c, shape_name, size=s)

    def set_color(self, color):
        """
        set controller's color

        Args:
            color (str/list): controller's rgb color
        """
        if isinstance(color, basestring):
            color = COLOR_CONFIG[color]

        for c, col in zip(self._ctrls, [color, [color[0] * 0.5, color[1] * 0.5, color[2] * 0.5]]):
            shape = cmds.listRelatives(c, shapes=True)[0]
            curveUtils.set_display_setting(shape, display_type='normal', color=col)


# functions
# create/edit controller related nodes
def create(description, side='center', index=1, limb_index=None, additional_description=None, sub=True, parent=None,
           position=None, rotate_order=0, manip_orient=None, lock_hide=None, shape='cube', color=None, size=1,
           input_matrix=None, tag=True, tag_parent=None):
    """
    create controller

    hierarchy:
        zero
          -- driven
            -- space
              -- connect
                -- sdk
                  -- offset
                    -- control
                      -- sub control (optional)
                        -- output

    Args:
        description (str/list): controller's description, it can be a string,
                                which only contains the node's description,
                                or it can be a list of  tokens, [description1, description2, description3...],
                                additional description is optional
        side (str/list): controller's side, it can be a string,
                         which only contains primary side token (left/right/center)
                         or it can be a list with two tokens, one for primary,
                         and one for secondary(front/back/top/bottom)
        index (int): controller's index
        limb_index (int/None): limb's index, normally used for rigging related controller, default is None
        additional_description (str/list): additional descriptions if need to be added
        sub (bool): add sub controller if set to True, default is True
        parent (str/None): parent controller to the given node, default is None
        position (str/list/None): match controller's transformation to given node/transform value
                                  str: match translate,rotate and scale to the given node
                                  [str/None, str/None, str/None]: match translate/rotate/scale to the given node,
                                                                  scale is optional
                                  [[x,y,z], [x,y,z], [x,y,z]: match translate/rotate/scale to given values
                                                              scale is optional
        rotate_order (int): controller's default rotate order, default is 0
        manip_orient (str/list/None): if need translation orient different with rotation,
                                      normally used for some ik controller, which need rotation orientation,
                                      but keep translation as world orientation.
                                      by given a match node name, or a rotation values list,
                                      it will reset the translation orientation
                                      use 'world' to set it to world orientation.
                                      default is None
        lock_hide (list/None): lock and hide attributes for controller, default is None
        shape (str): controller's shape, default is 'cube'
        color (str/list/None): controller's rgb color, it will use preset base on side if None, default is None
        size (float): controller's size
        input_matrix (str/list): input matrix need to be plugged with the controller,
                                 that way, control's hierarchy matrix can output with the driver matrix together
                                 normally is the control's parent node's matrix, default is None
        tag (bool): tag control using maya controlTag node, default is True
        tag_parent (str): set pick walk parent node for controller

    Returns:
        ctrl_name (str): controller's name

    Examples:
        import utils.rigging.controlUtils as controlUtils

        controlUtils.create('test', side='left', position='locator1', manip_orient='world')
        # 'ctrl__l__test__001'
    """
    # get name
    ctrl = namingUtils.compose(type='control', side=side, description=description, index=index,
                               limb_index=limb_index, additional_description=additional_description)

    # create control transform node, use joint because we may need to use joint orientation to offset rotation axis
    jointUtils.create(ctrl, position=position, rotate_order=rotate_order)
    # set draw style to None so we won't see the joint shape
    cmds.setAttr(ctrl + '.drawStyle', 2)
    # add control shape
    _add_shape(ctrl, shape=shape, size=size, color=color)
    # tag controller
    if tag:
        add_tag(ctrl, parent_node=tag_parent)

    # controller hierarchy
    # add hierarchy message attrs
    cmds.addAttr(ctrl, longName=HIERARCHY_ATTR, attributeType='message', multi=True)
    # create groups
    ctrl_nodes = []
    ctrl_node_parent = None
    for i, node in enumerate(['zero', 'driven', 'space', 'connect', 'sdk', 'offset']):
        # create transform node
        grp = cmds.createNode('transform', name=namingUtils.update(ctrl, type=node), parent=ctrl_node_parent)
        # connect message to hierarchy
        cmds.connectAttr(grp + '.message', '{0}.{1}[{2}]'.format(ctrl, HIERARCHY_ATTR, i))

        ctrl_node_parent = grp
        ctrl_nodes.append(grp)
    # parent zero to parent node
    parent_control(ctrl_nodes[0], parent)

    # connect control's message to hierarchy
    cmds.connectAttr(ctrl + '.message', '{0}.{1}[6]'.format(ctrl, HIERARCHY_ATTR))

    # create output group
    output = cmds.createNode('transform', name=namingUtils.update(ctrl, type='output'), parent=ctrl)
    # connect output message to hierarchy, connect to 8th, leave 7 for sub control
    cmds.connectAttr(output + '.message', '{0}.{1}[8]'.format(ctrl, HIERARCHY_ATTR))

    # match zero group position to control
    zero_position = [ctrl, ctrl]
    if manip_orient == 'world':
        zero_position = [ctrl, [0, 0, 0]]
    elif manip_orient:
        zero_position = [ctrl, manip_orient]
    transformUtils.set_position(ctrl_nodes[0], zero_position, translate=True, rotate=True, scale=False, method='snap')

    # parent controller under offset group
    cmds.parent(ctrl, ctrl_nodes[-1])

    # add matrix attrs
    attributeUtils.add(ctrl, [INPUT_MATRIX_ATTR, WORLD_MATRIX_ATTR, HIERARCHY_MATRIX_ATTR, OUT_MATRIX_ATTR,
                              LOCAL_MATRIX_ATTR, PARTIAL_MATRIX_ATTR, WORLD_INVERSE_MATRIX_ATTR,
                              HIERARCHY_INVERSE_MATRIX_ATTR, OUT_INVERSE_MATRIX_ATTR, LOCAL_INVERSE_MATRIX_ATTR,
                              PARTIAL_INVERSE_MATRIX_ATTR],
                       attribute_type='matrix')

    # create mult matrix nodes to get output matrix
    # get partial matrix
    # the partial matrix is from output node to connect group,
    # output is the first slot, leave the second slot for sub, if not sub then keep this slot empty
    partial_nodes = [output, ctrl] + ctrl_nodes[:2:-1]
    # compose matrix attr
    partial_matrix_attrs = attributeUtils.compose_attrs(partial_nodes, attributeUtils.MATRIX)
    # insert an identity matrix to sub matrix slot
    partial_matrix_attrs.insert(1, mathUtils.matrix.IDENTITY)
    # create mult matrix node to get output matrix
    partial_matrix_output = nodeUtils.matrix.mult_matrix(*partial_matrix_attrs,
                                                         name=namingUtils.update(ctrl, type='multMatrix',
                                                                                 additional_description='matrixPartial')
                                                         )
    # get partial mult matrix node for further using
    mult_matrix_partial = attributeUtils.compose_attr(partial_matrix_output)[1]
    # create local matrix to include space, driven matrix
    local_matrix_output = nodeUtils.matrix.mult_matrix(partial_matrix_output,
                                                       '{0}.{1}'.format(ctrl_nodes[2], attributeUtils.MATRIX),
                                                       '{0}.{1}'.format(ctrl_nodes[1], attributeUtils.MATRIX),
                                                       name=namingUtils.update(ctrl, type='multMatrix',
                                                                               additional_description='matrixLocal'))

    # create out matrix to include zero matrix
    out_matrix_output = nodeUtils.matrix.mult_matrix(local_matrix_output, '{0}.{1}'.format(ctrl_nodes[0],
                                                                                           attributeUtils.MATRIX),
                                                     name=namingUtils.update(ctrl, type='multMatrix',
                                                                             additional_description='matrixOut'))
    # create hierarchy matrix to include out matrix and input matrix
    hierarchy_matrix_output = nodeUtils.matrix.mult_matrix(out_matrix_output, '{0}.{1}'.format(ctrl, INPUT_MATRIX_ATTR),
                                                           name=namingUtils.update(ctrl, type='multMatrix',
                                                                                   additional_description='matrixHie'))
    # set input matrix to attribute or connect input matrix plug
    if input_matrix:
        if isinstance(input_matrix, basestring):
            cmds.connectAttr(input_matrix, '{0}.{1}'.format(ctrl, INPUT_MATRIX_ATTR))
        else:
            cmds.setAttr('{0}.{1}'.format(ctrl, INPUT_MATRIX_ATTR), input_matrix, type='matrix')
    # connect matrix attrs to attributes
    cmds.connectAttr(partial_matrix_output, '{0}.{1}'.format(ctrl, PARTIAL_MATRIX_ATTR))
    cmds.connectAttr(local_matrix_output, '{0}.{1}'.format(ctrl, LOCAL_MATRIX_ATTR))
    cmds.connectAttr(out_matrix_output, '{0}.{1}'.format(ctrl, OUT_MATRIX_ATTR))
    cmds.connectAttr(hierarchy_matrix_output, '{0}.{1}'.format(ctrl, HIERARCHY_MATRIX_ATTR))
    cmds.connectAttr('{0}.{1}'.format(output, attributeUtils.WORLD_MATRIX), '{0}.{1}'.format(ctrl, WORLD_MATRIX_ATTR))

    # create inverse matrix node to get inverse matrix
    nodeUtils.matrix.inverse_matrix(partial_matrix_output,
                                    name=namingUtils.update(ctrl, type='inverseMatrix',
                                                            additional_description='matrixPartial'),
                                    connect_attr='{0}.{1}'.format(ctrl, PARTIAL_INVERSE_MATRIX_ATTR))

    nodeUtils.matrix.inverse_matrix(local_matrix_output,
                                    name=namingUtils.update(ctrl, type='inverseMatrix',
                                                            additional_description='matrixLocal'),
                                    connect_attr='{0}.{1}'.format(ctrl, LOCAL_INVERSE_MATRIX_ATTR))

    nodeUtils.matrix.inverse_matrix(out_matrix_output,
                                    name=namingUtils.update(ctrl, type='inverseMatrix',
                                                            additional_description='matrixOut'),
                                    connect_attr='{0}.{1}'.format(ctrl, OUT_INVERSE_MATRIX_ATTR))

    nodeUtils.matrix.inverse_matrix(hierarchy_matrix_output,
                                    name=namingUtils.update(ctrl, type='inverseMatrix',
                                                            additional_description='matrixHierarchy'),
                                    connect_attr='{0}.{1}'.format(ctrl, HIERARCHY_INVERSE_MATRIX_ATTR))

    cmds.connectAttr('{0}.{1}'.format(output, attributeUtils.WORLD_INVERSE_MATRIX),
                     '{0}.{1}'.format(ctrl, WORLD_INVERSE_MATRIX_ATTR))

    # add sub control
    ctrls = [ctrl]
    if sub:
        # add sub vis attr
        sub_vis = attributeUtils.add(ctrl, 'subCtrlVis', attribute_type='bool', keyable=False, channel_box=True)[0]
        # create sub controller
        sub_ctrl = jointUtils.create(namingUtils.update(ctrl, additional_description='sub'), position=ctrl,
                                     parent_node=ctrl, rotate_order=rotate_order)
        cmds.setAttr(sub_ctrl + '.drawStyle', 2)
        # connect message to hierarchy
        cmds.connectAttr(sub_ctrl + '.message', '{0}.{1}[7]'.format(ctrl, HIERARCHY_ATTR))
        # re-parent output
        cmds.parent(output, sub_ctrl)

        # add control shape
        sub_shape = _add_shape(sub_ctrl, shape=shape, size=0.95, color=color, color_multiplier=0.5)
        # connect vis
        cmds.connectAttr(sub_vis, '{0}.{1}'.format(sub_shape, attributeUtils.VISIBILITY))

        # add matrix to calculation
        cmds.connectAttr('{0}.{1}'.format(sub_ctrl, attributeUtils.MATRIX), mult_matrix_partial + '.matrixIn[1]')

        # tag controller, and pick walk parent to main controller
        if tag:
            add_tag(sub_ctrl, parent_node=ctrl)

        ctrls.append(sub_ctrl)

    # lock hide attrs
    if not lock_hide:
        lock_hide = [attributeUtils.VISIBILITY, 'radius']
    else:
        lock_hide = lock_hide[:] + [attributeUtils.VISIBILITY, 'radius']
        lock_hide = list(set(lock_hide))

        # check if need to hide rotate order
        if (attributeUtils.ROTATE[0] in lock_hide and attributeUtils.ROTATE[1] in lock_hide
                and attributeUtils.ROTATE[2] in lock_hide and attributeUtils.ROTATE_ORDER not in lock_hide):
            lock_hide.append(attributeUtils.ROTATE_ORDER)

    for c in ctrls:
        cmds.setAttr('{0}.{1}'.format(c, attributeUtils.ROTATE_ORDER), channelBox=True)
        attributeUtils.lock(lock_hide, node=c, channel_box=False)

    return ctrl


def hide_controller(ctrl, shape=False):
    if not shape:
        zero = get_hierarchy_node(ctrl, 'zero')
        attributeUtils.set_value(attributeUtils.VISIBILITY, 0, node=zero)
    else:
        # get shape node
        shapes = cmds.listRelatives(ctrl, shapes=True)
        # get sub controller
        sub = get_hierarchy_node(ctrl, 'sub')
        if sub:
            shapes += cmds.listRelatives(sub, shapes=True)

        for s in shapes:
            attributeUtils.set_value(attributeUtils.VISIBILITY, 0, node=s)


def show_controller(ctrl, shape=False):
    if not shape:
        zero = get_hierarchy_node(ctrl, 'zero')
        attributeUtils.set_value(attributeUtils.VISIBILITY, 1, node=zero)
    else:
        # get shape node
        shapes = cmds.listRelatives(ctrl, shapes=True)
        # get sub controller
        sub = get_hierarchy_node(ctrl, 'sub')
        if sub:
            shapes += cmds.listRelatives(sub, shapes=True)

        for s in shapes:
            attributeUtils.set_value(attributeUtils.VISIBILITY, 1, node=s)


def get_hierarchy(ctrl):
    """
    get controller's hierarchy

    Args:
        ctrl (str): control's name

    Returns:
        control_nodes (list): all transform nodes contain in a controller as hierarchy

    Examples:
        import utils.rigging.controlUtils as controlUtils

        controlUtils.get_hierarchy('ctrl__l__test__001')
        # ['zero__l__test__001',
        #  'driven__l__test__001',
        #  'space__l__test__001',
        #  'connect__l__test__001',
        #  'sdk__l__test__001',
        #  'offset__l__test__001',
        #  'ctrl__l__test__001',
        #  'ctrl__l__test_sub__001',
        #  'output__l__test__001']
    """
    return cmds.listConnections('{0}.{1}'.format(ctrl, HIERARCHY_ATTR), source=True, destination=False, plugs=False)


def get_hierarchy_node(ctrl, node_type):
    """
    get controller's hierarchy node by given the node type name

    it will be based on the controller's hierarchy

    hierarchy:
        zero
          -- driven
            -- space
              -- connect
                -- sdk
                  -- offset
                    -- control
                      -- sub control (optional)
                        -- output
    Args:
        ctrl (str): controller's name
        node_type (str): controller's hierarchy node name, zero/driven/space/connect/offset/control/sub/output

    Returns:
        node_name (str): controller's hierarchy node name, return None if not exist

    Examples:
        import utils.rigging.controlUtils as controlUtils

        controlUtils.get_hierarchy_node('ctrl__l__test__001', 'zero')
        # zero__l__test__001
    """
    # get controller's node index
    index = ['zero', 'driven', 'space', 'connect', 'sdk', 'offset', 'control', 'sub', 'output'].index(node_type)
    node_name = cmds.listConnections('{0}.{1}[{2}]'.format(ctrl, HIERARCHY_ATTR, index), source=True, destination=False,
                                     plugs=False)
    if node_name:
        return node_name[0]
    else:
        return None


def parent_control(ctrl, parent_node):
    """
    parent controller under given parent node,
    it will parent controller's zero group instead if it's a controller,
    and if the parent node is a controller, it will use output node instead of controller

    Args:
        ctrl (str/list): control/node name
        parent_node (str): parent node name
    """
    if isinstance(ctrl, basestring):
        ctrl = [ctrl]

    # check if parent node is a controller, get output node
    if is_control(parent_node):
        parent_node = get_hierarchy_node(parent_node, 'output')

    for c in ctrl:
        # get controller's zero node
        if is_control(c):
            c = get_hierarchy_node(c, 'zero')
        hierarchyUtils.parent(c, parent_node)


def update_name(ctrl, side=None, description=None, index=None, limb_index=None, primary_side=None,
                secondary_side=None, additional_description=None):
    """
    update controller's name, it will update all controller nodes as well

    Args:
        ctrl (str): controller's name
        side (str/list): controller's side, it can be a string,
                             which only contains primary side token (left/right/center)
                             or it can be a list with two tokens, one for primary,
                             and one for secondary(front/back/top/bottom)
        description (str/list): controller's description,
                                it can be a string, which only contains the node's description
                                or it can be a list with two  tokens, [description, additional description],
                                additional description is optional
        index (int): controller's index
        limb_index (int): limb's index, normally used for rigging related controller, default is None
        primary_side (str): primary side full name if need to be updated
        secondary_side (str): secondary side full name if need to be updated
        additional_description (str/list): additional descriptions if need to be added

    Returns:
        ctrl (str): controller's name
    """
    if isinstance(additional_description, basestring):
        additional_description = [additional_description]
    elif not additional_description:
        additional_description = []

    # get controller's hierarchy
    ctrl_nodes = get_hierarchy(ctrl)
    # rename each hierarchy node except controller
    for node, node_type in zip(ctrl_nodes[:6] + [ctrl_nodes[-1]],
                               ['zero', 'driven', 'space', 'connect', 'offset', 'output']):
        cmds.rename(node, namingUtils.update(ctrl, type=node_type, side=side, description=description, index=index,
                                             limb_index=limb_index, primary_side=primary_side,
                                             secondary_side=secondary_side,
                                             additional_description=additional_description))

    # put controller into a list
    ctrls = []
    # get sub controller
    if len(ctrl_nodes) == 8:
        # it has sub controller
        # rename sub controller
        if not additional_description:
            sub_description = 'sub'
        elif isinstance(additional_description, basestring):
            sub_description = [additional_description, 'sub']
        else:
            sub_description = additional_description + ['sub']

        sub = cmds.rename(ctrl_nodes[-2], namingUtils.update(ctrl, side=side, description=description, index=index,
                                                             limb_index=limb_index, primary_side=primary_side,
                                                             secondary_side=secondary_side,
                                                             additional_description=sub_description))
        ctrls.append(sub)

    # rename controller
    ctrl = cmds.rename(ctrl, namingUtils.update(ctrl, side=side, description=description, index=index,
                                                limb_index=limb_index, primary_side=primary_side,
                                                secondary_side=secondary_side,
                                                additional_description=additional_description))
    ctrls.append(ctrl)

    # rename matrix nodes
    for matrix_attr, suffix in zip([OUT_MATRIX_ATTR, LOCAL_MATRIX_ATTR, PARTIAL_MATRIX_ATTR,
                                    OUT_INVERSE_MATRIX_ATTR, LOCAL_INVERSE_MATRIX_ATTR, PARTIAL_INVERSE_MATRIX_ATTR],
                                   ['matrixOut', 'matrixLocal', 'matrixPartial',
                                    'matrixOut', 'matrixLocal', 'matrixPartial']):
        # get source node
        matrix_node = cmds.listConnections('{0}.{1}'.format(ctrl, matrix_attr), source=True, destination=False,
                                           plugs=False)[0]
        # update the name
        cmds.rename(matrix_node, namingUtils.update(matrix_node, side=side, description=description, index=index,
                                                    limb_index=limb_index, primary_side=primary_side,
                                                    secondary_side=secondary_side,
                                                    additional_description=additional_description + [suffix]))

    # rename controller tag
    for c in ctrls:
        tag_node = is_tagged(c)
        if tag_node:
            cmds.rename(tag_node, namingUtils.update(c, type='controlTag'))

    return ctrl


def add_sub(ctrl):
    """
    add sub controller

    Args:
        ctrl (str): controller's name

    Returns:
        sub_ctrl (str): sub controller's name
    """
    # try to get sub controller first
    sub_ctrl = get_hierarchy_node(ctrl, 'sub')
    if sub_ctrl:
        warnings.warn('controller: "{0}" already has a sub controller, skipped'.format(ctrl))
        return sub_ctrl

    # add sub controller
    # add sub vis attr
    sub_vis = attributeUtils.add(ctrl, 'subCtrlVis', attribute_type='bool', keyable=False, channel_box=True)[0]
    # create sub controller
    sub_ctrl = jointUtils.create(namingUtils.update(ctrl, additional_description='sub'), position=ctrl,
                                 parent_node=ctrl,
                                 rotate_order=cmds.getAttr('{0}.{1}'.format(ctrl, attributeUtils.ROTATE_ORDER)))
    cmds.setAttr(sub_ctrl + '.drawStyle', 2)
    # connect message to hierarchy
    cmds.connectAttr(sub_ctrl + '.message', '{0}.{1}[6]'.format(ctrl, HIERARCHY_ATTR))
    # re-parent output
    output = get_hierarchy_node(ctrl, 'output')
    cmds.parent(output, sub_ctrl)

    # add control shape
    sub_shape = _transfer_shape(ctrl, sub_ctrl, size=0.95, color=True, color_multiplier=0.5)
    # connect vis
    cmds.connectAttr(sub_vis, '{0}.{1}'.format(sub_shape, attributeUtils.VISIBILITY))

    # add matrix to calculation
    mult_matrix_local = cmds.listConnections('{0}.{1}'.format(ctrl, attributeUtils.MATRIX), source=False,
                                             destination=True, plugs=False)[0]
    cmds.connectAttr('{0}.{1}'.format(sub_ctrl, attributeUtils.MATRIX), mult_matrix_local + '.matrixIn[1]')

    # tag controller, and pick walk parent to main controller
    # check if controller is tagged
    tag_node = is_tagged(ctrl)
    if tag_node:
        add_tag(sub_ctrl, parent_node=ctrl)

    # transfer default attrs status from controller
    attributeUtils.transfer_default_attrs_status(ctrl, sub_ctrl)

    return sub_ctrl


def remove_sub(ctrl):
    """
    remove sub controller for given control

    Args:
        ctrl (str): controller's name
    """
    sub_ctrl = get_hierarchy_node(ctrl, 'sub')
    if not sub_ctrl:
        warnings.warn('controller: "{0}" does not have a sub controller, skipped'.format(ctrl))
        return

    # get output node
    output = get_hierarchy_node(ctrl, 'output')
    # re-parent output under controller
    cmds.parent(output, ctrl)
    # remove sub controller
    cmds.delete(sub_ctrl)


def add_tag(ctrl, parent_node=None):
    """
    tag controllers with maya control tag node

    Args:
        ctrl (str/list): ctrl transform node name
        parent_node (str): set pick walk parent node

    Returns:
        tag_nodes (list): list of tag nodes
    """
    if isinstance(ctrl, basestring):
        ctrl = [ctrl]

    tag_nodes = []
    for c in ctrl:
        tag_node = is_tagged(c)
        if tag_node:
            warnings.warn('given controller: {0} is already tagged, skip'.format(c))
        else:
            cmds.controller(c)
            # get tag node
            tag_node = cmds.listConnections(c + '.message', destination=True, plugs=False, type='controller')[0]
            tag_node = cmds.rename(tag_node, namingUtils.update(c, type='controlTag'))
        # append list
        tag_nodes.append(tag_node)

    # parent nodes
    if parent_node:
        cmds.controller(ctrl, parent_node, parent=True)

    return tag_nodes


def remove_tag(ctrl):
    """
    remove controller tag nodes for given controllers

    Args:
        ctrl (str/list):  ctrl transform node name
    """
    if isinstance(ctrl, basestring):
        ctrl = [ctrl]

    for c in ctrl:
        tag_node = is_tagged(c)
        if tag_node:
            cmds.delete(tag_node)
        else:
            warnings.warn('given controller: {0} is not tagged, skip'.format(c))


def set_tag_parent(ctrl, parent_node):
    """
    set pick walk parent node for controller

    Args:
        ctrl (str/list): ctrl transform node name, given controls must be tagged
        parent_node (str): set pick walk parent node
    """
    if isinstance(ctrl, basestring):
        ctrl = [ctrl]

    cmds.controller(ctrl, parent_node, parent=True)


def get_tag(ctrl):
    """
    get control tag nodes from given controls

    Args:
        ctrl (str/list): ctrl transform node name, given controls must be tagged

    Returns:
        tag_nodes (list): control tag node names
    """
    if isinstance(ctrl, basestring):
        ctrl = [ctrl]
    tag_nodes = []
    for c in ctrl:
        tag_node = cmds.listConnections(c + '.message', destination=True, plugs=False, type='controller')[0]
        tag_nodes.append(tag_node)
    return tag_nodes


def is_tagged(ctrl):
    """
    check if controller is tagged or not

    Args:
        ctrl (str): controller name

    Returns:
        tag_node (str): tag node's name, return None if not tagged
    """
    tag_node = cmds.listConnections(ctrl + '.message', destination=True, plugs=False, type='controller')
    if tag_node:
        return tag_node[0]
    else:
        return None


def is_control(node):
    """
    check if the given node is a controller

    Args:
        node (str): node name

    Returns:
        True/False
    """
    # check if the node has hierarchy attribute
    if attributeUtils.check_exists(HIERARCHY_ATTR, node=node):
        return True
    else:
        return False


def add_annotation(ctrl, target, additional_description='annotation'):
    """
    add annotation shape from controller to given target, normally use as guideline for pole vector or aim target

    Args:
        ctrl (str): controller name
        target (str): target node name
        additional_description (str/list): add additional description to name if needed

    Returns:
        annotation_shape (str): annotation shape node
    """
    annotation = cmds.createNode('annotationShape',
                                 name=namingUtils.update(target, type='annotation',
                                                         additional_description=additional_description))

    # parent shape under controller's output node
    # get original parents
    annotation_parent = cmds.listRelatives(annotation, parent=True)
    # get output node
    output = get_hierarchy_node(ctrl, 'output')
    # parent shape
    cmds.parent(annotation, output, add=True, shape=True)
    # delete original parents
    cmds.delete(annotation_parent)
    # set enable override to reference
    attributeUtils.set_value([annotation + '.overrideEnabled', annotation + '.overrideDisplayType'], [1, 2])
    # create locator to connect the annotation's arrow
    loc_annotation = cmds.spaceLocator(name=namingUtils.update(target, type='locator',
                                                               additional_description=additional_description))[0]
    # parent annotation locator under output, and hide locator
    cmds.parent(loc_annotation, output)
    cmds.setAttr('{0}.{1}'.format(loc_annotation, attributeUtils.VISIBILITY), 0)
    # point constraint locator with joint, and connect shape world matrix to annotation shape
    # annotation shape seems only work with locator shape's world matrix, so use maya normal point constraint
    cmds.pointConstraint(target, loc_annotation, maintainOffset=False)
    cmds.connectAttr(cmds.listRelatives(loc_annotation, shapes=True)[0] + '.worldMatrix[0]',
                     annotation + '.dagObjectMatrix[0]')
    # return annotation shape node
    return annotation


# create/edit controller shape
def transform_shape(ctrl_shape, translate=None, rotate=None, scale=None, pivot='shape'):
    """
    adjust control shapes by transforming the cv points

    Args:
        ctrl_shape (str/list): controls shape nodes
        translate (list): translation values need to be offset
        rotate (list): rotation values need to be offset
        scale (list): scale values need to be offset
        pivot (str): transform/shape, define the offset pivot, default is shape
    """
    if translate is None:
        translate = [0, 0, 0]
    if rotate is None:
        rotate = [0, 0, 0]
    if scale is None:
        scale = [1, 1, 1]

    if isinstance(ctrl_shape, basestring):
        ctrl_shape = [ctrl_shape]

    # compose offset matrix
    offset_matrix = transformUtils.compose_matrix(translate=translate, rotate=rotate, scale=scale)
    # convert to numpy
    offset_matrix = mathUtils.matrix.list_to_matrix(offset_matrix)

    for shape in ctrl_shape:
        if cmds.objExists(shape):
            # get cv positions
            control_vertices = curveUtils.get_shape_info(shape)['control_vertices']
            # get pivot position
            if pivot == 'shape':
                pivot_pos = transformUtils.bounding_box(control_vertices)[2]
            else:
                pivot_pos = [0, 0, 0]
            # convert to numpy
            pivot_matrix = mathUtils.matrix.four_by_four_matrix([1, 0, 0], [0, 1, 0], [0, 0, 1], pivot_pos,
                                                                output_type='numpy')

            # get control vertices local positions
            pivot_matrix_invs = mathUtils.matrix.inverse(pivot_matrix, output_type='numpy')
            control_vertices_local = mathUtils.point.array_mult_matrix(control_vertices, pivot_matrix_invs,
                                                                       output_type='numpy')
            # get the offset matrix
            control_offset_matrix = mathUtils.matrix.multiply(pivot_matrix, offset_matrix, output_type='numpy')

            # get control vertices position
            control_vertices = mathUtils.point.array_mult_matrix(control_vertices_local, control_offset_matrix,
                                                                 output_type='list')
            # set position
            curveUtils.set_points(shape, control_vertices)


def replace_shape(ctrl, shape_name, size=1):
    """
    replace given controls shapes to the given shape
    Args:
        ctrl(str/list): controls name
        shape_name(str): control shape name, like 'cube', 'circle' ect.. base on config's CONTROL_SHAPE.cfg
        size(float): uniformly scale the control shape, default is 1
    """
    if isinstance(ctrl, basestring):
        ctrl = [ctrl]

    # get control color info
    for c in ctrl:
        c_shape = cmds.listRelatives(c, shapes=True)[0]
        color = curveUtils.get_color(c_shape)
        # add shape
        _add_shape(c, shape=shape_name, size=size, color=color)


def mirror_shape(ctrl_source, ctrl_target, mirror_space=None):
    """
    get source ctrl shape info, and mirror to target ctrl shape
    Args:
        ctrl_source(str): source control's  shape node name
        ctrl_target(str): target control's shape node name
        mirror_space(list): mirror space, control shape point world position will multiply this as vector to get the
                            mirrored position, default is [-1, 1, 1]
    """
    if not mirror_space:
        mirror_space = [-1, 1, 1]

    ctrl_source = [ctrl_source]
    ctrl_target = [ctrl_target]

    # get source control's sub control
    ctrl_sub_source = get_hierarchy_node(ctrl_source[0], 'sub')
    if ctrl_sub_source:
        ctrl_source.append(ctrl_sub_source)

    # get target control's sub control
    ctrl_sub_target = get_hierarchy_node(ctrl_target[0], 'sub')
    if ctrl_sub_target:
        ctrl_target.append(ctrl_sub_target)

    # get mirror space matrix
    mirror_space_matrix = transformUtils.compose_matrix(scale=mirror_space)

    for c_s, c_t in zip(ctrl_source, ctrl_target):
        # get source control vertices
        c_s_shape = cmds.listRelatives(c_s, shapes=True)[0]
        shape_info = curveUtils.get_shape_info(c_s_shape)
        control_vertices = shape_info['control_vertices']
        # get source control world matrix
        c_s_matrix = cmds.getAttr('{0}.{1}'.format(c_s, attributeUtils.WORLD_MATRIX))
        # get target control world inverse matrix
        c_t_matrix = cmds.getAttr('{0}.{1}'.format(c_t, attributeUtils.WORLD_INVERSE_MATRIX))
        # get transformed matrix
        transform_matrix = mathUtils.matrix.multiply(c_s_matrix, mirror_space_matrix, c_t_matrix, output_type='numpy')
        # get target control vertices position
        control_vertices = mathUtils.point.array_mult_matrix(control_vertices, transform_matrix, output_type='list')
        # update shape info
        shape_info['control_vertices'] = control_vertices
        # get target shape color
        c_t_shape = cmds.listRelatives(c_t, shapes=True)[0]
        color = curveUtils.get_color(c_t_shape)
        # add shape for target control
        _add_shape(c_t, color=color, shape_info=shape_info)


# import/export control shape
def export_data(ctrl, file_path):
    """
    export control shapes information to the given file path
    control shape information include shape info and color

    Args:
        ctrl (str/list): controls name
        file_path (str): control shape export file path
    """
    if isinstance(ctrl, basestring):
        ctrl = [ctrl]

    export_info = {}
    for c in ctrl:
        # get shape info
        if cmds.objectType(c) != 'nurbsCurve':
            shape = cmds.listRelatives(c, shapes=True)[0]
        else:
            shape = c
            c = cmds.listRelatives(shape, parent=True)[0]
        shape_info = curveUtils.get_shape_info(shape)
        color = curveUtils.get_color(shape)
        export_info.update({c: {'color': color,
                                'shape_info': shape_info}})

    # export control info
    fileUtils.jsonUtils.write(file_path, export_info)


def build_data(ctrl_info, control_list=None, exception_list=None, size=1):
    """
    add shapes to controllers base on the given control shapes info

    Args:
        ctrl_info(dict): ctrl shape info
        control_list(list): only load ctrl shape info to those controls in the list, None will load all, default is None
        exception_list(list): skip loading ctrl shape info to those controls in the list, default is None
        size(float): scale controls shapes uniformly, default is 1
    """
    for ctrl, info in ctrl_info.iteritems():
        if cmds.objExists(ctrl):
            if control_list and ctrl not in control_list:
                # skip if control list given, and controller name is not on list
                pass
            elif exception_list and ctrl in exception_list:
                # skip if controller is on exception list
                pass
            else:
                info.update({'size': size})
                _add_shape(ctrl, **info)
        else:
            warnings.warn(ctrl + ' does not exist in the scene, skipped')


def import_data(file_path, control_list=None, exception_list=None, size=1):
    """
    import control shapes information

    Args:
        file_path (str): control shape info path
        control_list(list): only load ctrl shape info to those controls in the list, None will load all, default is None
        exception_list(list): skip loading ctrl shape info to those controls in the list, default is None
        size(float): scale controls shapes uniformly, default is 1
    """
    ctrl_info = fileUtils.jsonUtils.read(file_path)
    build_data(ctrl_info, control_list=control_list, exception_list=exception_list, size=size)


# sub functions
def _add_shape(ctrl, shape='cube', size=1, color=None, color_multiplier=1, shape_info=None):
    """
    add shape node to controller

    Args:
        ctrl(str): control's name
        shape(str): control's shape, default is 'cube'
        size(float): control shape's size, default is size
        color(str/list): control's color, None will follow the side preset
        color_multiplier (float): multiply the given value with color rgb, to make the color brighter/darker
        shape_info(dict): if has custom shape node (like copy/paste), or load from file
    """
    if not shape_info:
        shape_info = SHAPE_CONFIG[shape]  # get shape info from config

    # get control shape name
    shape_name = namingUtils.update(ctrl, type='controlShape')

    vis_plug = None
    vis_attr = '{0}.{1}'.format(shape_name, attributeUtils.VISIBILITY)
    if cmds.objExists(shape_name):
        # check if it has visibility connected
        vis_plug = cmds.listConnections(vis_attr, source=True, destination=False, plugs=True)
        # delete existing shape node
        cmds.delete(shape_name)

    # create curve shape
    crv_transform, crv_shape = curveUtils.create(ctrl, shape_info['control_vertices'], shape_info['knots'],
                                                 degree=shape_info['degree'], form=shape_info['form'])
    # rename control shape
    cmds.rename(crv_shape, shape_name)
    # connect visibility
    if vis_plug:
        cmds.connectAttr(vis_plug[0], vis_attr)

    # set shape color
    if not color:
        # use preset color if not given
        side = namingUtils.decompose(ctrl)['side']
        side_color_key = SIDE_CONFIG[side[0]]
        color = COLOR_CONFIG[side_color_key]
    elif isinstance(color, basestring):
        color = COLOR_CONFIG[color]

    curveUtils.set_display_setting(shape_name,
                                   color=[color[0] * color_multiplier,
                                          color[1] * color_multiplier,
                                          color[2] * color_multiplier])

    # resize the shape
    if size != 1:
        transform_shape(shape_name, scale=[size, size, size])
    # return shape node
    return shape_name


def _transfer_shape(source_ctrl, target_ctrl, size=1, color=False, color_multiplier=1):
    """
    transfer source shape to target shape
    Args:
        source_ctrl (str): source controller
        target_ctrl (str): target controller
        size (float): target shape's size, default is 1
        color (bool): if transfer the color, default is False
        color_multiplier (float):  multiply the given value with color rgb, to make the color brighter/darker

    Returns:
        shape_name (str): target control shape name
    """
    # get source control shape node
    source_shape = cmds.listRelatives(source_ctrl, shapes=True)[0]

    # get target control shape node
    target_shape = cmds.listRelatives(target_ctrl, shapes=True)

    # get control info
    shape_info = curveUtils.get_shape_info(source_shape)
    if color:
        color = curveUtils.get_color(source_shape)
    elif target_shape:
        color = curveUtils.get_color(target_shape[0])
    else:
        color = None

    # add shape for the target controller
    return _add_shape(target_ctrl, size=size, color=color, color_multiplier=color_multiplier, shape_info=shape_info)
