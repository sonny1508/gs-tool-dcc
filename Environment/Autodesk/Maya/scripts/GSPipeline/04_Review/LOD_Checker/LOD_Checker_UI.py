import maya.cmds as cmds
import maya.OpenMayaUI as omui
import sys
import os

# Python 2/3 compatibility
try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
except ImportError:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from shiboken import wrapInstance

def maya_main_window():
    """Get the main Maya window as a Python object"""
    main_window_ptr = omui.MQtUtil.mainWindow()
    # Python 2/3 compatibility for long type
    try:
        return wrapInstance(long(main_window_ptr), QWidget)
    except NameError:
        return wrapInstance(int(main_window_ptr), QWidget)

class LODCheckerUI(QDialog):
    def __init__(self, parent=maya_main_window()):
        super(LODCheckerUI, self).__init__(parent)
        
        # Store original positions for reset
        self.original_positions = {}
        self.lod_objects = {'A': [], 'B': [], 'C': [], 'D': [], 'E': [], 'F': [], 'G': [], 'H': []}
        self.display_layers = []
        
        # UI state variables
        self.current_mode = "LOD_SLIDER"  # LOD_SLIDER, TRANSLATE, PICKER
        self.picker_before = None
        self.picker_after = None
        self.switch_state = "AFTER"  # AFTER, BEFORE
        
        self.setup_ui()
        self.refresh_lod_objects()
        self.enable_all_display_layers()
        self.reset_to_default()
        
    def setup_ui(self):
        self.setWindowTitle("LOD Checker")
        self.setFixedSize(540, 480)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Reset button at the top
        reset_btn = QPushButton("RESET")
        reset_btn.setFixedHeight(30)
        reset_btn.setStyleSheet("QPushButton { background-color: #6b0914; color: white; font-weight: bold; }")
        reset_btn.clicked.connect(self.reset_to_default)
        main_layout.addWidget(reset_btn)
        
        # LOD Slider section
        lod_group = QGroupBox()
        lod_group.setStyleSheet("QGroupBox { background-color: #333333; padding-top: 5px; }")
        lod_layout = QVBoxLayout(lod_group)
        
        # Section title
        lod_title = QLabel("Select LOD")
        lod_title.setAlignment(Qt.AlignCenter)
        lod_title.setStyleSheet("QLabel { color: white; font-weight: bold; background-color: #333333; padding: 5px; }")
        lod_layout.addWidget(lod_title)
        
        # LOD input and slider container
        lod_control_layout = QHBoxLayout()
        
        # LOD input box
        self.lod_input = QComboBox()
        self.lod_input.addItems(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'])
        self.lod_input.currentTextChanged.connect(self.on_lod_input_changed)
        self.lod_input.setFixedWidth(55)
        lod_control_layout.addWidget(self.lod_input)
        
        # LOD slider with A-F labels
        slider_container = QWidget()
        slider_layout = QVBoxLayout(slider_container)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lod_slider = QSlider(Qt.Horizontal)
        self.lod_slider.setMinimum(0)
        self.lod_slider.setMaximum(7)
        self.lod_slider.setValue(0)
        self.lod_slider.setTickPosition(QSlider.TicksBelow)
        self.lod_slider.setTickInterval(1)
        self.lod_slider.valueChanged.connect(self.on_lod_slider_changed)
        
        # Labels for A-F with exact slider alignment
        labels_widget = QWidget()
        labels_layout = QHBoxLayout(labels_widget)
        labels_layout.setContentsMargins(0, 0, 0, 0)  # Adjusted to match slider groove
        labels_layout.setSpacing(45)
        
        for letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            label = QLabel(letter)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("QLabel { color: white; }")
            labels_layout.addWidget(label)
        
        slider_layout.addWidget(self.lod_slider)
        slider_layout.addWidget(labels_widget)
        lod_control_layout.addWidget(slider_container)
        
        lod_layout.addLayout(lod_control_layout)
        main_layout.addWidget(lod_group)
        
        # Translate LOD section
        translate_group = QGroupBox()
        translate_group.setStyleSheet("QGroupBox { background-color: #333333; padding-top: 5px; }")
        translate_layout = QVBoxLayout(translate_group)
        
        # Section title
        translate_title = QLabel("Slider Translate LOD")
        translate_title.setAlignment(Qt.AlignCenter)
        translate_title.setStyleSheet("QLabel { color: white; font-weight: bold; background-color: #333333; padding: 5px; }")
        translate_layout.addWidget(translate_title)
        
        # X Axis
        x_layout = QHBoxLayout()
        x_label = QLabel("X Axis")
        x_label.setStyleSheet("QLabel { color: white; }")
        x_label.setFixedWidth(50)
        x_layout.addWidget(x_label)
        
        self.x_input = QSpinBox()
        self.x_input.setMinimum(0)
        self.x_input.setMaximum(2000)
        self.x_input.setValue(0)
        self.x_input.valueChanged.connect(self.on_x_input_changed)
        self.x_input.setFixedWidth(70)
        x_layout.addWidget(self.x_input)
        
        self.x_slider = QSlider(Qt.Horizontal)
        self.x_slider.setMinimum(0)
        self.x_slider.setMaximum(2000)
        self.x_slider.setValue(0)
        self.x_slider.valueChanged.connect(self.on_x_slider_changed)
        x_layout.addWidget(self.x_slider)
        
        translate_layout.addLayout(x_layout)
        
        # Y Axis
        y_layout = QHBoxLayout()
        y_label = QLabel("Y Axis")
        y_label.setStyleSheet("QLabel { color: white; }")
        y_label.setFixedWidth(50)
        y_layout.addWidget(y_label)
        
        self.y_input = QSpinBox()
        self.y_input.setMinimum(0)
        self.y_input.setMaximum(2000)
        self.y_input.setValue(0)
        self.y_input.valueChanged.connect(self.on_y_input_changed)
        self.y_input.setFixedWidth(70)
        y_layout.addWidget(self.y_input)
        
        self.y_slider = QSlider(Qt.Horizontal)
        self.y_slider.setMinimum(0)
        self.y_slider.setMaximum(2000)
        self.y_slider.setValue(0)
        self.y_slider.valueChanged.connect(self.on_y_slider_changed)
        y_layout.addWidget(self.y_slider)
        
        translate_layout.addLayout(y_layout)
        main_layout.addWidget(translate_group)
        
        # Picker Before After section
        picker_group = QGroupBox()
        picker_group.setStyleSheet("QGroupBox { background-color: #333333; padding-top: 5px; }")
        picker_layout = QVBoxLayout(picker_group)
        
        # Section title
        picker_title = QLabel("Picker Before After")
        picker_title.setAlignment(Qt.AlignCenter)
        picker_title.setStyleSheet("QLabel { color: white; font-weight: bold; background-color: #333333; padding: 5px; }")
        picker_layout.addWidget(picker_title)
        
        # Before row
        before_container = QWidget()
        before_layout = QHBoxLayout(before_container)
        before_layout.setContentsMargins(0, 0, 0, 0)
        before_layout.setSpacing(5)
        
        before_label = QLabel("Before:")
        before_label.setStyleSheet("QLabel { color: white; }")
        before_label.setFixedWidth(50)
        before_layout.addWidget(before_label)
        
        # Button container for Before row
        before_buttons_widget = QWidget()
        before_buttons_layout = QHBoxLayout(before_buttons_widget)
        before_buttons_layout.setContentsMargins(0, 0, 0, 0)
        before_buttons_layout.setSpacing(2)
        
        self.before_buttons = {}
        for letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            btn = QPushButton(letter)
            btn.setCheckable(True)
            btn.clicked.connect(self.create_before_click_handler(letter))
            self.before_buttons[letter] = btn
            before_buttons_layout.addWidget(btn)
        
        before_layout.addWidget(before_buttons_widget)
        picker_layout.addWidget(before_container)
        
        # After row
        after_container = QWidget()
        after_layout = QHBoxLayout(after_container)
        after_layout.setContentsMargins(0, 0, 0, 0)
        after_layout.setSpacing(5)
        
        after_label = QLabel("After:")
        after_label.setStyleSheet("QLabel { color: white; }")
        after_label.setFixedWidth(50)
        after_layout.addWidget(after_label)
        
        # Button container for After row
        after_buttons_widget = QWidget()
        after_buttons_layout = QHBoxLayout(after_buttons_widget)
        after_buttons_layout.setContentsMargins(0, 0, 0, 0)
        after_buttons_layout.setSpacing(2)
        
        self.after_buttons = {}
        for letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            btn = QPushButton(letter)
            btn.setCheckable(True)
            btn.clicked.connect(self.create_after_click_handler(letter))
            self.after_buttons[letter] = btn
            after_buttons_layout.addWidget(btn)
        
        after_layout.addWidget(after_buttons_widget)
        picker_layout.addWidget(after_container)
        
        main_layout.addWidget(picker_group)
        
        # Switch section
        switch_layout = QVBoxLayout()
        
        self.switch_btn = QPushButton("SWITCH")
        self.switch_btn.setFixedHeight(40)
        self.switch_btn.setStyleSheet("QPushButton { background-color: #f6921e; color: white; font-weight: bold; }")
        self.switch_btn.clicked.connect(self.on_switch_clicked)
        switch_layout.addWidget(self.switch_btn)
        
        # Show/Hide All buttons
        show_hide_layout = QHBoxLayout()
        show_all_btn = QPushButton("Show All LODs")
        show_all_btn.clicked.connect(self.show_all_lods)
        hide_all_btn = QPushButton("Hide All LODs")
        hide_all_btn.clicked.connect(self.hide_all_lods)
        
        show_hide_layout.addWidget(show_all_btn)
        show_hide_layout.addWidget(hide_all_btn)
        switch_layout.addLayout(show_hide_layout)
        
        main_layout.addLayout(switch_layout)
        
    def enable_all_display_layers(self):
        """Enable visibility for all display layers on startup"""
        self.display_layers = cmds.ls(type='displayLayer')
        for layer in self.display_layers:
            if layer != 'defaultLayer':
                cmds.setAttr(layer + '.visibility', True)
    
    def disable_all_display_layers_except_loda(self):
        """Disable all display layers except those containing LODA objects"""
        for layer in self.display_layers:
            if layer != 'defaultLayer':
                # Check if layer contains LODA objects
                layer_objects = cmds.editDisplayLayerMembers(layer, query=True, fullNames=True) or []
                has_loda = False
                for obj in layer_objects:
                    if obj in self.lod_objects['A']:
                        has_loda = True
                        break
                
                if not has_loda:
                    cmds.setAttr(layer + '.visibility', False)
    
    def refresh_lod_objects(self):
        """Find all LOD objects in the scene"""
        self.lod_objects = {'A': [], 'B': [], 'C': [], 'D': [], 'E': [], 'F': [], 'G': [], 'H': []}
        self.original_positions = {}
        
        all_objects = cmds.ls(dag=True, long=True)
        
        for obj in all_objects:
            short_name = obj.split('|')[-1]
            for lod in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                if short_name.endswith('_LOD' + lod):
                    self.lod_objects[lod].append(obj)
                    # Store original position
                    if cmds.objExists(obj):
                        pos = cmds.xform(obj, q=True, ws=True, t=True)
                        self.original_positions[obj] = pos
                    break
        """Find all LOD objects in the scene"""
        self.lod_objects = {'A': [], 'B': [], 'C': [], 'D': [], 'E': [], 'F': [], 'G': [], 'H': []}
        self.original_positions = {}
        
        all_objects = cmds.ls(dag=True, long=True)
        
        for obj in all_objects:
            short_name = obj.split('|')[-1]
            for lod in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                if short_name.endswith('_LOD' + lod):
                    self.lod_objects[lod].append(obj)
                    # Store original position
                    if cmds.objExists(obj):
                        pos = cmds.xform(obj, q=True, ws=True, t=True)
                        self.original_positions[obj] = pos
                    break
    
    def on_lod_input_changed(self, text):
        """Handle LOD input box changes"""
        lod_index = ord(text) - ord('A')
        self.lod_slider.setValue(lod_index)
    
    def on_lod_slider_changed(self, value):
        """Handle LOD slider changes"""
        self.current_mode = "LOD_SLIDER"
        lod_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        current_lod = lod_letters[value]
        
        # Update input box
        self.lod_input.setCurrentText(current_lod)
        
        # Hide all LODs first
        for lod in self.lod_objects:
            for obj in self.lod_objects[lod]:
                if cmds.objExists(obj):
                    cmds.setAttr(obj + '.visibility', False)
        
        # Show only current LOD
        for obj in self.lod_objects[current_lod]:
            if cmds.objExists(obj):
                cmds.setAttr(obj + '.visibility', True)
    
    def on_x_input_changed(self, value):
        """Handle X input box changes"""
        self.x_slider.setValue(value)
    
    def on_x_slider_changed(self, value):
        """Handle X slider changes"""
        self.x_input.setValue(value)
        self.on_translate_changed()
    
    def on_y_input_changed(self, value):
        """Handle Y input box changes"""
        self.y_slider.setValue(value)
    
    def on_y_slider_changed(self, value):
        """Handle Y slider changes"""
        self.y_input.setValue(value)
        self.on_translate_changed()
    
    def on_translate_changed(self):
        """Handle translation slider changes"""
        if self.current_mode != "TRANSLATE":
            return
            
        x_value = self.x_slider.value()
        y_value = self.y_slider.value()
        
        # Apply cumulative translation
        for i, lod in enumerate(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']):
            offset_x = x_value * i
            offset_y = y_value * i
            
            for obj in self.lod_objects[lod]:
                if cmds.objExists(obj) and obj in self.original_positions:
                    orig_pos = self.original_positions[obj]
                    new_pos = [orig_pos[0] + offset_x, orig_pos[1] + offset_y, orig_pos[2]]
                    cmds.xform(obj, ws=True, t=new_pos)
    
    def create_before_click_handler(self, letter):
        """Create a click handler for before buttons"""
        def handler():
            self.on_picker_before_clicked(letter)
        return handler
    
    def create_after_click_handler(self, letter):
        """Create a click handler for after buttons"""
        def handler():
            self.on_picker_after_clicked(letter)
        return handler
    
    def on_picker_before_clicked(self, letter):
        """Handle before picker button clicks"""
        # If this button is already selected, deselect it
        if self.picker_before == letter:
            self.before_buttons[letter].setChecked(False)
            self.picker_before = None
            return
        
        # Clear all other before buttons
        for btn_letter, btn in self.before_buttons.items():
            btn.setChecked(False)
        
        # Select the clicked button
        self.before_buttons[letter].setChecked(True)
        self.picker_before = letter
    
    def on_picker_after_clicked(self, letter):
        """Handle after picker button clicks"""
        # If this button is already selected, deselect it
        if self.picker_after == letter:
            self.after_buttons[letter].setChecked(False)
            self.picker_after = None
            return
        
        # Clear all other after buttons
        for btn_letter, btn in self.after_buttons.items():
            btn.setChecked(False)
        
        # Select the clicked button
        self.after_buttons[letter].setChecked(True)
        self.picker_after = letter
    
    def on_switch_clicked(self):
        """Handle switch button clicks"""
        if self.picker_before is None or self.picker_after is None:
            cmds.warning("Please select both Before and After LODs first")
            return
        
        self.current_mode = "PICKER"
        
        # Hide all LODs first
        self.hide_all_lods()
        
        # Switch between AFTER and BEFORE
        if self.switch_state == "AFTER":
            # Show After LOD
            for obj in self.lod_objects[self.picker_after]:
                if cmds.objExists(obj):
                    cmds.setAttr(obj + '.visibility', True)
            self.switch_state = "BEFORE"
        else:
            # Show Before LOD
            for obj in self.lod_objects[self.picker_before]:
                if cmds.objExists(obj):
                    cmds.setAttr(obj + '.visibility', True)
            self.switch_state = "AFTER"
    
    def show_all_lods(self):
        """Show all LOD objects"""
        self.current_mode = "TRANSLATE"
        for lod in self.lod_objects:
            for obj in self.lod_objects[lod]:
                if cmds.objExists(obj):
                    cmds.setAttr(obj + '.visibility', True)
    
    def hide_all_lods(self):
        """Hide all LOD objects"""
        for lod in self.lod_objects:
            for obj in self.lod_objects[lod]:
                if cmds.objExists(obj):
                    cmds.setAttr(obj + '.visibility', False)
    
    def reset_to_default(self):
        """Reset everything to default state"""
        # Reset sliders and inputs
        self.lod_slider.setValue(0)
        self.lod_input.setCurrentText('A')
        self.x_slider.setValue(0)
        self.y_slider.setValue(0)
        self.x_input.setValue(0)
        self.y_input.setValue(0)
        
        # Reset picker buttons
        for btn in self.before_buttons.values():
            btn.setChecked(False)
        for btn in self.after_buttons.values():
            btn.setChecked(False)
        
        # Reset variables
        self.picker_before = None
        self.picker_after = None
        self.switch_state = "AFTER"
        self.current_mode = "LOD_SLIDER"
        
        # Reset positions
        for obj, orig_pos in self.original_positions.items():
            if cmds.objExists(obj):
                cmds.xform(obj, ws=True, t=orig_pos)
        
        # Show all LODs
        self.show_all_lods()
    
    def closeEvent(self, event):
        """Reset translations and display layers when closing the UI"""
        # Reset positions to original
        for obj, orig_pos in self.original_positions.items():
            if cmds.objExists(obj):
                cmds.xform(obj, ws=True, t=orig_pos)
        
        # Show all LODs
        self.show_all_lods()
        
        # Disable all display layers except LODA
        self.disable_all_display_layers_except_loda()
        
        event.accept()

def show_lod_checker():
    """Function to show the LOD Checker UI"""
    global lod_checker_ui
    
    try:
        lod_checker_ui.close()
        lod_checker_ui.deleteLater()
    except:
        pass
    
    lod_checker_ui = LODCheckerUI()
    lod_checker_ui.show()

# Run the tool
if __name__ == "__main__":
    show_lod_checker()