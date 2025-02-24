import webbrowser
from zoovendor.Qt import QtCore, QtWidgets

from zoo.libs.utils import general
from zoo.core.util import env
from zoo.apps.toolsetsui.widgets import toolsetwidgetitem
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.widgets import stackwidget
from zoo.libs.utils import color
from zoo.core.util import zlogging
from zoo.apps.toolsetsui.widgets import toolsettree
from zoo.libs.pyqt.extended.imageview.thumbnail.minibrowser import MiniBrowserThumbnail

logger = zlogging.getLogger(__name__)

SAVESIGNAL = 0
GET_SETTER_LIST = 1
VALUE_SETTER = 0
VALUE_GET = 1
SKIPCHILDREN = 2

# arg1: signal to save property, arg2: list[(set value, get value),...], arg3: skip the children for properties
SUPPORTED_TYPES_INFO = {elements.ComboBoxRegular: ("itemChanged", [("setIndex", "currentIndex")], True),
                        elements.ComboEditRename: (
                            "itemChanged", [("setIndexInt", "currentIndexInt"), ("setText", "text")], True),
                        elements.ComboEditWidget: (
                            "comboEditChanged", [("setValues", "values"), ("setAspectLinked", "aspectLinked")], True),
                        elements.FloatSlider: ("numSliderChanged", [("setValue", "value")], True),
                        elements.IntSlider: ("numSliderChanged", [("setValue", "value")], True),
                        MiniBrowserThumbnail: ("stateChanged", [("setState", "state")], True),
                        elements.ComboBoxSearchable: ("itemChanged", [("setIndex", "currentIndex")], True),
                        elements.IconMenuButton: ("actionTriggered", [("setMenuName", "currentText")], True),
                        elements.VectorLineEdit: ("textChanged", [("setValue", "value")], True),
                        elements.StringEdit: ("textChanged", [("setText", "text")], True),
                        elements.FloatEdit: ("textChanged", [("setValue", "value")], True),
                        elements.IntEdit: ("textChanged", [("setValue", "value")], True),
                        elements.RadioButtonGroup: ("toggled", [("setChecked", "checkedIndex")], True),
                        elements.VectorSpinBox: ("valueChanged", [("setValue", "value")], True),
                        elements.CheckBox: ("toggled", [("setChecked", "isChecked")], True),
                        elements.SearchLineEdit: ("textChanged", [("setText", "text")], True),
                        elements.HSlider: ("valueChanged", [("setValue", "value")], True),
                        elements.VSlider: ("valueChanged", [("setValue", "value")], True),
                        elements.Slider: ("valueChanged", [("setValue", "value")], True),
                        elements.EmbeddedWindow: ("visibilityChanged", [("setState", "state")], False),
                        elements.LineEdit: ("textChanged", [("setText", "text")], True),
                        elements.FloatLineEdit: ("textChanged", [("setValue", "value")], True),
                        elements.IntLineEdit: ("textChanged", [("setValue", "value")], True),
                        QtWidgets.QLineEdit: ("textChanged", [("setText", "text")], True),
                        QtWidgets.QCheckBox: ("toggled", [("setChecked", "isChecked")], True)
                        }

# todo: convert these to app agnostic versions
if env.isMaya():
    SUPPORTED_TYPES_INFO.update({
        elements.ThumbnailWidget: ("stateChanged", [("setState", "state")], True),
        elements.ColorSlider: ("colorSliderChanged", [("setColorSrgbFloat", "colorSrgbFloat")], True),
        elements.ColorBtn: ("colorChanged", [("setColorLinearFloat", "colorLinearFloat")], True),
        elements.ColorHsvBtns: ("colorChanged", [("setColorLinearFloat", "colorLinearFloat")], True),
        elements.ThumbnailSearchWidget: ("searchChanged", [("setState", "state")], True),
    })

SUPPORTED_TYPES = SUPPORTED_TYPES_INFO.keys()


