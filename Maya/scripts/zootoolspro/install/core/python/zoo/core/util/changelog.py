"""Helper utilities for manipulating a Zoo package changelog build for RST/Sphinx.

Zoo ChangeLog has a certain syntax which we'll outline here.

A changelog is made up of 4 primary sections.


.. list-table::
   :widths: 25 25 50
   :header-rows: 1

   * - Type
     - Token
     - Description
   * - Header
     - `====`
     - Token Surrounds the header label, defaults to "Changelog".
   * - Version
     - `----`
     - Underlined with "----" And Version is in the format of "{version} (year-month-day)".
   * - Category
     - `~~~~`
     - underlined with "~~~~" either "Added", "Changes", "Bug, "Removed"
   * - ChangeMessage
     - `- (messageTopicOrLabel) message body`
     - The formatted message which occurred.

Example Changelog Output::

    =========
    ChangeLog
    =========

    1.2.13 (2022-01-2022)
    ---------------------

    Added
    ~~~~~

    Added - (docs) Pycharm setup documentation for zoo tools.
    Added - (docs) sphinxcontrib.youtube thirdparty dependency when build docs to support youtube and vimeo links.

    Bug Fixes
    ~~~~~~~~~
    BugFix - (MayaPlugin) Fix FileNotFoundError being raised due to incorrect zoo initialization order.

"""

from collections import OrderedDict
from distutils.version import LooseVersion
import re

# capture regex for the category from a single change messge ie. "- Category (subject)"
REGEX_CATEGORY = re.compile(r"(\w+(?=[ -]+\())", re.IGNORECASE)
# capture regex group between (), used by changeMessage and version date.
REGEX_SUBJECT = re.compile(r"(\(.*?\))", re.IGNORECASE)
# regex capture all content after the first occurrence of ) for the message body.
REGEX_MESSAGE_BODY = re.compile(r"(?<=\)).*", re.IGNORECASE)
HEADER_UNDERLINE_TOKEN = "=="
VERSION_UNDERLINE_TOKEN = "--"
CATEGORY_UNDERLINE_TOKEN = "~~"
MESSAGE_TOKEN = "-"
MESSAGE_FORMAT = "- ({}) {}"


class Changelog(object):
    """Interface to manage changelog versions and output rst lines via asRstLines.

    :param label: The changelog header label ie. ChangeLog.
    :type label: str
    """

    def __init__(self, label):
        self.label = label
        self.versions = OrderedDict()

    def children(self):
        """Returns the child versions in the order they were added.

        :rtype: iterable[:class:`ChangelogVersion`]
        """
        return self.versions.values()

    def sortedVersions(self):
        """Returns a sorted tuple by the version. version sorting using stdlib LooseVersion instances.

        :rtype: tuple[str, :class:`ChangelogVersion`]
        """
        return sorted(self.versions.items(), key=lambda x: x[1].version, reverse=True)

    def printTree(self):
        """Simply does a formatted print statement for visual debugging of the changelog hierarchy.
        """
        _pprintTree(self, ["label"])

    def asRstLines(self):
        """Returns a formatted flatten list of rst lines which can be written directly into a file.

        This doesn't include newlines.
        This loops through all current versions, categories and changes and flattens everything.

        :rtype: list[str]
        """
        line = (HEADER_UNDERLINE_TOKEN[0] * len(self.label))
        output = [line, self.label, line, ""]
        for _, version in self.sortedVersions():
            output.extend(version.asRstLines())
        return output


