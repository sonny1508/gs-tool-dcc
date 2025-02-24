"""
from zoo.libs.skinwrangler import skinwrangler
skinwrangler.skinWrangler()

"""


import webbrowser

from zoo.libs.utils import output

def skinWrangler():
    try:
        from skinWrangler import skinWranglerui
        skinWranglerWindow = skinWranglerui.show()
    except Exception as e:
        address = "https://create3dcharacters.com/maya-third-party/#skinwrangler"
        webbrowser.open(address)
        output.displayWarning("Skin Wrangler is a third party script and is not installed correctly, "
                              "please install from the instructions at {}.".format(address))