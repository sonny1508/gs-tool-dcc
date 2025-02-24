
from zoo.preferences.core import prefinterface

# 1. Rename filename
# 2. Set _relativePath to the location of your pref file
from zoo.preferences.assets import BrowserPreference


class ShaderPreference(prefinterface.PreferenceInterface):
    id = "shader_interface"
    _relativePath = "prefs/maya/zoo_shader_tools.pref"

    def __init__(self, preference):
        super(ShaderPreference, self).__init__(preference)
        self.shaderPresetsAssets = BrowserPreference("shaders", self, fileTypes=["zooScene"])
        self.mayaShaderAssets = BrowserPreference("maya_shaders", self, fileTypes=["ma"])
