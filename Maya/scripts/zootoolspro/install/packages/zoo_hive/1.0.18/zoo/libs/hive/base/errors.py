class HiveError(Exception):
    msg = ""

    def __init__(self, msg="", *args, **kwargs):
        msg = self.msg.format(str(msg))
        super(HiveError, self).__init__(msg, *args)


class HiveRigDuplicateRigsError(HiveError):
    msg = "Duplicate rigs in the scene, please use namespace filtering: {}"

    def __init__(self, dupes, *args, **kwargs):
        super(HiveRigDuplicateRigsError, self).__init__(dupes, *args, **kwargs)


class ComponentDoesntExistError(HiveError):
    msg = "Component doesn't exist in the scene: "


class ComponentGroupAlreadyExists(HiveError):
    msg = "Component group already exists for this rig instance"


class TemplateAlreadyExistsError(HiveError):
    msg = "Template path: {} already exists!"


class TemplateMissingComponents(HiveError):
    msg = "No Components specified in template: {}"


class TemplateRootPathDoesntExist(HiveError):
    msg = "Template root path doesn't exist on disk: {}"


class InvalidInputNodeMetaData(HiveError):
    msg = "InputLayer meta data is missing inputNode connection"


class InvalidOutputNodeMetaData(HiveError):
    msg = "OutputLayer meta data is missing outputNode connection"


class InitializeComponentError(HiveError):
    msg = "Failed to initialize component: {}"

    def __init__(self, componentName, *args, **kwargs):
        msg = self.msg.format(componentName)
        super(InitializeComponentError, self).__init__(msg, *args, **kwargs)


class MissingRootTransform(HiveError):
    msg = "Missing Root transform on meta node: {}"

    def __init__(self, metaName, *args, **kwargs):
        msg = self.msg.format(metaName)
        super(MissingRootTransform, self).__init__(msg, *args, **kwargs)


class RootNamespaceActiveError(HiveError):
    msg = "Current namespace is already the root"


class BuildComponentGuideUnknownError(HiveError):
    msg = "Unknown build guide error"


class BuildComponentDeformUnknownError(Exception):
    msg = "Unknown build Deform error"


class BuildComponentRigUnknownError(HiveError):
    msg = "Unknown build Rig error"


class BuildError(HiveError):
    pass


class MissingRigForNode(HiveError):
    msg = "Node: {} is not attached to a rig"


class MissingMetaNode(HiveError):
    msg = "Attached meta node is not a valid hive node"


class MissingComponentType(HiveError):
    msg = "Missing component of type: {}, from the hive component registry"

    def __init__(self, componentName, *args, **kwargs):
        self.msg = self.msg.format(componentName)
        super(MissingComponentType, self).__init__("", *args, **kwargs)


class ComponentNameError(NameError):
    msg = "Component by the name: {}, already exists!"

    def __init__(self, componentName, *args, **kwargs):
        msg = self.msg.format(componentName)
        super(ComponentNameError, self).__init__(msg, *args, **kwargs)


class MissingJoint(NameError):
    msg = "Missing Joint by id : {}"

    def __init__(self, jointId, *args, **kwargs):
        msg = self.msg.format(jointId)
        super(MissingJoint, self).__init__(msg, *args, **kwargs)


class MissingControlError(HiveError):
    msg = "Missing Control by id : {}"


class UnSupportedConnectableNode(HiveError):
    msg = "Attempting to connect to unsupported guide: '{}'"


class InvalidDefinitionAttrExpression(Exception):
    pass


class InvalidDefinitionAttrForSceneNode(Exception):
    pass
