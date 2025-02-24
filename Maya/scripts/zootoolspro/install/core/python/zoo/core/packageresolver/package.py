import platform

import os
import shutil
import sys
import re
import copy
import tempfile

from zoo.core import errors, constants
from zoo.core.util import version as zooversion
from zoo.core.util import zlogging
from zoo.core.util import env, filesystem, modules
from zoo.core.packageresolver import requirements
from zoovendor.six import string_types

logger = zlogging.getLogger(__name__)


def isPackageDirectory(directory):
    return os.path.exists(os.path.join(directory, constants.PACKAGE_NAME))


class Variable(object):
    def __init__(self, key, values):
        self.key = key
        self.values = values
        self.originalValues = values
        envVar = os.getenv(key)
        if envVar:
            self.values.extend([i for i in envVar.split(os.pathsep)])

    def __str__(self):
        if len(self.values) > 1:
            return os.pathsep.join(self.values)
        return self.values[0]

    def split(self, sep):
        return str(self).split(sep)

    def dependencies(self):
        results = set()
        for i in self.values:
            results.union(set(re.findall(constants.DEPENDENT_FILTER, i)))
        return results

    def solve(self, tokens):
        result = self.values
        for index, value in enumerate(result):
            for key, replaceValue in tokens.items():
                result[index] = result[index].replace("".join(("{", key, "}")), replaceValue)
        self.values = result
        return result


