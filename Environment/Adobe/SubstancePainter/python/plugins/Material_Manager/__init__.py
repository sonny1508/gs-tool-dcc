import importlib
import os
import platform
import subprocess
import sys
from pathlib import Path

import PySide6
from PySide6 import QtCore, QtGui, QtWidgets

import substance_painter.ui as sbsui

from . import dialogs
from . import utilities as util
from .ui import icon

# Only reload modules if they're already loaded to avoid unnecessary overhead
if 'icon' in sys.modules:
    importlib.reload(icon)
if 'dialogs' in sys.modules:
    importlib.reload(dialogs)
if 'util' in sys.modules:
    importlib.reload(util)


def showErrorDialog():
    """Opens the error dialog showing to the user that something went wrong during the installation of the needed dependencies.
    
    And guiding the user to the manual dependencies installation guide on the documentation website
    """    
    try:
        mainWindow = sbsui.get_main_window()
        dialog = dialogs.DependencyErrorDialog(mainWindow)
        dialog.show()
    except Exception as e:
        print(f"Error showing dependency dialog: {e}")


class Data(object):
    """Dataclass used to store references to items so they don't get garbage collected"""    
    toolbar = None
    settings_dialog = None  # Cache the dialog to avoid recreating it


def openSettingsDialog():
    """Opens the Settings dialog for the user to change the socket port number and other import settings"""
    try:
        mainWindow = sbsui.get_main_window()
        
        # Reuse existing dialog if it exists and is still valid
        if (Data.settings_dialog is None or 
            not Data.settings_dialog.isVisible() or 
            Data.settings_dialog.parent() != mainWindow):
            
            # Clean up old dialog if it exists
            if Data.settings_dialog:
                Data.settings_dialog.deleteLater()
            
            # Create new dialog
            Data.settings_dialog = dialogs.SettingsDialog(mainWindow)
        
        # Show the dialog
        Data.settings_dialog.show()
        Data.settings_dialog.raise_()
        Data.settings_dialog.activateWindow()
        
    except Exception as e:
        print(f"Error opening settings dialog: {e}")


def createToolBar(): 
    """Creates the toolbar containing the action to open the Settings Dialog"""    
    try:
        # Check if toolbar already exists to avoid duplicates
        if Data.toolbar is not None:
            return
        
        Data.toolbar = sbsui.add_toolbar("Material Manager", "materialManager")
        
        # Create icon with better error handling
        qicon = QtGui.QIcon()
        try:
            idle_pixmap = icon.getIconAsQPixmap("logo_idle.png")
            active_pixmap = icon.getIconAsQPixmap("logo.png")
            
            if not idle_pixmap.isNull():
                qicon.addPixmap(idle_pixmap)
            if not active_pixmap.isNull():
                qicon.addPixmap(active_pixmap, QtGui.QIcon.Active)
                
        except Exception as e:
            print(f"Error loading toolbar icons: {e}")
            # Fallback to default icon if custom icons fail
            qicon = QtGui.QIcon()
        
        # Create action
        action = Data.toolbar.addAction(qicon, "Material Manager")
        action.setToolTip("Open Material Manager")
        action.triggered.connect(openSettingsDialog)
        
    except Exception as e:
        print(f"Error creating toolbar: {e}")


def start_plugin():
    """**Entry point** of the plugin."""
    try:
        print("Starting Material Manager plugin...")
        
        # Get reference to qt window of substance painter
        mainWindow = sbsui.get_main_window()
        if mainWindow is None:
            print("Warning: Could not get main window reference")
            return
        
        # Create toolbar
        createToolBar()
        
        print("Material Manager plugin started successfully")
        
    except Exception as e:
        print(f"Error starting Material Manager plugin: {e}")
        # Show error dialog as fallback
        try:
            showErrorDialog()
        except:
            pass  # Avoid cascading errors


def close_plugin():
    """**Exit point** of the plugin.

    Here we perform the clean up before closing the plugin, stopping any running processes and removing the toolbar action
    """
    try:
        print("Closing Material Manager plugin...")
        
        # Clean up settings dialog
        if Data.settings_dialog:
            try:
                # Stop any background operations in the dialog
                if hasattr(Data.settings_dialog, 'stop_thumbnail_worker'):
                    Data.settings_dialog.stop_thumbnail_worker()
                
                # Close and clean up dialog
                if Data.settings_dialog.isVisible():
                    Data.settings_dialog.close()
                Data.settings_dialog.deleteLater()
                Data.settings_dialog = None
                
            except Exception as e:
                print(f"Error cleaning up settings dialog: {e}")
        
        # Clean up toolbar
        if Data.toolbar:
            try:
                sbsui.delete_ui_element(Data.toolbar)
                Data.toolbar = None
            except Exception as e:
                print(f"Error removing toolbar: {e}")
        
        print("Material Manager plugin closed successfully")
        
    except Exception as e:
        print(f"Error closing Material Manager plugin: {e}")


# Optional: Add plugin metadata for better management
__plugin_name__ = "Material Manager"
__plugin_version__ = "2.0.0"
__plugin_author__ = "Sonny"
__plugin_description__ = "Advanced material management system for Substance Painter"