import maya.cmds as cmds

import utils.common.namingUtils as namingUtils
import utils.common.mathUtils as mathUtils
import utils.common.attributeUtils as attributeUtils
import utils.common.transformUtils as transformUtils
import utils.common.nodeUtils as nodeUtils
import utils.modeling.curveUtils as curveUtils


def position_constraint(input_matrices, nodes, weights=1, parent_inverse_matrices=None, maintain_offset=True,
                        skip=None, target_translate=None, target_rotate=None, force=True, constraint_only=False,
                        parent=None, constraint_name=None):
    """
    constraint using given matrices
    Args:
        input_matrices (list/str): list of input matrices, can be attribute or matrix list
        nodes (str/list): driven nodes names
        weights (float/str/list): weight value for each target matrix, each value can be a float number or attribute
        parent_inverse_matrices (list/str/None): parent inverse matrices for given nodes,
                                                 can be attribute or matrix list
        maintain_offset (bool): keep the offset between the drivers and driven objects, default is True
        skip (list/None): skip channels
        target_translate (str/list): target object local position, with input matrix,
                                     it get the target's world position, default is None
        target_rotate (str/list): target object local rotation, with input matrix, it get the target's world rotation,
                                  default is None
        force (bool): force connect with driven nodes, default is True
        constraint_only (bool): create constraint node without attach to anything, default is False
        parent (str): parent constraint nodes to given node
        constraint_name (str): if use constraint only, then constraint node name need to be given

    Returns:
        constraints (list): constraints nodes
    """
    if input_matrices is None or isinstance(input_matrices, basestring) or isinstance(input_matrices[0], (float, int)):
        input_matrices = [input_matrices]

    # get input matrices number
    input_num = len(input_matrices)

    if not isinstance(target_translate, list) or isinstance(target_translate[0], float) or \
            isinstance(target_translate[0], int):
        target_translate = [target_translate] * input_num

    if not isinstance(target_rotate, list) or isinstance(target_rotate[0], float) or \
            isinstance(target_rotate[0], int):
        target_rotate = [target_rotate] * input_num

    if not isinstance(weights, list):
        weights = [weights] * input_num

    # loop in each node and constrain with the input matrices
    if constraint_only:
        # create dummy node to temp receive constraint connection
        nodes = [cmds.createNode('transform', name='DUMMY_NODE')]
        maintain_offset = False

    elif isinstance(nodes, basestring):
        nodes = [nodes]

    if not isinstance(parent_inverse_matrices, list) or isinstance(parent_inverse_matrices[0], (float, int)):
        parent_inverse_matrices = [parent_inverse_matrices] * len(nodes)

    constraints = []
    for n, ivs_mtx in zip(nodes, parent_inverse_matrices):
        # create parent constraint node
        # check node name if follow naming convention, replace name type to constraint if follow,
        # otherwise use maya constraint naming convention, add '_parentConstraint1' as suffix
        if constraint_name and constraint_only:
            cons = constraint_name
        else:
            name_check = namingUtils.check(n)
            if name_check:
                name_info = namingUtils.decompose(n)
                cons = namingUtils.update(n, type='parentConstraint', additional_description=name_info['type'])
            else:
                cons = n + '_parentConstraint1'

        if parent:
            parent_node = parent
        else:
            parent_node = n
        cons = cmds.createNode('parentConstraint', name=cons, parent=parent_node)
        # set interp type to shortest
        cmds.setAttr(cons + '.interpType', 2)

        # connect parent inverse matrix and get node's matrix position
        node_matrix = cmds.getAttr('{0}.{1}'.format(n, attributeUtils.MATRIX))
        if ivs_mtx:
            if isinstance(ivs_mtx, basestring):
                cmds.connectAttr(ivs_mtx, cons + '.constraintParentInverseMatrix')
                # get matrix value for offset calculation
                ivs_mtx = cmds.getAttr(ivs_mtx)
            else:
                cmds.setAttr(cons + '.constraintParentInverseMatrix', ivs_mtx, type='matrix')

            # get node's position matrix
            parent_matrix = mathUtils.matrix.inverse(ivs_mtx, output_type='numpy')
            pos_matrix = mathUtils.matrix.multiply(node_matrix, parent_matrix, output_type='numpy')

        else:
            pos_matrix = node_matrix

        # connect joint orient
        if cmds.objectType(n) == 'joint':
            cmds.connectAttr(n + '.jointOrient', cons + '.constraintJointOrient')

        # connect each input matrix to the constraint node
        for i, (mtx, w, trgt_t, trgt_r) in enumerate(zip(input_matrices, weights, target_translate, target_rotate)):
            if isinstance(mtx, basestring):
                cmds.connectAttr(mtx, '{0}.target[{1}].targetParentMatrix'.format(cons, i))
                # get matrix value for offset calculation
                mtx = cmds.getAttr(mtx)
            elif mtx:
                cmds.setAttr('{0}.target[{1}].targetParentMatrix'.format(cons, i), mtx, type='matrix')
            else:
                cmds.setAttr('{0}.target[{1}].targetParentMatrix'.format(cons, i), mathUtils.matrix.IDENTITY,
                             type='matrix')
                mtx = mathUtils.matrix.IDENTITY

            # set target position and rotation
            local_transform = [[0, 0, 0], [0, 0, 0]]
            if trgt_t:
                if isinstance(trgt_t, basestring):
                    cmds.connectAttr(trgt_t, '{0}.target[{1}].targetTranslate'.format(cons, i))
                else:
                    cmds.setAttr('{0}.target[{1}].targetTranslate'.format(cons, i), *trgt_t)

                values = cmds.getAttr('{0}.target[{1}].targetTranslate'.format(cons, i))[0]
                local_transform[0][0] = values[0]
                local_transform[0][1] = values[1]
                local_transform[0][2] = values[2]

            if trgt_r:
                if isinstance(trgt_r, basestring):
                    cmds.connectAttr(trgt_r, '{0}.target[{1}].targetRotate'.format(cons, i))
                else:
                    cmds.setAttr('{0}.target[{1}].targetRotate'.format(cons, i), *trgt_t)

                values = cmds.getAttr('{0}.target[{1}].targetRotate'.format(cons, i))[0]
                local_transform[1][0] = values[0]
                local_transform[1][1] = values[1]
                local_transform[1][2] = values[2]

            # connect weight value
            if isinstance(w, basestring):
                cmds.connectAttr(w, '{0}.target[{1}].targetWeight'.format(cons, i))
            else:
                cmds.setAttr('{0}.target[{1}].targetWeight'.format(cons, i), w)

            if maintain_offset:
                # get target matrix
                mtx_local = transformUtils.compose_matrix(translate=local_transform[0], rotate=local_transform[1])
                mtx = mathUtils.matrix.multiply(mtx_local, mtx, output_type='numpy')
                # get offset value if needed
                local_matrix = mathUtils.matrix.localize(pos_matrix, mtx, output_type='list')
                # decompose to get translate and rotate values
                offset_values = transformUtils.decompose_matrix(local_matrix)
                # set offset
                cmds.setAttr('{0}.target[{1}].targetOffsetTranslate'.format(cons, i), *offset_values[0])
                cmds.setAttr('{0}.target[{1}].targetOffsetRotate'.format(cons, i), *offset_values[1])

        # connect with node
        if not constraint_only:
            cons_attrs = []
            driven_attrs = []

            for attr in ['translate', 'rotate']:
                for axis in 'XYZ':
                    connect_attr = attr + axis
                    if not skip or connect_attr not in skip:
                        cons_attrs.append('constraint{0}{1}'.format(attr.title(), axis))
                        driven_attrs.append(connect_attr)
            attributeUtils.connect(cons_attrs, driven_attrs, driver=cons, driven=n, force=force)

        constraints.append(cons)

    # remove dummy node
    if constraint_only:
        cmds.delete(nodes)

    return constraints


