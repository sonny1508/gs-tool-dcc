from functools import partial

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.core.util import env

from zoo.libs.maya.cmds.objutils import filtertypes
from zoo.libs.maya.cmds.objutils import namehandling as names
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output

SUFFIX = "suffix"
PREFIX = "prefix"

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

NAMESPACE_COMBO_LIST = ("Add/Replace", "Remove")
RENUMBER_COMBO_LIST = ("Replace", "Append", "Change Pad")


class ZooRenamer(toolsetwidget.ToolsetWidget):
    id = "zooRenamer"
    uiData = {"label": "Zoo Renamer",
              "icon": "zooRenamer",
              "tooltip": "Tools For Renaming Objects",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-zoo-renamer/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = RenamerCompactWidget(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        self.advancedWidget = RenamerAdvancedWidget(parent=self, properties=self.properties, toolsetWidget=self)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.allDisableWidgets = [self.advancedWidget.atIndexTxt, self.advancedWidget.indexCombo,
                                  self.advancedWidget.indexTxt, self.advancedWidget.atIndexBtn,
                                  self.advancedWidget.indexLabel, self.advancedWidget.removeAllNumbersBtn,
                                  self.advancedWidget.removeTrailingNumbersBtn]
        for widget in self.widgets():  # add from both ui modes
            self.allDisableWidgets += [widget.indexShuffleNegBtn, widget.indexShuffleLabel,
                                       widget.indexShufflePosBtn, widget.indexShuffleTxt,
                                       widget.indexShuffleTxt, widget.renumberBtn, widget.renumberLabel,
                                       widget.renumberCombo, widget.renumberPaddingInt, widget.forceBtn,
                                       widget.forceRenameTxt, widget.forcePaddingInt]
        self.displaySwitched.connect(self.updateFromProperties)
        self.connectionsRenamer()

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  :class:`RenamerWidgets`
        """
        return super(ZooRenamer, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[:class:`RenamerCompactWidget` or :class:`RenamerAdvancedWidget`]
        """
        return super(ZooRenamer, self).widgets()

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        """Used to store and update UI data

        For use in the GUI use:
            current value: self.properties.itemName.value
            default value (automatic): self.properties.itemName.default

        :return properties: special dictionary used to save and update all GUI widgets
        :rtype properties: list(dict)
        """
        return [{"name": "search", "value": ""},
                {"name": "replace", "value": ""},
                {"name": "prefix", "value": ""},
                {"name": "prefixCombo", "value": 0},
                {"name": "suffix", "value": ""},
                {"name": "suffixCombo", "value": 0},
                {"name": "atIndex", "value": ""},
                {"name": "indexCombo", "value": 0},
                {"name": "index", "value": -2},
                {"name": "renumberCombo", "value": 0},
                {"name": "padding", "value": 2},
                {"name": "optionsRadio", "value": 0},
                {"name": "objFilterCombo", "value": 0},
                {"name": "namespaceCombo", "value": 0},
                {"name": "namespace", "value": ""},
                {"name": "shapesBox", "value": 1},
                {"name": "shuffleIndex", "value": -1}]

    # ------------------
    # UI LOGIC
    # ------------------

    def disableWidgetsInAllMode(self, ):
        radioOptionsInt = self.properties.optionsRadio.value
        if radioOptionsInt == 2:  # disable while in delete mode (self.properties.indexCombo.value)
            for widget in self.allDisableWidgets:
                widget.setDisabled(True)
        else:
            for widget in self.allDisableWidgets:
                widget.setDisabled(False)
            if self.properties.indexCombo.value == 2:  # keep the atIndexTxt disabled if remove mode
                self.advancedWidget.atIndexTxt.setDisabled(True)

    def disableEnableAtIndexTxt(self, event):
        """Disables the 'Add At Index' lineEdit while the combo box is in 'Remove' mode

        :param event: Event with all the values related to the change.
        :type event: zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent
        :return:
        :rtype:
        """
        if event.index == 2:  # disable while in delete mode (self.properties.indexCombo.value)
            self.advancedWidget.atIndexTxt.setDisabled(True)
        else:
            self.advancedWidget.atIndexTxt.setDisabled(False)

    def populatePrefixSuffix(self, comboObject, sptype=SUFFIX):
        """Adds the suffix/prefix text into the prefix or suffix lineEdits when changing the prefix/suffix combo boxes

        :param comboObject: The combo object, can get index and text comboObject.index, comboObject.text
        :type comboObject: object
        :param comboText: The combo value as a string
        :type comboText: str
        :param sptype: "prefix" or "suffix", switches the mode of the method
        :type sptype: str
        """
        text = comboObject.text
        if comboObject.text == filtertypes.SUFFIXLIST[0]:  # then it's "Select..." so do nothing
            return
        textParts = text.split("'")

        if sptype == names.SUFFIX:
            textParts = text.split("'")
            self.properties.suffixTxt.value = "_{}".format(textParts[-2])
        if sptype == names.PREFIX:
            self.properties.prefixTxt.value = "{}_".format(textParts[-2])
        self.updateFromProperties()

    def openNamespaceEditor(self):
        """Opens the Namespace Editor"""
        import maya.mel as mel
        mel.eval('namespaceEditor')

    def openReferenceEditor(self):
        """Opens the Reference Editor"""
        import maya.mel as mel
        mel.eval('tearOffRestorePanel "Reference Editor" referenceEditor true')

    # ------------------
    # CORE LOGIC
    # ------------------

    def setFilterVars(self):
        """sets variables for the filter radio box used in the filterTypes.filterByNiceType() function

        :return searchHierarchy: search hierarchy option
        :rtype searchHierarchy: bool
        :return selectionOnly: selectionOnly option
        :rtype selectionOnly: bool
        """
        checkedRadioNumber = self.properties.optionsRadio.value
        if checkedRadioNumber == 0:  # selection
            searchHierarchy = False
            selectionOnly = True
        elif checkedRadioNumber == 1:  # hierarchy
            searchHierarchy = True
            selectionOnly = True
        else:  # all
            searchHierarchy = False
            selectionOnly = False
        return searchHierarchy, selectionOnly

    @toolsetwidget.ToolsetWidget.undoDecorator
    def forceRename(self):
        searchHierarchy, selectionOnly = self.setFilterVars()
        if not searchHierarchy and not selectionOnly:
            output.displayWarning("The `All` filter cannot be used with force name, "
                                  "all nodes in the scene may be named with the same names.")
            return
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        forceTxt = self.properties.forceRenameTxt.value
        if forceTxt == "":
            output.displayWarning("Please type force text")
            return
        if ":" in forceTxt:
            output.displayWarning("':' is an illegal character in regular Maya names, use the namespaces instead")
            return
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:  # If compact mode then search all nodes
            niceNameType = filtertypes.ALL
        names.forceRenameListSel(self.properties.forceRenameTxt.value,
                                 niceNameType,
                                 padding=self.properties.forcePaddingInt.value,
                                 renameShape=True,
                                 hierarchy=searchHierarchy,
                                 message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def searchReplace(self):
        """Prefix and suffix logic, see names.searchReplaceFilteredType() for documentation"""
        searchHierarchy, selectionOnly = self.setFilterVars()
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        searchTxt = self.properties.searchTxt.value
        replaceTxt = self.properties.replaceTxt.value
        if searchTxt == "":
            output.displayWarning("Please type search text")
            return
        if ":" in replaceTxt or ":" in searchTxt:
            output.displayWarning("':' is an illegal character in regular Maya names, use the namespaces instead")
            return
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.searchReplaceFilteredType(searchTxt,
                                            replaceTxt,
                                            filtertypes.ALL,
                                            renameShape=True,
                                            searchHierarchy=searchHierarchy,
                                            selectionOnly=selectionOnly,
                                            dag=False,
                                            removeMayaDefaults=True,
                                            transformsOnly=True,
                                            message=True)
            return
        # Advanced UI mode -----------------------------
        names.searchReplaceFilteredType(searchTxt,
                                        replaceTxt,
                                        niceNameType,
                                        renameShape=self.properties.autoShapesBox.value,
                                        searchHierarchy=searchHierarchy,
                                        selectionOnly=selectionOnly,
                                        dag=False,
                                        removeMayaDefaults=True,
                                        transformsOnly=True,
                                        message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def addPrefixSuffix(self, sptype=SUFFIX):
        """Prefix and suffix logic, see names.prefixSuffixFilteredType() for documentation

        :param sptype: "suffix" or "prefix"
        :type sptype: str
        """
        searchHierarchy, selectionOnly = self.setFilterVars()
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        if sptype == names.SUFFIX:
            prefixSuffix = self.properties.suffixTxt.value
        else:
            prefixSuffix = self.properties.prefixTxt.value
        if prefixSuffix == "":  # nothing entered
            output.displayWarning("Please type prefix or suffix text")
            return
        if prefixSuffix[0].isdigit() and sptype == names.PREFIX:  # first letter is a digit which is illegal in Maya
            output.displayWarning("Maya names cannot start with numbers")
            return

        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.prefixSuffixFilteredType(prefixSuffix,
                                           niceNameType,
                                           sptype=sptype,
                                           renameShape=True,
                                           searchHierarchy=searchHierarchy,
                                           selectionOnly=selectionOnly,
                                           dag=False,
                                           removeMayaDefaults=True,
                                           transformsOnly=True,
                                           message=True)
            return
        # Advanced UI mode -----------------------------
        names.prefixSuffixFilteredType(prefixSuffix,
                                       niceNameType,
                                       sptype=sptype,
                                       renameShape=self.properties.autoShapesBox.value,
                                       searchHierarchy=searchHierarchy,
                                       selectionOnly=selectionOnly,
                                       dag=False,
                                       removeMayaDefaults=True,
                                       transformsOnly=True,
                                       message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def autoPrefixSuffix(self, sptype=SUFFIX):
        """Auto prefix logic, see names.autoPrefixSuffixFilteredType() for documentation

        :param sptype: "suffix" or "prefix"
        :type sptype: str
        """
        searchHierarchy, selectionOnly = self.setFilterVars()
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.autoPrefixSuffixFilteredType(niceNameType,
                                               sptype=sptype,
                                               renameShape=True,
                                               searchHierarchy=searchHierarchy,
                                               selectionOnly=selectionOnly,
                                               dag=False,
                                               removeMayaDefaults=True,
                                               transformsOnly=True,
                                               message=True)
            return
        # Advanced UI mode -----------------------------
        names.autoPrefixSuffixFilteredType(niceNameType,
                                           sptype=sptype,
                                           renameShape=self.properties.autoShapesBox.value,
                                           searchHierarchy=searchHierarchy,
                                           selectionOnly=selectionOnly,
                                           dag=False,
                                           removeMayaDefaults=True,
                                           transformsOnly=True,
                                           message=True)

    def renumberUI(self):
        """Method called by the renumber button, combo could be in "Change Pad" or "Append" modes, so run logic
        """
        renumberOptions = RENUMBER_COMBO_LIST[self.properties.renumberCombo.value]
        if renumberOptions == "Change Pad":
            self.changePadding()
            return
        if renumberOptions == "Append":
            self.renumber(trailingOnly=False)
        else:
            self.renumber(trailingOnly=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def renumber(self, trailingOnly=False):
        """Renumber logic
        See names.renumberFilteredType() for filter documentation"""
        searchHierarchy, selectionOnly = self.setFilterVars()
        if not searchHierarchy and not selectionOnly:  # all so bail
            output.displayWarning("Renumber must be used with 'Selected' or 'Hierarchy', not 'All'")
            return
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.renumberFilteredType(filtertypes.ALL,
                                       removeTrailingNumbers=trailingOnly,
                                       padding=self.properties.renumberPaddingInt.value,
                                       addUnderscore=True,
                                       renameShape=True,
                                       searchHierarchy=searchHierarchy,
                                       selectionOnly=selectionOnly,
                                       dag=False,
                                       removeMayaDefaults=True,
                                       transformsOnly=True,
                                       message=True)
            return
        # Advanced UI mode -----------------------------
        if not searchHierarchy and not selectionOnly:  # all so bail
            output.displayWarning("Renumber must be used with 'Selected' or 'Hierarchy', not 'All'")
            return
        names.renumberFilteredType(niceNameType,
                                   removeTrailingNumbers=trailingOnly,
                                   padding=self.properties.renumberPaddingInt.value,
                                   addUnderscore=True,
                                   renameShape=self.properties.autoShapesBox.value,
                                   searchHierarchy=searchHierarchy,
                                   selectionOnly=selectionOnly,
                                   dag=False,
                                   removeMayaDefaults=True,
                                   transformsOnly=True,
                                   message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def removeNumbers(self, trailingOnly=True):
        """Removing number logic,
        See names.removeNumbersFilteredType() for filter documentation"""
        searchHierarchy, selectionOnly = self.setFilterVars()
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        names.removeNumbersFilteredType(niceNameType,
                                        trailingOnly=trailingOnly,
                                        renameShape=self.properties.autoShapesBox.value,
                                        searchHierarchy=searchHierarchy,
                                        selectionOnly=selectionOnly,
                                        dag=False,
                                        removeMayaDefaults=True,
                                        transformsOnly=True,
                                        message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def changePadding(self):
        """Change padding logic
        See names.changeSuffixPaddingFilter() for filter documentation"""
        searchHierarchy, selectionOnly = self.setFilterVars()
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        if not searchHierarchy and not selectionOnly:  # all so bail
            output.displayWarning("Renumber must be used with 'Selected' or 'Hierarchy', not 'All'")
            return
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.changeSuffixPaddingFilter(filtertypes.ALL,
                                            padding=self.properties.renumberPaddingInt.value,
                                            addUnderscore=True,
                                            renameShape=True,
                                            searchHierarchy=searchHierarchy,
                                            selectionOnly=selectionOnly,
                                            dag=False,
                                            removeMayaDefaults=True,
                                            transformsOnly=True,
                                            message=True)
            return
        # Advanced UI mode -----------------------------
        names.changeSuffixPaddingFilter(niceNameType,
                                        padding=self.properties.renumberPaddingInt.value,
                                        addUnderscore=True,
                                        renameShape=self.properties.autoShapesBox.value,
                                        searchHierarchy=searchHierarchy,
                                        selectionOnly=selectionOnly,
                                        dag=False,
                                        removeMayaDefaults=True,
                                        transformsOnly=True,
                                        message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def uniqueNames(self):
        """Unique names logic,
        See names.forceUniqueShortNameFiltered() for filter documentation"""
        searchHierarchy, selectionOnly = self.setFilterVars()
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.forceUniqueShortNameFiltered(filtertypes.ALL,
                                               padding=self.properties.renumberPaddingInt.value,
                                               shortNewName=True,
                                               renameShape=True,
                                               searchHierarchy=searchHierarchy,
                                               selectionOnly=selectionOnly,
                                               dag=False,
                                               removeMayaDefaults=True,
                                               transformsOnly=True,
                                               message=True)
            return
        # Advanced UI mode -----------------------------
        names.forceUniqueShortNameFiltered(niceNameType,
                                           padding=self.properties.renumberPaddingInt.value,
                                           shortNewName=True,
                                           renameShape=self.properties.autoShapesBox.value,
                                           searchHierarchy=searchHierarchy,
                                           selectionOnly=selectionOnly,
                                           dag=False,
                                           removeMayaDefaults=True,
                                           transformsOnly=True,
                                           message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def editIndex(self, removeSuffix=False, removePrefix=False):
        """

        See names.searchReplaceFilteredType() for filter documentation
        """
        searchHierarchy, selectionOnly = self.setFilterVars()
        if not searchHierarchy and not selectionOnly:  # all so bail
            output.displayWarning("Move By Index must be used with 'Selected' or 'Hierarchy', not 'All'")
            return
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        text = ""
        if not removePrefix and not removeSuffix:  # then use the GUI settings
            modeInt = self.properties.indexCombo.value
            text = self.properties.atIndexTxt.value
            if modeInt == 0:
                mode = names.EDIT_INDEX_INSERT
            elif modeInt == 1:
                mode = names.EDIT_INDEX_REPLACE
            else:  # == 2
                mode = names.EDIT_INDEX_REMOVE
            index = self.properties.indexTxt.value
            if index > 0:  # if not negative, make artist friendly GUI numbers start at 1, (code functions start at 0)
                index -= 1
        if removePrefix:
            mode = names.EDIT_INDEX_REMOVE
            index = 0
        elif removeSuffix:
            mode = names.EDIT_INDEX_REMOVE
            index = -1
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.editIndexItemFilteredType(index,
                                            niceNameType,
                                            text=text,
                                            mode=mode,
                                            separator="_",
                                            renameShape=True,
                                            searchHierarchy=searchHierarchy,
                                            selectionOnly=selectionOnly,
                                            dag=False,
                                            removeMayaDefaults=True,
                                            transformsOnly=True,
                                            message=True)
        else:
            # Advanced UI mode -----------------------------
            names.editIndexItemFilteredType(index,
                                            niceNameType,
                                            text=text,
                                            mode=mode,
                                            separator="_",
                                            renameShape=self.properties.autoShapesBox.value,
                                            searchHierarchy=searchHierarchy,
                                            selectionOnly=selectionOnly,
                                            dag=False,
                                            removeMayaDefaults=True,
                                            transformsOnly=True,
                                            message=True)
        return

    @toolsetwidget.ToolsetWidget.undoDecorator
    def shuffleItemByIndex(self, offset):
        """Move text items separated by underscores to a new position.  With filters from GUI
        Updates the GUI after the move so the same item stays in focus

        Example:

            objName: "pCube1_xxx_yyy_001"
            index 3:
            offset -1:
            result: "pCube1_xxx_001_yyy

        See names.searchReplaceFilteredType() for filter documentation
        """
        searchHierarchy, selectionOnly = self.setFilterVars()
        if not searchHierarchy and not selectionOnly:  # all so bail
            output.displayWarning("Move By Index must be used with 'Selected' or 'Hierarchy', not 'All'")
            return
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        shuffleIndex = self.properties.indexShuffleTxt.value
        if shuffleIndex > 0:  # if not negative, make artist friendly GUI numbers start at 1, (code functions start 0)
            shuffleIndex -= 1
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.shuffleItemByIndexFilteredType(shuffleIndex,
                                                 niceNameType,
                                                 offset=offset,
                                                 separator="_",
                                                 renameShape=True,
                                                 searchHierarchy=searchHierarchy,
                                                 selectionOnly=selectionOnly,
                                                 dag=False,
                                                 removeMayaDefaults=True,
                                                 transformsOnly=True,
                                                 message=True)
        else:
            # Advanced UI mode -----------------------------
            names.shuffleItemByIndexFilteredType(shuffleIndex,
                                                 niceNameType,
                                                 offset=offset,
                                                 separator="_",
                                                 renameShape=self.properties.autoShapesBox.value,
                                                 searchHierarchy=searchHierarchy,
                                                 selectionOnly=selectionOnly,
                                                 dag=False,
                                                 removeMayaDefaults=True,
                                                 transformsOnly=True,
                                                 message=True)
        oldValue = self.properties.indexShuffleTxt.value
        newValue = oldValue + offset
        if newValue == 0:  # make pos 1
            if oldValue > 1:
                newValue = 1
            else:
                newValue = -1
        self.properties.indexShuffleTxt.value = newValue
        self.updateFromProperties()
        return

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteSelectedNamespace(self):
        """Will empty the first selected namespace and then try and delete the namespace"""
        if self.displayIndex() == UI_MODE_COMPACT:
            names.deleteSelectedNamespace(renameShape=True)
        else:
            names.deleteSelectedNamespace(renameShape=self.properties.autoShapesBox.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def assignNamespace(self):
        """Assign Namespace names"""
        removeNamespace = False
        searchHierarchy, selectionOnly = self.setFilterVars()
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        namespaceName = self.properties.namespaceTxt.value
        if self.properties.namespaceCombo.value == 1:  # remove mode
            removeNamespace = True
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.createAssignNamespaceFilteredType(namespaceName,
                                                    niceNameType,
                                                    removeNamespace=removeNamespace,
                                                    renameShape=True,
                                                    searchHierarchy=searchHierarchy,
                                                    selectionOnly=selectionOnly,
                                                    dag=False,
                                                    removeMayaDefaults=True,
                                                    transformsOnly=True,
                                                    message=True)
            return
        # Advanced UI mode -----------------------------
        names.createAssignNamespaceFilteredType(namespaceName,
                                                niceNameType,
                                                removeNamespace=removeNamespace,
                                                renameShape=self.properties.autoShapesBox.value,
                                                searchHierarchy=searchHierarchy,
                                                selectionOnly=selectionOnly,
                                                dag=False,
                                                removeMayaDefaults=True,
                                                transformsOnly=True,
                                                message=True)

    # ------------------
    # CONNECTIONS
    # ------------------

    def connectionsRenamer(self):
        """Connects up the buttons to the Zoo Renamer logic """
        # both GUIs
        for widget in self.widgets():
            widget.forceBtn.clicked.connect(self.forceRename)
            widget.searchReplaceBtn.clicked.connect(self.searchReplace)
            widget.prefixBtn.clicked.connect(partial(self.addPrefixSuffix, sptype=names.PREFIX))
            widget.suffixBtn.clicked.connect(partial(self.addPrefixSuffix, sptype=names.SUFFIX))
            widget.autoSuffixBtn.clicked.connect(partial(self.autoPrefixSuffix, sptype=names.SUFFIX))
            widget.renumberBtn.clicked.connect(self.renumberUI)
            widget.indexShuffleNegBtn.clicked.connect(partial(self.shuffleItemByIndex, offset=-1))
            widget.indexShufflePosBtn.clicked.connect(partial(self.shuffleItemByIndex, offset=1))
            widget.prefixListCombo.itemChanged.connect(partial(self.populatePrefixSuffix, sptype=names.PREFIX))
            widget.suffixListCombo.itemChanged.connect(partial(self.populatePrefixSuffix, sptype=names.SUFFIX))
            widget.deleteSelNamespaceBtn.clicked.connect(self.deleteSelectedNamespace)
            widget.optionsRadio.toggled.connect(self.disableWidgetsInAllMode)
            widget.removeAllNumbersBtn.clicked.connect(partial(self.removeNumbers, trailingOnly=False))
            widget.removeTrailingNumbersBtn.clicked.connect(partial(self.removeNumbers, trailingOnly=True))
        # advanced GUI
        self.advancedWidget.atIndexBtn.clicked.connect(self.saveProperties)
        self.advancedWidget.atIndexBtn.clicked.connect(self.editIndex)
        self.advancedWidget.namespaceWindowOpenBtn.clicked.connect(self.openNamespaceEditor)
        self.advancedWidget.referenceWindowOpenBtn.clicked.connect(self.openReferenceEditor)
        self.advancedWidget.removePrefixBtn.clicked.connect(partial(self.editIndex, removePrefix=True))
        self.advancedWidget.indexCombo.itemChanged.connect(self.disableEnableAtIndexTxt)
        self.advancedWidget.namespaceBtn.clicked.connect(self.assignNamespace)
        self.advancedWidget.removeSuffixBtn.clicked.connect(partial(self.editIndex, removeSuffix=True))
        self.advancedWidget.makeUniqueBtn.clicked.connect(self.uniqueNames)


class RenamerWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: ZooRenamer
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: object
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(RenamerWidgets, self).__init__(parent=parent)

        self.toolsetWidget = toolsetWidget
        self.properties = properties
        # Top Radio Buttons ------------------------------------
        radioNameList = ["Selected", "Hierarchy", "All"]
        radioToolTipList = ["Rename based on selected objects/nodes.",
                            "Rename the selected object and it's hierarchy below.",
                            "Rename all objects/nodes in the scene."]
        self.optionsRadio = elements.RadioButtonGroup(radioList=radioNameList, toolTipList=radioToolTipList,
                                                      default=0, parent=parent)
        # Force Rename ------------------------------------
        toolTip = "Select objects in order, objects will be renamed with numeric suffixing. "
        self.forceRenameTxt = elements.LineEdit(text=self.properties.search.value,
                                                placeholder="Force Rename",
                                                toolTip=toolTip,
                                                parent=parent)
        self.forceBtn = elements.styledButton("",
                                              "checkList",
                                              toolTip=toolTip,
                                              parent=self,
                                              minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Numeric padding of the trailing numbers \n" \
                  "1: 1 , 2, 3, 4\n" \
                  "2: 01, 02, 03, 04\n" \
                  "3: 001, 002, 003, 004"
        self.forcePaddingInt = elements.IntEdit("Numeric Padding",
                                                int(self.properties.padding.value),
                                                toolTip=toolTip,
                                                parent=parent,
                                                labelRatio=10,
                                                editRatio=6)
        # Search Replace ------------------------------------
        toolTip = "Search and replace selected object/node names\n" \
                  "Text in the first text box gets replaced by the second."
        self.searchTxt = elements.LineEdit(text=self.properties.search.value,
                                           placeholder="Search",
                                           toolTip=toolTip,
                                           parent=parent)
        self.replaceTxt = elements.LineEdit(text=self.properties.replace.value,
                                            placeholder="Replace",
                                            toolTip=toolTip,
                                            parent=parent)
        self.searchReplaceBtn = elements.styledButton("",
                                                      "searchReplace",
                                                      toolTip=toolTip,
                                                      parent=self,
                                                      minWidth=uic.BTN_W_ICN_MED)
        # Prefix ------------------------------------
        toolTip = "Add a prefix to the selected object/node names"
        self.prefixTxt = elements.StringEdit(self.properties.prefix.value,
                                             editPlaceholder="Add Prefix",
                                             toolTip=toolTip,
                                             parent=parent)
        self.prefixBtn = elements.styledButton("",
                                               "prefix",
                                               toolTip=toolTip,
                                               parent=self,
                                               minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Predefined Maya suffix/prefix name list"

        self.prefixListCombo = elements.ComboBoxSearchable(items=filtertypes.SUFFIXLIST,
                                                           setIndex=self.properties.prefixCombo.value,
                                                           parent=self,
                                                           toolTip=toolTip)
        # Suffix ------------------------------------
        toolTip = "Add a suffix to the selected object/node names"
        self.suffixTxt = elements.StringEdit(self.properties.suffix.value,
                                             editPlaceholder="Add Suffix",
                                             toolTip=toolTip,
                                             parent=parent)
        self.suffixBtn = elements.styledButton("",
                                               "suffix",
                                               toolTip=toolTip,
                                               parent=self,
                                               minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Predefined Maya suffix/prefix name list"
        self.suffixListCombo = elements.ComboBoxSearchable(items=filtertypes.SUFFIXLIST,
                                                           setIndex=self.properties.suffixCombo.value,
                                                           parent=self,
                                                           toolTip=toolTip)
        # Index Shuffle ------------------------------------
        toolTip = "Shuffle the item part of a name, usually separated by underscores '_'\n" \
                  "The index value is artist friendly and starts at 1\n" \
                  "Negative numbers start at the end values\n" \
                  "'object_geo_01' with index -1 (left arrow) will become 'object_01_geo'\n" \
                  "'object_geo_01' with index 1 (right arrow) will become 'geo_object_01'"
        self.indexShuffleLabel = elements.Label("Shuffle By Index", parent=self, toolTip=toolTip)
        self.indexShuffleNegBtn = elements.styledButton("",
                                                        "arrowStandardLeft",
                                                        toolTip=toolTip,
                                                        parent=self,
                                                        minWidth=uic.BTN_W_ICN_MED)
        self.indexShuffleTxt = elements.IntEdit("",
                                                self.properties.shuffleIndex.value,
                                                toolTip=toolTip,
                                                parent=parent)
        self.indexShufflePosBtn = elements.styledButton("",
                                                        "arrowStandardRight",
                                                        toolTip=toolTip,
                                                        parent=self,
                                                        minWidth=uic.BTN_W_ICN_MED)
        # Renumber ------------------------------------
        toolTip = "Renumber or change numerical padding\n" \
                  "Replace: Renumbers in sel or hierarchy order. 'object1' becomes 'object_01'\n" \
                  "Append: Renumbers in sel or hierarchy order. 'object1' becomes 'object1_01'\n" \
                  "Change Pad: Keeps the number and changes padding. 'char1_object3' becomes 'char1_object_03'\n" \
                  "*Change Pad only affects the trailing numbers. 'object3' not 'object3_geo'"
        if uiMode == UI_MODE_COMPACT:
            self.renumberLabel = elements.Label("Renumber", self, toolTip=toolTip)
        if uiMode == UI_MODE_ADVANCED:
            self.renumberLabel = elements.Label("Renumber", self, toolTip=toolTip, bold=True)  # bold for advanced
        self.renumberBtn = elements.styledButton("",
                                                 "renumber",
                                                 toolTip=toolTip,
                                                 parent=self,
                                                 minWidth=uic.BTN_W_ICN_MED)
        self.renumberCombo = elements.ComboBoxRegular(items=RENUMBER_COMBO_LIST,
                                                      parent=self,
                                                      setIndex=self.properties.renumberCombo.value,
                                                      toolTip=toolTip)
        toolTip = "Numeric padding of the trailing number\n" \
                  "1: 1 , 2, 3, 4\n" \
                  "2: 01, 02, 03, 04\n" \
                  "3: 001, 002, 003, 004"
        self.renumberPaddingInt = elements.IntEdit("Pad",
                                                   int(self.properties.padding.value),
                                                   toolTip=toolTip,
                                                   parent=parent)
        # Renumber Remove Buttons ------------------------------------
        toolTip = "Remove all numbers from object names\n" \
                  "'scene2_pcube1' becomes 'scene_pcube'\n" \
                  "Note: names must not clash with other nodes of the same name"
        self.removeAllNumbersBtn = elements.styledButton("Remove All Numbers",
                                                         "trash",
                                                         toolTip=toolTip,
                                                         parent=self,
                                                         style=uic.BTN_LABEL_SML)
        toolTip = "Remove the trailing numbers from object names\n" \
                  "'scene2_pcube1' becomes 'scene2_pcube'\n" \
                  "Note: names must not clash with other nodes of the same name\n"
        self.removeTrailingNumbersBtn = elements.styledButton("Remove Tail Numbers",
                                                              "trash",
                                                              toolTip=toolTip,
                                                              parent=self,
                                                              style=uic.BTN_LABEL_SML)
        # Auto Names ------------------------------------
        toolTip = "Automatically suffix objects based off their type\n" \
                  "'pCube1' becomes 'pCube1_geo'\n" \
                  "'locator1' becomes 'locator1_loc'"
        self.autoSuffixBtn = elements.styledButton("Automatic Suffix",
                                                   "suffix",
                                                   toolTip=toolTip,
                                                   parent=self,
                                                   style=uic.BTN_LABEL_SML)
        # Delete selected Namespace btn ------------------------------------
        toolTip = "Deletes the selected namespace/s for the whole scene. Select objects and run.\n" \
                  "'scene:geo1' becomes 'geo1'\n" \
                  "Will delete the namespace for all objects in the scene."
        self.deleteSelNamespaceBtn = elements.styledButton("Delete Namespace",
                                                           "trash",
                                                           toolTip=toolTip,
                                                           parent=self,
                                                           style=uic.BTN_LABEL_SML)

        if uiMode == UI_MODE_ADVANCED:
            # filter label ------------------------------------
            toolTip = "Filter renaming with the following options"
            self.filtersLabel = elements.Label("Filters", self, toolTip=toolTip, bold=True)
            # dividers ------------------------------------
            self.filtersDivider = elements.Divider(parent=parent)
            self.searchReplaceDivider = elements.Divider(parent=parent)
            self.prefixSuffixDivider = elements.Divider(parent=parent)
            self.atIndexDivider = elements.Divider(parent=parent)
            self.renumberDivider = elements.Divider(parent=parent)
            self.namespaceDivider = elements.Divider(parent=parent)
            self.miscDivider = elements.Divider(parent=parent)
            # object filter ------------------------------------
            toolTip = "Only rename these object types"
            self.objFilterCombo = elements.ComboBoxSearchable(items=filtertypes.TYPE_FILTER_LIST,
                                                              setIndex=self.properties.objFilterCombo.value,
                                                              parent=self,
                                                              toolTip=toolTip)
            # checkbox options ------------------------------------
            toolTip = "When on, shape nodes will be renamed with the transform names.\n" \
                      "Example: `pCube_002` renames it's shape node `pCube_002Shape`"
            self.autoShapesBox = elements.CheckBox("Auto Shapes",
                                                   checked=self.properties.shapesBox.value,
                                                   parent=self,
                                                   toolTip=toolTip)
            # Index Label ------------------------------------
            toolTip = "Add/Edit by Artist friendly index, underscore seperated \n" \
                      "Example: 01_02_03_-02_-01 etc"
            self.indexLabel = elements.Label("Index", parent=self, toolTip=toolTip, bold=True)
            # Prefix Suffix Label ------------------------------------
            toolTip = "Add a suffix or prefix to object/node names"
            self.prefixSuffixLabel = elements.Label("Prefix/Suffix", parent=self, toolTip=toolTip, bold=True)
            # Search & Replace Label ------------------------------------
            toolTip = "Search and replace selected object/node names\n" \
                      "Text in the first text box gets replaced by the second."
            self.searchReplaceLabel = elements.Label("Search And Replace", parent=self, toolTip=toolTip, bold=True)
            # Prefix Delete Button ------------------------------------
            toolTip = "Removes the prefix separated by an underscore '_'\n" \
                      "'scene1_pCube1_geo', becomes 'pCube1_geo'"
            self.removePrefixBtn = elements.styledButton("Remove Prefix",
                                                         "trash",
                                                         toolTip=toolTip,
                                                         parent=self,
                                                         style=uic.BTN_LABEL_SML)
            # At Index ------------------------------------
            toolTip = "Add _text_ with artist friendly index value. Examples...  \n" \
                      "1: Adds a prefix\n" \
                      "-1: Adds a suffix\n" \
                      "2: Adds after the first underscore\n" \
                      "-2: Adds before the last underscore"
            self.atIndexTxt = elements.StringEdit(self.properties.atIndex.value,
                                                  editPlaceholder="Add At Index",
                                                  toolTip=toolTip,
                                                  parent=parent)
            self.indexTxt = elements.IntEdit("Index",
                                             int(self.properties.index.value),
                                             toolTip=toolTip,
                                             parent=parent)
            self.atIndexBtn = elements.styledButton("",
                                                    "indexText",
                                                    toolTip=toolTip,
                                                    parent=self,
                                                    minWidth=uic.BTN_W_ICN_MED)
            toolTip = "Insert: \n" \
                      "'geo' at 2: 'object_char_L' becomes 'object_geo_char_L'\n" \
                      "Replace:\n" \
                      "'geo' at -2: 'object_char_L' becomes 'object_geo_L'\n" \
                      "Remove:\n" \
                      "-2: 'object_char_L' becomes 'object_L'"
            self.indexCombo = elements.ComboBoxRegular(items=("Insert", "Replace", "Remove"),
                                                       setIndex=int(self.properties.indexCombo.value),
                                                       parent=self,
                                                       toolTip=toolTip)
            # Namespace ------------------------------------
            toolTip = "Edit add or delete namespaces (name suffix followed by a colon)\n" \
                      "Example:  `scene5:pCube1` > `scene5` is the namespace\n" \
                      "Note: Namespaces have hierarchies, use the 'Namespace Editor' for renaming and advanced features"
            self.namespaceLabel = elements.Label("Namespace", parent=self, toolTip=toolTip, bold=True)
            self.namespaceTxt = elements.StringEdit(self.properties.namespace.value,
                                                    editPlaceholder="Namespace",
                                                    toolTip=toolTip,
                                                    parent=parent)
            self.namespaceCombo = elements.ComboBoxRegular(items=NAMESPACE_COMBO_LIST,
                                                           setIndex=self.properties.namespaceCombo.value,
                                                           parent=self,
                                                           toolTip=toolTip)
            self.namespaceBtn = elements.styledButton("",
                                                      "namespace",
                                                      toolTip=toolTip,
                                                      parent=self,
                                                      minWidth=uic.BTN_W_ICN_MED)
            # Namespace Delete  Empty Buttons ------------------------------------
            toolTip = "Deletes all empty/unused namespaces in the scene."
            self.deleteUnusedNamespaceBtn = elements.styledButton("Unused Namespaces",
                                                                  "trash",
                                                                  toolTip=toolTip,
                                                                  parent=self,
                                                                  style=uic.BTN_LABEL_SML)
            # General Label ------------------------------------
            toolTip = "General buttons"
            self.miscLabel = elements.Label("Misc", parent=self, toolTip=toolTip, bold=True)
            # Window Buttons ------------------------------------
            toolTip = "Opens the Namespace Editor, manages semi colon prefix names\n" \
                      "Example: 'scene01:***'"
            self.namespaceWindowOpenBtn = elements.styledButton("Namespace Editor",
                                                                "browserWindow",
                                                                toolTip=toolTip,
                                                                parent=self,
                                                                style=uic.BTN_LABEL_SML)
            toolTip = "Opens the Reference Editor, manages referenced semi colon prefix names\n" \
                      "Example: 'rig:***'"
            self.referenceWindowOpenBtn = elements.styledButton("Reference Editor",
                                                                "browserWindow",
                                                                toolTip=toolTip,
                                                                parent=self,
                                                                style=uic.BTN_LABEL_SML)
            # Make Unique Button ------------------------------------
            toolTip = "Make node names unique.\n" \
                      "If a name is duplicated it will be renamed with an incremental number\n" \
                      "Example:\n" \
                      "'shaderName' becomes 'shaderName_01'\n" \
                      "'shaderName2' becomes 'shaderName3'\n" \
                      "'shaderName_04' becomes 'shaderName_05'\n" \
                      "'shaderName_04' becomes 'shaderName_05'\n" \
                      "'shaderName_99' becomes 'shaderName_100'\n" \
                      "'shaderName_0009' becomes 'shaderName_0010'"
            self.makeUniqueBtn = elements.styledButton("Make Unique",
                                                       "snowflake",
                                                       toolTip=toolTip,
                                                       parent=self,
                                                       style=uic.BTN_LABEL_SML)
            # Delete suffix btn ------------------------------------
            toolTip = "Removes the suffix separated by an underscore '_'\n" \
                      "'scene1_pCube1_geo', becomes 'scene1_pCube1'"
            self.removeSuffixBtn = elements.styledButton("Remove Suffix",
                                                         "trash",
                                                         toolTip=toolTip,
                                                         parent=self,
                                                         style=uic.BTN_LABEL_SML)


class RenamerCompactWidget(RenamerWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the advanced version of the directional light UI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(RenamerCompactWidget, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                                   toolsetWidget=toolsetWidget)
        # Main Layout ------------------------------------
        contentsLayout = elements.vBoxLayout(self,
                                             margins=(uic.WINSIDEPAD,
                                                      0,
                                                      uic.WINSIDEPAD,
                                                      uic.WINBOTPAD),
                                             spacing=uic.SREG)
        # Top Radio Button Layout ------------------------------------
        optionsRadioLayout = elements.hBoxLayout(spacing=0)
        optionsRadioLayout.addWidget(self.optionsRadio)
        # Force Sub Layout ---------------------------------------
        forceSubLayout = elements.hBoxLayout(margins=(uic.SLRG, 0, 0, 0))
        forceSubLayout.addWidget(self.forcePaddingInt)
        # Force Rename Layout ------------------------------------
        forceLayout = elements.hBoxLayout(spacing=uic.SREG)
        forceLayout.addWidget(self.forceRenameTxt, 5)
        forceLayout.addLayout(forceSubLayout, 5)
        forceLayout.addWidget(self.forceBtn, 1)
        # Search Replace Layout ------------------------------------
        searchLayout = elements.hBoxLayout(spacing=uic.SREG)
        searchLayout.addWidget(self.searchTxt, 12)
        searchLayout.addWidget(self.replaceTxt, 12)
        searchLayout.addWidget(self.searchReplaceBtn, 1)
        # Prefix Layout ------------------------------------
        prefixLayout = elements.hBoxLayout(spacing=uic.SREG)
        prefixLayout.addWidget(self.prefixTxt, 12)
        prefixLayout.addWidget(self.prefixListCombo, 12)
        prefixLayout.addWidget(self.prefixBtn, 1)
        # Suffix Layout ------------------------------------
        suffixLayout = elements.hBoxLayout(spacing=uic.SREG)
        suffixLayout.addWidget(self.suffixTxt, 12)
        suffixLayout.addWidget(self.suffixListCombo, 12)
        suffixLayout.addWidget(self.suffixBtn, 1)
        # Index Shuffle ------------------------------------
        indexShuffleLayout = elements.hBoxLayout(spacing=uic.SREG)
        indexShuffleLayout.addWidget(self.indexShuffleLabel, 20)
        indexShuffleLayout.addWidget(self.indexShuffleNegBtn, 1)
        indexShuffleLayout.addWidget(self.indexShuffleTxt, 4)
        indexShuffleLayout.addWidget(self.indexShufflePosBtn, 1)
        # Renumber Layout ------------------------------------
        renumberLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        renumberLayout.addWidget(self.renumberLabel, 8)
        renumberLayout.addWidget(self.renumberCombo, 8)
        renumberLayout.addWidget(self.renumberPaddingInt, 8)
        renumberLayout.addWidget(self.renumberBtn, 1)
        # Renumber Btn Layout ------------------------------------
        renumberBtnLayout = elements.hBoxLayout(spacing=uic.SVLRG2)
        renumberBtnLayout.addWidget(self.removeAllNumbersBtn, 1)
        renumberBtnLayout.addWidget(self.removeTrailingNumbersBtn, 1)
        # Button Bottom Layout ------------------------------------
        btnLayout = elements.hBoxLayout(spacing=uic.SVLRG2)
        btnLayout.addWidget(self.autoSuffixBtn, 1)
        btnLayout.addWidget(self.deleteSelNamespaceBtn, 1)
        # Add to main Layout ------------------------------------
        contentsLayout.addLayout(optionsRadioLayout)
        contentsLayout.addLayout(forceLayout)
        contentsLayout.addLayout(searchLayout)
        contentsLayout.addLayout(prefixLayout)
        contentsLayout.addLayout(suffixLayout)
        contentsLayout.addLayout(indexShuffleLayout)
        contentsLayout.addLayout(renumberLayout)
        contentsLayout.addLayout(renumberBtnLayout)
        contentsLayout.addLayout(btnLayout)
        contentsLayout.addStretch(1)


class RenamerAdvancedWidget(RenamerWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the directional light UI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(RenamerAdvancedWidget, self).__init__(parent=parent, properties=properties,
                                                    uiMode=uiMode, toolsetWidget=toolsetWidget)
        # Main Layout ------------------------------------
        contentsLayout = elements.vBoxLayout(self,
                                             margins=(uic.WINSIDEPAD,
                                                      uic.WINBOTPAD,
                                                      uic.WINSIDEPAD,
                                                      uic.WINBOTPAD),
                                             spacing=uic.SREG)
        # Filter Label Layout ------------------------------------
        filterLabelLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SSML), spacing=uic.SREG)
        filterLabelLayout.addWidget(self.filtersLabel, 1)
        filterLabelLayout.addWidget(self.filtersDivider, 10)
        # Filter Layout ------------------------------------
        filterLayout = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SLRG)
        filterLayout.addWidget(self.objFilterCombo, 2)
        filterLayout.addWidget(self.autoShapesBox, 1)
        # Top Radio Button Layout ------------------------------------
        optionsRadioLayout = elements.hBoxLayout(spacing=0)
        optionsRadioLayout.addWidget(self.optionsRadio)
        # Force Sub Layout ---------------------------------------
        forceSubLayout = elements.hBoxLayout(margins=(uic.SLRG, 0, 0, 0))
        forceSubLayout.addWidget(self.forcePaddingInt)
        # Force Rename Layout ------------------------------------
        forceLayout = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        forceLayout.addWidget(self.forceRenameTxt, 5)
        forceLayout.addLayout(forceSubLayout, 5)
        forceLayout.addWidget(self.forceBtn, 1)
        # Search Replace Label Layout ------------------------------------
        searchReplaceLabelLayout = elements.hBoxLayout(margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        searchReplaceLabelLayout.addWidget(self.searchReplaceLabel, 1)
        searchReplaceLabelLayout.addWidget(self.searchReplaceDivider, 10)
        # Search Replace Layout ------------------------------------
        searchLayout = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        searchLayout.addWidget(self.searchTxt, 12)
        searchLayout.addWidget(self.replaceTxt, 12)
        searchLayout.addWidget(self.searchReplaceBtn, 1)
        # Prefix Suffix Label Layout ------------------------------------
        prefixLabelLayout = elements.hBoxLayout(margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        prefixLabelLayout.addWidget(self.prefixSuffixLabel, 1)
        prefixLabelLayout.addWidget(self.prefixSuffixDivider, 10)
        # Prefix Layout ------------------------------------
        prefixLayout = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        prefixLayout.addWidget(self.prefixTxt, 13)
        prefixLayout.addWidget(self.prefixListCombo, 11)
        prefixLayout.addWidget(self.prefixBtn, 1)
        # Suffix Layout ------------------------------------
        suffixLayout = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        suffixLayout.addWidget(self.suffixTxt, 13)
        suffixLayout.addWidget(self.suffixListCombo, 11)
        suffixLayout.addWidget(self.suffixBtn, 1)
        # Remove Prefix/Suffix Button Layout ------------------------------------
        removePrefixSuffixLayout = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, 0),
                                                       spacing=uic.SVLRG2)
        removePrefixSuffixLayout.addWidget(self.removePrefixBtn, 1)
        removePrefixSuffixLayout.addWidget(self.removeSuffixBtn, 1)
        # At Index Label Layout ------------------------------------
        indexAtLabelLayout = elements.hBoxLayout(margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        indexAtLabelLayout.addWidget(self.indexLabel, 1)
        indexAtLabelLayout.addWidget(self.atIndexDivider, 10)
        # At Index Layout ------------------------------------
        indexAtLayout = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        indexAtLayout.addWidget(self.atIndexTxt, 8)
        indexAtLayout.addWidget(self.indexCombo, 8)
        indexAtLayout.addWidget(self.indexTxt, 8)
        indexAtLayout.addWidget(self.atIndexBtn, 1)
        # Index Shuffle ------------------------------------
        indexShuffleLayout = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        indexShuffleLayout.addWidget(self.indexShuffleLabel, 20)
        indexShuffleLayout.addWidget(self.indexShuffleNegBtn, 1)
        indexShuffleLayout.addWidget(self.indexShuffleTxt, 4)
        indexShuffleLayout.addWidget(self.indexShufflePosBtn, 1)
        # Renumber Label Layout ------------------------------------
        renumberLabelLayout = elements.hBoxLayout(margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        renumberLabelLayout.addWidget(self.renumberLabel, 1)
        renumberLabelLayout.addWidget(self.renumberDivider, 10)
        # Renumber Layout ------------------------------------
        renumberLayout = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        renumberLayout.addWidget(self.renumberCombo, 16)
        renumberLayout.addWidget(self.renumberPaddingInt, 8)
        renumberLayout.addWidget(self.renumberBtn, 1)
        # Renumber Btn Layout ------------------------------------
        renumberBtnLayout = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SVLRG2)
        renumberBtnLayout.addWidget(self.removeAllNumbersBtn, 1)
        renumberBtnLayout.addWidget(self.removeTrailingNumbersBtn, 1)
        # Namespace Label Layout ------------------------------------
        namespaceLabelLayout = elements.hBoxLayout(margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        namespaceLabelLayout.addWidget(self.namespaceLabel, 1)
        namespaceLabelLayout.addWidget(self.namespaceDivider, 10)
        # Namespace Layout ------------------------------------
        namespaceLayout = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        namespaceLayout.addWidget(self.namespaceTxt, 16)
        namespaceLayout.addWidget(self.namespaceCombo, 8)
        namespaceLayout.addWidget(self.namespaceBtn, 1)
        # Namespace Delete Btn Layout ------------------------------------
        delNamespaceLayout = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SVLRG2)
        delNamespaceLayout.addWidget(self.deleteSelNamespaceBtn, 1)
        delNamespaceLayout.addWidget(self.deleteUnusedNamespaceBtn, 1)
        # Misc Label Layout ------------------------------------
        miscLabelLayout = elements.hBoxLayout(margins=(0, uic.SREG, 0, uic.SREG), spacing=uic.SREG)
        miscLabelLayout.addWidget(self.miscLabel, 1)
        miscLabelLayout.addWidget(self.miscDivider, 10)
        # Bottom Button Layout 1 ------------------------------------
        bottomBtnLayout1 = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SVLRG2)
        bottomBtnLayout1.addWidget(self.autoSuffixBtn, 1)
        bottomBtnLayout1.addWidget(self.makeUniqueBtn, 1)
        # Bottom Button Layout 2 ------------------------------------
        bottomBtnLayout2 = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SVLRG2)
        bottomBtnLayout2.addWidget(self.namespaceWindowOpenBtn, 1)
        bottomBtnLayout2.addWidget(self.referenceWindowOpenBtn, 1)
        # Add to main Layout ------------------------------------
        contentsLayout.addLayout(filterLabelLayout)
        contentsLayout.addLayout(filterLayout)
        contentsLayout.addLayout(optionsRadioLayout)
        contentsLayout.addItem(elements.Spacer(1, uic.SREG))
        contentsLayout.addWidget(elements.LabelDivider("Force Rename"))
        contentsLayout.addLayout(forceLayout)
        contentsLayout.addLayout(searchReplaceLabelLayout)
        contentsLayout.addLayout(searchLayout)
        contentsLayout.addItem(elements.Spacer(1, uic.SREG))
        contentsLayout.addLayout(prefixLabelLayout)
        contentsLayout.addLayout(prefixLayout)
        contentsLayout.addLayout(suffixLayout)
        contentsLayout.addLayout(removePrefixSuffixLayout)
        contentsLayout.addItem(elements.Spacer(1, uic.SREG))
        contentsLayout.addLayout(indexAtLabelLayout)
        contentsLayout.addLayout(indexAtLayout)
        contentsLayout.addLayout(indexShuffleLayout)
        contentsLayout.addItem(elements.Spacer(1, uic.SREG))
        contentsLayout.addLayout(renumberLabelLayout)
        contentsLayout.addLayout(renumberLayout)
        contentsLayout.addItem(elements.Spacer(1, uic.SREG))
        contentsLayout.addLayout(renumberBtnLayout)
        contentsLayout.addItem(elements.Spacer(1, uic.SREG))
        contentsLayout.addLayout(namespaceLabelLayout)
        contentsLayout.addLayout(namespaceLayout)
        contentsLayout.addLayout(delNamespaceLayout)
        contentsLayout.addLayout(bottomBtnLayout2)
        contentsLayout.addItem(elements.Spacer(1, uic.SREG))
        contentsLayout.addLayout(miscLabelLayout)
        contentsLayout.addLayout(bottomBtnLayout1)
        contentsLayout.addStretch(1)
