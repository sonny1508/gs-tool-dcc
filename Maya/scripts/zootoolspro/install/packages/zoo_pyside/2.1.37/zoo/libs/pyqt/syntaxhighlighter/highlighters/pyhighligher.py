from collections import OrderedDict

from zoovendor.Qt import QtCore
from zoo.libs.pyqt.syntaxhighlighter import highlighter


class PythonHighlighter(highlighter.HighlighterBase):
    """Syntax highlighter for the Python language.
    """
    id = "python"

    def __init__(self, document, syntax, style=None):
        """
        :param document:
        :type document: the textEdit document
        :param style: The style dict
        :type style: dict
        """
        super(PythonHighlighter, self).__init__(document, syntax, style)
        syntax = self.syntax["syntax"]
        self.syntaxRules = OrderedDict(
            (
                # ("variable", ["'''|" + '"""']),
                # ("attribute", ["'''|" + '"""']),
                ("keyword", [("|".join(r'\b{}\b'.format(w) for w in syntax["keyword"]), 0)]),
                ("controlFlow", [("|".join(r'\b{}\b'.format(w) for w in syntax["controlFlow"]), 0)]),
                ("operator", [(i, 0) for i in syntax["operator"]]),
                ("function", [(r"(\w+)(?=\()", 1)]),
                ("class", [(r'\bclass\b\s*(\w+)', 1)]),
                ("builtin", [(r'\b{}\b'.format(w), 0) for w in syntax["builtin"]]),
                ("dataType", [("|".join(r'\b{}\b'.format(w) for w in syntax["dataType"]), 0)]),
                ("number", [(r"\b[+-]?[0-9]+[lL]?\b|"
                             r"\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b|"
                             r"\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b", 0)]),
                ("string", [
                    (r'"[^"\\]*(\\.[^"\\]*)*"', 0),  # double-quoted string
                    (r"'[^'\\]*(\\.[^'\\]*)*'", 0)  # single quoted
                ]),
                ("import", [("|".join(r'\b{}\b'.format(w) for w in syntax["import"]), 0)]),
                ("preprocessor", [("|".join(r'\b{}\b'.format(w) for w in syntax["preprocessor"]), 0)]),
                ("self", [(r"\bself\b", 0)]),
                ("annotation", [(r'\b{}\b'.format(w), 0) for w in syntax["annotation"]] +
                 [(r'@[\w.]+', 0)],),  # decorators
                ("comment", [(r'#[^\n]*', 0)])
            )
            # ("information", ["|".join(r'\b{}\b'.format(w) for w in self.syntax["information"])]),
            # ("alert", ["|".join(r'\b{}\b'.format(w) for w in syntax["alert"])]))

        )
        self.documentationSyntax = QtCore.QRegularExpression("'''|" + '"""')
        for keyword, regex in self.syntaxRules.items():
            self.syntaxRules[keyword] = [(QtCore.QRegularExpression(i), index) for i, index in regex]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        colors = self.style.get("colors")
        if not colors:
            return
        # Do other syntax formatting
        for k, expressions in self.syntaxRules.items():
            color = colors.get(k)
            if color is None:
                continue
            textFormat = highlighter.formatColor(**color)
            for expr, nth in expressions:
                match = expr.match(text)
                index = match.capturedStart()
                while index >= 0:
                    length = match.capturedLength()
                    self.setFormat(index, length, textFormat)
                    # We actually want the index of the nth match for the next iteration
                    match = expr.match(text, index + length)
                    index = match.capturedStart()

        self.setCurrentBlockState(0)
        docFormat = highlighter.formatColor(**colors["documentation"])
        self.matchMultiline(text, self.documentationSyntax, 1, docFormat)


    def matchMultiline(self, text, delimiter, inState, textFormat):
        """Highlighting of multi-line strings.

        :type text: str
        :param delimiter: regex instance for triple-single-quotes and/or triple-double-quotes
        :type delimiter: :class:`QtCore.QRegularExpression`
        :param inState: Unique integer to represent the corresponding state changes when inside those strings
        :type inState: int
        :param textFormat The textFormat to use.
        :type textFormat: :class:`QtCore.QTextCharFormat`
        :return Returns True if we're still inside a multi-line string when this function is finished.
        :rtype: bool
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == inState:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            match = delimiter.match(text)
            start = match.capturedStart()
            # Move past this match
            add = match.capturedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            match = delimiter.match(text, start + add)
            end = match.capturedStart()
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + match.capturedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(inState)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, textFormat)
            # Look for the next match
            match = delimiter.match(text, start + length)
            start = match.capturedStart()

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == inState:
            return True
        return False
