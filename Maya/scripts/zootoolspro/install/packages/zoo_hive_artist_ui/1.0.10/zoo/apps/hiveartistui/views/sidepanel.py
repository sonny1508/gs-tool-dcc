from zoovendor.Qt import QtWidgets


class SidePanel(QtWidgets.QStackedWidget):
    def __init__(self, parent=None, themePref=None, startHidden=True):
        """ Side panel (currently on the right panel)

        :param parent:
        :param themePref:
        :param startHidden:
        """
        super(SidePanel, self).__init__(parent=parent)

        self.propertiesPanel = None


        if startHidden:
            self.hide()

    def activateProperties(self):
        """ Activate the properties panel

        :return:
        """
        self.setCurrentWidget(self.propertiesPanel)


