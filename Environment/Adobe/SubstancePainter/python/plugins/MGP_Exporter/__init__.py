import importlib

from PySide6 import QtGui

import substance_painter.ui as sbsui

from . import dialogs
from . import utilities as util
from .ui import (icon)

importlib.reload(icon)
importlib.reload(dialogs)
importlib.reload(util)


def showErrorDialog():
	"""Opens the error dialog showing to the user that something went wrong during the installation of the needed dependencies.
	
	And guiding the user to the manual dependecies installation guide on the documentation website
	"""	
	mainWindow = sbsui.get_main_window()
	dialog = dialogs.DependencyErrorDialog(mainWindow)
	dialog.show()

class Data(object):
	"""Dataclass used to store references to items so they dont get garbage collected
	"""    
	toolbar = None

def openSettingsDialog():
	"""Opens the Setings dialog for the user to change the socket port number and other import settings
	"""
	mainWindow = sbsui.get_main_window()
	dialog = dialogs.SettingsDialog(mainWindow)
	dialog.show()

def createToolBar(): 
	"""Creates the toolbar containing the action to open the Settings Dialog
	"""    
	Data.toolbar = sbsui.add_toolbar("MGP Material Manager", "materialManagerMGP")
	qicon = QtGui.QIcon()
	qicon.addPixmap(icon.getIconAsQPixmap("GS_Mat_Manager_logo_idle.png"))
	qicon.addPixmap(icon.getIconAsQPixmap("GS_Mat_Manager_logo.png"), QtGui.QIcon.Active)
	action = Data.toolbar.addAction(qicon, None)
	action.triggered.connect(openSettingsDialog)

def start_plugin():
	"""**Entry point** of the plugin.
	"""
	# =================================================
	# Get reference to qt window of substance painter
	mainWindow = sbsui.get_main_window()
	# =================================================
	# if checkDependencies():
	createToolBar()
	# =================================================


def close_plugin():
	"""**Exit point** of the plugin.

	Here we perform the clean up before closing the plugin, stopping the socket thread and removing the toolbar action
	"""
	mainWindow = sbsui.get_main_window()
	if Data.toolbar:
		sbsui.delete_ui_element(Data.toolbar)
