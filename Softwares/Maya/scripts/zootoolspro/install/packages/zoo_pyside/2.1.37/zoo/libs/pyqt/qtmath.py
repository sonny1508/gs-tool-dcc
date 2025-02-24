import math

from zoovendor.Qt import QtCore


def normalized(pt):
    mag = magnitude(pt) or 0.001
    return QtCore.QPointF(pt.x() / mag, pt.y() / mag)


def magnitude(pt):
    return math.sqrt(pt.x() ** 2 + pt.y() ** 2)


def distance(pt1, pt2):
    return magnitude(pt2 - pt1)
