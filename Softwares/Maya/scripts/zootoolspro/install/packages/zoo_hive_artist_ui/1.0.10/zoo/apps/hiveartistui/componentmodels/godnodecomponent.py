from zoo.apps.hiveartistui import model
from zoo.apps.hiveartistui.views import componentsettings


class GodNodeComponentModel(model.ComponentModel):
    """Base Class for Vchain class and subclasses to support better UI
    organization.
    """
    componentType = "godnodecomponent"

    def createWidget(self, componentWidget, parentWidget):
        return GodNodeSettingsWidget(componentWidget,
                                     parentWidget,
                                     componentModel=self)


class GodNodeSettingsWidget(componentsettings.ComponentSettingsWidget):
    showSpaceSwitching = False

    def __init__(self, componentWidget, parent, componentModel):
        super(GodNodeSettingsWidget, self).__init__(componentWidget, parent, componentModel)
