"""Zoo tools wrapper around gitpython with a strong focus zoo package release workflows.
"""
from datetime import datetime

import tempfile
import os
import re

from git import Repo
import git

from zoo.core.util import changelog, zlogging

REGEX_COMMIT_MESSAGE = re.compile(
    # example:  Bug - (maya api) while still support no whitespaces between -
    r"(\w+[ ]?- +\(.*?\)|"
    # example: -Added(Uninstance) while still support whitespaces between -
    r"(?:-.?)+\w+[ -]?\(.*?\))",
    re.IGNORECASE)

IGNORE_KEY_PHRASES = ("Create new version Tag",
                      "Merge branch",
                      "Merge remote",
                      "Auto stash")

logger = zlogging.getLogger(__name__)


class DirtyGitRepoException(Exception):
    """Raised when the current branch has uncommitted changes.
    """
    pass


class IncorrectCurrentBranchException(Exception):
    """Raised when the current branch isn't the primary master branch.
    """
    pass


class GitCommandError(Exception):
    """Raised when the current branch isn't the primary master branch.
    """
    pass


class InvalidGitRepositoryError(Exception):
    """Raised when the current branch isn't the primary master branch.
    """
    pass


class GitRepo(object):
    """ Wrapper around the gitpython Repo class to provide Zoo related operations.

    :param repoPath: The physical disk or URL to the Git repository
    :type repoPath: str
    """

    def __init__(self, repoPath=None):

        if repoPath is not None:
            self.repo = Repo(repoPath)  # type: git.Repo
        else:
            self.repo = None
        self.repoPath = repoPath

    @classmethod
    def clone(cls, repoPath, destination, **kwargs):
        """ Clones the given git URL to the destination path.

        :param repoPath: the Git VCS to clone
        :type repoPath: str
        :param destination: The folder path to clone to
        :type destination: str
        :param kwargs: see :class:`Repo.clone_from`
        :type kwargs: dict
        :return: :class:`GitRepo`
        :rtype: :class:`GitRepo`
        """
        rep = Repo.clone_from(repoPath, destination, **kwargs)
        wrapper = cls(os.path.dirname(rep.git_dir))
        return wrapper

    def checkout(self, name):
        """Checks out a branch or tag based on the name.

        :param name: The branch or tag name to checkout ie. master
        :type name: str
        :return: The branch instance which was checked out. see git.Head class.
        :rtype: :class:`git.Head`
        """
        return self.repo.git.checkout(name)

    def assertRepo(self):
        """Checks whether this repo is either dirty ie. uncommitted changes in which
        case a :class:`DirtyGitRepoException` will be raised. or the current branch
        isn't master in which case :class:`IncorrectCurrentBranchException` is raised.

        :return: True when everything checks out to be fine.
        :rtype: bool
        :raise DirtyGitRepoException: In the case we're the current branch has uncommitted changes
        :raise IncorrectCurrentBranchException: In the case that the current branch isn't master \
        which is required when releasing our packages.
        :raise AssertionError: if the repository is bare
        """
        assert not self.repo.bare
        if self.repo.is_dirty():
            raise DirtyGitRepoException("Current Repo has uncommitted changes")

        if not self.repo.active_branch.name == "master":
            raise IncorrectCurrentBranchException(
                "Can't release on branch: {} only master allowed".format(self.repo.active_branch.name))
        return True

    def archive(self, fileName):
        """Archive the current repo state as a zip into a temp location.

        .. note::

            Relies heavily on gitpython to do the packing.

        :param fileName: The file base name to use before the extension.
        :type fileName: str
        :return: The output archive file path which was created in the OS temp folder.
        :rtype: str
        """
        # ok make a temp directory for downloading the zip
        tempDir = tempfile.mkdtemp()
        archivePath = str(fileName)
        if not archivePath.endswith(".zip"):
            archivePath = os.path.join(tempDir, archivePath + ".zip")

        with open(archivePath, "wb") as fp:
            self.repo.archive(fp, format="zip")
        return archivePath

    def tags(self):
        """Returns a sorted list based on the commit date of all tags on the repository

        :rtype: iterable[:class:`git.TagReference`]
        """
        return sorted(self.repo.tags, key=lambda t: t.commit.committed_datetime)

    def latestTag(self):
        """ Returns the latest tag based on the commit date.

        :rtype: :class:`git.TagReference`
        """

        tags = sorted(self.repo.tags, key=lambda t: t.commit.committed_datetime)
        if not tags:
            logger.warning("no tags")
            return ""
        return tags[-1]

    def commit(self, msg):
        """Commits All current changes to the branch with the given message.

        :param msg: The commit message
        :type msg: str
        """
        logger.info("Commit to current branch, with message: {}".format(msg))
        self.repo.git.add("--all")
        self.repo.git.commit("-m", msg)

    def createTag(self, name, message):
        """Creates and returns a new tag locally. use :func:`GitRepo.pushTag` to push to origin.

        :param name: The new tag name ie. 1.0.0
        :type name: str
        :param message: The Message for the new tag.
        :type message: str
        :rtype: :class:`git.TagReference`
        """
        logger.info("Creating Tag {} with message: {}".format(name, message))
        return self.repo.create_tag(name, message=message)

    def pushChanges(self):
        """Pushes any uncommitted changes to origin.
        """
        logger.debug("Push local changes")
        self.repo.git.push()

    def pullTags(self):
        """Does a fetch --tags on the current branch
        """
        self.repo.git.fetch("--tags")

    def pushTag(self, tag):
        """Pushes a single tag to origin.

        :param tag: The tag to push.
        :type tag: :class:`git.TagReference`
        """
        logger.info("Pushing next tag {}".format(tag))
        self.repo.remotes.origin.push(tag)
        logger.info("Finished pushing tag {} to remote ".format(tag))

    def hasChangesSinceLastTag(self):
        """Checks to see if there's been any commits since the latest tag.

        :rtype: bool
        """
        try:
            return next(self.commitMessagesSinceTag(self.latestTag())) is not None
        except StopIteration:
            return False

    def commitMessagesSinceTag(self, firstTag, secondTag=None):
        """finds and returns all commits between to tags if secondTag is None then the HEAD
        will be used.

        :param firstTag: The first/ older tag to to search from.
        :type firstTag:  :class:`gitTagReference` or str
        :param secondTag: The Tag to search to if None then HEAD will be used.
        :type secondTag: :class:`gitTagReference` or str or None
        :return: A generator where each element is commit object containing the date,author and message.
        :rtype: iterable[:class:`Commit`]

        .. note::

            Ignores certain commit messages like "Merge branch", "auto stash",
            "Create new version Tag"(which is done by our release tool).
            Exits early if theres a fatal reply by git.log
        """
        g = git.Git(self.repoPath)
        commitMsgs = g.log("{}..{}".format(firstTag, secondTag or "HEAD"), "--oneline",
                           '--pretty=format:[%an] | %ad | %s ')
        for line in iter(commitMsgs.split("\n")):
            if any(i in line for i in IGNORE_KEY_PHRASES):
                continue
            elif "fatal" in line:
                break
            messageParts = [i.strip() for i in line.split("|")]
            if len(messageParts) < 3:
                continue
            author = messageParts[0]
            date = messageParts[1]
            message = "".join(messageParts[2:])

            info = {"date": datetime.strptime(date, '%a %b %d %H:%M:%S %Y %z'),
                    "author": author,
                    "message": message}
            yield Commit(info)

    def latestCommitMsg(self):
        """Returns the latest commit message string.

        :rtype: str
        """
        return self.repo.head.commit.message