def scale_constraint(input_matrices, nodes, weights=1, parent_inverse_matrices=None, skip=None, target_scale=None,
                     force=True, constraint_only=False, parent=None, constraint_name=None):
    """
    scale constraint using given matrices

    Args:
        input_matrices (list/str): list of input matrices, can be attribute or matrix list
        nodes (str/list): driven nodes names
        weights (float/str/list): weight value for each target matrix, each value can be a float number or attribute
        parent_inverse_matrices (list/str/None): parent inverse matrices for given nodes,
                                                 can be attribute or matrix list
        skip (list/None): skip channels
        target_scale (str/list): target object local scale, with input matrix,
                                 it get the target's world scale value, default is None
        force (bool): force connect with driven nodes, default is True
        constraint_only (bool): create constraint node without attach to anything, default is False
        parent (str): parent constraint nodes to given node
        constraint_name (str): if use constraint only, then constraint node name need to be given
    Returns:
        constraints (list): constraints nodes
    """
    if input_matrices is None or isinstance(input_matrices, basestring) or isinstance(input_matrices[0], (float, int)):
        input_matrices = [input_matrices]

    # get input matrices number
    input_num = len(input_matrices)

    if not isinstance(target_scale, list) or isinstance(target_scale[0], (float, int)):
        target_scale = [target_scale] * input_num

    if not isinstance(weights, list):
        weights = [weights] * input_num

    # loop in each node and constrain with the input matrices
    if constraint_only:
        # create dummy node to temp receive constraint connection
        nodes = [cmds.createNode('transform', name='DUMMY_NODE')]
    elif isinstance(nodes, basestring):
        nodes = [nodes]

    if not isinstance(parent_inverse_matrices, list) or isinstance(parent_inverse_matrices[0], (float, int)):
        parent_inverse_matrices = [parent_inverse_matrices] * len(nodes)

    constraints = []
    for n, ivs_mtx in zip(nodes, parent_inverse_matrices):
        # create scale constraint node
        # check node name if follow naming convention, replace name type to constraint if follow,
        # otherwise use maya constraint naming convention, add '_scaleConstraint1' as suffix
        if constraint_name and constraint_only:
            cons = constraint_name
        else:
            name_check = namingUtils.check(n)
            if name_check:
                cons = namingUtils.update(n, type='scaleConstraint')
            else:
                cons = n + '_scaleConstraint1'

        if parent:
            parent_node = parent
        else:
            parent_node = n
        cmds.createNode('scaleConstraint', name=cons, parent=parent_node)

        # connect parent inverse matrix and get node's matrix position
        if ivs_mtx:
            if isinstance(ivs_mtx, basestring):
                cmds.connectAttr(ivs_mtx, cons + '.constraintParentInverseMatrix')
            else:
                cmds.setAttr(cons + '.constraintParentInverseMatrix', ivs_mtx, type='matrix')

        # connect each input matrix to the constraint node
        for i, (mtx, w, trgt_s) in enumerate(zip(input_matrices, weights, target_scale)):
            print mtx
            if isinstance(mtx, basestring):
                cmds.connectAttr(mtx, '{0}.target[{1}].targetParentMatrix'.format(cons, i))
            elif mtx:
                cmds.setAttr('{0}.target[{1}].targetParentMatrix'.format(cons, i), mtx, type='matrix')
            else:
                cmds.setAttr('{0}.target[{1}].targetParentMatrix'.format(cons, i), mathUtils.matrix.IDENTITY,
                             type='matrix')

            # set target scale
            if trgt_s:
                if isinstance(trgt_s, basestring):
                    cmds.connectAttr(trgt_s, '{0}.target[{1}].targetScale'.format(cons, i))
                else:
                    cmds.setAttr('{0}.target[{1}].targetScale'.format(cons, i), *trgt_s)

            # connect weight value
            if isinstance(w, basestring):
                cmds.connectAttr(w, '{0}.target[{1}].targetWeight'.format(cons, i))
            else:
                cmds.setAttr('{0}.target[{1}].targetWeight'.format(cons, i), w)

        # connect with node
        if not constraint_only:
            cons_attrs = []
            driven_attrs = []

            for axis in 'XYZ':
                connect_attr = 'scale' + axis
                if not skip or connect_attr not in skip:
                    cons_attrs.append('constraintScale' + axis)
                    driven_attrs.append(connect_attr)
            attributeUtils.connect(cons_attrs, driven_attrs, driver=cons, driven=n, force=force)

        constraints.append(cons)

    # delete dummy node
    if constraint_only:
        cmds.delete(nodes)

    return constraints


