import warnings

import numpy

import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as OpenMaya2
import maya.api.OpenMayaAnim as OpenMayaAnim2

import utils.common.namingUtils as namingUtils
import utils.common.fileUtils as fileUtils
import utils.common.apiUtils as apiUtils
import utils.modeling.meshUtils as meshUtils
import utils.modeling.curveUtils as curveUtils
import utils.modeling.surfaceUtils as surfaceUtils


# function
# create/edit skin cluster
def get(geo):
    """
    get skin cluster from the given geo

    Args:
        geo (str): geo name, can be a mesh, nurbs surface or curve

    Returns:
        skin_cluster (str): skin cluster name
    """
    skin = mel.eval('findRelatedSkinCluster("' + geo + '")')
    return skin


def create(geo, influence_objects, force=False):
    """
    create skin cluster with given influences
    TODO: curve/geometry influence support (or maybe not)

    Args:
        geo (str): geometry's name
        influence_objects (list): influences contribute to the skin cluster
        force (bool): if set to True, will delete current geometry's skin cluster, and bind with influences,
                      default is False

    Returns:
        skin_cluster (str): skin cluster's name
    """
    #  get current skin cluster
    skin_cluster = get(geo)
    if skin_cluster:
        if not force:
            warnings.warn(geo + ' already has a skin cluster attached, skipped')
            return None
        else:
            # remove current skin cluster
            cmds.delete(skin_cluster)

    missing_joints_group = '_MISS_INFLUENCES'
    for inf_obj in influence_objects:
        if not cmds.objExists(inf_obj):
            # check if missing joints group exists
            if not cmds.objExists(missing_joints_group):
                # create missing joints group
                cmds.createNode('transform', name=missing_joints_group)
            # create missing joint
            cmds.createNode('transform', name=inf_obj, parent=missing_joints_group)

    # check if geometry name is follow naming convention
    if namingUtils.check(geo):
        skin_cluster = namingUtils.update(geo, type='skinCluster')
    else:
        skin_cluster = 'skin_' + geo

    cmds.skinCluster(influence_objects, geo, toSelectedBones=True, name=skin_cluster)
    return skin_cluster


def transfer(source, targets, remove_unused=True, force=False):
    """
    transfer skin weights from source mesh to target meshes,
    it will create skin cluster and do copy skin weights for each target geometry

    Args:
        source (str): source geometry
        targets (str/list): target geometries
        remove_unused (bool): remove unused influence objects, default is True
        force (bool): if set to True, will delete current geometry's skin cluster, and bind with influences,
                      default is False

    Returns:
        skin_cluster_target (list): target skin clusters
    """
    source_skin = get(source)
    if not source_skin:
        warnings.warn('source geometry: {0} does not have skin cluster attached, skipped'.format(source))
        return []

    # get influence objects
    inf_objs = get_influence_objects(source_skin)

    # loop in each geometry
    if isinstance(targets, basestring):
        targets = [targets]

    skin_cluster_target = []
    for geo in targets:
        # create skin cluster
        skin = create(geo, inf_objs, force=force)
        if skin:
            cmds.copySkinWeights(sourceSkin=source_skin, destinationSkin=skin, noMirror=True,
                                 surfaceAssociation='closestPoint', influenceAssociation=['label', 'oneToOne'],
                                 normalize=True)
            if remove_unused:
                remove_unused_influence(skin)
        skin_cluster_target.append(skin)

    return skin_cluster_target


# add/remove influence objects
def get_influence_objects(skin_cluster, include_unused=True):
    """
    get skin cluster's influence objects

    Args:
        skin_cluster (str): skin cluster
        include_unused (bool): if False, will only return influences with actual weight values, default is True

    Returns:
        influence_objects (list): influence objects connect with the skin cluster
    """
    if include_unused:
        influence_objects = cmds.skinCluster(skin_cluster, query=True, influence=True)
    else:
        influence_objects = cmds.skinCluster(skin_cluster, query=True, weightedInfluence=True)
    return influence_objects


def add_influence_objects(skin_cluster, influence_objects):
    """
    add influence objects to the given skin cluster
    Args:
        skin_cluster (str): skin cluster name
        influence_objects (str/list): influence need to add to the skin cluster
    """
    if isinstance(influence_objects, basestring):
        influence_objects = [influence_objects]
    for inf_obj in influence_objects:
        cmds.skinCluster(skin_cluster, edit=True, addInfluence=inf_obj, weight=0, lockWeights=False)


