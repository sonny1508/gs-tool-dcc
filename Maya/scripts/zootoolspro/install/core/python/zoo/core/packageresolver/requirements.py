import re

PIP_REQ_REGEX = re.compile("(.*)==(.*)")
REQ_PIP_TYPE = 0


class Requirement(object):
    @classmethod
    def fromLine(cls, line):
        req = cls(line)
        # todo: support uris etc
        pipRequires = PIP_REQ_REGEX.match(line)
        if pipRequires is not None:
            req.name, req.version = list(pipRequires.groups())
        else:  # assume name without a version
            req.name = line
        req.valid = True
        return req

    def __init__(self, line):
        self.line = line
        self.version = ""
        self.type = REQ_PIP_TYPE
        self.name = ""
        self.valid = False

    def __repr__(self):
        return "<Requirement: {}>".format(self.line)

    def __str__(self):
        return self.line

    def __eq__(self, other):
        return self.line == other.line

    def __hash__(self):
        return hash("{}=={}".format(self.name, self.version))


class RequirementList(object):
    def __init__(self, requirements=None):
        self.requirements = requirements or []
        self.requirementsDict = {}

    def __bool__(self):
        return len(self.requirements) > 0

    def __iter__(self):
        return iter(self.requirements)

    def append(self, requirement):
        if requirement in self.requirementsDict:
            return
        self.requirements.append(requirement)

    def extend(self, requirements):
        toExtend = [i for i in requirements if i not in self.requirementsDict]
        self.requirements.extend(toExtend)
        self.requirementsDict.update({i: i for i in toExtend})


def parseRequirementsFile(filePath):
    requirements = RequirementList()
    with open(filePath, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            requirements.append(Requirement.fromLine(line))
    return requirements


def mergeRequirements(requirements):
    return list(set(requirements))
