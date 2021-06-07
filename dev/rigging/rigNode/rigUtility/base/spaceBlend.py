import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils
import utils.common.nodeUtils as nodeUtils
import utils.rigging.constraintUtils as constraintUtils

import dev.rigging.rigNode.rigUtility.core.coreUtility as coreUtility
import dev.rigging.utils.spaceUtils as spaceUtils


class SpaceBlend(coreUtility.CoreUtility):
    SPACE_NAME = 'space'
    JOINT_ORIENT_ATTR = 'jointOrients'
    BLEND_MATRIX_ATTR = 'blendMatrix'

    def __init__(self, **kwargs):
        super(SpaceBlend, self).__init__(**kwargs)
        self._input_matrices = None
        self._joint_orients = None
        self._translate = None
        self._rotate = None
        self._scale = None
        self._parent_inverse_matrices = None
        self._defaults = None
        self._input_space_attrs = None
        self._input_blend_attr = None
        self._custom_space_index = None

        self._output_count = None

        self._spaces_sort = None
        self._default_indexes = None

        self._position_constraints_group = None
        self._scale_constraints_group = None
        self._position_constraints = []
        self._scale_constraints = []

        self._blend_matrix_attr = None
        self._space_attrs = None
        self._blend_attrs = None

    @property
    def space_attrs(self):
        return self._space_attrs

    @property
    def blend_attr(self):
        return self._blend_attrs[0]

    @property
    def blend_matrix_attr(self):
        return self._blend_matrix_attr

    def create_hierarchy(self):
        super(SpaceBlend, self).create_hierarchy()
        self._position_constraints_group = transformUtils.create(namingUtils.update(self._node, type='group',
                                                                                    additional_description='position'),
                                                                 lock_hide=attributeUtils.ALL, parent=self._node)

        self._scale_constraints_group = transformUtils.create(namingUtils.update(self._node, type='group',
                                                                                 additional_description='scale'),
                                                              lock_hide=attributeUtils.ALL, parent=self._node)

    def post_register_inputs(self):
        super(SpaceBlend, self).post_register_inputs()
        for space, matrices in self._input_matrices.iteritems():
            # add matrix list attribute
            matrix_attr = attributeUtils.add(self._input_node, namingUtils.to_camel_case(space),
                                             attribute_type='matrix', multi=True)[0]
            # connect with input matrices
            if isinstance(matrices, basestring) or isinstance(matrices[0], (float, int)):
                matrices = [matrices]
            for i, mtx in enumerate(matrices):
                if isinstance(mtx, basestring):
                    cmds.connectAttr(mtx, '{0}[{1}]'.format(matrix_attr, i))
                else:
                    cmds.setAttr('{0}[{1}]'.format(matrix_attr, i), mtx, type='matrix')

        # add joint orients attr
        cmds.addAttr(self._input_node, longName=self.JOINT_ORIENT_ATTR, attributeType='double3', multi=True)
        for axis in 'XYZ':
            cmds.addAttr(self._input_node, longName=self.JOINT_ORIENT_ATTR + axis, attributeType='doubleAngle',
                         parent=self.JOINT_ORIENT_ATTR)
        # loop in each joint orient and connect
        if self._joint_orients:
            if isinstance(self._joint_orients, basestring) or isinstance(self._joint_orients[0], (float, int)):
                self._joint_orients = [self._joint_orients]
            for i, jnt_ont in enumerate(self._joint_orients):
                if isinstance(jnt_ont, basestring):
                    cmds.connectAttr(jnt_ont, '{0}.{1}[{2}]'.format(self._input_node, self.JOINT_ORIENT_ATTR, i))
                else:
                    cmds.setAttr('{0}.{1}[{2}]'.format(self._input_node, self.JOINT_ORIENT_ATTR, i), *jnt_ont)

        # sort spaces
        self._spaces_sort, self._default_indexes = spaceUtils.sort_spaces(self._input_matrices.keys(),
                                                                          default_values=self._defaults,
                                                                          custom_index=self._custom_space_index)

        # add blend attr
        space_blend_attrs = spaceUtils.add_blend_attr(self._spaces_sort, self._input_node, self._default_indexes,
                                                      name=self.SPACE_NAME)
        self._space_attrs = space_blend_attrs[:2]
        self._blend_attrs = space_blend_attrs[2:]

        # connect if have input
        if self._input_space_attrs:
            attributeUtils.connect(self._input_space_attrs, self._space_attrs)

        if self._input_blend_attr:
            attributeUtils.connect(self._input_blend_attr, self._blend_attrs[0])

    def post_build(self):
        super(SpaceBlend, self).post_build()
        # get skip attributes
        skip_attrs = []
        if not self._translate:
            skip_attrs += attributeUtils.TRANSLATE
        if not self._rotate:
            skip_attrs += attributeUtils.ROTATE

        # loop into each node and create choice nodes
        choice_nodes = []
        for i, invs_mtx in enumerate(self._parent_inverse_matrices):
            # create choice nodes
            choices = []
            for enum_attr, suffix in zip(self._space_attrs, ['A', 'B']):
                choice = nodeUtils.create('choice',
                                          namingUtils.update(self._node, type='choice',
                                                             additional_description=self.SPACE_NAME + suffix.title()))
                # connect enum attr to choice node
                cmds.connectAttr(enum_attr, choice + '.selector')
                # add to choice list
                choices.append(choice)
            choice_nodes.append(choices)

            if self._translate or self._rotate:
                cons_name = namingUtils.update(self._node, type='parentConstraint',
                                               additional_description='positionBlend')
                cons_node = constraintUtils.position_constraint([choices[0] + '.output', choices[1] + '.output'],
                                                                None,
                                                                weights=[self._blend_attrs[-1], self._blend_attrs[0]],
                                                                parent_inverse_matrices=invs_mtx, maintain_offset=False,
                                                                skip=skip_attrs, force=True, constraint_only=True,
                                                                parent=self._position_constraints_group,
                                                                constraint_name=cons_name)[0]
                # connect joint orient
                cmds.connectAttr('{0}.{1}[{2}]'.format(self._input_node, self.JOINT_ORIENT_ATTR, i),
                                 cons_node + '.constraintJointOrient')

                self._position_constraints.append(cons_node)

            if self._scale:
                cons_name = namingUtils.update(self._node, type='scaleConstraint', additional_description='scaleBlend')
                cons_node = constraintUtils.scale_constraint([choices[0] + '.output', choices[1] + '.output'],
                                                             None,
                                                             weights=[self._blend_attrs[-1], self._blend_attrs[0]],
                                                             parent_inverse_matrices=invs_mtx, skip=skip_attrs,
                                                             force=True, constraint_only=True,
                                                             parent=self._scale_constraints_group,
                                                             constraint_name=cons_name)[0]

                self._scale_constraints.append(cons_node)

        # loop in each space and connect input to choice node
        for space, index in self._spaces_sort.iteritems():
            # convert space to camelcase
            space_attr = namingUtils.to_camel_case(space)
            # loop in each matrix attr and connect with choice nodes
            for i, choices in enumerate(choice_nodes):
                attributeUtils.connect(['{0}[{1}]'.format(space_attr, i), '{0}[{1}]'.format(space_attr, i)],
                                       ['{0}.input[{1}]'.format(choices[0], index),
                                        '{0}.input[{1}]'.format(choices[1], index)],
                                       driver=self._input_node)

    def post_register_outputs(self):
        super(SpaceBlend, self).post_register_outputs()
        # add multi matrix attr to hold all output transformation
        cmds.addAttr(self._output_node, longName=self.BLEND_MATRIX_ATTR, attributeType='matrix', multi=True)
        # compose matrix and connect with blend matrix attr
        for i in range(self._output_count):
            if self._translate:
                translate = [self._position_constraints[i] + '.constraintTranslateX',
                             self._position_constraints[i] + '.constraintTranslateY',
                             self._position_constraints[i] + '.constraintTranslateZ']
            else:
                translate = None

            if self._rotate:
                rotate = [self._position_constraints[i] + '.constraintRotateX',
                          self._position_constraints[i] + '.constraintRotateY',
                          self._position_constraints[i] + '.constraintRotateZ']
            else:
                rotate = None

            if self._scale:
                scale = [self._scale_constraints[i] + '.constraintScaleX',
                         self._scale_constraints[i] + '.constraintScaleY',
                         self._scale_constraints[i] + '.constraintScaleZ']
            else:
                scale = None

            nodeUtils.matrix.compose_matrix(namingUtils.update(self._node, type='composeMatrix',
                                                               additional_description='blend{:03d}'.format(i+1)),
                                            translate=translate, rotate=rotate, scale=scale,
                                            connect_attr='{0}.{1}[{2}]'.format(self._output_node,
                                                                               self.BLEND_MATRIX_ATTR, i))

        self._blend_matrix_attr = self.get_multi_attr_names(self.BLEND_MATRIX_ATTR, node=self._output_node)

    def get_connection_kwargs(self, **kwargs):
        super(SpaceBlend, self).get_connection_kwargs(**kwargs)
        self._input_matrices = kwargs.get('input_matrices', {})
        self._joint_orients = kwargs.get('joint_orients', [])
        self._translate = kwargs.get('translate', False)
        self._rotate = kwargs.get('rotate', True)
        self._scale = kwargs.get('scale', False)
        self._parent_inverse_matrices = kwargs.get('parent_inverse_matrices', None)
        self._defaults = kwargs.get('defaults', [])
        self._input_space_attrs = kwargs.get('input_space_attrs', None)
        self._input_blend_attr = kwargs.get('input_blend_attr', None)
        self._custom_space_index = kwargs.get('custom_space_index', 100)

        # get output nodes count, it depends on how many input matrices given for each space
        if isinstance(self._input_matrices.values()[0], basestring) or \
                isinstance(self._input_matrices.values()[0][0], (float, int)):
            self._output_count = 1
        else:
            self._output_count = len(self._input_matrices.values()[0])

        # get parent inverse matrices as list
        if not isinstance(self._parent_inverse_matrices, list) or \
                isinstance(self._parent_inverse_matrices[0][0], (float, int)):
            self._parent_inverse_matrices = [self._parent_inverse_matrices] * self._output_count

    def get_input_info(self):
        super(SpaceBlend, self).get_input_info()
        self._space_attrs = ['{0}.{1}A'.format(self._input_node, self.SPACE_NAME),
                             '{0}.{1}B'.format(self._input_node, self.SPACE_NAME)]
        self._blend_attrs = ['{0}.{1}Blend'.format(self._input_node, self.SPACE_NAME),
                             '{0}.{1}BlendRvs'.format(self._input_node, self.SPACE_NAME)]

    def get_output_info(self):
        super(SpaceBlend, self).get_output_info()
        self._blend_matrix_attr = self.get_multi_attr_names(self.BLEND_MATRIX_ATTR, node=self._output_node)
