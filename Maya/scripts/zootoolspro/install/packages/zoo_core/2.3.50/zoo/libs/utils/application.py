from zoo.core.util import env

if env.isMaya():
    from zoo.libs.maya.utils.application import saveCurrentScene, restartMaya
    from zoo.libs.maya.qt import mayaui
    from maya import cmds

    saveScene = saveCurrentScene
    restart = restartMaya
    quit = cmds.quit
    mainWindow = mayaui.getMayaWindow

else:
    def mainWindow():
        pass


    def quit():
        pass


    def saveScene():
        pass


    def restart(force=False, delay=3):
        pass
