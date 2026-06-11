import importlib, hashlib

import os, time, ctypes
from datetime import datetime, timedelta
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QTimer

from .ui import icon, dialogs_UI
import random
import tempfile
import shutil

import substance_painter.resource
import substance_painter_plugins

importlib.reload(dialogs_UI)


class FileSystemCache:
    """Cache for file system operations to avoid repeated directory walks"""
    def __init__(self):
        self.file_cache = {}
        self.cache_timestamp = {}
        self.cache_duration = 300  # 5 minutes
    
    def get_files(self, path, extensions=None):
        """Get cached file list or perform directory walk"""
        if extensions is None:
            extensions = ['.png', '.jpg', '.sbsar', '.spsm', '.tif']
        
        cache_key = f"{path}_{','.join(extensions)}"
        current_time = time.time()
        
        # Check if cache is valid
        if (cache_key in self.file_cache and 
            cache_key in self.cache_timestamp and
            current_time - self.cache_timestamp[cache_key] < self.cache_duration):
            return self.file_cache[cache_key]
        
        # Perform directory walk
        files = []
        try:
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    if any(filename.lower().endswith(ext.lower()) for ext in extensions):
                        files.append(os.path.join(root, filename))
        except Exception as e:
            print(f"Error walking directory {path}: {e}")
        
        # Cache the results
        self.file_cache[cache_key] = files
        self.cache_timestamp[cache_key] = current_time
        
        return files
    
    def clear_cache(self):
        """Clear the file cache"""
        self.file_cache.clear()
        self.cache_timestamp.clear()


class LazyLoadingListWidget(QtWidgets.QListWidget):
    def __init__(self, image_paths, parent=None):
        super().__init__(parent)
        self.image_paths = image_paths
        self.setIconSize(QtCore.QSize(64, 64))  # Keep original thumbnail size
        self.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.setViewMode(QtWidgets.QListWidget.IconMode)
        self.setSpacing(5)

        # Lazy loading parameters
        self.loaded_count = 0
        self.batch_size = 20  # Number of images to load per batch

        self.load_more_images()  # Load initial batch
        self.verticalScrollBar().valueChanged.connect(self.load_more_images)

    def load_images(self):
        """Initial load of images, loading only a limited batch"""
        self.clear()
        self.loaded_count = 0
        self.load_more_images()

    def load_more_images(self):
        """Lazy loads more images as the user scrolls down"""
        max_count = min(self.loaded_count + self.batch_size, len(self.image_paths))

        for i in range(self.loaded_count, max_count):
            path = self.image_paths[i]
            name = os.path.splitext(os.path.basename(path))[0]
            item = QtWidgets.QListWidgetItem(QtGui.QIcon(path), name)
            item.setData(Qt.UserRole, path)  # Store path for later use
            self.addItem(item)

        self.loaded_count = max_count  # Update count


