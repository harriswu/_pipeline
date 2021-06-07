import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.rigging.controlUtils as controlUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigLimb.core.coreLimb as coreLimb


class FkChain(coreLimb.CoreLimb):
    INPUT_HIERARCHY_MATRIX_ATTR = 'inputHierarchyMatrix'

    def __init__(self, **kwargs):
        super(FkChain, self).__init__(**kwargs)
        self._lock_hide = kwargs.get('lock_hide', attributeUtils.SCALE)
        self._additional_description = kwargs.get('additional_description', 'fk')
        self._control_end_joint = kwargs.get('control_end_joint', False)

        # input attr
        self._input_hierarchy_matrix_attr = None

        # connections
        self._input_hierarchy_matrix = kwargs.get('input_hierarchy_matrix', None)

    def register_inputs(self):
        super(FkChain, self).register_inputs()
        self._input_hierarchy_matrix_attr = attributeUtils.add(self._input_node, self.INPUT_HIERARCHY_MATRIX_ATTR,
                                                               attribute_type='matrix')[0]

    def create_controls(self):
        super(FkChain, self).create_controls()
        # get control parent node
        parent = self._controls_group
        # get guide joints info
        guides = self._guide_joints
        if not self._control_end_joint and len(self._guide_joints) > 1:
            guides = self._guide_joints[:-1]

        # loop into each guide joint and create fk controller
        input_matrix = self._input_hierarchy_matrix_attr
        for g in guides:
            name_info = namingUtils.decompose(g)
            ctrl = controlUtils.create(name_info['description'], side=name_info['side'], index=name_info['index'],
                                       limb_index=name_info['limb_index'], sub=True, parent=parent, position=g,
                                       rotate_order=0, manip_orient=None, lock_hide=self._lock_hide,
                                       shape=self._control_shape, color=self._control_color, size=self._control_size,
                                       tag=self._tag_control, input_matrix=input_matrix)

            # add to control list
            self._controls.append(ctrl)

            # override control parent node
            parent = ctrl
            tag_parent = ctrl
            # override input matrix
            input_matrix = '{0}.{1}'.format(ctrl, controlUtils.HIERARCHY_MATRIX_ATTR)
        # override setup nodes
        self._setup_nodes = self._controls

    def connect_to_joints(self):
        super(FkChain, self).connect_to_joints()
        for ctrl, jnt in zip(self._controls, self._joints):
            constraintUtils.position_constraint('{0}.{1}'.format(ctrl, controlUtils.OUT_MATRIX_ATTR), jnt,
                                                maintain_offset=False)
            
    def connect(self, **kwargs):
        super(FkChain, self).connect(**kwargs)
        self._input_hierarchy_matrix = kwargs.get('input_hierarchy_matrix', None)
        if self._input_hierarchy_matrix:
            attributeUtils.connect(self._input_hierarchy_matrix, self.INPUT_HIERARCHY_MATRIX_ATTR,
                                   driven=self._input_node)
