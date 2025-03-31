import unreal
import sys
import os
import re
from pathlib import Path

python_lib = "//192.168.1.10/Softwares/Pipeline/GSTools/Library/Python/Python39/Lib/site-packages"
sys.path.append(python_lib)

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, 
                             QTextEdit, QMessageBox, QInputDialog, QCheckBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor

# Root directory finding logic
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def find_root_dir():
    # Start with the current file's directory
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Keep going up until we find a directory named "scripts"
    while True:
        # Check if we've reached the root of the filesystem
        PARENT_DIR = os.path.dirname(CURRENT_DIR)
        if PARENT_DIR == CURRENT_DIR:  # We've reached the filesystem root
            return None  # or raise an exception
        
        # Check if the current directory is named "scripts"
        if os.path.basename(CURRENT_DIR) == "Scripts":
            # Return the parent directory of "scripts"
            return CURRENT_DIR
        
        # Move up one level
        CURRENT_DIR = PARENT_DIR

# Usage
ROOT_DIR = find_root_dir()

class UVPrecisionTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Skeletal Mesh Full UVs Precision Tool")
        self.setFixedSize(400, 500)
        
        # Initialize UI
        self.init_ui()
        self.load_style()
        
        # Store selected meshes
        self.selected_meshes = []
        
    def init_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Select Mesh Button
        self.select_button = QPushButton("Select Skeletal Mesh")
        self.select_button.clicked.connect(self.get_selected_meshes)
        main_layout.addWidget(self.select_button)
        
        # Mesh List Table - simplified with just number and mesh name - remove header
        self.mesh_table = QTableWidget(0, 2)  # 0 rows initially, 2 columns (index and name)
        self.mesh_table.setHorizontalHeaderLabels(["#", ""])
        self.mesh_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.mesh_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.mesh_table.setSelectionMode(QTableWidget.NoSelection)  # Non-selectable
        self.mesh_table.verticalHeader().setVisible(False)
        self.mesh_table.setFocusPolicy(Qt.NoFocus)  # Remove focus indication
        
        # The style file already has appropriate colors for QWidget and QAbstractItemView
        # We'll rely on those instead of setting explicit colors
        
        # Increase the height to show more rows (approximately 10 rows)
        self.mesh_table.setMinimumHeight(300)
        
        main_layout.addWidget(self.mesh_table)
        
        # LOD Checkboxes
        lod_label = QLabel("Select LODs for Full Precision UVs:")
        lod_label.setProperty("boldLabel", "true")
        main_layout.addWidget(lod_label)
        
        # Create 4x2 grid layout for LOD checkboxes
        lod_grid = QGridLayout()
        self.lod_checkboxes = []
        
        # Arrange checkboxes in a 4x2 grid
        for i in range(8):
            checkbox = QCheckBox(f"LOD{i}")
            self.lod_checkboxes.append(checkbox)
            row = i // 4  # 0 for first 4, 1 for last 4
            col = i % 4   # 0, 1, 2, 3 repeating
            lod_grid.addWidget(checkbox, row, col)
        
        main_layout.addLayout(lod_grid)
        
        # Apply Button
        self.apply_button = QPushButton("Apply Full Precision UVs")
        self.apply_button.clicked.connect(self.apply_uv_precision)
        main_layout.addWidget(self.apply_button)
        
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)  # Allow word wrap for error messages
        main_layout.addWidget(self.status_label)
        
        # Add stretch to keep everything at the top
        main_layout.addStretch()
    
    def load_style(self):
        """Load QSS style file"""
        style = ''
        for style_path in [os.path.join(dir, 'style.qss') for dir in [ROOT_DIR]]:
            if os.path.exists(style_path):
                try:
                    with open(style_path, 'r') as f:
                        style = f.read()
                        break
                except Exception as e:
                    print(f"Warning: Could not load style file: {e}")
                    
        self.setStyleSheet(style)
    
    def get_selected_meshes(self):
        """Get selected skeletal meshes from content browser or viewport"""
        self.selected_meshes = []
        
        # Try to get selected assets from content browser first (priority)
        selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
        
        if selected_assets:
            # Filter for skeletal meshes only
            for asset in selected_assets:
                if isinstance(asset, unreal.SkeletalMesh):
                    self.selected_meshes.append(asset)
        else:
            # If no content browser selection, check viewport selection
            selected_actors = unreal.EditorLevelLibrary.get_selected_level_actors()
            for actor in selected_actors:
                if actor.is_a(unreal.SkeletalMeshActor):
                    skel_mesh_comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
                    if skel_mesh_comp and skel_mesh_comp.skeletal_mesh:
                        self.selected_meshes.append(skel_mesh_comp.skeletal_mesh)
        
        # Sort meshes alphabetically by name
        self.selected_meshes.sort(key=lambda x: x.get_name().lower())
        
        # Populate the table
        self.populate_mesh_table()
    
    def populate_mesh_table(self):
        """Populate the table with selected skeletal meshes"""
        # Clear existing rows
        self.mesh_table.setRowCount(0)
        
        # Add meshes to table
        for i, mesh in enumerate(self.selected_meshes):
            row_position = self.mesh_table.rowCount()
            self.mesh_table.insertRow(row_position)
            
            # Add index number
            index_item = QTableWidgetItem(str(i + 1))
            index_item.setTextAlignment(Qt.AlignCenter)
            index_item.setFlags(index_item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            self.mesh_table.setItem(row_position, 0, index_item)
            
            # Add mesh name
            name_item = QTableWidgetItem(mesh.get_name())
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            self.mesh_table.setItem(row_position, 1, name_item)
    
    def apply_uv_precision(self):
        """Apply full precision UVs to selected LODs for selected meshes"""
        if not self.selected_meshes:
            self.status_label.setText("No skeletal meshes selected.")
            self.status_label.setProperty("status", "error")
            return
        
        # Get selected LODs
        selected_lods = []
        for i, checkbox in enumerate(self.lod_checkboxes):
            if checkbox.isChecked():
                selected_lods.append(i)
        
        if not selected_lods:
            self.status_label.setText("No LODs selected.")
            self.status_label.setProperty("status", "warning")
            return
        
        try:
            count = 0
            # Apply changes to each selected mesh
            for mesh in self.selected_meshes:
                mesh_name = mesh.get_name()
                
                # Use the skeletal mesh editor subsystem
                skeletal_mesh_editor = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
                
                for lod_index in selected_lods:
                    try:
                        # Create build settings with full precision UVs enabled
                        settings = unreal.SkeletalMeshBuildSettings()
                        settings.set_editor_property('use_full_precision_u_vs', True)
                        
                        # Apply the settings to the mesh's LOD
                        skeletal_mesh_editor.set_lod_build_settings(mesh, lod_index, settings)
                        count += 1
                        print(f"Set full precision UVs for {mesh_name} LOD{lod_index}")
                    except Exception as e:
                        print(f"Failed to set full precision UVs for {mesh_name} LOD{lod_index}: {e}")
            
            # Update status
            if count > 0:
                self.status_label.setText(f"Applied full precision UVs to {count} LODs across selected meshes.")
                self.status_label.setProperty("status", "success")
            else:
                self.status_label.setText("No changes applied. Could not access build settings for the selected LODs.")
                self.status_label.setProperty("status", "warning")
                
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setProperty("status", "error")
            print(f"Error applying UV precision: {e}")

try:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        font = QFont("Meiryo UI")
        font.setPointSize(10)
        app.setFont(font)

    widget = UVPrecisionTool()
    widget.show()
    unreal.parent_external_window_to_slate(widget.winId())
except ImportError:
    print("This tool must be run within Unreal Engine.")
    sys.exit(1)