class SettingsDialog(QtWidgets.QDialog, dialogs_UI.Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.background_color = "#262626"
        self.base_path = r'\\192.168.1.210\Library\Substance'

        # Initialize file system cache
        self.fs_cache = FileSystemCache()
        
        # Define disk cache directory with category separation
        self.cache_dir = os.path.join(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.CacheLocation),
                                      "image_cache")
        os.makedirs(self.cache_dir, exist_ok=True)  # Ensure cache folder exists

        # Current category tracking for cache isolation
        self.current_category = None
        self.last_selected_folder = None  # Track last selected folder for filter restoration

        # Add variables for improved lazy loading
        self.all_image_paths = []
        self.loaded_count = 0
        self.is_loading = False  # Prevent multiple simultaneous loads
        self.is_filtered = False  # Track if we're currently in filtered mode
        
        self.radioMaterial.clicked.connect(self.updateTreeview)
        self.radioAlpha.clicked.connect(self.updateTreeview)
        self.radioSmartMaterial.clicked.connect(self.updateTreeview)
        self.radioBrush.clicked.connect(self.updateTreeview)

        self.listWidget.setStyleSheet('background-color:' + self.background_color)
        self.treeView.setStyleSheet('background-color:' + self.background_color)
        self.groupBox.setStyleSheet('background-color:' + self.background_color)

        self.updateTreeview()

        self.treeView.clicked.connect(self.on_clicked)
        self.listWidget.itemDoubleClicked.connect(self.toSP)

        # Debounced filter with improved handling
        self.filter_timer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.apply_filter)
        self.filterLineEdit.textChanged.connect(self.on_filter_changed)

        self.editMenu.addAction('Change Path', self.changeResourepath)

        # Set up improved scroll detection
        self.setup_scroll_detection()

    def setup_scroll_detection(self):
        """Setup better scroll detection for lazy loading"""
        scrollbar = self.listWidget.verticalScrollBar()
        
        # Connect to multiple scroll events for better detection
        scrollbar.valueChanged.connect(self.on_scroll_changed)
        scrollbar.actionTriggered.connect(self.on_scroll_action)
        
        # Also connect to resize events
        self.listWidget.resizeEvent = self.on_list_resize

    def on_scroll_changed(self, value):
        """Handle scroll value changes"""
        self.check_load_more()

    def on_scroll_action(self, action):
        """Handle scroll bar actions"""
        QtCore.QTimer.singleShot(50, self.check_load_more)  # Small delay to ensure scroll is processed

    def on_list_resize(self, event):
        """Handle list widget resize events"""
        # Call original resize event if it exists
        if hasattr(QtWidgets.QListWidget, 'resizeEvent'):
            QtWidgets.QListWidget.resizeEvent(self.listWidget, event)
        
        # Check if we need to load more items after resize
        QtCore.QTimer.singleShot(100, self.check_load_more)

    def check_load_more(self):
        """Check if we need to load more items and do so if necessary"""
        if self.is_loading or not hasattr(self, 'all_image_paths'):
            return
        
        if self.loaded_count >= len(self.all_image_paths):
            return
        
        scrollbar = self.listWidget.verticalScrollBar()
        
        # More sensitive scroll detection - load when we're 80% down or near the bottom
        scroll_threshold = max(scrollbar.maximum() * 0.8, scrollbar.maximum() - 200)
        
        if scrollbar.value() >= scroll_threshold:
            self.load_more_items()

    def load_more_items(self):
        """Load more items with proper UI updates"""
        if self.is_loading:
            return
        
        self.is_loading = True
        
        try:
            batch_size = 25  # Slightly increased batch size for better performance
            start_idx = self.loaded_count
            end_idx = min(start_idx + batch_size, len(self.all_image_paths))
            
            if start_idx >= end_idx:
                return
            
            # Temporarily disable updates for better performance
            self.listWidget.setUpdatesEnabled(False)
            
            # Pre-allocate items list for better performance
            items_to_add = []
            
            # Add more items
            for i in range(start_idx, end_idx):
                path = self.all_image_paths[i]
                name = os.path.splitext(os.path.basename(path))[0]
                cropped_name = self.crop_text_for_thumbnail(name)
                
                # Generate thumbnail with category-separated cache
                icon = self.generate_thumbnail(path)
                item = QtWidgets.QListWidgetItem(icon, cropped_name)
                item.setData(Qt.UserRole, path)
                item.setToolTip(name)  # Show full name on hover
                items_to_add.append(item)
            
            # Add all items at once for better performance
            for item in items_to_add:
                self.listWidget.addItem(item)
            
            self.loaded_count = end_idx
            
            # Re-enable updates and force refresh
            self.listWidget.setUpdatesEnabled(True)
            self.listWidget.repaint()  # Force immediate repaint
            
            # Process events to ensure UI updates
            QtWidgets.QApplication.processEvents()
            
        finally:
            self.is_loading = False

    def get_current_category(self):
        """Get the currently selected category for cache isolation"""
        if self.radioMaterial.isChecked():
            return "material"
        elif self.radioSmartMaterial.isChecked():
            return "smart_material"
        elif self.radioAlpha.isChecked():
            return "alpha"
        elif self.radioBrush.isChecked():
            return "brush"
        return "unknown"

    def get_cache_path(self, image_path):
        """Generates a unique cache filename using category + hash to prevent cross-contamination"""
        category = self.get_current_category()
        path_with_category = f"{category}_{image_path}"
        hashed_name = hashlib.md5(path_with_category.encode()).hexdigest() + ".png"
        return os.path.join(self.cache_dir, hashed_name)

    def generate_thumbnail(self, image_path, size=(128, 128)):
        """Creates a thumbnail and saves it to disk cache with category separation"""
        cache_path = self.get_cache_path(image_path)

        if os.path.exists(cache_path):  # Use cached version if available
            return QtGui.QIcon(cache_path)

        try:
            pixmap = QtGui.QPixmap(image_path)
            if pixmap.isNull():  # Skip invalid images
                return QtGui.QIcon(image_path)  # Fallback to original

            pixmap = pixmap.scaled(size[0], size[1], QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            
            # Save to cache for future use
            try:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                pixmap.save(cache_path, "PNG")
            except:
                pass  # Cache save failed, but we have the pixmap
            
            return QtGui.QIcon(pixmap)
        except:
            return QtGui.QIcon(image_path)  # Fallback to original

    def crop_text_for_thumbnail(self, text, max_chars=15):
        """Crop text to fit thumbnail width and add ellipsis if needed"""
        if len(text) <= max_chars:
            return text
        return text[:max_chars-3] + "..."

    def load_images_lazy(self, folder_path):
        """Collects image paths for lazy loading using cache"""
        return self.fs_cache.get_files(folder_path, [".png", ".jpg"])

    def get_base_path(self):
        """Get the base path for the current category - now supports multiple paths for Alpha"""
        if self.radioMaterial.isChecked():
            return os.path.join(self.base_path, 'SubstanceMaterial')
        elif self.radioSmartMaterial.isChecked():
            return os.path.join(self.base_path, 'SmartMaterial')
        elif self.radioAlpha.isChecked():
            # For Alpha, we'll use the first existing path as the tree root
            # but we'll handle multiple paths in other methods
            alpha_paths = [
                # os.path.join(self.base_path, 'SubstanceAtlas'),
                os.path.join(self.base_path, 'SubstanceDecal'),
                os.path.join(self.base_path, 'Alpha'),
            ]
            for path in alpha_paths:
                if os.path.exists(path):
                    return path
            return self.base_path
        elif self.radioBrush.isChecked():
            return os.path.join(self.base_path, '/Brush')
        else:
            return self.base_path

    def get_all_category_paths(self):
        """Get all paths for the current category"""
        if self.radioMaterial.isChecked():
            return [os.path.join(self.base_path, 'SubstanceMaterial')]
        elif self.radioSmartMaterial.isChecked():
            return [os.path.join(self.base_path, 'SmartMaterial')]
        elif self.radioAlpha.isChecked():
            return [
                # os.path.join(self.base_path, 'SubstanceAtlas'),
                os.path.join(self.base_path, 'SubstanceDecal'),
                os.path.join(self.base_path, 'Alpha'),
            ]
        else:
            return [self.base_path]

    def updateTreeview(self):
        # Clear cache when category changes to prevent cross-contamination
        current_category = self.get_current_category()
        if self.current_category != current_category:
            self.fs_cache.clear_cache()
            self.current_category = current_category
            self.last_selected_folder = None  # Reset folder selection on category change

        path = self.get_base_path()

        self.dirModel = QtWidgets.QFileSystemModel()
        self.dirModel.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)
        self.dirModel.setNameFilterDisables(False)
        self.dirModel.setRootPath(path)

        self.fileModel = QtWidgets.QFileSystemModel()
        self.fileModel.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.Files)
        self.fileModel.setNameFilters(['*.png'])
        self.fileModel.setNameFilterDisables(False)

        self.treeView.setModel(self.dirModel)
        self.treeView.setRootIndex(self.dirModel.index(path))

        self.treeView.setItemsExpandable(True)
        self.treeView.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.treeView.header().hideSection(2)
        self.treeView.setColumnHidden(2, True)
        self.treeView.setColumnHidden(3, True)

        # Reset filter state when updating tree view
        self.is_filtered = False

        ix = self.treeView.selectedIndexes()
        if not ix:
            # Get files from all category paths, not just the tree root
            all_category_paths = self.get_all_category_paths()
            all_files = []
            for category_path in all_category_paths:
                if os.path.exists(category_path):
                    files = self.fs_cache.get_files(category_path, ['.png'])
                    all_files.extend(files)
            
            if all_files:
                # Use more random files for better variety
                sample_size = min(30, len(all_files))
                random_files = random.choices(population=all_files, k=sample_size)
                self.update_list_widget(random_files)

    def on_clicked(self, index):
        """Triggered when clicking a folder, updates image list lazily"""
        folder_path = self.dirModel.fileInfo(index).absoluteFilePath()
        self.last_selected_folder = folder_path  # Store the selected folder
        image_paths = self.load_images_lazy(folder_path)
        self.update_list_widget(image_paths)
        self.is_filtered = False  # Reset filter state when clicking folder

    def update_list_widget(self, image_paths):
        """Updates listWidget items and resets scroll position"""
        # Reset loading state
        self.is_loading = False
        self.all_image_paths = image_paths
        self.loaded_count = 0
        
        # Clear and reset
        self.listWidget.clear()
        self.listWidget.verticalScrollBar().setValue(0)
        
        # Load initial batch
        batch_size = 25  # Increased initial batch size
        initial_count = min(batch_size, len(image_paths))
        
        if initial_count > 0:
            # Disable updates during bulk operation
            self.listWidget.setUpdatesEnabled(False)
            
            # Pre-allocate items for better performance
            items_to_add = []
            
            for i in range(initial_count):
                path = image_paths[i]
                name = os.path.splitext(os.path.basename(path))[0]
                cropped_name = self.crop_text_for_thumbnail(name)
                
                # Generate thumbnail with category-separated cache
                icon = self.generate_thumbnail(path)
                item = QtWidgets.QListWidgetItem(icon, cropped_name)
                item.setData(Qt.UserRole, path)
                item.setToolTip(name)  # Show full name on hover
                items_to_add.append(item)
            
            # Add all items at once
            for item in items_to_add:
                self.listWidget.addItem(item)
            
            self.loaded_count = initial_count
            
            # Re-enable updates and refresh
            self.listWidget.setUpdatesEnabled(True)
            self.listWidget.repaint()
            QtWidgets.QApplication.processEvents()

    def on_filter_changed(self):
        """Handle filter text changes with debouncing"""
        self.filter_timer.stop()
        self.filter_timer.start(300)  # 300ms delay

    def apply_filter(self):
        """Apply the current filter across all category paths - FIXED to handle clearing"""
        filter_text = self.filterLineEdit.text().strip()
        
        # If filter is empty or too short, restore to normal view
        if len(filter_text) == 0:
            self.clear_filter()
            return
        elif len(filter_text) < 3:
            # Don't apply filter for very short text, but don't clear either
            return
        
        # Apply the filter
        all_category_paths = self.get_all_category_paths()
        all_files = []
        
        # Search across all category paths
        for category_path in all_category_paths:
            if os.path.exists(category_path):
                files = self.fs_cache.get_files(category_path, ['.png', '.jpg'])
                all_files.extend(files)
        
        # Filter files based on the search text
        filter_lower = filter_text.lower()
        filtered_files = [
            f for f in all_files 
            if filter_lower in os.path.basename(f).lower()
        ]
        
        self.update_list_widget(filtered_files)
        self.treeView.clearSelection()
        self.is_filtered = True

    def clear_filter(self):
        """Clear the current filter and restore previous view"""
        self.is_filtered = False
        
        # If we have a previously selected folder, restore its contents
        if self.last_selected_folder and os.path.exists(self.last_selected_folder):
            image_paths = self.load_images_lazy(self.last_selected_folder)
            self.update_list_widget(image_paths)
            
            # Try to restore tree selection
            try:
                index = self.dirModel.index(self.last_selected_folder)
                if index.isValid():
                    self.treeView.setCurrentIndex(index)
            except:
                pass  # If we can't restore selection, that's okay
        else:
            # No previous folder selection, show random files from all categories
            self.updateTreeview()

    def toSP(self, index):
        selected_item = self.listWidget.currentItem()
        if not selected_item:
            return
            
        # Get the full name from tooltip (which contains the uncropped name)
        full_name = selected_item.toolTip()
        if not full_name:
            # Fallback to displayed text if no tooltip
            full_name = selected_item.text().replace("...", "")
        
        file_path = selected_item.data(Qt.UserRole)
        
        if not file_path:
            # Fallback to original search method using full name across all category paths
            all_category_paths = self.get_all_category_paths()
            mat_path = []
            mat_name = []
            
            for base_path in all_category_paths:
                if not os.path.exists(base_path):
                    continue
                    
                for root, dirs, files in os.walk(base_path):
                    for f in files:
                        f_no_extension = os.path.splitext(f)[0]
                        if full_name == f_no_extension:
                            if self.radioMaterial.isChecked():
                                if os.path.splitext(f)[1] == '.sbsar':
                                    mat_path.append(root)
                                    mat_name.append(f)
                            if self.radioAlpha.isChecked():
                                if os.path.splitext(f)[1] in ['.sbsar', '.png', '.tif']:
                                    mat_path.append(root)
                                    mat_name.append(f)
                            if self.radioSmartMaterial.isChecked():
                                if os.path.splitext(f)[1] == '.spsm':
                                    mat_path.append(root)
                                    mat_name.append(f)

            if mat_path and mat_name:
                full_path = os.path.join(mat_path[0], mat_name[0])
        else:
            # Find the actual substance file based on the image path
            directory = os.path.dirname(file_path)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Look for substance files with the same base name
            for f in os.listdir(directory):
                f_no_extension = os.path.splitext(f)[0]
                if base_name == f_no_extension:
                    if self.radioMaterial.isChecked() and f.endswith('.sbsar'):
                        full_path = os.path.join(directory, f)
                        break
                    elif self.radioAlpha.isChecked() and f.endswith(('.sbsar', '.png', '.tif')):
                        full_path = os.path.join(directory, f)
                        break
                    elif self.radioSmartMaterial.isChecked() and f.endswith('.spsm'):
                        full_path = os.path.join(directory, f)
                        break

        if 'full_path' in locals() and full_path:
            print(full_path)
            tmp_dir = tempfile.gettempdir()
            shutil.copy(full_path, tmp_dir)
            temp_file = os.path.join(tmp_dir, os.path.basename(full_path))
            
            try:
                if self.radioMaterial.isChecked():
                    new_material = substance_painter.resource.import_session_resource(temp_file, substance_painter.resource.Usage.BASE_MATERIAL)
                elif self.radioAlpha.isChecked():
                    new_material = substance_painter.resource.import_session_resource(temp_file, substance_painter.resource.Usage.ALPHA)
                elif self.radioSmartMaterial.isChecked():
                    new_material = substance_painter.resource.import_session_resource(temp_file, substance_painter.resource.Usage.SMART_MATERIAL)
                os.remove(temp_file)
            except Exception as e:
                print(f"Error importing material: {e}")
                if os.path.exists(temp_file):
                    os.remove(temp_file)

    def stop_thumbnail_worker(self):
        """Stop any background thumbnail operations (called from close_plugin)"""
        self.is_loading = False

    def changeResourepath(self):
        ctypes.windll.user32.MessageBoxW(0, 'Cannot change resource path', 'Resource Settings', 0)

    def updateSM(self):
        # latest_SM_path = (r'\\192.168.1.10\Softwares\Technical_Script\Substance\SP_Material_Manager')
        current_SM_path = os.path.expanduser('~/Documents/Adobe/Adobe Substance 3D Painter/python/plugins/SP_Material_Manager')

        try:
            shutil.copytree(latest_SM_path, current_SM_path, dirs_exist_ok=True)
            ctypes.windll.user32.MessageBoxW(0, 'Latest version updated, please reload Plugin', 'Update', 0)
        except:
            ctypes.windll.user32.MessageBoxW(0, 'An error while updating Plugin, please check again', 'Update', 0)


class DependencyErrorDialog(QtWidgets.QDialog):
    """Generic Error dialog for displaying error messages"""
    
    def __init__(self, parent, helpLink=None):
        super().__init__(parent=parent)
        self.setupUi(self)
    
    def setupUi(self, dialog):
        """Simple setup for the error dialog"""
        dialog.setObjectName("DependencyErrorDialog")
        dialog.resize(400, 200)
        dialog.setWindowTitle("Dependency Error")
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        label = QtWidgets.QLabel("Error: Missing dependencies or configuration issues.")
        layout.addWidget(label)
        
        self.dontShowAgain = QtWidgets.QCheckBox("Don't show this again")
        layout.addWidget(self.dontShowAgain)
        
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)
    
    def show(self):
        """Shows the error dialog"""
        super().show()