def pole_vector_constraint(input_matrix, ik_handle, root_joint, ik_parent_inverse_matrix=None,
                           joint_parent_matrix=None, force=True):
    """
    pole vector constraint using given matrix

    Args:
        input_matrix (str/list): input matrix, can be attribute or matrix list
        ik_handle (str): ik handle name
        root_joint (str): root joint name
        ik_parent_inverse_matrix (str/list): ik handle's parent inverse matrix, can be attribute or matrix list
        joint_parent_matrix (str/list): joint's parent matrix, can be attribute or matrix list
        force (bool): force connection

    Returns:
        constraint (str): pole vector constraint node
    """
    # create pole vector constraint node
    # check node name if follow naming convention, replace name type to constraint if follow,
    # otherwise use maya constraint naming convention, add '_poleVectorConstraint1' as suffix
    name_check = namingUtils.check(ik_handle)
    if name_check:
        cons = namingUtils.update(ik_handle, type='poleVectorConstraint')
    else:
        cons = ik_handle + '_poleVectorConstraint1'

    cmds.createNode('poleVectorConstraint', name=cons, parent=ik_handle)

    if isinstance(input_matrix, basestring):
        # connect input matrix
        cmds.connectAttr(input_matrix, cons + '.target[0].targetParentMatrix')
    else:
        # set matrix value
        cmds.setAttr(cons + '.target[0].targetParentMatrix', input_matrix, type='matrix')

    # connect root joint's translation
    attributeUtils.connect(attributeUtils.TRANSLATE, ['constraintRotatePivotX',
                                                      'constraintRotatePivotY',
                                                      'constraintRotatePivotZ'], driver=root_joint, driven=cons)

    if joint_parent_matrix:
        if isinstance(joint_parent_matrix, basestring):
            # connect joint parent matrix
            cmds.connectAttr(joint_parent_matrix, cons + '.pivotSpace')
        else:
            # set joint parent matrix value
            cmds.setAttr(cons + '.pivotSpace', joint_parent_matrix, type='matrix')

    if ik_parent_inverse_matrix:
        if isinstance(ik_parent_inverse_matrix, basestring):
            # connect ik's parent inverse matrix
            cmds.connectAttr(ik_parent_inverse_matrix, cons + '.constraintParentInverseMatrix')
        else:
            # set joint parent matrix value
            cmds.setAttr(cons + '.constraintParentInverseMatrix', ik_parent_inverse_matrix, type='matrix')

    # connect with ik handle
    attributeUtils.connect(['constraintTranslateX', 'constraintTranslateY', 'constraintTranslateZ'],
                           ['poleVectorX', 'poleVectorY', 'poleVectorZ'], driver=cons, driven=ik_handle,
                           force=force)

    return cons


