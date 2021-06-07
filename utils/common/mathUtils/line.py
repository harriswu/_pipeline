import vector
import numeric


def closest_point(line_points, point_pos, clamp=False):
    """
    get closest point on line

    Args:
        line_points (list): start and end point position of the line
        point_pos (list): given point position
        clamp (bool): the point position will be clamped into the start/end point range if set to True,
                      otherwise it will be a point on the line's vector direction

    Returns:
        cls_pnt (list): closest point position
        para (float): the point's parameter on the line

    Examples:
        import utils.common.mathUtils

        mathUtils.line.closest_point([[0, 0, 3], [-4, 0, -6]], [-5, 0, -0], clamp=True)
        # ([-1.9381443298969072, 0.0, -1.3608247422680408], 0.4845360824742268)

        mathUtils.line.closest_point([[0, 0, 3], [-4, 0, -6]], [-8, 0, -8], clamp=True)
        # ([-4, 0, -6], 1)
        mathUtils.line.closest_point([[0, 0, 3], [-4, 0, -6]], [-8, 0, -8], clamp=False)
        # ([-5.402061855670103, 0.0, -9.154639175257733], 1.3505154639175259)
    """
    vector_line = vector.create(line_points[0], line_points[1], normalize=False)
    vector_point = vector.create(line_points[0], point_pos, normalize=False)
    param = vector.dot_product(vector_point, vector_line) / vector.dot_product(vector_line, vector_line)
    if clamp:
        param = numeric.clamp(param, [0, 1])
    return vector.add(line_points[0], vector.scale(vector_line, param)), param
