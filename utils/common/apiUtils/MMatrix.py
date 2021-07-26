# import python library
import math

# import maya python library
import maya.api.OpenMaya as OpenMaya2


# function
def compose(translate=None, rotate=None, scale=None, rotate_order=0, matrix=None):
    """
    compose MMatrix with given transform values

    Args:
        translate (list): translation values, default is [0, 0, 0]
        rotate (list): rotation values, default is [0, 0, 0]
        scale (list): scale values, default is [1, 1, 1]
        rotate_order (int): current transform values' rotate order, default is 0
        matrix (list) convert matrix list to MMatrix object instead using transform values

    Returns:
        m_matrix(MMatrix)

    Examples:
        import utils.common.apiUtils as apiUtils

        apiUtils.MMatrix.compose(translate=[1, 2, 3], rotate=[10, 20, 30], scale=[1, 0.5, 0.5])
        # maya.api.OpenMaya.MMatrix(((0.81379768134937369162, 0.46984631039295421395, -0.34202014332566871291, 0),
        #                            (-0.22048480526494124154, 0.44128205962969280218, 0.081587955583267410264, 0),
        #                            (0.18926115318489628025, 0.0090141556181486340998, 0.46270828919916168198, 0),
        #                            (1, 2, 3, 1)))

        apiUtils.MMatrix.compose(matrix=[0.8358376208927379, 0.44803661357929825, 0.31723597588035696, 0.0,
                                         -0.32491492643983527, 0.8695226186000968, -0.3719686899719209, 0.0,
                                         -0.44249944867419244, 0.20783072110548328, 0.872353500186599, 0.0,
                                         7.496652602921901, 5.867761491900925, -4.584176306197449, 1.0])
        # maya.api.OpenMaya.MMatrix(((0.83583762089273794249, 0.44803661357929824849, 0.31723597588035695738, 0),
        #                            (-0.32491492643983527211, 0.86952261860009683048, -0.37196868997192089612, 0),
        #                            (-0.44249944867419244154, 0.20783072110548328482, 0.87235350018659896243, 0),
        #                            (7.496652602921900943, 5.8677614919009251082, -4.5841763061974489801, 1)))
    """
    # check if have input matrix, convert to MMatrix if have values
    if matrix:
        return OpenMaya2.MMatrix(matrix)

    # get transform values
    if not translate:
        translate = [0, 0, 0]
    if not rotate:
        rotate = [0, 0, 0]
    if not scale:
        scale = [1, 1, 1]

    # create MTransformationMatrix object
    m_transform_matrix = OpenMaya2.MTransformationMatrix()

    # create MVector for translation
    m_vector = OpenMaya2.MVector(translate[0], translate[1], translate[2])

    # create MDoubleArray for rotation
    m_rotate = OpenMaya2.MEulerRotation(math.radians(rotate[0]),
                                        math.radians(rotate[1]),
                                        math.radians(rotate[2]),
                                        rotate_order)

    # set MMatrix
    m_transform_matrix.setTranslation(m_vector, OpenMaya2.MSpace.kWorld)
    m_transform_matrix.setRotation(m_rotate)
    m_transform_matrix.setScale(scale, OpenMaya2.MSpace.kWorld)

    # get MMatrix
    m_matrix = m_transform_matrix.asMatrix()

    return m_matrix


def decompose(m_matrix, rotate_order=0):
    """
    decompose input MMatrix object to transform information

    Args:
        m_matrix(MMatrix): OpenMaya MMatrix object
        rotate_order(int): input rotate order, default is 0

    Returns:
        [translate, rotate, scale](list)

    Examples:
        import utils.common.apiUtils as apiUtils

        # get MMatrix object
        m_matrix = apiUtils.MMatrix.compose(translate=[1, 2, 3], rotate=[10, 20, 30], scale=[1, 0.5, 0.5])
        apiUtils.MMatrix.decompose(m_matrix)
        # [[1, 2, 3], [10, 20, 30], [1, 0.5, 0.5]]
    """
    # get MTransformationMatrix from MMatrix
    m_transform_matrix = OpenMaya2.MTransformationMatrix(m_matrix)

    # get MTranslate, MRotate, scale
    m_translate = m_transform_matrix.translation(OpenMaya2.MSpace.kWorld)
    m_rotate = m_transform_matrix.rotation(asQuaternion=False)
    m_rotate.reorderIt(rotate_order)
    scale = m_transform_matrix.scale(OpenMaya2.MSpace.kWorld)

    # get transform information
    translate = [m_translate.x, m_translate.y, m_translate.z]
    rotate = [math.degrees(m_rotate.x), math.degrees(m_rotate.y), math.degrees(m_rotate.z)]
    return [translate, rotate, scale]


def to_list(m_matrix):
    """
    Args:
        m_matrix (MMatrix): OpenMaya MMatrix object

    Returns:
        matrix(list)

    Examples:
        import utils.common.apiUtils as apiUtils

        # get MMatrix object
        m_matrix = apiUtils.MMatrix.compose(matrix=[0.8358376208927379, 0.44803661357929825, 0.31723597588035696, 0.0,
                                                    -0.32491492643983527, 0.8695226186000968, -0.3719686899719209, 0.0,
                                                    -0.44249944867419244, 0.20783072110548328, 0.872353500186599, 0.0,
                                                    7.496652602921901, 5.867761491900925, -4.584176306197449, 1.0])
        apiUtils.MMatrix.to_list(m_matrix)
        # [0.8358376208927379, 0.44803661357929825, 0.31723597588035696, 0.0,
        #  -0.32491492643983527, 0.8695226186000968, -0.3719686899719209, 0.0,
        #  -0.44249944867419244, 0.20783072110548328, 0.872353500186599, 0.0,
        #  7.496652602921901, 5.867761491900925, -4.584176306197449, 1.0]
    """

    matrix = []
    for i in range(4):
        for j in range(4):
            matrix.append(m_matrix.getElement(i, j))
    return matrix