def remove_unused_influence(skin_cluster):
    """
    remove unused influence objects from the given skin cluster

    Args:
        skin_cluster (str): skin cluster name
    """
    # get influence objects in skin cluster
    influence_objects = get_influence_objects(skin_cluster)
    # get influence objects with non zero weighting
    influence_objects_used = get_influence_objects(skin_cluster, include_unused=False)

    # loop in each influence
    for inf_obj in influence_objects:
        # check if it has non zero weight, if not, remove it from skin cluster
        if inf_obj not in influence_objects_used:
            cmds.skinCluster(skin_cluster, edit=True, removeInfluence=inf_obj)


def remove_bind_pose(skin_cluster):
    """
    remove bind pose connect to skin cluster
    one bind pose node may connect with multiple skin clusters, so be careful when using this function

    Args:
        skin_cluster (str): skin cluster name
    """
    # get skin cluster's bind pose connection
    bind_pose_nodes = cmds.listConnections(skin_cluster + '.bindPose', source=True, destination=False, plugs=False)
    if bind_pose_nodes:
        # it has bind pose node connected, delete bind pose nodes
        cmds.delete(bind_pose_nodes)


# skin cluster data
def get_data(geo):
    """
    get skin cluster weights values and influence objects list from given geometry's skin cluster

    TODO: get blend weights data and skinning method

    Args:
        geo (str): geometry need to get skin cluster data

    Returns:
        weights (numpy.ndarray): numpy matrix array, each column presents for influence object,
                                 and each row presents all components weight values for this influence
        influence_objects (list): a list of influence objects names
    """
    # get skin cluster
    skin = get(geo)
    # return if no skin cluster found
    if not skin:
        warnings.warn(geo + ' does not have a skin cluster attached, skipped')
        return None

    # get MFnSkinCluster
    mfn_skin = get_MFnSkinCluster(skin)

    # get weight array
    m_dag, m_obj = _get_components_info(mfn_skin)
    m_array_weight = mfn_skin.getWeights(m_dag, m_obj)
    # convert weight array to numpy
    array_weights = numpy.array(m_array_weight[0])

    # get components number
    inf_num = m_array_weight[1]
    components_num = array_weights.size / m_array_weight[1]
    # reshape numpy array base on components number and influence number
    array_weights = array_weights.reshape((components_num, inf_num)).T

    # get influence objects array
    m_array_inf = mfn_skin.influenceObjects()
    # get influence objects names as list
    inf_objs = apiUtils.MArray.to_list(m_array_inf)

    return array_weights, inf_objs


def to_dict(array_weights, influence_objects):
    """
    convert skin data to a dictionary, the keys are influence objects,
    and each item is the component weight values for this influence

    Args:
        array_weights (numpy.ndarray): skin cluster's numpy matrix array comping from get_data function
        influence_objects (list): influence objects names

    Returns:
        skin_data (dict): skin data as dictionary format, like {'joint1': numpy.array[0.2, 0.1, 0.3 ....],
                                                                'joint2}: numpy.array[0.2, 0.2, 0.5 ....],
                                                                ...}

    """
    # get skin data in dictionary
    skin_data = {}
    for i, inf_obj in enumerate(influence_objects):
        skin_data.update({inf_obj: array_weights[i]})

    return skin_data


def to_array(skin_data):
    """
    convert skin data from a dictionary to numpy matrix array and influence objects list
    set_data() function need to be in this format to set weights for skin cluster

    Args:
        skin_data (dict): skin data dictionary, the keys are influence objects names,
                          and items are component weights values for influences

    Returns:
        array_weights (numpy.ndarray): skin cluster's numpy matrix array comping from get_data function
        influence_objects (list): influence objects names
    """
    # get influence list
    influence_objects = skin_data.keys()

    # get components count
    components_count = skin_data[influence_objects[0]].size
    # create array weights
    array_weights = numpy.empty((0, components_count))
    # loop in each influence and add array to weights array
    for inf_array in skin_data.values():
        array_weights = numpy.vstack((array_weights, inf_array))
    return array_weights, influence_objects


