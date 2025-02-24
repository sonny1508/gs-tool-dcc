def update_members(members):
    """An example of adding Qsci to Qt.py.

    Arguments:
        members (dict): The default list of members in Qt.py.
            Update this dict with any modifications needed.
    """
    members["QtCore"].append("QRegularExpression")
    members["QtGui"].append("QRegularExpressionValidator")


def update_misplaced_members(members):
    members["PySide2"]["QtCore.QRegExp"] = "QtCore.QRegExp"