class ChangelogVersion(object):
    """A Single Version in the changelog which manages and sorts categories.

    :param version: The version str ie. 1.0.0. casts to version.LooseVersion.
    :type version: str
    :param date: The date that the version was created.
    :type date:  str
    :param changelog: The current changelog instance this version is linked too.
    :type changelog: :class:`ChangeLog`
    """

    @classmethod
    def parseString(cls, st, changelog):
        date = REGEX_SUBJECT.search(st).group(0)
        version, _ = st.split(date)

        return cls(version.strip(), date[1:-1], changelog)

    def __init__(self, version, date, changelog):
        self._changelog = changelog
        self.categories = []
        self.date = date
        self.version = LooseVersion(version)  # type: LooseVersion

    @property
    def label(self):
        """ Returns a formatted label ie. 1.0.0 (2022-01-18)

        :rtype: str
        """
        return " ".join((str(self.version), self.date))

    def children(self):
        """Returns all child categories in the same order they were added.

        :rtype: list[:class:`ChangelogCategory`]
        """
        return self.categories

    def asRstLines(self):
        """Does the same as Changelog.asRstLines but just for the version.

        :rtype: list[str]
        """
        label = " ".join((str(self.version), "({})".format(self.date)))
        line = VERSION_UNDERLINE_TOKEN[0] * len(label)
        output = ["", label, line, ""]
        for cat in sorted(self.categories, key=lambda x: x.label):
            if cat.label.lower() == "ignore":
                continue
            output.extend(cat.asRstLines() + [""])
        return output


class ChangelogCategory(object):
    """Wraps a Category which contains a list of messages/changes.

    :param changelogVersion: The version instance which the category is linked too.
    :type changelogVersion: :class:`ChangelogVersion`
    :param label:
    :type label: str
    """
    def __init__(self, changelogVersion, label):
        self.changelogVersion = changelogVersion
        self.label = label
        self.messages = []
        self.sorted = True

    def children(self):
        """Returns a list of messages in the order they were added.

        :rtype: list[:class:`ChangeMessage`]
        """
        return self.messages

    def sortMessages(self):
        """Sorts and returns current change messages for the category.

        :rtype: list[:class:`ChangeMessage`]
        """
        return sorted(self.messages, key=lambda x: x.label)

    def asRstLines(self):
        """Does the same as Changelog.asRstLines but just for the category.

        :rtype: list[str]
        """
        body = [str(self.label).title(), CATEGORY_UNDERLINE_TOKEN[0] * len(self.label), ""]
        if self.sorted:
            messages = sorted(self.sortMessages(), key=lambda x: x.subject)
        else:
            messages = self.messages
        for message in messages:
            body.append(message.asRst())
        return body


class ChangeMessage(object):
    """Single line message which includes a subject and body.

    The output of rst is the below.::

        - (subject) body

    :param label: The original string which includes the subject and body of the message.
    :type label: str
    :param subject: The subject of the message when  converted to rst this will be surround with ().
    :type subject: str
    :param body: The message body.
    :type body: str
    """
    @classmethod
    def parseString(cls, st):

        subject = REGEX_SUBJECT.search(st)
        if subject:
            subject = subject.group(0).strip()[1:-1].strip()
        else:
            subject = ""
        body = REGEX_MESSAGE_BODY.search(st)
        if body:
            body = body.group(0).strip()
        else:
            body = ""

        return cls(st, subject, body.strip())

    def __init__(self, label, subject, body):
        self.label = label
        self.subject = subject
        self.body = body

    def asRst(self):
        """Returns a formatted rst line in the form::

            - (label) body

        :rtype: str
        """
        if not self.body:
            body = self.label
        else:
            body = str(self.body)
            body = body[0].upper() + body[1:]
        if not body.endswith("."):
            body += "."
        if self.subject:
            return MESSAGE_FORMAT.format(self.subject.title(), body)
        return MESSAGE_FORMAT.format("Misc", body)


