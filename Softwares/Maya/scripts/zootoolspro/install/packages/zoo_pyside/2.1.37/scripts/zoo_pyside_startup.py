
def startup(package):
    from zoo.libs.pyqt import stylesheet
    from zoovendor.Qt import QtWidgets
    if QtWidgets.QApplication.instance() is not None:
        stylesheet.loadDefaultFonts()


def shutdown(package):
    from zoo.libs.pyqt import stylesheet
    from zoovendor.Qt import QtWidgets
    if QtWidgets.QApplication.instance() is not None:
        stylesheet.unloadFonts()
