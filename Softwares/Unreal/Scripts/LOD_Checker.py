#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import os.path

# Import subfolders
sys.path.append(__file__.rsplit("/",1)[0])

python_lib = "Z:/Pipeline/GSTools/Library/Python/Python39/Lib/site-packages"
if os.path.exists(python_lib):
    sys.path.append(python_lib)
else:
    print(f"Warning: {python_lib} does not exist")

from PySide6.QtWidgets import *
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QCoreApplication

class CustomSlider(QSlider):
    """Custom slider that allows direct click value setting."""
    
    def mousePressEvent(self, event):
        """Handle mouse press events for direct value setting."""
        if event.button() == Qt.LeftButton:
            value = self._pixel_pos_to_value(event.pos())
            self.setValue(value)
        super().mousePressEvent(event)
    
    def _pixel_pos_to_value(self, pos):
        """Convert pixel position to slider value."""
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        handle = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
        
        if self.orientation() == Qt.Horizontal:
            slider_length = handle.width()
            slider_min = groove.x()
            slider_max = groove.right() - slider_length + 1
            pos_value = pos.x() - slider_length // 2
        else:
            slider_length = handle.height()
            slider_min = groove.y()
            slider_max = groove.bottom() - slider_length + 1
            pos_value = pos.y() - slider_length // 2
        
        return QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(),
            pos_value - slider_min,
            slider_max - slider_min,
            opt.upsideDown
        )

