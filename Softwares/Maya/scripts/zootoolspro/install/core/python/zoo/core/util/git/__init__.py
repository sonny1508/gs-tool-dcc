from zoo.core.util import processes

try:
    from .gitwrapper import GitCommandError, GitRepo, InvalidGitRepositoryError, tagToChangeLog
except ImportError:
    GitCommandError, GitRepo, InvalidGitRepositoryError, tagToChangeLog = None, None, None, None


def hasGit():
    processes.checkOutput(("git", "--version"))