def _parseLines(lines):
    """Given a list of strings which represent a rst doc.
    Translate into our wrapper Changelog object.

    :param lines: A list of formatted rst compatible lines
    :type lines: list[str]
    :return: A fully translated Changelog instance.
    :rtype: :class:`Changelog`
    """
    changeLog = Changelog("ChangeLog")
    currentVersion = None  # type: ChangelogVersion or None
    currentCategory = None  # type: ChangelogCategory or None

    for lineno, line in enumerate(lines):
        parts = line.split()
        if not parts:
            continue
        token = parts[0]
        # file header
        if token.startswith(HEADER_UNDERLINE_TOKEN):
            continue
        # version section
        elif token.startswith(VERSION_UNDERLINE_TOKEN):
            versionLine = lines[lineno - 1].strip()
            # starting new version block so add the current into the global contents
            # before starting new block
            if currentVersion is not None:
                changeLog.versions[currentVersion.label] = currentVersion
            currentVersion = ChangelogVersion.parseString(versionLine, changeLog)

        # category
        elif token.startswith(CATEGORY_UNDERLINE_TOKEN):
            currentCategory = ChangelogCategory(currentVersion, parseCategory(lines[lineno - 1].strip()))
            currentVersion.categories.append(currentCategory)
        # commit message
        elif token == MESSAGE_TOKEN:
            currentCategory.messages.append(ChangeMessage.parseString(" ".join(parts[1:])))
    else:
        if currentVersion:
            changeLog.versions[currentVersion.label] = currentVersion
    return changeLog


def parseChangelog(changelog):
    """Providing a changelog as a raw string this function will return a changelog instance.

    :param changelog: The raw string for a RST changelog
    :type changelog: str
    :rtype: :class:`Changelog`
    """
    return _parseLines(changelog.split())


def parseChangeLogFile(f):
    """Providing a changelog File object will generate a Changelog instance.

    :param f: The file instance
    :type f:  :class:`file`
    :rtype: :class:`Changelog`
    """
    return _parseLines(f.readlines())


def createRstTitle(beforeToken, title, afterToken):
    """Generates Rst title based on the before and after title

    .. code-block:: python

        # creates the below ignoring "#"
        # -------
        # myTitle
        # -------
        createRstTitle("-", "myTitle", "-")

        # creates the below ignoring "#"

        # myTitle
        # -------
        createRstTitle(None, "myTitle", "-")


    :param beforeToken: The token to use for the previous line before the title.
    :type beforeToken: str
    :param title: The title to use can be any string.
    :type title: str
    :param afterToken: The token to use for the next line after the title.
    :type afterToken: str
    :return: MultiLine string.
    :rtype: str
    """
    length = len(title)
    output = ""
    if beforeToken:
        output += beforeToken * length
    output += title

    if afterToken:
        output += afterToken * length
    return output


def _pprintTree(node, attributes, _prefix="", _last=True):
    """ adapted from https://vallentin.dev/2016/11/29/pretty-print-tree

    :param node:
    :param attributes:
    :param _prefix:
    :param _last:
    :return:
    """
    treeSep = "`- " if _last else "|- "
    values = [_prefix, treeSep] + ["-".join([getattr(node, attr) for attr in attributes]) or node]
    msg = "".join(values)
    print(msg)
    _prefix += "   " if _last else "|  "
    if not hasattr(node, "children"):
        return
    children = node.children()
    child_count = len(children)
    for i, child in enumerate(children):
        _last = i == (child_count - 1)
        _pprintTree(child, attributes, _prefix, _last)


def parseCategory(cat):
    """Converts a category label ie. bug to a standardized name for the rst changelog.

    :param cat: category label
    :type cat: str
    :rtype: str
    """
    category = cat.lower()
    if "bug" in category:
        return "bug"
    elif category.startswith("ch"):
        return "change"
    elif category.startswith("add"):
        return "added"
    elif category.startswith("ignore"):
        return "ignore"
    return category


def iterChangelog(node):
    """Generator function which iterators the change log starting from `node`

    :param node:
    :type node: :class:`Changelog` or :class:`ChangelogVersion` or `ChangelogCategory` or `ChangelogMessage`
    :return:
    :rtype: list[:class:`Changelog` or :class:`ChangelogVersion` or `ChangelogCategory` or `ChangelogMessage`]
    """
    if not hasattr(node, "children"):
        return
    for child in node.children():
        yield child
        for i in iterChangelog(child):
            yield i
