import importlib
import sys
import json
import os
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QStandardPaths

from . import config
from .ui import dialogs_UI

import substance_painter.export
import substance_painter.resource
import substance_painter.ui
import substance_painter.project
import substance_painter.textureset
import substance_painter.event

importlib.reload(dialogs_UI)


class SettingsDialog(QtWidgets.QDialog, dialogs_UI.Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.background_color = "#262626"

        # JSON file path
        self.json_file_path = os.path.join(QStandardPaths.writableLocation(QStandardPaths.TempLocation),
                                           "export_app_config.json")

        # all texture set
        self.items = []

        allstack = substance_painter.textureset.all_texture_sets()
        for item in allstack:
            if "mat_" in item.name():
                self.items.append(item.name())

        self.checkboxes = []

        # Additional checkboxes
        self.additional_checkboxes = []

        # Initialize layout and UI
        self.initUI()

        # Load saved configuration if it exists
        self.load_config()

    def initUI(self):
        main_layout = QtWidgets.QVBoxLayout()

        # Create checkboxes for each item in the list
        for item in self.items:
            # Create a layout for the row
            row_layout = QtWidgets.QVBoxLayout()

            checkbox_layout = QtWidgets.QHBoxLayout()
            checkbox = QtWidgets.QCheckBox(item, self)
            checkbox.stateChanged.connect(self.update_export_button)
            checkbox_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

            # Add additional clearcoat mask checkboxes next to Livery, cockpit and mechanics
            if item == "mat_livery":
                # Add livery clearcoat
                livery_mask_checkbox = QtWidgets.QCheckBox("Livery Clearcoat", self)
                livery_mask_checkbox.stateChanged.connect(self.update_export_button)
                checkbox_layout.addWidget(livery_mask_checkbox)
                self.additional_checkboxes.append(livery_mask_checkbox)

                #Add Livery Carbon
                #livery_carbon_checkbox = QtWidgets.QCheckBox("Livery Carbon", self)
                #livery_carbon_checkbox.stateChanged.connect(self.update_export_button)
                #checkbox_layout.addWidget(livery_carbon_checkbox)
                #self.additional_checkboxes.append(livery_carbon_checkbox)
            elif item == "mat_cockpit":
                cockpit_mask_checkbox = QtWidgets.QCheckBox("Cockpit Clearcoat", self)
                cockpit_mask_checkbox.stateChanged.connect(self.update_export_button)
                checkbox_layout.addWidget(cockpit_mask_checkbox)
                self.additional_checkboxes.append(cockpit_mask_checkbox)
            elif item == "mat_mechanics":
                mechanics_mask_checkbox = QtWidgets.QCheckBox("Mechanics Clearcoat", self)
                mechanics_mask_checkbox.stateChanged.connect(self.update_export_button)
                checkbox_layout.addWidget(mechanics_mask_checkbox)
                self.additional_checkboxes.append(mechanics_mask_checkbox)

            row_layout.addLayout(checkbox_layout)

            # Add a horizontal line after each row
            line = QtWidgets.QFrame(self)
            line.setFrameShape(QtWidgets.QFrame.HLine)
            line.setFrameShadow(QtWidgets.QFrame.Sunken)
            row_layout.addWidget(line)

            main_layout.addLayout(row_layout)

        # QLineEdit to display the selected path
        self.path_line_edit = QtWidgets.QLineEdit(self)
        self.path_line_edit.setPlaceholderText("Select directory for export...")
        main_layout.addWidget(self.path_line_edit)

        p_path = substance_painter.project.file_path()
        d_path = os.path.dirname(p_path) + "/"
        self.path_line_edit.setText(d_path)

        # ComboBox with values "001", "002", "003", "004"
        self.combo_box = QtWidgets.QComboBox(self)
        self.combo_box.addItems(["001", "002", "003", "004", "005", "006", "007", "008", "009", "010", "011", "012", "013", "014", "015", "016", "017", "018",
                                 "019", "020", "021", "022", "023", "024", "025", "026", "027", "028", "029", "030"])
        main_layout.addWidget(self.combo_box)

        # Button to browse and select a path
        self.browse_button = QtWidgets.QPushButton('Browse Path', self)
        self.browse_button.clicked.connect(self.open_folder_dialog)
        main_layout.addWidget(self.browse_button)

        # Export button to create the text file with selected items
        self.export_button = QtWidgets.QPushButton('Export', self)
        self.export_button.clicked.connect(self.export_textures)
        self.export_button.setEnabled(False)  # Initially disabled
        main_layout.addWidget(self.export_button)

        self.setLayout(main_layout)
        self.setWindowTitle("MGP Exporter")
        self.resize(500, 400)

    def open_folder_dialog(self):
        # Open the file dialog to select a folder
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")

        # If a folder was selected, update the QLineEdit
        if folder_path:
            self.path_line_edit.setText(folder_path)

    def update_export_button(self):
        # Enable export button if any checkbox is checked, otherwise disable
        all_checkboxes = self.checkboxes + self.additional_checkboxes
        any_checked = any(checkbox.isChecked() for checkbox in all_checkboxes)
        self.export_button.setEnabled(any_checked)

    def export_textures(self):
        # Verify if a project is open before trying to export something
        if not substance_painter.project.is_open():
            return
        # Get Path
        Path = self.path_line_edit.text() + "/"

        if os.path.isdir(Path):

            # Gather names of checked items
            checked_items = [checkbox.text() for checkbox in self.checkboxes + self.additional_checkboxes if
                             checkbox.isChecked()]
            # Get selected value from combo box
            combo_value = self.combo_box.currentText()

            # Get the currently active layer stack (paintable)
            stack = substance_painter.textureset.get_active_stack()

            # Get the parent Texture Set of this layer stack
            material = stack.material()

            # Setup the export settings
            # resolution = material.get_resolution()

            for item in checked_items:
                print(item)
                texsets = substance_painter.textureset.all_texture_sets()
                for texset in texsets:
                    if texset.name() == item:
                        if "brake" in texset.name() or "glass" in texset.name():
                            exp_pre = "MGP-A"
                        else:
                            exp_pre = "MGP"

                        # Build Export Preset resource URL
                        # - Context: name of the library where the resource is located
                        # - Name: name of the resource (filename without extension or Substance graph path)
                        export_preset = substance_painter.resource.ResourceID(
                            context="mgp",
                            name=exp_pre)

                        print("Preset:")
                        print(export_preset.url())

                        resolution = texset.get_resolution()
                        # Build the configuration
                        config = {
                            "exportShaderParams": False,
                            "exportPath": Path,
                            "exportList": [{"rootPath": item}],
                            "exportPresets": [{"name": "default", "maps": []}],
                            "defaultExportPreset": export_preset.url(),
                            "exportParameters": [
                                {
                                    "parameters": {"paddingAlgorithm": "infinite"}
                                }
                            ]
                        }

                        # substance_painter.export.export_project_textures( config )

                        # Actual export operation:
                        export_result = substance_painter.export.export_project_textures(config)

                        # Iterate through files in the given directory
                        direct = []
                        for stack, files in export_result.textures.items():
                            for exported_filename in files:
                                direct.append(os.path.abspath(exported_filename))

                        for file_path in direct:
                            directory, filename = os.path.split(file_path)

                            # Check if filename starts with "mat_"
                            if filename.startswith("mat_"):
                                # Remove "mat_" from the beginning of the filename
                                filename = filename[4:]

                                # Find the position to insert "001"
                                insert_position = len(filename) - 6  # Assuming a 6-letter extension
                                new_filename = filename[:insert_position] + combo_value + filename[insert_position:]

                                # Construct the full new file path
                                new_file_path = os.path.join(directory, new_filename)

                                # Rename (overwrite if exists)
                                os.replace(file_path, new_file_path)

                if item == "Livery Clearcoat" or item == "Cockpit Clearcoat" or item == "Mechanics Clearcoat":
                    exp_pre = "MGP-A_Clearcoat"

                    # Build Export Preset resource URL
                    # - Context: name of the library where the resource is located
                    # - Name: name of the resource (filename without extension or Substance graph path)
                    export_preset = substance_painter.resource.ResourceID(
                        context="mgp",
                        name=exp_pre)

                    print("Preset:")
                    print(export_preset.url())

                    # Using item for textureset
                    exp_item = "mat_livery"
                    if "Livery Clearcoat" in item:
                        exp_item = "mat_livery"
                    elif "Cockpit Clearcoat" in item:
                        exp_item = "mat_cockpit"
                    elif "Mechanics Clearcoat" in item:
                        exp_item = "mat_mechanics"

                    resolution = texset.get_resolution()
                    # Build the configuration
                    config = {
                        "exportShaderParams": False,
                        "exportPath": Path,
                        "exportList": [{"rootPath": exp_item}],
                        "exportPresets": [{"name": "default", "maps": []}],
                        "defaultExportPreset": export_preset.url(),
                        "exportParameters": [
                            {
                                "parameters": {"paddingAlgorithm": "infinite"}
                            }
                        ]
                    }

                    # substance_painter.export.export_project_textures( config )

                    # Actual export operation:
                    export_result = substance_painter.export.export_project_textures(config)

                    # Iterate through files in the given directory
                    direct = []
                    for stack, files in export_result.textures.items():
                        for exported_filename in files:
                            direct.append(os.path.abspath(exported_filename))

                    for file_path in direct:
                        directory, filename = os.path.split(file_path)

                        # Check if filename starts with "mat_"
                        if filename.startswith("mat_"):
                            # Remove "mat_" from the beginning of the filename
                            filename = filename[4:]

                            # Find the position to insert "001"
                            insert_position = len(filename) - 19  # Assuming a 19-letter extension
                            new_filename = filename[:insert_position] + combo_value + filename[insert_position:]

                            # Construct the full new file path
                            new_file_path = os.path.join(directory, new_filename)

                            # Rename (overwrite if exists)
                            os.replace(file_path, new_file_path)
            # Save the selected path and combo box value to a JSON file
            self.save_config(Path, combo_value)
        else:
            print("Invalid directory. Please select a valid folder path.")

    def save_config(self, path, combo_value):
        config = {"path": path, "combo_value": combo_value}
        with open(self.json_file_path, 'w') as config_file:
            json.dump(config, config_file)
        print(f"Configuration saved to {self.json_file_path}")

    def load_config(self):
        if os.path.exists(self.json_file_path):
            try:
                with open(self.json_file_path, 'r') as config_file:
                    config = json.load(config_file)
                self.path_line_edit.setText(config.get("path", ""))
                combo_value = config.get("combo_value", "")
                if combo_value in [self.combo_box.itemText(i) for i in range(self.combo_box.count())]:
                    self.combo_box.setCurrentText(combo_value)
                print(f"Configuration loaded from {self.json_file_path}")
            except Exception as e:
                print(f"Failed to load configuration: {e}")

class DependencyErrorDialog(QtWidgets.QDialog):
    """
    Generic Error dialog for displaying error messages
    """

    def __init__(self, parent, helpLink=None):
        super().__init__(parent=parent)
        self.setupUi(self)

    def close(self):
        """
        Close the dialog and updates the ini file if necessary
        """
        dontShowAgainState = True if self.dontShowAgain.checkState() != Qt.CheckState.Checked else False
        config.ConfigSettings.updateConfigSetting("General", "showDependencyError", dontShowAgainState, False)
        config.ConfigSettings.flush()
        super().close()

    def show(self):
        """
        Shows the error dialog only if the users has not checked before the "don't show again" checkbox
        """
        if (config.ConfigSettings.checkIfOptionIsSet("General", "showDependencyError", 'True')):
            super().show()

