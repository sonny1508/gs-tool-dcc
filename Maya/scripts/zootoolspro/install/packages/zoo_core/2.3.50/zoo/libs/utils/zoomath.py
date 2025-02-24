import sys
import math
from zoovendor.six.moves import range

AXIS = {"x": 0,
        "y": 1,
        "z": 2}


def lerp(current, goal, weight=0.5):
    return (goal * weight) + ((1.0 - weight) * current)


def lerpCount(start, end, count):
    """Iterates between start and goal for the given count.

    .. code-block:: python

        for i in lerpCount(-10, 10, 8):
            print(i)

    Outputs::

        # 0.0
        # 0.25
        # 0.5
        # 0.75
        # 1.0

    :param start: The starting number i.e. 0.0
    :type start: float
    :param end: The goal number i.e. 1.0
    :type end: float
    :param count: The number of iterations.
    :type count: int
    :rtype: Iterable[float]
    """
    primaryFraction = (end - start) / float(count - 1)

    multiplier = start + primaryFraction
    yield start
    for n in range(count - 2):
        yield multiplier
        multiplier += primaryFraction
    yield end


def remap(value, oldMin, oldMax, newMin, newMax):
    return (((value - oldMin) * (newMax - newMin)) / (oldMax - oldMin)) + newMin


def almostEqual(x, y, tailCount):
    return math.fabs(x - y) < sys.float_info.epsilon * math.fabs(x + y) * tailCount or math.fabs(
        x - y) < sys.float_info.min


def mean(numbers):  # because we have to use py2 as well otherwise statistics stdlib module would be better
    """Returns the mean/average of the numbers.

    :param numbers: The numbers to average.
    :type numbers: list[float]
    :rtype: float
    """
    return float(sum(numbers)) / max(len(numbers), 1)


def threePointParabola(a, b, c, iterations):
    positions = []
    for t in range(1, int(iterations)):
        x = t / iterations
        q = b + (b - a) * x
        r = c + (c - b) * x
        p = r + (r - q) * x
        positions.append(p)
    return positions


def clamp(value, minValue=0.0, maxValue=1.0):
    """Clamps a value withing a max and min range

    :param value: value/number
    :type value: float
    :param minValue: clamp/stop any value below this value
    :type minValue: float
    :param maxValue: clamp/stop any value above this value
    :type maxValue: float
    :return clampedValue: clamped value as a float
    :rtype clampedValue: float
    """
    return max(minValue, min(value, maxValue))