class Package(object):
    # todo: resolve package dependencies

    @classmethod
    def fromData(cls, data):
        pack = cls()
        pack.processData(data)
        return pack

    def __init__(self, packagePath=None):
        self.path = packagePath or ""
        self.root = os.path.dirname(packagePath) if packagePath else ""
        # resolved environment
        self.environ = {}
        # cached environment
        self.cache = {}
        self.version = zooversion.LooseVersion()
        self.name = ""
        self.displayName = ""
        self.description = ""
        self.author = ""
        self.authorEmail = ""
        self.tokens = {}
        self.requirements = requirements.RequirementList()  # type: requirements.RequirementList
        self.pipRequirementsPath = ""
        self.pipRequirements = requirements.RequirementList()  # type: requirements.RequirementList
        self.tests = []
        self.documentation = {}
        # whether this package has been resolved(loaded) into the current environment
        self.resolved = False
        # package startup and shutdown script path
        self.commandPaths = []
        # the resolved environment after self.resolve is called
        self.resolvedEnv = {}

        if packagePath is not None and os.path.exists(packagePath):
            self.processFile(packagePath=packagePath)

    def setVersion(self, versionStr):
        self.version = zooversion.LooseVersion(versionStr)
        self.cache["version"] = str(self.version)

    def processFile(self, packagePath):
        self.setPath(packagePath)
        try:
            data = filesystem.loadJson(self.path)
        except ValueError:
            logger.error("Failed to load package due to possible syntax error, {}".format(packagePath))
            data = {}
        self.processData(data)

    def setPath(self, path):
        self.path = os.path.normpath(path)
        self.root = os.path.dirname(path)

    def exists(self):
        return os.path.exists(self.path)

    def processData(self, data):

        self.environ = data.get("environment", {})
        self.cache = copy.deepcopy(data)
        self.version = zooversion.LooseVersion(data.get("version", ""))
        self.name = data.get("name", "NO_NAME")
        self.displayName = data.get("displayName", "NO NAME")
        self.description = data.get("description", "NO Description")
        self.tokens = {"self": self.root,
                       "self.name": self.name,
                       "self.path": self.root,
                       "self.version": str(self.version),
                       "platform.system": platform.system().lower(),
                       "platform.arch": platform.machine()
                       }
        self.tests = Variable("tests", data.get("tests", [])).solve(self.tokens)
        self.author = data.get("author", "")
        self.authorEmail = data.get("authorEmail", "")
        self.documentation = data.get("documentation", {})
        # convert the requirements to a list of Requirement objects so we can handle versions
        reqs = data.get("requirements", [])
        convertedRequirements = list(map(requirements.Requirement.fromLine, reqs))
        self.requirements = requirements.RequirementList(convertedRequirements)
        # convert the commandPaths to absolute paths.
        self.commandPaths = Variable("commands", data.get("commands", [])).solve(self.tokens)

    def dirname(self):
        return os.path.dirname(self.path)

    def setName(self, name):
        self.name = name
        self.save()

    def delete(self):
        if os.path.exists(self.root):
            try:
                shutil.rmtree(self.root)
            except OSError:
                logger.error("Failed to remove Package: {}".format(os.path.dirname(self.name)),
                             exc_info=True,
                             extra=self.cache)

    def searchStr(self):
        try:
            return self.name + "-" + str(self.version)
        except AttributeError:
            return self.path + "- (Fail)"

    def __repr__(self):
        return self.searchStr()

    @staticmethod
    def nameForPackageNameAndVersion(packageName, packageVersion):
        return "-".join([packageName, packageVersion])

    def resolve(self, applyEnvironment=True):
        # todo: move to the resolver so dependencies can be resolved
        environ = self.environ
        if not environ:
            logger.warning("Unable to resolve package environment due to invalid package: {}".format(self.path))
            self.resolved = False
            return

        pkgVariables = {}
        for k, paths in environ.items():
            if isinstance(paths, string_types):
                var = Variable(k, [paths])
            else:
                var = Variable(k, paths)
            var.solve(self.tokens)

            if applyEnvironment:
                env.addToEnv(k, var.values)
            pkgVariables[k] = var

        if applyEnvironment and "PYTHONPATH" in pkgVariables:
            for i in pkgVariables["PYTHONPATH"].values:
                i = os.path.abspath(i)
                if i not in sys.path:
                    sys.path.append(i)
        self.resolvedEnv = pkgVariables
        logger.debug("Resolved {}: {}".format(self.name, self.root))
        self.resolved = True

    def resolveEnvPath(self, key, values, applyEnvironment=True):
        existingVar = self.resolvedEnv.get(key)
        if existingVar:
            existingVar.values += values
            existingVar.solve(self.tokens)
        else:
            existingVar = Variable(key, values)
            existingVar.solve(self.tokens)
            self.resolvedEnv[key] = existingVar
        if not applyEnvironment:
            return
        env.addToEnv(key, existingVar.values)
        if key == "PYTHONPATH":
            for i in existingVar["PYTHONPATH"].values:
                i = os.path.abspath(i)
                if i not in sys.path:
                    sys.path.append(i)

    def save(self):
        data = self.cache
        data.update(version=str(self.version),
                    name=self.name,
                    displayName=self.displayName,
                    description=self.description,
                    requirements=list(map(str, self.requirements)),
                    author=self.author,
                    authorEmail=self.authorEmail)
        return filesystem.saveJson(data, self.path, indent=4, sort_keys=True)

    def updateAndWriteVersion(self, newVersion):
        data = self.cache
        self.version = newVersion
        data["version"] = str(newVersion)
        if not self.save():
            raise IOError("Failed to save out package json: {}".format(self.path))

    def createZip(self, destinationDirectory=None):
        tempDir = destinationDirectory or tempfile.mkdtemp()
        zipPath = os.path.join(tempDir, "{}-{}.zip".format(self.name, self.version))

        zipped = filesystem.zipdir(self.dirname(), zipPath, constants.FILE_FILTER_EXCLUDE)
        if not zipped:
            logger.error("Failed to write zip to: {}".format(zipPath))
            raise OSError("Failed to write zip file to: {}".format(zipPath))

        return zipPath, tempDir

    @staticmethod
    def copyTo(package, destination, ignore=shutil.ignore_patterns(*constants.FILE_FILTER_EXCLUDE)):
        if os.path.exists(destination):
            raise errors.FileNotFoundError(destination)
        shutil.copytree(package.dirname(),
                        destination,
                        ignore=ignore)
        return Package(os.path.join(destination, constants.PACKAGE_NAME))

    def runInstall(self):
        self._runCommands("install")

    def runUninstall(self):
        self._runCommands("uninstall")

    def runStartup(self):
        self._runCommands("startup")

    def shutdown(self):
        self._runCommands("shutdown")

    def _runCommands(self, commandName):
        for commandPath in self.commandPaths:
            if not os.path.exists(commandPath):
                return
            logger.debug("Importing package {} file: {}".format(commandName, commandPath))
            filePath = os.path.realpath(commandPath)
            modules.runScriptFunction(filePath,
                                      commandName,
                                      "Running {} Function for Module: {}".format(commandName, commandPath),
                                      self)
