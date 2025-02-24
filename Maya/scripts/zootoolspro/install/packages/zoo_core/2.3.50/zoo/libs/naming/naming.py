"""Generic naming configuration handling

Naming works off a json based configuration which contains rules and tokens.
see config.json under the test folder formatting example.

Naming management provides a useful way to provide strict rules over how a name is formatted and generated.
A rule contain to important pieces a Name i.e. myRule and an expression ie. "{area}_{side}_noToken".
See :class:`NameManager` for working with the config.

"""
import re
import os

from zoo.core.util import filesystem
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)



class NameManager(object):
    """The name manager deals with the manipulation of a string based on an expression allowing for a formalised
    naming convention, we use the terms 'rule' and 'tokens' throughout the class to describe the logic.
    rules are just a basic expression like so '{side}_{area}_{counter}_{type}', the '_' isn't necessary for any logic.
    the characters within the curly brackets are tokens which will be replaced when it's resolved.

    You can add tokens and values in memory per instance, or you can add it to the config JSON file.

    :param config: The config to load if required.
    :type config: dict or None
    :param configPath: The json absolute json file path containing rules and tokens.
    :type configPath: str or None
    """
    _refilter = r"(?<={)[^}]*"
    _reFieldResolver = r"(_*{field}_*)"
    @classmethod
    def fromPath(cls, configPath):
        """Loads the provided configPath and resets this instance with said paths.

        :param configPath: The absolute config path to a valid json file to load.
        :type configPath: str
        """
        if not os.path.exists(configPath):
            return
        config = filesystem.loadJson(configPath)
        return cls(config, configPath)

    @classmethod
    def flatten(cls, configuration):
        """

        :param configuration:
        :type configuration: :class:`NameManager`
        :return:
        :rtype:
        """
        parentConfig = configuration.parentConfig
        fields = {field.name: field for field in configuration.fields(recursive=True)}

        for field in parentConfig.fields(recursive=True):
            match = fields.get(field.name)
            match.update(field)

    def __init__(self, config=None, configPath=None):
        self.originalConfig = config or None
        self.configPath = configPath or ""
        self._rules = set()  # type: set[Rule]
        self._fields = []  # type: list[Field]
        self.name = ""
        self.description = ""
        self.parentConfig = None  # type: NameManager or None
        if config is not None:
            self._parseConfig(config)

    def __repr__(self):
        return "<NameManager {}>(name={}, path={})".format(id(self), self.name, self.configPath)

    def changes(self, target=None):
        target = target or self.parentConfig
        assert target is not None, "Source must be provided"
        assert target != self, "Source can't be the same"
        diff = NamingChanges(self, target)
        diff.compute()
        return diff

    def ruleCount(self, recursive=False):
        """Returns the count rule count on the config.

        :param recursive: Whether to recursively search the parent config hierarchy if the parent is valid.
        :type recursive: bool
        :return: The total rule count.
        :rtype: int
        """
        count = len(self._rules)
        if recursive and self.parentConfig is not None:
            count += self.parentConfig.ruleCount()
        return count

    def fieldCount(self, recursive=False):
        """Returns the count field count on the config.

        :param recursive: Whether to recursively search the parent config hierarchy if the parent is valid.
        :type recursive: bool
        :return: The total field count.
        :rtype: int
        """
        count = len(self._fields)
        if recursive and self.parentConfig is not None:
            count += self.parentConfig.fieldCount()
        return count

    def rules(self, recursive=True):
        """Returns all the currently active rules

        :param recursive: Whether to recursively search the parent config hierarchy if the parent is valid.
        :type recursive: bool
        :return: a list of active rule names
        :rtype: list[:class:`Rule`]
        """
        visited = set()
        for rule in self._rules:
            visited.add(rule.name)
            yield rule
        if not recursive or not self.parentConfig:
            return
        for rule in self.parentConfig.rules():
            if rule.name in visited:
                continue
            yield rule
            visited.add(rule.name)

    def hasRule(self, name, recursive=True):
        """Whether the config has the given rule by name.

        :param name: The rule name.
        :type name: str
        :param recursive: If True then the parent config will be searched as the fallback.
        :type recursive: bool
        :rtype: bool
        """
        return self.rule(name, recursive=recursive) is not None

    def addRule(self, name, expression, description, exampleFields, creator=None, recursive=True):
        """Adds the provided rule to the config. If the rule already exists then it will be
        updated.

        :param name: The rule name to add or update.
        :type name: str
        :param expression: The new expression string.
        :type expression: str
        :param description: The rule description
        :type description: str
        :param exampleFields: A dict containing an example KeyValues for the expression fields.
        :type exampleFields: dict
        :param creator: The rule creator name
        :type creator: str
        :param recursive: If True then the parent config will be searched as the fallback.
        :type recursive: bool
        """
        if not self.hasRule(name, recursive=recursive):
            logger.debug("Adding new rule: {}".format(name))
            newRule = Rule(name, creator, description, expression, exampleFields=exampleFields)
            self._rules.add(newRule)
            return newRule

    def rule(self, name, recursive=True):
        """Returns the rule info data for the given Rule.

        :param name: The rule name ie. "object"
        :type name: str
        :param recursive: If True then the parent config will be searched as the fallback.
        :type recursive: bool
        :return: The Rule Instance or None if not found
        :rtype: :class:`Rule` or None
        """
        for rule in self.rules(recursive):
            if rule.name == name:
                return rule

    def ruleFromExpression(self, expression, recursive=True):
        """Given the expression return the matching expression name.

        :param recursive: If True then the parent config will be searched as the fallback.
        :type recursive: bool
        :param expression: The expression format ie. "{my}_{expression}"
        :type expression: str
        :return: The rule name which matches the expression.
        :rtype: :class:`Rule`
        """
        for rule in self.rules(recursive=recursive):
            if rule.expression == expression:
                return rule

    def deleteRule(self, rule):
        """Deletes the given rule from the config, ignoring the parent hierarchy.

        :param rule: The rule to delete from the config
        :type rule: :class:`Rule`
        :return: Whether the rule was deleted successfully.
        :rtype: bool
        """
        try:
            self._rules.remove(rule)
            logger.debug("Rule Deleted: {}".format(rule.name))
        except ValueError:
            return False
        return True

    def deleteRuleByName(self, name):
        """Deletes the given rule  by name from the config, ignoring the parent hierarchy.

        :param name: The rule name ie. "object"
        :type name: str
        :return: Whether the rule was deleted successfully.
        :rtype: bool
        """
        toRemove = None
        for index, rule in enumerate(self.rules(recursive=False)):
            if rule.name == name:
                toRemove = rule
                break
        return self.deleteRule(toRemove)

    def updateRules(self, rules):
        """Updates the configs rule list with the provided rules. Rules are stored as a set, so
        we use set.update.

        :param rules: A list of rules to add to the configs rules.
        :type rules: list[:class:`Rule`]
        """
        self._rules.update(set(rules))

    def clearRules(self):
        """Clears All current rules for the config.
        """
        self._rules.clear()

    def clearFields(self):
        """Clears All current fields for the config.
        """
        self._fields.clear()

    def setRules(self, rules):
        """Overrides the current rules with the provided ones.

        :param rules: The Rules to set for the config.
        :type rules: set[:class:`Rule`]
        """
        self._rules = rules

    def field(self, name, recursive=True):
        """Returns the field table for the given name.

        If recursive id true then if the current config doesn't contain the token then
        the parent config if specified will be searched.

        :param name: The token name to query.
        :type name: str
        :param recursive: If True then the parent config will be searched as the fallback.
        :type recursive: bool
        :return: The token table.
        :rtype: :class:`Field`
        """
        for field in self.fields(recursive=recursive):
            if field.name == name:
                return field

    def fields(self, recursive=True):
        """Generator function which returns all fields on the config.

        :param recursive: If True then the parent config will be searched as well
        :type recursive: bool
        :rtype: list[:class:`Field`]
        """
        visited = set()
        for field in self._fields:
            visited.add(field.name)
            yield field
        if recursive and self.parentConfig is not None:
            for field in self.parentConfig.fields(recursive=recursive):
                if field.name in visited:
                    continue
                visited.add(field.name)
                yield field

    def addField(self, name, fields):
        """Adds the token with the value and sets the default.

        :param name: The new token name.
        :type name: str
        :param fields: the dict of key value pairs.
        :type fields: dict[str,str]
        :rtype: :class:`Field`
        """
        if self.hasField(name):
            return
        newField = Field.fromDict({"name": name, "description": "", "table": fields})
        self._fields.append(newField)
        logger.debug("Added field: {}".format(name))
        return newField

    def hasField(self, name, recursive=True):
        """Checks if the token exists in the config.

        :param name: The field name to query
        :type name: str
        :param recursive: If True then the parent config will be searched as the fallback
        :type recursive: bool
        :rtype: bool
        """
        return self.field(name, recursive=recursive) is not None

    def hasFieldKey(self, name, value, recursive=True):
        """Checks if the value exists with in the token table.

        :param name: The field name to query.
        :type name: str
        :param value: The token table value.
        :type value: str
        :param recursive: If True then the parent config will be searched as the fallback
        :type recursive: bool
        :rtype: bool
        """
        field = self.field(name, recursive=recursive) or []
        return value in field

    def setFields(self, fields):
        """Overrides the current fields with the provided ones.

        :param fields: The fields to set for the config.
        :type fields: set[:class:`Field`]
        """
        self._fields = fields

    def expressionFromString(self, name):
        """Returns the expression from the name, if the name cannot be resolved then we raise ValueError,
        If we resolve to multiple expressions then we raise ValueError. Only one expression is possible.
        To resolve a name, all tokens must exist within the config, and we must be able to resolve more
        than 50% for an expression for it to be viable.
        
        :param name: the string the resolve.
        :type name: str
        :return: the config expression eg. {side}_{type}{section}.
        :rtype: str
        """
        expressedName = []
        for field in self.fields():
            tName = field.name
            for keyValue in field.keyValues():
                if tName not in expressedName and keyValue.name in name:
                    expressedName.append(tName)
                    break
        # we don't have an exact match so lets find which expression is the most probable
        possibles = set()
        tokenizedLength = len(expressedName)
        for rule in self.rules(recursive=True):
            expression = rule.expression
            expressionFields = re.findall(NameManager._refilter, expression)
            totalCount = 0
            for tokName in expressedName:
                if tokName in expressionFields:
                    totalCount += 1
            if totalCount > tokenizedLength / 2:
                possibles.add((expression, totalCount))
        if not possibles:
            raise ValueError("Could not resolve name: {} to an existing expression".format(name))

        maxPossible = max([i[1] for i in possibles])
        truePossibles = []
        # filter out the possibles down to just the best resolved
        for possible, tc in iter(possibles):
            if tc == maxPossible:
                truePossibles.append(possible)
        if len(truePossibles) > 1:
            raise ValueError("Could not Resolve name: {}, due too many possible expressions".format(name))
        return truePossibles[0]

    def resolve(self, rule, fields):
        """Resolves the given rule expression using the provided fields as values.
        Each field value will be converted via the config's field table if a field or field key doesn't exist
        then the provided value will be used instead.

        :param rule: The rule Name.
        :type rule: str
        :param fields: The fields key and values to set for the expression.
        :type fields: dict
        :return: The formatted string. tokenAValue_tokenBValue_anim.
        :rtype: str
        """
        try:
            expression = self.rule(rule).expression
        except AttributeError:
            raise ValueError("Rule: {} isn't a valid registered name".format(rule))
        expressionFields = set(re.findall(NameManager._refilter, expression))
        newStr = expression
        missingKeys = set()
        for field in expressionFields:  # type: str
            tokenValue = fields.get(field)  # type: Field or None
            resolvedField = self.field(field, recursive=True)
            if tokenValue is None:
                # if the field is strict then we want to fail otherwise we remove the field from the
                # string with an empty string.
                if resolvedField.strict:
                    missingKeys.add(field)
                    continue
                remappedValue = "_"
                pattern = NameManager._reFieldResolver.format(field=surroundFieldExpr(field))
            else:
                try:
                    remappedValue = resolvedField.valueForKey(tokenValue, tokenValue)
                except AttributeError:  # hit when the field doesn't exist, so we use the provided value
                    remappedValue = tokenValue
                if not remappedValue:
                    # basically empty string so removes the field and makes sure only
                    # one underscore exists
                    pattern = NameManager._reFieldResolver.format(field=surroundFieldExpr(field))
                    remappedValue = "_"
                else:
                    pattern = surroundFieldExpr(field)
            newStr = re.sub(pattern, remappedValue, newStr)
        if missingKeys:
            raise ValueError("Missing Expression fields, rule: {}, fields:{}".format(rule, missingKeys))
        return newStr

    def serialize(self):
        data = {"name": self.name,
                "description": self.description,
                "rules": [i.serialize() for i in self._rules],
                "fields": [i.serialize() for i in self._fields]}
        return data

    def refresh(self):
        """Loads a fresh version of the config based on the original config paths.
        """
        self._load(self.configPath)

    def _load(self, configPath):

        if not os.path.exists(configPath) or not configPath.endswith(".json"):
            return
        self.configPath = configPath
        self.originalConfig = filesystem.loadJson(configPath)
        self._parseConfig(self.originalConfig)

    def _parseConfig(self, config):
        self._fields = [Field.fromDict(fieldMap) for fieldMap in config.get("fields", [])]
        self._rules = set(Rule.fromDict(rule) for rule in config.get("rules", []))
        self.name = config.get("name", "")


