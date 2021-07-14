import numpy


# function
def clamp(value, clamp_range):
    """
    clamp the given value in range

    Args:
        value(float): given value
        clamp_range(list): [min, max]

    Returns:
        clamp_value(float)

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.numeric.clamp(10, [-5, 5])
        # 5

        mathUtils.numeric.clamp(-10, [-5, 5])
        # -5

        mathUtils.numeric.clamp(3, [-5, 5])
        # 3
    """
    if value < clamp_range[0]:
        value = clamp_range[0]
    if value > clamp_range[1]:
        value = clamp_range[1]
    return value


def remap(value, input_range, output_range):
    """
    remap given value from the input range to output range

    Args:
        value(float): given value
        input_range(list): [min, max]
        output_range(list): [min, max]

    Returns:
        remap_value(float)

    Examples:
        import utils.common.mathUtils as mathUtils

        mathUtils.numeric.remap(5, [0, 10], [0, 20])
        # 10
    """
    # clamp value
    value = clamp(value, input_range)
    # get weight
    weight = (value - input_range[0])/float(input_range[1] - input_range[0])
    # remap to output range
    value = (output_range[1] - output_range[0])*weight + output_range[0]

    return value


def linear_space(start_value, end_value, number=5):
    """
    evenly spaced values, calculated over the interval [start, stop]

    Args:
        start_value (float): start value
        end_value (float): end value
        number (int): number of values need to be evenly spaced, start and end values included

    Returns:
        outputs (list): output values
    """
    outputs = numpy.linspace(start_value, end_value, num=number).tolist()
    return outputs