def aim_constraint(input_matrix, node, aim_vector=None, up_vector=None, world_up_type='object', world_up_matrix=None,
                   world_up_vector=None, target_position=None, parent_inverse_matrix=None, force=True):
    """
    aim constraint using given matrix

    Args:
        input_matrix (str/list): input matrix, can be attribute or matrix list
        node (str): driven node name
        aim_vector (list): aim vector, default is [1, 0, 0]
        up_vector (list): up vector, default is [0, 1, 0]
        world_up_type (str): 'object', 'object_rotation' or 'none', default is 'object'
        world_up_matrix (str/list): world up matrix as up vector's reference
        world_up_vector (list): world up vector, default is [0, 1, 0],
                                only used when world up type set to object rotation
        target_position (str/list): target object position, with input matrix, it get the target's world position,
                                    default is None
        parent_inverse_matrix (list/str/None): parent inverse matrices for given nodes, can be attribute or matrix list
        force (bool): force connection

    Returns:
        constraint (str): aim constraint node
    """
    # get world up type index mapping
    world_up_indexes = {'object': 1,
                        'object_rotation': 2,
                        'none': 4}
    # set default vectors
    if not aim_vector:
        aim_vector = [1, 0, 0]
    if not up_vector:
        up_vector = [0, 1, 0]
    if not world_up_vector:
        world_up_vector = [0, 1, 0]
    # create aim vector constraint node
    # check node name if follow naming convention, replace name type to constraint if follow,
    # otherwise use maya constraint naming convention, add '_poleVectorConstraint1' as suffix
    name_check = namingUtils.check(node)
    if name_check:
        cons = namingUtils.update(node, type='aimConstraint')
    else:
        cons = node + '_aimConstraint1'

    cmds.createNode('aimConstraint', name=cons, parent=node)

    if isinstance(input_matrix, basestring):
        # connect input matrix
        cmds.connectAttr(input_matrix, cons + '.target[0].targetParentMatrix')
    elif input_matrix:
        # set matrix value
        cmds.setAttr(cons + '.target[0].targetParentMatrix', input_matrix, type='matrix')
    else:
        # set identity matrix
        cmds.setAttr(cons + '.target[0].targetParentMatrix', mathUtils.matrix.IDENTITY, type='matrix')

    if target_position:
        if isinstance(target_position, basestring):
            # connect target position
            cmds.connectAttr(target_position, cons + '.target[0].targetTranslate')
        else:
            # set target position value
            cmds.setAttr(cons + '.target[0].targetTranslate', *target_position)

    # set world up type
    cmds.setAttr(cons + '.worldUpType', world_up_indexes[world_up_type])
    # set vector
    cmds.setAttr(cons + '.aimVector', *aim_vector)
    cmds.setAttr(cons + '.upVector', *up_vector)
    cmds.setAttr(cons + '.worldUpVector', *world_up_vector)

    # set world up matrix
    if world_up_matrix:
        if isinstance(world_up_matrix, basestring):
            # connect world up matrix
            cmds.connectAttr(world_up_matrix, cons + '.worldUpMatrix')
        else:
            # set joint parent matrix value
            cmds.setAttr(cons + '.worldUpMatrix', world_up_matrix, type='matrix')

    # check if driven node is joint, connect joint orient
    if cmds.objectType(node) == 'joint':
        cmds.connectAttr(node + '.jointOrient', cons + '.constraintJointOrient')

    # set parent inverse matrix
    if parent_inverse_matrix:
        if isinstance(parent_inverse_matrix, basestring):
            # connect parent inverse matrix
            cmds.connectAttr(parent_inverse_matrix, cons + '.constraintParentInverseMatrix')
        else:
            # set joint parent matrix value
            cmds.setAttr(cons + '.constraintParentInverseMatrix', parent_inverse_matrix, type='matrix')

    # connect with node
    cons_attrs = []

    for axis in 'XYZ':
        cons_attrs.append('constraintRotate' + axis)

    attributeUtils.connect(cons_attrs, attributeUtils.ROTATE, driver=cons, driven=node, force=force)

    return cons