class NamingChanges(object):
    """NamingChanges handles creating a new naming config based on the changes in the source config
    vs the target config.

    :param source: The source config where it's local rules/fields are diffed against the target.
    :type source: :class:`NameManager`
    :param target: Commonly the parent config of the source, used to check changes for the source.
    :type target: :class:`NameManager`
    """

    def __init__(self, source, target):

        self.source = source
        self.target = target  # if target.parentConfig is None else target.parentConfig
        self.diff = NameManager()

    def hasChanges(self):
        """Whether There's any changes made on the source compared to the target.

        :rtype: bool
        """
        return self.diff.ruleCount(recursive=False) != 0 or self.diff.fieldCount() != 0

    def serialize(self):
        """Returns the changes for the source based on the target.

        :rtype: dict
        """
        return self.diff.serialize()

    def compute(self):
        targetRules = {i.name: i for i in self.target.rules(recursive=True)}
        targetFields = {i.name: i for i in self.target.fields(recursive=True)}
        diffRules = []
        diffFields = []
        for sourceRule in self.source.rules(recursive=False):
            targetRule = targetRules.get(sourceRule.name)
            if targetRule is None:
                continue
            elif sourceRule.expression == targetRule.expression:
                continue
            diffRules.append(sourceRule)

        for sourceField in self.source.fields(recursive=False):
            targetField = targetFields.get(sourceField.name)
            if targetField is None:
                continue
            sourceKeyValues = {i.name: i.value for i in sourceField.keyValues()}
            targetKeyValues = {i.name: i.value for i in targetField.keyValues()}
            if sourceKeyValues == targetKeyValues:
                continue
            diffFields.append(sourceField)
        self.diff.setFields(diffFields)
        self.diff.setRules(diffRules)
        self.diff.name = self.source.name
        self.diff.description = self.source.description
        self.diff.configPath = self.source.configPath

        return self.diff