class LODCheckerGUI(QMainWindow):
    """Main GUI class for the LOD Checker tool."""
    
    LOD_NAMES = ['LOD A', 'LOD B', 'LOD C', 'LOD D', 'LOD E', 'LOD F', 'LOD G', 'LOD H']
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_swapped = False
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Initialize and setup the UI components."""
        self._load_style()
        self._setup_window_properties()
        self._create_central_widget()
        self._setup_widgets()
        self._setup_layouts()
        self._setup_status_bar()
        self._set_window_text()
    
    def _load_style(self):
        """Load QSS style from file if available."""
        try:
            style_path = os.path.join(os.path.dirname(__file__), 'style.qss')
            with open(style_path, 'r') as f:
                self.setStyleSheet(f.read())
        except (IOError, OSError):
            pass
    
    def _setup_window_properties(self):
        """Set basic window properties."""
        self.setFont(QFont("Meiryo UI", 10))
        self.resize(400, 250)
        self.setMinimumSize(400, 250)
    
    def _create_central_widget(self):
        """Create and set the central widget."""
        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralwidget")
        self.setCentralWidget(self.central_widget)
        
        self.grid_layout = QGridLayout(self.central_widget)
        self.grid_layout.setVerticalSpacing(15)
    
    def _setup_widgets(self):
        """Create and configure all widgets."""
        # Actor Name Label
        self.actor_name = QLabel()
        self.actor_name.setFont(QFont("Meiryo UI", 20, QFont.Weight.Bold))
        self.actor_name.setAlignment(Qt.AlignCenter)
        
        # LOD Name Label
        self.lod_name = QLabel()
        self.lod_name.setFont(QFont("Meiryo UI", 20, QFont.Weight.Bold))
        self.lod_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Swap Button
        self.swap_btn = QPushButton()
        self.swap_btn.setFont(QFont("Meiryo UI", 12, QFont.Weight.Bold))
        self.swap_btn.setMinimumWidth(100)
        self.swap_btn.setMaximumWidth(150)
        
        # LOD Slider
        self.lod_slider = CustomSlider(Qt.Horizontal)
        self.lod_slider.setMaximum(7)
        self.lod_slider.setPageStep(1)
        self.lod_slider.setTracking(True)
        self.lod_slider.setTickPosition(QSlider.TicksBelow)
        self.lod_slider.setTickInterval(1)
    
    def _setup_layouts(self):
        """Setup all layouts and add widgets."""
        # LOD Controls Container
        lod_controls = QHBoxLayout()
        lod_controls.setContentsMargins(0, 0, 0, 0)
        lod_controls.addSpacing(20)
        lod_controls.addWidget(self.lod_name)
        lod_controls.addWidget(self.swap_btn)
        lod_controls.addSpacing(20)
        
        # Main Layout
        self.grid_layout.addWidget(self.actor_name, 0, 0)
        self.grid_layout.addLayout(lod_controls, 1, 0)
        self.grid_layout.addItem(QSpacerItem(15, 15, QSizePolicy.Minimum, QSizePolicy.Fixed), 2, 0)
        self.grid_layout.addWidget(self.lod_slider, 3, 0)
    
    def _setup_status_bar(self):
        """Create and set the status bar."""
        self.setStatusBar(QStatusBar())
    
    def _set_window_text(self):
        """Set text for all UI elements."""
        self.setWindowTitle("LOD Checker")
        self.actor_name.setText("Actor Name")
        self.lod_name.setText("LOD A")
        self.swap_btn.setText("Swap to LOD A")
    
    def _connect_signals(self):
        """Connect all signal handlers."""
        self.lod_slider.valueChanged.connect(self.set_lod)
        self.swap_btn.clicked.connect(self.swap_lod)
    
    def get_selected_actors(self):
        """Get currently selected actors in the editor."""
        try:
            import unreal
            editor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            return editor_subsystem.get_selected_level_actors()
        except ImportError:
            return []
    
    def set_lod(self):
        """Update LOD based on slider value."""
        value = self.lod_slider.value()
        self.lod_name.setText(self.LOD_NAMES[value])
        
        # Reset swap state
        self.is_swapped = False
        self._update_swap_button_state()
        
        # Update LOD in editor
        self._update_actor_lods(value)
    
    def swap_lod(self):
        """Handle LOD swapping functionality."""
        current_lod = self.lod_slider.value()
        if current_lod == 0:
            return
            
        self.is_swapped = not self.is_swapped
        self._update_swap_button_state()
        self._update_actor_lods(0 if self.is_swapped else current_lod)
    
    def _update_swap_button_state(self):
        """Update swap button appearance based on state."""
        self.swap_btn.setProperty("isSwapped", self.is_swapped)
        self.swap_btn.setText("Return to Previous" if self.is_swapped else "Swap to LOD A")
        self.swap_btn.style().unpolish(self.swap_btn)
        self.swap_btn.style().polish(self.swap_btn)
    
    def _update_actor_lods(self, lod_value: int):
        """Update LOD values for selected actors."""
        for actor in self.get_selected_actors():
            # Try static mesh first
            static_mesh = actor.get_component_by_class(unreal.StaticMeshComponent)
            if static_mesh:
                self._update_static_mesh_lod(static_mesh, lod_value)
            else:
                # Try skeletal mesh
                skeletal_mesh = actor.get_component_by_class(unreal.SkeletalMeshComponent)
                if skeletal_mesh:
                    self._update_skeletal_mesh_lod(skeletal_mesh, lod_value)
    
    def _update_static_mesh_lod(self, mesh, lod_value: int):
        """Update LOD for static mesh component."""
        self.actor_name.setText(mesh.static_mesh.get_name())
        mesh.set_editor_property("override_min_lod", True)
        mesh.set_editor_property("min_lod", lod_value)
    
    def _update_skeletal_mesh_lod(self, mesh, lod_value: int):
        """Update LOD for skeletal mesh component."""
        self.actor_name.setText(mesh.skeletal_mesh.get_name())
        mesh.set_editor_property("override_min_lod", True)
        mesh.set_editor_property("min_lod_model", lod_value)

try:
    import unreal
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        font = QFont("Meiryo UI")
        font.setPointSize(10)
        app.setFont(font)
    
    widget = LODCheckerGUI()
    widget.show()
    unreal.parent_external_window_to_slate(widget.winId())
except ImportError:
    print("This tool must be run within Unreal Engine.")
    sys.exit(1)