class ToolsetWidgetBase(stackwidget.StackItem):
    """ The Widget itself that gets placed in the TreeWidgetItems.

    Contains each tool, including the main icon contents simple/advanced and close button

    """
    id = "toolsetId"
    uiData = {"label": "Tool set",
              "icon": "magic",
              "tooltip": "",
              "defaultActionDoubleClick": False,
              "helpUrl": "",
              "autoLinkProperties": True}
    tags = []
    creator = ""
    _widgetOutIconName = "logoutarrow"
    _deleteIconName = "xMark"

    displaySwitched = QtCore.Signal()
    updatePropertyRequested = QtCore.Signal()  # When the ui needs to be updated with the changes in properties
    savePropertyRequested = QtCore.Signal()  # maybe dont need this
    toolsetClosed = QtCore.Signal()

    toolsetHidden = QtCore.Signal()
    toolsetShown = QtCore.Signal()  # When toolset is shown
    toolsetDragged = QtCore.Signal()  # When toolset is dragged
    toolsetDropped = QtCore.Signal()
    toolsetDragCancelled = QtCore.Signal()
    toolsetMousePressed = QtCore.Signal()
    # TODO toolsetActivated does not emit when first opening a toolset, should add
    toolsetActivated = QtCore.Signal()  # use for tracking the active state of the window (example callbacks)
    toolsetDeactivated = QtCore.Signal()  # use for tracking the active state of the window (example callbacks)

    StartLargest = -1
    StartSmallest = 0

    def __init__(self, parent=None, treeWidget=None, iconColor=(255, 255, 255), widgetItem=None):
        self._blockSave = False
        self.iconName = self.uiData['icon']
        self.iconColor = iconColor
        self.treeWidget = treeWidget  # type: toolsettree.ToolsetTreeWidget
        self.showWarnings = True

        self.toolsetWidgetItem = widgetItem  # type: toolsetwidgetitem.ToolsetWidgetItem
        self.stackedWidget = None  # type: QtWidgets.QStackedWidget
        self.displayModeButton = None  # type: DisplayModeButton
        self.helpButton = None  # type: elements.ExtendedButton

        title = self.uiData['label']
        self.properties = self.setupProperties()

        super(ToolsetWidgetBase, self).__init__(title, parent=parent or treeWidget,
                                                collapsed=True,
                                                icon=self.iconName, shiftArrowsEnabled=False,
                                                titleEditable=False, titleUpper=True)

        self._widgets = []  # type: list[QtWidgets.QWidget]

    @property
    def windowClosed(self):
        return self.treeWidget._toolsetFrame.toolsetUi.closed

    def initUi(self):
        super(ToolsetWidgetBase, self).initUi()

        self.stackedWidget = QtWidgets.QStackedWidget(self.widgetHider)
        displayButtonPos = 7  # Position in the horizontal layout

        self.contentsLayout.addWidget(self.stackedWidget)
        self.showExpandIndicator(False)
        self.setTitleTextMouseTransparent(True)

        self.titleFrame.mouseReleaseEvent = self.activateEvent
        self.stackedWidget.setContentsMargins(0, 0, 0, 0)
        self.stackedWidget.setLineWidth(0)
        self.stackedWidget.setMidLineWidth(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.contentsLayout.setContentsMargins(0, 0, 0, 0)
        self.contentsLayout.setSpacing(0)

        self.displayModeButton = DisplayModeButton(parent=self, color=self.iconColor, size=16)
        self.helpButton = elements.ExtendedButton(parent=self)
        self.helpButton.setIconByName("help")

        self.setIconColor(self.iconColor)

        self.visualUpdate(collapse=True)

        if self.uiData.get("helpUrl", "") == "":
            self.helpButton.hide()

        self.titleFrame.horizontalLayout.insertWidget(displayButtonPos, self.helpButton)
        self.titleFrame.horizontalLayout.insertWidget(displayButtonPos, self.displayModeButton)
        self.titleFrame.horizontalLayout.setSpacing(0)
        self.titleFrame.horizontalLayout.setContentsMargins(0, 0, 0, utils.dpiScale(1))

        self.displayModeButton.setIconSize(QtCore.QSize(20, 20))
        self.helpButton.setIconSize(QtCore.QSize(15, 15))
        self.titleFrame.deleteBtn.setIconSize(QtCore.QSize(12, 12))
        self.titleFrame.itemIcon.setIconSize(QtCore.QSize(20, 20))

        self.toolsetHidden.connect(self.toolsetDeactivated.emit)
        self.toolsetDragged.connect(self.toolsetDeactivated.emit)
        self.windowClosed.connect(self.toolsetDeactivated.emit)
        self.toolsetShown.connect(self.toolsetActivated.emit)
        self.toolsetDragCancelled.connect(self.toolsetActivated.emit)
        self.toolsetDeactivated.connect(self.treeWidget._toolsetFrame.updateColors)
        self.helpButton.leftClicked.connect(self.helpButtonClicked)

    def helpButtonClicked(self):
        """ Open url on help button clicked.

        :return:
        :rtype:
        """

        url = self.uiData.get("helpUrl", "")
        if url != "":
            webbrowser.open(url)

    def widgets(self):
        """ Return all the display widgets

        :return:
        :rtype: list[QtWidgets.QWidget]
        """
        return self._widgets

    def displayIndex(self):
        """ Current index of the stackedwidget

        :return:
        """
        return self.stackedWidget.currentIndex()

    def currentWidget(self):
        """ Currently active widget

        :return:
        :rtype: QtWidgets.QWidget
        """
        return self.widgets()[self.displayIndex()]

    def updateTree(self, delayed=False):
        """ Update the tree for any changes in the toolset sizes

        :param delayed: If delayed is true, it will do it after the timer of 0 seconds. Can help with some refresh issues
        :return:
        """
        self.treeWidget.updateTree(delayed)

    def updateTreeWidget(self):
        """ Update the tree widget

        :return:
        :rtype:
        """
        self.treeWidget.updateTreeWidget()

    def resizeUiWindow(self, delayed=False):
        """ Resize the toolset ui window

        :return:
        :rtype:
        """
        self.treeWidget._toolsetFrame.window().resizeWindow(delayed=delayed)

    def preContentSetup(self):
        """ Run before the contents are created

        Code for the user to override

        :return:
        :rtype:
        """
        pass

    def contents(self):
        """ to be overridden

        :return:
        :rtype:
        """
        pass

    def actions(self):
        """ To be overridden

        return example:

        return [
            {"type": "action",
             "name": "select_in_scene",
             "label": "Create Turntable",
             "icon": "cursorSelect",
             "tooltip": ""}
        ]

        :return:
        :rtype:
        """
        return []

    def executeActions(self, action):
        """ When the actions is executing it goes here.

        :param action:
        :type action:
        :return:
        :rtype:
        """
        pass

    def postContentSetup(self):
        """ Run after the contents are created

        Code for the user to override.

        :return:
        :rtype:
        """
        pass

    def autoLinkProperties(self, widgets):
        """ Auto Link properties if allowed

        :return:
        :rtype:
        """
        if not self.uiData.get("autoLinkProperties", True):
            return

        newProperties = []
        names = []  # to check quickly against
        for name, lpWidget in self.linkableProperties(self):
            # skip the children for toolset widgets, so it doesn't recursively add the children
            skipChildren = SUPPORTED_TYPES_INFO.get(type(lpWidget))[SKIPCHILDREN]
            lpWidget.setProperty("skipChildren", skipChildren)

            if not self.linkProperty(lpWidget, name):
                continue
            # Add to new properties, don't include duplicates
            if name not in names:
                appendNew = {"name": name}
                appendNew.update(self.widgetValues(lpWidget))
                newProperties.append(appendNew)
                names.append(name)

        # Update the new properties
        newProps = self.setupProperties(newProperties)
        self.properties.update(newProps)

    @classmethod
    def pairProperties(cls, widget, props):
        """ Pairs properties so the property will equal to the widgets property, with any custom name set.

        Example:

            # same as: widget.setProperty("extraProperties", {"propertyName": "size"})

            widget.size() will be run for property "propertyName"

            print(self.properties.widgetName)
            # {u'propertyName': PySide2.QtCore.QSize(118, 24), 'text': u'camera1', 'value': 0}

            print(self.properties.widgetName.propertyName)
            # PySide2.QtCore.QSize(118, 24)

        :param widget: The Widget to apply the extra properties to
        :type widget: QtWidgets.QWidget
        :param props: Properties to add
        :type props: dict
        :return:
        :rtype:
        """
        extraProps = widget.property("extraProperties")
        if extraProps is None:
            extraProps = {}
        extraProps.update(props)
        widget.setProperty("extraProperties", extraProps)

    def resetProperties(self):
        """ Resets the properties back to default as specified in self.properties.widget.default

        :return:
        :rtype:
        """
        for v in self.properties.values():
            v.update({'value': v['default']})

    def resetUi(self):
        """ Resets the ui values back to default

        :return:
        :rtype:
        """
        self.resetProperties()
        self.updateFromProperties()

    @classmethod
    def addExtraProperties(cls, widget, props):
        """ Add extra properties.

        Pretty much the same as pairProperties except the property name is set automatically.

        Example:

            widget.size()  # eg. QtCore.QSize(64,64)
            widget.text()  # eg. "Hello World"

            addExtraProperties(widget, ['size', 'text'])

            # After saveProperties() is run
            print(self.properties.widgetName)
            # {'propertyName': PySide2.QtCore.QSize(64, 64), 'text': 'Hello World', 'value': 0}


        :param widget: The widget to add from
        :type widget: :class:`QtWidgets.QWidget`
        :param props: The properties from the widget to add to toolset properties
        :type props: :class:`list` or str
        :return:
        :rtype:
        """
        if type(props) is not list:
            props = [props]
        pairProps = {p: p for p in props}  # ['hello', 'world'] ==> {'hello': 'hello', 'world': 'world'}
        cls.pairProperties(widget, pairProps)

    @classmethod
    def addExtraProperty(cls, widget, prop):
        """ Add Extra property to toolset property

        :param widget:
        :type widget:
        :param prop:
        :type prop:
        :return:
        :rtype:
        """
        cls.addExtraProperties(widget, [prop])

    def linkableProperties(self, widget):
        """ Get linkable properties from widgets children

        :param widget:
        :type widget:
        :return:
        :rtype:
        """
        # Check current widget first
        for attr in widget.__dict__:
            if type(getattr(widget, attr)) in SUPPORTED_TYPES:
                yield attr, getattr(widget, attr)

        # Then descendants
        children = widget.children()
        for child in children:
            for attr in child.__dict__:
                if type(getattr(child, attr)) in SUPPORTED_TYPES:
                    yield attr, getattr(child, attr)

            for grandchild in self.linkableProperties(child):
                yield grandchild

    def populateWidgets(self):
        """Make the connections for all widgets linked in the toolset UI via:

            self.linkProperty(widget, "propertyKey")
            or
            self.toolsetWidget.linkProperty(widget, "propertyKey")

        Any change to a Qt widget will connect (activate) to self.saveProperties
        More unsupported widgets can be added here
        or manually added directly in the toolset ui, just connect to saveProperties()
        """
        propWidgets = self.propertyWidgets()

        # Do connections
        for p in propWidgets:
            modified = False

            info = SUPPORTED_TYPES_INFO.get(type(p), None)
            if info:
                signal = getattr(p, info[SAVESIGNAL])
                signal.connect(self.saveProperties)
                modified = True

            if not modified:
                if self.showWarnings:
                    logger.warning(
                        "populateWidgets(): Unsupported widget: {}. Property: {}".format(p, self.widgetName(p)))

        # Update
        self.savePropertyRequested.connect(self.saveProperties)
        self.updatePropertyRequested.connect(self.updateFromProperties)

    def linkProperty(self, widget, prop):
        """ Link the property to the widget

        Convenience function to set the property of the widget so ToolsetWidget can read.

        :param widget:
        :type widget:
        :param prop:
        :type prop:
        :return: Returns true if link was made, false if it already exists
        :rtype: bool
        """
        if self.widgetName(widget) is None:
            # Bit hacky of a workaround for the StringEdit
            if prop == "edit" and type(widget.parent()) == elements.StringEdit:
                # logger.info("Ignoring sub-widget \"edit\" from StringEdit for \"{}\".".format(self.widgetProperty(widget.parent())))
                return False
            widget.setProperty("prop", prop)
            return True

        return False

    def saveProperties(self, currentWidget=False):
        """ Saves the properties from the UI -> ToolsetWidget.properties attribute

        Widgets are linked in the toolset UI via:

            self.linkProperty(widget, "propertyKey")
            or
            self.toolsetWidget.linkProperty(widget, "propertyKey")

        Any change to a Qt widget connects to this method saving all ui values to self.properties
        Unsupported widgets can be added in self.widgetValue(), or manually added directly in the toolset ui
        after super() on the overridden saveProperties() class in a single toolset tool GUI
        """
        if self._blockSave:
            return
        propWidgets = self.propertyWidgets(currentWidget=currentWidget)  # only save properties from the current widget
        for w in propWidgets:
            widgetDict = self.widgetValues(w)
            for k, v in widgetDict.items():
                setattr(self.properties[self.widgetName(w)], k, v)

    def updateSingleProperty(self, property):
        """ Update Single property

        :param property:
        :return:
        """
        self.setUpdatesEnabled(False)

        propWidgets = self.widgetsByProperty(property)
        self._blockSave = True

        for w in propWidgets:
            self._updateWidget(w)

        self.blockSignalsWidgets(propWidgets, False)
        self.setUpdatesEnabled(True)
        self._blockSave = False

    def updateFromProperties(self):
        """ Fill in the widgets based on the properties.  Will affect widgets linked in the toolset UI via:

            self.linkProperty(widget, "propertyKey")
            or
            self.toolsetWidget.linkProperty(widget, "propertyKey")

        Block callbacks, block signals and disable updates while updating properties.  This stops loops.

        Unsupported widgets can be added here or manually added directly in the toolset ui
        after super() on the overridden updateFromProperties() class in a single toolset tool GUI
        """
        self.blockCallbacks(True)

        self.setUpdatesEnabled(False)

        propWidgets = self.propertyWidgets()
        self._blockSave = True

        for w in propWidgets:
            self._updateWidget(w)

        self.blockSignalsWidgets(propWidgets, False)
        self.setUpdatesEnabled(True)
        self._blockSave = False
        self.blockCallbacks(False)

    def _updateWidget(self, w):
        """ Update widget

        :param w:
        :return:
        """
        modified = None
        if self.toolsetWidgetUpdateAllowed(w):
            w.blockSignals(False)
        else:
            w.blockSignals(True)

        # Get the info related to the widget
        info = SUPPORTED_TYPES_INFO.get(
            type(w))  # eg. info = ("itemChanged", [("setIndex", "currentIndex")]), # from elements.ComboBoxRegular:

        for i, getset in enumerate(info[GET_SETTER_LIST]):  # eg. info[GET_SETTER_LIST] = [("setIndex", "currentIndex")]
            if i == 0:
                prop = "value"
            else:
                prop = getset[VALUE_GET]
            widgetName = self.widgetName(w)
            value = self.properties[widgetName][prop]
            modified = False

            if info:  # Set the widget the data from the property
                setter = getattr(w, getset[VALUE_SETTER])
                try:
                    setter(value)  # Set the new value to the widget
                except TypeError:
                    raise TypeError("Unable to set widget attribute method: {},"
                                    " property: {}, value: {}".format(widgetName, getset[VALUE_SETTER], value))
                modified = True

        if not modified:
            if self.showWarnings:
                logger.warning(
                    "updateFromProperties(): Unsupported widget: {}. Property: {}".format(w, self.widgetName(w)))

    def widgetValues(self, widget):
        """ Returns the value of the widget depending on the widget type

        :param widget: The qt widget that will return its value
        :type widget: QtWidgets.QWidget
        :rtype: dict
        """
        info = SUPPORTED_TYPES_INFO.get(type(widget))

        if info:
            ret = {}
            for i, getset in enumerate(info[GET_SETTER_LIST]):
                getter = getattr(widget, getset[VALUE_GET])  # get the value from the widget
                if i == 0:
                    prop = "value"  # First value has to be value
                else:
                    prop = getset[VALUE_GET]
                ret[prop] = getter()
            extraProps = {}

            # Add extra properties as described by user in the "extraProperties" property
            if isinstance(widget.property("extraProperties"), dict):
                extraProps.update(widget.property("extraProperties"))

            # add the extra values
            for k, v in extraProps.items():
                ret[k] = getattr(widget, v)()

            return ret

        if self.showWarnings:
            logger.warning("Unsupported widget: {}. Property: {}".format(widget, self.widgetName(widget)))
        return {}

    def widgetName(self, widget):
        """ The name of the property that is linked to the widget.

        Eg self.comboEdit --> self.properties.comboEdit. "comboEdit" is returned, unless it has already been linked prior

        :param widget:
        :type widget: QtWidgets.QWidget
        :return:
        :rtype:
        """
        return widget.property("prop")

    def setAllowToolsetUpdate(self, w, allow=True):
        """ Usually when running updateFromProperties() signals are blocked. If allow is True it will
        allow it to send the signal.

        :return:
        :rtype:
        """
        w.setProperty("toolsetSwitchUpdate", allow)

    def toolsetWidgetUpdateAllowed(self, w):
        """ Return true if toolset widget update signals are allowed through. False otherwise

        :param w:
        :return:
        """
        return w.property("toolsetSwitchUpdate")

    def blockSignalsWidgets(self, widgets, block):
        """ Block or unblock signals from widgets

        :param widgets:
        :type widgets: list of QtWidgets.QWidget
        :param block:
        :type block: bool
        :return:
        :rtype:
        """
        for w in widgets:
            w.blockSignals(block)

    def setupProperties(self, properties=None):
        """ Initialize all the properties dicts and return them

        :param properties:
        :type properties:
        :return:
        :rtype: PropertiesDict
        """
        toolProps = properties or self.initializeProperties()
        instanceProp = PropertiesDict()
        for p in toolProps:
            instanceProp[p["name"]] = PropertiesDict(**p)

            # set default value
            if "default" not in instanceProp[p["name"]]:
                instanceProp[p["name"]].default = instanceProp[p["name"]].value

        return instanceProp

    def updateDisplayButton(self):
        """ Updates the display button based on number of widgets in the stackedLayout.

        :return:
        """

        self.setDisplays(self.count())

    def setDisplays(self, displays):

        if displays in [Displays.Single, Displays.Double, Displays.Triple]:
            self.displayModeButton.setDisplays(displays)
        else:
            logger.error("setDisplays(): Must be 2 or 3!")  # Unless we want more than 2 or 3 then change this

    def initializeProperties(self):
        """ Properties of the toolsetWidget

        :return:
        :rtype:
        """
        # Usually overridden
        return []

    def count(self):
        return self.stackedWidget.count()

    def addStackedWidget(self, widget):
        """

        :param widget: The method to create the widgets for the ToolsetWidgetItems.
                                     eg initAdvancedWidget, initCompactWidget. Or QWidget instance
        :type widget: callable or QtWidgets.QWidget
        :return:
        """

        if widget is None:
            raise ValueError("Toolset \"{}\": contents() must return list of widgets. None found".format(
                str(self.__class__.__name__)))

        self._widgets.append(widget)
        widget.setParent(self.widgetHider)
        widget.setProperty("color", self.iconColor)

        self.stackedWidget.addWidget(widget)

    def itemAt(self, index):
        """

        :param index:
        :return:
        """
        return self.stackedWidget.widget(index)

    def toolsetClosedEvent(self):
        """ Toolset closed event

        :return:
        :rtype:
        """
        self.toolsetClosed.emit()
        if self.treeWidget._toolsetFrame:
            self.treeWidget._toolsetFrame.toolsetClosed.emit(self)

    def connections(self):
        """ Connections

        :return:
        :rtype:
        """
        super(ToolsetWidgetBase, self).connections()

        self.titleFrame.deletePressed.connect(self.toolsetClosedEvent)

        if self.toolsetWidgetItem:
            self.displayModeButton.clicked.connect(self.toolsetWidgetItem.setCurrentIndex)
            self.displayModeButton.clicked.connect(lambda: self.displaySwitched.emit())
            self.displaySwitched.connect(lambda: self.updateRequested.emit())

    def setCurrentIndex(self, index):
        """ Set the current index of the stacked widget for the toolsetwidget

        :param index:
        :type index:
        :return:
        :rtype:
        """

        self.blockSave(True)
        # Make sure everything is squished
        for i in range(0, self.stackedWidget.count()):
            w = self.stackedWidget.widget(i)
            w.setSizePolicy(w.sizePolicy().horizontalPolicy(), QtWidgets.QSizePolicy.Ignored)

        self.stackedWidget.setCurrentIndex(index)

        widget = self.stackedWidget.widget(index)
        if widget is not None:
            widget.setSizePolicy(widget.sizePolicy().horizontalPolicy(), QtWidgets.QSizePolicy.Expanding)
        else:
            logger.warning("Widget not found for ToolsetWidget.setCurrentIndex()!")
        self.blockSave(False)

    def blockSignals(self, b):
        """ Makes sure the signals and its childrens signals are blocked

        :param b:
        :type b:
        :return:
        :rtype:
        """
        super(ToolsetWidgetBase, self).blockSignals(b)
        [w.blockSignals(b) for w in utils.iterChildren(self)]

    def blockSave(self, block):
        self._blockSave = block

    def visualUpdate(self, collapse=True):
        """ Update visuals based on opened or closed

        :param collapse:
        :return:
        """
        if collapse:
            self.setIconColor(color.desaturate(self.iconColor, 0.75), setColour=False)
            self.titleTextWidget().setObjectName("disabled")
            self.titleTextWidget().setStyleSheet("")

        else:
            self.setIconColor(self.iconColor)
            self.titleTextWidget().setObjectName("active")

            # self.titleTextWidget().setStyleSheet("color: rgb{}; font-weight: bold".format(color.desaturate(self.iconColor, 0.2)))

        utils.updateStyle(self.titleTextWidget())

        self.setUpdatesEnabled(False)
        self.updatePropertyRequested.emit()
        self.setUpdatesEnabled(True)

    def activateEvent(self, event, emit=True):
        self.toggleContents(emit)
        event.ignore()

    def setActive(self, active=True, emit=True):
        """

        :param active:
        :param emit: emit signal (true) or don't emit (false)
        :type emit: bool
        :return:
        """
        if active:
            self.expand(emit=emit)
        else:
            self.collapse(emit=emit)
            utils.singleShotTimer(
                lambda: self.toolsetHidden.emit())  # todo if toolset hidden is the correct signal to use here

        self.visualUpdate(collapse=not active)

    def setIconColor(self, col=(255, 255, 255), setColour=True):
        """Sets the icon colour for all the icons including the item icon, and move icon and the close icon

        :param col: the colour in rgb 0-255 range
        :type col: tuple
        :param setColour: saves the current colour over writing self.iconColor
        :type setColour: bool
        """
        if setColour:
            self.iconColor = col

        darken = 0.8

        self.setItemIconColor(col)
        self.displayModeButton.setIconColor(col)
        self.helpButton.setIconColor((col[0] * darken, col[1] * darken, col[2] * darken))
        self.titleFrame.deleteBtn.setIconColor(col)

    @property
    def toolsetUi(self):
        return self.treeWidget.toolsetFrame.toolsetUi

    def propertyWidgets(self, widget=None, currentWidget=False):
        """ Get the property widgets from the stackWidget

        :param currentWidget: Set this to true if we want to only search the current active widget or all the widgets in
                              the stackedWidget
        :type currentWidget:
        :param widget:
        :type widget:
        :return:
        :rtype:
        """

        if currentWidget:
            widget = widget or self.stackedWidget.currentWidget()
        else:
            widget = widget or self.stackedWidget
        ret = []
        for c in utils.iterChildren(widget, skip="skipChildren"):
            if c.property("prop") is not None:
                ret.append(c)

        return ret

    def widgetsByProperty(self, propertyName):
        """ Get the property widgets from the stackWidget
        """

        widget = self.stackedWidget
        ret = []
        for c in utils.iterChildren(widget, skip="skipChildren"):
            if c.property("prop") == propertyName:
                ret.append(c)

        return ret

    def mousePressEvent(self, event):
        """ Mouse Press event.

        :param event:
        :type event:
        :return:
        :rtype:
        """

        # Force the focus out event as it doesn't always get called
        utils.clearFocusWidgets()
        self.toolsetMousePressed.emit()
        self.switchOnClick()
        super(ToolsetWidgetBase, self).mousePressEvent(event)

    def switchOnClick(self):
        if self.treeWidget._toolsetFrame.switchOnClick:
            self.treeWidget._toolsetFrame.setGroupFromToolset(self.id)

    @staticmethod
    def undoDecorator(func):
        return func

    def openUndoChunk(self, name=None):
        """Opens the undo chunk. Overridden by subclasses """
        pass

    def closeUndoChunk(self, name=None):
        """Closes the undo chunk. Overridden by subclasses"""
        pass


class PropertiesDict(general.ObjectDict):
    def update(self, others, convertDict=False):
        """ Update dicts found in the items as well

        :param others: The dictionary to update this object with
        :type others: dict
        :param convertDict: Convert the dictionaries in others items to PropertyDict
        :type convertDict: bool
        :return:
        :rtype:
        """

        if convertDict:
            for k, d in others.items():
                others[k] = PropertiesDict(**d) if type(d) == dict else others[k]
        super(PropertiesDict, self).update(others)

    def get(self, *args, **kwargs):
        """

        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype: PropertiesDict or None
        """
        return super(PropertiesDict, self).get(*args, **kwargs)


class Displays:
    """ Display modes for the toolset widget items

    todo: possibly deprecated since the code should be able to handle any amount of displays

    """
    Single = 1
    Double = 2
    Triple = 3


class DisplayModeButton(elements.ExtendedButton):
    _menuIconTriple = ["menuTripleEmpty", "menuTripleOne", "menuTripleTwo", "menuTripleFull"]
    _menuIconDouble = ["menuDoubleEmpty", "menuDoubleOne", "menuDoubleFull"]

    clicked = QtCore.Signal(object)
    LastIndex = -1
    FirstIndex = 1

    def __init__(self, parent=None, size=16, color=(255, 255, 255), initialIndex=FirstIndex):
        super(DisplayModeButton, self).__init__(parent=parent)
        self.currentIcon = None
        self.icons = None  # type: list # _menuIconTriple or _menuIconDouble
        self.displays = None
        self.initialDisplay = initialIndex

        self.currentSize = size
        self.setIconSize(QtCore.QSize(size, size))
        self.iconColor = color
        self.setDisplays(Displays.Double)
        self.highlightOffset = 40

    def setDisplays(self, displays=Displays.Triple):
        """ Set number of displays,

        :param displays: Can be Displays.Triple or Displays.Double
        :return:
        """
        self.displays = displays
        self.show()

        if displays == 3:
            self.icons = self._menuIconTriple
        elif displays == 2:
            self.icons = self._menuIconDouble
        elif displays == 1:
            self.hide()
        else:
            logger.error("setNumDisplays can only be 2 or 3!")

        self.currentIcon = self.icons[self.initialDisplay]
        self.setIconIndex(self.initialDisplay)

    def setIconIndex(self, index, size=None, color=None):
        """ Set icon by index

        :param index:
        :return:
        """
        if size is None:
            size = self.currentSize

        if color is None:
            color = self.iconColor

        self.setIconByName(self.icons[index], size=size, colors=color)

    def mousePressEvent(self, event):
        self.setDown(False)

    def mouseReleaseEvent(self, event):
        # Next item in the queue
        newIcon, newIndex = self.nextIcon()

        self.setIconByName(newIcon, size=self.currentSize, colors=self.iconColor)

        self.currentIcon = newIcon
        self.clicked.emit(newIndex - 1)

    def nextIcon(self):
        startFrom = 1

        # wip: we dont want it to be 0 at the moment
        newIndex = max((self.icons.index(self.currentIcon) + 1) % len(self.icons),
                       startFrom)

        newIcon = self.icons[newIndex]
        return newIcon, newIndex


# Application dependent code
if not env.isMaya():
    ToolsetWidget = ToolsetWidgetBase
else:
    from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya

    ToolsetWidget = toolsetwidgetmaya.ToolsetWidgetMaya