class Rule(object):
    """Encapsulates a rule expression.

    :param name:  The Rule name.
    :type name: str
    :param creator: The person who created the rule
    :type creator: str
    :param description: The description of what the expression represents, should include example.
    :type description: str
    :param expression: The Expression to use which can contain fields using the format, "{myField}_{anotherField}"
    :type expression: str
    :param exampleFields: example fields for the expression which is used in UIs for generating examples.
    :type exampleFields: dict
    """

    @classmethod
    def fromDict(cls, data):
        return cls(data["name"],
                   data.get("creator", ""),
                   data.get("description", ""),
                   data["expression"],
                   data.get("exampleFields", {}))

    def __init__(self, name, creator, description, expression, exampleFields):
        self.name = name
        self.creator = creator
        self.description = description
        self.expression = expression
        self.exampleFields = exampleFields

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, Rule):
            return False
        return self.name == other.name

    def __ne__(self, other):
        if isinstance(other, Rule):
            return True
        return self.name != other.name

    def __repr__(self):
        return "Rule(name={}, expression={})".format(self.name, self.expression)

    def fields(self):
        """Returns all the fields within the current expression.

        :rtype: list[str]
        """
        return re.findall(NameManager._refilter, self.expression)

    def serialize(self):
        """Returns the raw data for the rule.

        .. code-block:: python

            myRule = myRule.fromData({'name': 'componentName',
                                    'creator': 'ZooToolsPro',
                                    'description': 'Some description',
                                    'expression': '{componentName}_{side}',
                                    'exampleFields': {'componentName': 'arm', 'side': 'L'}})
            data = myRule.serialize()
            # {'name': 'componentName',
            # 'creator': 'ZooToolsPro',
            # 'description': 'Some description',
            # 'expression': '{componentName}_{side}',
            # 'exampleFields': {'componentName': 'arm', 'side': 'L'}}


        :rtype: dict
        """
        return {"name": self.name,
                "creator": self.creator,
                "description": self.description,
                "expression": self.expression,
                "exampleFields": self.exampleFields}


