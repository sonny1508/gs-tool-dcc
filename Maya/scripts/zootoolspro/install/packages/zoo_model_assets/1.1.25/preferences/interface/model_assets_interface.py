from zoo.preferences.core import prefinterface
from zoo.preferences.assets import BrowserPreference
from zoo.core.util import zlogging


logger = zlogging.getLogger(__name__)


class ModelAssetsPreference(prefinterface.PreferenceInterface):
    id = "model_assets_interface"
    _relativePath = "prefs/maya/zoo_model_assets.pref"

    def __init__(self, preference):
        super(ModelAssetsPreference, self).__init__(preference)
        self.modelAssetsPreference = BrowserPreference("model_assets", self)