def curve_constraint(curve, nodes, skip_rotate=False, aim_vector=None, up_vector=None, aim_type='tangent',
                     up_curve=None, parent_inverse_matrix=None, force=True):
    """
    attach node to the given curve

    Args:
        curve (str): curve name
        nodes (str/list): driven nodes names
        skip_rotate (bool): if set to True, will skip rotation connection for the given node, default is False
        aim_vector (list): aim vector, default is [1, 0, 0]
        up_vector (list): up vector, default is [0, 1, 0]
        aim_type (str): tangent/next, tangent will use curve's tangent as target vector,
                                      next will use vector to next point as target vector, default is tangent
        up_curve (str): if up curve given, will use up curve to define the up vector,
                        otherwise will use quaternion to match the target vector
                        (aim constraint with world up type to None)
        parent_inverse_matrix (str/list): parent inverse matrix for all attach nodes
        force (bool): force connection

    Returns:
        position_constraints (list): position constraint nodes,
                                     either point on curve info node, or parent constraint node
        aim_constraints (list): aim constraints nodes
    """
    if isinstance(nodes, basestring):
        nodes = [nodes]

    # loop in each node and attach node to curve first
    pos_cons = []
    poci_nodes = []
    for node in nodes:
        pos_con, poci_node = _curve_point_attach(curve, node, parent_inverse_matrix=parent_inverse_matrix, force=True)
        pos_cons.append(pos_con)
        poci_nodes.append(poci_node)

    # check if need skip rotation, if not, construct aim constraint for nodes
    aim_cons = []
    if not skip_rotate:
        # force target vector as tangent if only one given node
        # add second last to point on curve info list so we can use the next point on curve info to get target vector
        if len(nodes) == 1:
            aim_type = 'tangent'
            poci_nodes.append(None)
        else:
            poci_nodes.append(poci_nodes[:-2])

        # get reverse target as a list, only the last one should be True
        reverse_targets = [False] * len(nodes)
        reverse_targets[-1] = True

        # do aim constraint for each node
        for i, (node, poci, rvs_trgt) in enumerate(zip(nodes, poci_nodes, reverse_targets)):
            aim_con = _curve_orient_attach(poci, node, parent_inverse_matrix=parent_inverse_matrix,
                                           aim_vector=aim_vector, up_vector=up_vector, aim_type=aim_type,
                                           up_curve=up_curve, target_poci=poci_nodes[i + 1], reverse_target=rvs_trgt,
                                           force=force)
            aim_cons.append(aim_con)

    return pos_cons, aim_cons