def set_data(skin_cluster, array_weights, influence_objects):
    """
    set skin weights to the given skin cluster
    TODO: set blend weights values and skinning method
    Args:
        skin_cluster (str): skin cluster name
        array_weights (numpy.ndarray): numpy matrix array, each column presents for influence object,
                                       and each row presents all components weight values for this influence
        influence_objects (list): influence objects names
    """
    mfn_skin = get_MFnSkinCluster(skin_cluster)
    m_dag, m_obj = _get_components_info(mfn_skin)

    # get influence objects array
    m_array_inf = mfn_skin.influenceObjects()
    inf_num = len(m_array_inf)
    # get int array for influence order
    array_inf_order = []
    for i in range(inf_num):
        # get influence name
        inf = m_array_inf[i].partialPathName()
        # get the index in given influence object list, add to array
        array_inf_order.append(influence_objects.index(inf))
    # convert to int array
    m_array_inf_order = OpenMaya2.MIntArray(array_inf_order)
    # flatten given weights array and convert to MDoubleArray,
    # it need to be flatten in column major, skin cluster read in this order
    m_array_weights = OpenMaya2.MDoubleArray(array_weights.flatten('F').tolist())
    # set skin cluster
    mfn_skin.setWeights(m_dag, m_obj, m_array_inf_order, m_array_weights, normalize=True, returnOldWeights=False)


# import/export skin data
def export_data(geo, file_path):
    """
    export skin cluster data to the given path

    Args:
        geo (str): geometry name
        file_path (str): file path to save the skin cluster
    """
    skin_data = get_data(geo)
    if skin_data:
        # the skin data should contain weights array, influence objects and geometry name
        skin_data = numpy.array([skin_data[0], skin_data[1], geo])
        fileUtils.numpyUtils.write(file_path, skin_data)


def import_data(file_path, geo=None, flip=False, force=False):
    """
    import skin cluster data

    Args:
        file_path (str): skin data file
        geo (str/None): if need to attach skin cluster to a different name geometry than the one in the skin data,
                        default is None
        flip (bool): if set to True, instead of using the given side, it will use the other side influences to bind skin
        force (bool): if set to True, will delete current geometry's skin cluster, and bind with influences,
                      default is False

    Returns:
        skin_cluster (str): skin cluster name
    """
    # get skin data
    skin_data = fileUtils.numpyUtils.read(file_path)

    # get geo
    if not geo:
        geo = skin_data[2]

    # check if geometry exist or not, return if not exist
    if not cmds.objExists(geo):
        warnings.warn(geo + ' does not exist in the scene, skipped')
        return None

    # flip influences
    if flip:
        skin_data[1] = namingUtils.flip_names(skin_data[1])
    # check influence number, if only one joint, do a rigid biped
    if len(skin_data[1]) == 1:
        skin_cluster = create(geo, skin_data[1], force=force)
        return skin_cluster

    # check geometry's component count
    skin_component_count = skin_data[0][0].size
    shape = geo
    if cmds.objectType(shape) == 'transform':
        shape = cmds.listRelatives(shape, shapes=True)[0]
    if cmds.objectType(shape) == 'mesh':
        geo_component_count = meshUtils.get_shape_info(shape)['num_vertices']
    elif cmds.objectType(shape) == 'nurbsCurve':
        geo_component_count = curveUtils.get_shape_info(shape)['num_cvs']
    else:
        geo_component_count = surfaceUtils.get_shape_info(shape)['num_cvs']

    # if components count not match, return
    if skin_component_count != geo_component_count:
        warnings.warn('{0} component count: {1} does not match the source {2}, skipped'.format(geo,
                                                                                               geo_component_count,
                                                                                               skin_component_count))
        return None

    # create skin cluster
    skin_cluster = create(geo, skin_data[1], force=force)

    if not skin_cluster:
        # geometry already has skin cluster, return
        return None

    # set skin data
    set_data(skin_cluster, skin_data[0], skin_data[1])
    return skin_cluster


# MFnSkinCluster wrapper
def get_MFnSkinCluster(skin_cluster):
    """
    get MFnSkinCluster object from given skin cluster node

    Args:
        skin_cluster (str): skin cluster name

    Returns:
        mfn_skin (MFnSkinCluster)
    """
    # get MObject
    m_obj = apiUtils.MSelectionList.get_nodes_info(skin_cluster, info_type='MObject')[0]
    # get MFnNurbsCurve
    mfn_skin = OpenMayaAnim2.MFnSkinCluster(m_obj)
    return mfn_skin


# sub function
def _get_components_info(mfn_skin):
    """
    get MDagPath and MObject for components attached to the skin cluster

    Args:
        mfn_skin (MFnSkinCluster): maya.api.OpenMaya MFnSkinCluster object

    Returns:
        m_dag (MDagPath): MDagPath object for components
        m_obj (MObject): MObject for components
    """
    mfn_set = OpenMaya2.MFnSet(mfn_skin.deformerSet)
    m_sel_members = mfn_set.getMembers(flatten=False)
    m_dag, m_obj = m_sel_members.getComponent(0)
    return m_dag, m_obj
