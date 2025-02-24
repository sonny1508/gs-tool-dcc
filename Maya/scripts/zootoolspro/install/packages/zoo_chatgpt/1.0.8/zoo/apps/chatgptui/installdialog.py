import webbrowser

from zoo.core import api
from zoo.libs.utils import output
from zoo.libs.pyqt.widgets import elements
from zoovendor.Qt import QtWidgets, QtCore
from zoo.libs.pyqt import utils, uiconstants as uic
from zoo.libs import iconlib
from zoo.apps.chatgptui import constants


class InstallDialog(elements.ZooWindowThin):

    def __init__(self, name="KeyRequired", title="`Install `Zoo Chat GPT`", parent=None, resizable=True, width=340,
                 height=80, modal=False, alwaysShowAllTitle=False, minButton=False, maxButton=False, onTop=False,
                 saveWindowPref=False, titleBar=None, overlay=True, minimizeEnabled=True, initPos=None):
        super(InstallDialog, self).__init__(name, title, parent, resizable, width, height, modal, alwaysShowAllTitle,
                                            minButton, maxButton, onTop, saveWindowPref, titleBar, overlay,
                                            minimizeEnabled, initPos)
        self.result = ""
        self.msgClosed = False
        iconSize = 32
        image = QtWidgets.QToolButton(parent=self)
        image.setIcon(iconlib.iconColorizedLayered("warning", iconSize, colors=(220, 210, 0)))
        image.setIconSize(utils.sizeByDpi(QtCore.QSize(iconSize, iconSize)))
        image.setFixedSize(utils.sizeByDpi(QtCore.QSize(iconSize, iconSize)))

        titleLabel = elements.Label("Please Read:", bold=True, parent=self)
        text = constants.INSTALL_DIALOG_MESSAGE.format(api.currentConfig().cacheFolderPath())
        textLabel = elements.Label(text, bold=False, parent=self)
        okBtn = elements.styledButton("Install Open AI", "checkMark", parent=self)
        cancelBtn = elements.styledButton("Cancel", "xCircleMark")

        helpBtn = elements.styledButton("More Information", "help")

        # Layout --------------------------------
        mainLayout = elements.vBoxLayout(spacing=0,
                                         margins=(uic.REGPAD, uic.REGPAD, uic.REGPAD, uic.REGPAD))

        iconLayout = elements.vBoxLayout(spacing=uic.SREG, margins=(0, 0, 0, 0))
        iconLayout.addWidget(image)
        spacer = elements.Spacer(1, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        iconLayout.addItem(spacer)

        messageLayout = elements.vBoxLayout(spacing=uic.SLRG, margins=(0, 0, 0, 0))
        messageLayout.addWidget(titleLabel)
        messageLayout.addWidget(textLabel)

        topLayout = elements.hBoxLayout(spacing=uic.SVLRG2,
                                        margins=(uic.WINSIDEPAD, uic.BOTPAD, uic.WINSIDEPAD, uic.TOPPAD))
        topLayout.addLayout(iconLayout, 1)
        topLayout.addLayout(messageLayout, 2)

        buttonLayout = elements.hBoxLayout(spacing=uic.SREG, margins=(0, uic.TOPPAD, 0, 0))
        buttonLayout.addWidget(okBtn)
        buttonLayout.addWidget(cancelBtn)
        buttonLayout.addWidget(helpBtn)

        # Add To Main Layout ---------------------
        mainLayout.addLayout(topLayout)
        mainLayout.addLayout(buttonLayout)
        self.setMainLayout(mainLayout)

        # Connections -------------------------------
        okBtn.clicked.connect(self.okPressed)
        cancelBtn.clicked.connect(self.cancelPressed)
        helpBtn.clicked.connect(self._help)

    def _help(self):
        output.displayInfo("Opening help webpage: {}".format(constants.HELP_URL))
        webbrowser.open(constants.HELP_URL)

    def cancelPressed(self):
        self.result = False
        self.msgClosed = True
        self.close()

    def okPressed(self):
        """ Open the dialog
        """
        self.result = True
        self.msgClosed = True
        self.close()