class Commit(dict):
    """Wrapper dict for a single git commit which contains the date, author and message.
    """

    @property
    def date(self):
        return self["date"]

    @property
    def author(self):
        return self["author"]

    @property
    def message(self):
        return self["message"]

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            return super(Commit, self).__getattribute__(item)


def tagToChangeLog(repo, previousTag, toTag, version=None, change=None):
    """Given the previous tag and the future tag(toTag) a changelog object is generated based on the
    vcs commit log, removing any commits which need to be ignored.

    :param repo: The GitRepo to operate on.
    :type repo: :class:`GitRepo`
    :param previousTag: The tag to start filtering from ie. 1.2.0 while `toTag` would be 1.2.1
    :type previousTag: :class:`git.TagReference`
    :param toTag: The latest tag to filter commits too.
    :type toTag: :class:`git.TagReference`
    :param change: The changelog instance to update or None which will create a new instance.
    :type change: :class:`changelog.Changelog` or None
    :param version: The Version to use for the commit messages. only used
    :type version: str
    :return: Either the same instance provided by `change` or a newly created instance.
    :rtype:  :class:`changelog.Changelog`
    """
    change = change if change is not None else changelog.Changelog("ChangeLog")
    versionName = version or ""
    if isinstance(toTag, git.TagReference):
        logVersionDate = toTag.commit.committed_datetime.strftime("%Y-%m-%d")
        versionName = toTag.name
    else:
        logVersionDate = datetime.now().strftime("%Y-%m-%d")
        if not version:
            raise ValueError("Version Key Required when 'toTag' isn't a TagReference Instance")
    # all previous versions we'll leave untouched in regard to sorting
    for i in changelog.iterChangelog(change):
        if isinstance(i, changelog.ChangelogCategory):
            i.sorted = False
    taggedVersion = changelog.ChangelogVersion(versionName, logVersionDate,
                                               change)
    categories = {}
    # generic category used for commits which don't fit our syntax
    miscCat = changelog.ChangelogCategory(taggedVersion, "Misc")

    for commit in repo.commitMessagesSinceTag(previousTag, toTag):
        message = commit.message
        # split into to main parts so we have the category-(subject) and body as 2 element group
        # note we can have multiple messages per commit message
        splitMessage = [i for i in REGEX_COMMIT_MESSAGE.split(message) if i]
        # validate to ensure the message as all the required syntax, split doesn't work this way it will
        # just return the body without the category etc so hence we findall.
        search = REGEX_COMMIT_MESSAGE.findall(message)

        # generic or legacy commit messages which will be added into misc category
        if not search:
            message = changelog.ChangeMessage.parseString(message)
            miscCat.messages.append(message)
            continue
        # slice the message so we loop valid messages by category+subject and body
        for i in range(0, len(splitMessage), 2):
            try:
                messageInfo, body = (splitMessage[i:i + 2])
            except ValueError:
                continue
            try:
                category = changelog.REGEX_CATEGORY.search(messageInfo).group(0).strip()
            except AttributeError:
                continue
            category = changelog.parseCategory(category)
            if category == "ignore":
                continue
            message = changelog.ChangeMessage.parseString(" ".join([messageInfo, body]))
            existingCat = categories.get(category)
            # if we already have created the category previously then just add a new message
            # otherwise create a new category and cache it.
            if existingCat:
                existingCat.messages.append(message)
            else:
                existingCat = changelog.ChangelogCategory(taggedVersion, category)
                existingCat.messages.append(message)
                categories[category] = existingCat

    if categories:
        taggedVersion.categories = list(categories.values())
    if miscCat.messages:
        taggedVersion.categories.append(miscCat)
    if taggedVersion.categories:
        change.versions[taggedVersion.label] = taggedVersion

    return change