class Field(object):
    @classmethod
    def fromDict(cls, data):
        perms = {i["name"]: i for i in data.get("permissions", [])}
        keyValues = [KeyValue(k, v, protected=k in perms) for k, v in data.get('table', {}).items()]

        newToken = cls(data["name"], data.get("description", ""),
                       data.get("permissions", []), keyValues)
        return newToken

    def __init__(self, name, description, permissions, keyValues):
        self._tokenValues = set(keyValues)  # type: set[KeyValue]
        self.name = name
        self.description = description
        self.permissions = {i["name"]: i for i in permissions}
        self.strict = False

    def __iter__(self):
        return iter(self._tokenValues)

    def __len__(self):
        return len(self._tokenValues)

    def __repr__(self):
        return "Field(name={})".format(self.name)

    def count(self):
        """Returns the number of KeyValue instances for the field.

        :rtype: int
        """
        return len(self._tokenValues)

    def hasKey(self, key):
        """Whether the KeyValue by it's name exists.

        :param key: The key to check for.
        :type key: str
        :rtype: bool
        """
        return self.keyValue(key) is not None

    def add(self, name, value, protected=False):
        """Adds a new KeyValue to the field.

        :param name: The new keyValue name.
        :type name: str
        :param value: The new KeyValue Value. Should be a string.
        :type value: str
        :param protected: Whether this KeyValue is protected from deletion and renaming.
        :type protected: bool
        :return: Returns the newly created KeyValue Instance
        :rtype: :class:`KeyValue`
        """
        uniqueName = name
        existingNames = set(i.name for i in self._tokenValues)
        index = 1
        while uniqueName in existingNames:
            uniqueName = "".join((uniqueName, str(index).zfill(1)))

        keyValue = KeyValue(uniqueName, value, protected)
        self._tokenValues.add(keyValue)
        return keyValue

    def update(self, field):
        """Updates(merge) the provided field KeyValues with this field instance KeyValues.

        :param field: The Field instance to update this field.
        :type field: :class:`Field`
        """
        self._tokenValues.update(set(field))

    def remove(self, key):
        """Removes the KeyValue instance from the field by the key.

        :param key: The KeyValue name to remove.
        :type key: str
        :return: Whether removal was successful
        :rtype: bool
        """
        foundToken = self.keyValue(key)
        if foundToken is not None and not foundToken.protected:
            self._tokenValues = self._tokenValues - {foundToken}
            return True
        return False

    def serialize(self):
        tokenValues = {i.name: i.value for i in self._tokenValues}
        permissions = [{"name": i.name} for i in self._tokenValues if i.protected]
        return {"name": self.name,
                "description": self.description,
                "permissions": permissions,
                "table": tokenValues}

    def valueForKey(self, key, defaultValue=None):
        """Returns the field value for the key within the table

        :param key: The key to search for
        :type key: str
        :rtype: str
        """
        for token in self._tokenValues:
            if token.name == key:
                return token.value
        return defaultValue

    def keyForValue(self, value):
        """Returns the field key from the table based on the compare.

        :param value: The value to search from the table.
        :type value: str
        :rtype: str
        """
        for token in self._tokenValues:
            if token.value == value:
                return token.name
        return ""

    def keyValues(self):
        """Generator Function which returns each keyValue object in the table.

        :rtype: Iterable[:class:`KeyValue`]
        """
        for keyValue in self._tokenValues:
            yield keyValue

    def keyValue(self, key):
        """Returns the KeyValue object for the given key.

        :param key: The key within the table to return.
        :type key: str
        :rtype: :class:`KeyValue`
        """
        for keyValue in self._tokenValues:
            if keyValue.name == key:
                return keyValue