def matrix_connect(input_matrix, nodes, skip=None, force=True):
    """
    connect input matrix to given nodes

    Args:
        input_matrix (str): input matrix attribute
        nodes (str/list): given nodes
        skip (list/None): skip channels
        force (bool): force connection
    Returns:
        decompose_matrix_node (str): decompose matrix nodes connected to given node
    """
    # get input matrix node name
    input_matrix, input_node, input_attr = attributeUtils.check_exists(input_matrix)
    # create decompose matrix node
    decompose_node = cmds.createNode('decomposeMatrix',
                                     name=namingUtils.update(input_node, type='decomposeMatrix',
                                                             additional_description='matrixConnect'))

    cmds.connectAttr(input_matrix, decompose_node + '.inputMatrix')

    # put driven node into a list
    if isinstance(nodes, basestring):
        nodes = [nodes]

    # get skip attrs
    if not skip:
        skip = []

    driver_attrs = []
    driven_attrs = []
    for attr in attributeUtils.TRANSFORM:
        if attr not in skip:
            driver_attrs.append('{0}.output{1}{2}'.format(decompose_node, attr[0].upper(), attr[1:]))
            driven_attrs.append(attr)

    # loop into each node and connect attrs
    for n in nodes:
        attributeUtils.connect(driver_attrs, driven_attrs, driven=n, force=force)

    return decompose_node


# sub functions
def _curve_point_attach(curve, node, parent_inverse_matrix=None, force=True):
    """
    attach node's translation to the given curve's closest point
    Args:
        curve (str): curve name
        node (str): driven node name
        parent_inverse_matrix (str): parent inverse matrix for attach node
        force (bool): force connection

    Returns:
        position_constraint_node (str): position constraint node name,
                                        if parent inverse matrix given, it will be a parent constraint node
                                        otherwise it will be the point on curve info node
        point_on_curve_info (str): point on curve info node
    """
    # get curve's shape node
    curve_shape = cmds.listRelatives(curve, shapes=True)[0]

    # check node naming convention
    name_check = namingUtils.check(node)
    # get node position
    node_position = cmds.xform(node, query=True, translation=True, worldSpace=True)
    # get closest parameter on curve
    closest_point, parameter = curveUtils.get_closest_point(curve, node_position)
    # create point on curve info node to attach given node
    if name_check:
        poci_node = namingUtils.update(node, type='pointOnCurveInfo')
    else:
        poci_node = node + '_pointOnCurveInfo1'
    cmds.createNode('pointOnCurveInfo', name=poci_node)
    # connect with curve shape's local
    cmds.connectAttr(curve_shape + '.worldSpace[0]', poci_node + '.inputCurve')
    # set parameter
    cmds.setAttr(poci_node + '.parameter', parameter)
    # connect position to node
    if not parent_inverse_matrix:
        attributeUtils.connect(poci_node + '.position', node + '.translate', force=force)
        pos_cons = poci_node
    else:
        pos_cons = position_constraint(None, node, parent_inverse_matrices=parent_inverse_matrix,
                                       skip=['rotateX', 'rotateY', 'rotateZ'],
                                       target_translate=poci_node + '.position')[0]

    return pos_cons, poci_node


