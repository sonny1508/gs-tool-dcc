# This Python file uses the following encoding: utf-8
import os
from zoovendor import six
from zoovendor.Qt import QtGui
from zoo.libs.utils import filesystem



def formatColor(textColor, bold=False, italic=False):
    """Return a QtGui.QTextCharFormat with the given attributes.
    :param textColor: float3 rgb
    :type textColor: tuple
    """
    if isinstance(textColor, six.string_types):
        _color = QtGui.QColor(textColor)
    else:
        _color = QtGui.QColor(*textColor)
    _format = QtGui.QTextCharFormat()
    _format.setForeground(_color)
    if bold:
        _format.setFontWeight(QtGui.QFont.Bold)
    _format.setFontItalic(italic)

    return _format



def _loadStyle(style):
    return filesystem.loadJson(os.path.join(os.path.dirname(__file__), "themes", "{}.json".format(style)))


def highlighterForLanguage(document, language, style=None):
    # todo: swap syntax highlighter for plugin manager
    from zoo.libs.pyqt.syntaxhighlighter.highlighters import pyhighligher
    syntaxData = filesystem.loadJson(os.path.join(os.path.dirname(__file__), "syntax", "{}syntax.json".format(language)))
    if style:
        style = _loadStyle(style)
    highlighter = pyhighligher.PythonHighlighter(document, syntaxData, style)
    return highlighter


class HighlighterBase(QtGui.QSyntaxHighlighter):
    """
    Syntax and color keys.

    All keys for colors are in the form:

    .. code-block:: json

        {
        "textColor": [
            171,
            178,
            191
        ],
        "bold": false,
        "italic": false
        }


    #. normal: Default text style for normal text and source code without special highlighting.
    #. keyword: Text style for built-in language keywords.
    #. function: Text style for function definitions and function calls.
    #. class: Text style for class name.
    #. controlFlow: Text style for control flow keywords, such as if, then, else, return, switch, break, yield, continue, etc.
    #. operator: Text style for operators, such as +, -, *, /, %, etc.
    #. builtIn: Text style for built-in language classes, functions and objects.
    #. preprocessor: Text style for preprocessor statements or macro definitions.
    #. attribute: Text style for annotations eg. @property in python,
    #. dataType: Text style for built-in data types such as int, char, float, void, u64, etc.
    #. number:  Text style for integers and floats.
    #. string: Text style for strings like “hello world”.
    #. import: Text style for includes, imports, modules.
    #. comment: Text style for normal comments.
    #. documentation: Text style for docstrings either triple " or triple '.
    #. annotation: Text style for annotations in comments or documentation commands, such as @param in Doxygen or JavaDoc.
    #. information: Text style for information, notes and tips, such as the keyword @note in Doxygen.
    #. warning: Text style for warnings, such as the keyword @warning in Doxygen.
    #. alert: Text style for special words in comments, such as TODO, FIXME, XXXX and WARNING.


    """

    def __init__(self, document, syntax, style=None):
        """
        :param document:
        :type document: the textEdit document
        """
        super(HighlighterBase, self).__init__(document)
        self.syntax = syntax
        self.style = style or {}