class KeyValue(object):
    """KeyValue class is Responsible for a single key/value pair within a naming field.

    The Key Value can also be marked as protected in which case the value can still change
    but can't be renamed or deleted.

    :param name: The name for the KeyValue.
    :type name: str
    :param value: The value for the keyValue.
    :type value: str
    :param protected: if Protected Than this KeyValue can't be deleted or renamed, but it's value can change.
    :type protected:  bool
    """

    def __init__(self, name, value, protected=False):
        self._name = name
        self.value = value
        self.protected = protected

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        """Sets the name for the KeyValue only if it's not protected.

        :param value: The new Name for the KeyValue
        :type value: str
        """
        if self.protected:
            return
        self._name = value

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, KeyValue):
            return False
        return self.name == other.name and self.value == other.value

    def __ne__(self, other):
        if not isinstance(other, KeyValue):
            return True
        return self.name != other.name and self.value != other.value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "KeyValue(name={},value={})".format(self.name, self.value)

    def serialize(self):
        return {"name": self.name,
                "value": self.value}

def surroundFieldExpr(fieldValue):
    """Given a field value, returns the expression format for the field.

    :param fieldValue:  The field value to surround with the expression format.
    :type fieldValue: Str
    :return: The field value surrounded by "{}" e.g. {fieldValue}
    :rtype: str
    """
    return "{" + fieldValue + "}"