def _curve_orient_attach(poci, node, parent_inverse_matrix=None, aim_vector=None, up_vector=None, aim_type='tangent',
                         up_curve=None, target_poci=None, reverse_target=False, force=True):
    """
    connect given node's rotation with it's point on curve info node

    Args:
        poci (str): node's point on curve info node
        node (str): given node name
        parent_inverse_matrix (str): parent inverse matrix for attach node
        aim_vector (list): aim vector, default is [1, 0, 0]
        up_vector (list): up vector, default is [0, 1, 0]
        aim_type (str): tangent/next, tangent will use curve's tangent as target vector,
                                      next will use vector to next point as target vector, default is tangent
        up_curve (str): if up curve given, will use up curve to define the up vector,
                        otherwise will use quaternion to match the target vector
                        (aim constraint with world up type to None)
        target_poci (str): if the aim type set to next,
                           will need the next point on curve info node to get the target vector
        reverse_target (bool): if need to reverse the target vector (only when aim type set to next),
                               normally used for the curve's end joint
        force (bool): force connection

    Returns:
        aim_constraint (str): aim constraint node
    """
    # get target vector
    if aim_type == 'tangent':
        target_vector = poci + '.tangent'
    else:
        # get target vector by position subtract
        # get name
        if namingUtils.check(node):
            target_vector = namingUtils.update(node, type='plusMinusAverage', additional_description='target')
        else:
            target_vector = node + '_target_plusMinusAverage1'
        # get vector
        input_attrs = [target_poci + '.position', poci + '.position']
        if reverse_target:
            input_attrs.reverse()
        target_vector = nodeUtils.arithmetic.plus_minus_average(input_attrs, operation=2, name=target_vector)

    # get up curve if needed
    if up_curve:
        # get up curve shape
        up_shape = cmds.listRelatives(up_curve, shapes=True)[0]
        # get node names
        if namingUtils.check(node):
            poci_up = namingUtils.update(node, type='pointOnCurveInfo', additional_description='up')
            up_pos = namingUtils.update(node, type='plusMinusAverage', additional_description='upObj')
            up_matrix = namingUtils.update(node, type='composeMatrix', additional_description='upObj')
        else:
            poci_up = node + '_up_pointOnCurveInfo1'
            up_pos = node + '_up_obj_plusMinusAverage1'
            up_matrix = node + '_up_obj_composeMatrix1'
        # get point on curve info's parameter
        parameter = cmds.getAttr(poci + '.parameter')
        # create point on curve info node for up curve
        cmds.createNode('pointOnCurveInfo', name=poci_up)
        cmds.connectAttr(up_shape + '.worldSpace[0]', poci_up + '.inputCurve')
        cmds.setAttr(poci_up + '.parameter', parameter)
        # get up matrix
        cmds.createNode('composeMatrix', name=up_matrix)
        # get up vector and plug into matrix node
        nodeUtils.arithmetic.plus_minus_average([poci_up + '.position', poci + '.position'], name=up_pos, operation=2,
                                                connect_attr=up_matrix + '.inputTranslate')
        # get matrix plug
        up_matrix = up_matrix + '.outputMatrix'
        # set up type
        up_type = 'object'
    else:
        # clear matrix plug
        up_matrix = None
        # set up type to none
        up_type = 'none'

    # do an aim constraint
    aim_cons = aim_constraint(None, node, aim_vector=aim_vector, up_vector=up_vector, world_up_type=up_type,
                              world_up_matrix=up_matrix, target_position=target_vector,
                              parent_inverse_matrix=parent_inverse_matrix, force=force)

    return aim_cons
