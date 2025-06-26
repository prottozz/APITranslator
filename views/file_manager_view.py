# views/file_manager_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                             QPushButton, QMessageBox, QTreeView, QLabel)
from PyQt6.QtCore import Qt, QDir, QSize
from PyQt6.QtGui import QFileSystemModel, QIcon
from project_config import get_config
from gui_logger import gui_logger
import os
import shutil

try:
    import qtawesome as qta

    QTA_INSTALLED = True
except ImportError:
    QTA_INSTALLED = False


class FileManagerView(QWidget):
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.paths_map = {}
        self._init_ui()
        self.load_paths_into_manager()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("File Manager")
        title.setObjectName("h2_heading")
        main_layout.addWidget(title)

        container_widget = QWidget()
        container_layout = QHBoxLayout(container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(15)
        main_layout.addWidget(container_widget)

        # Left Panel: Directory List
        self.folder_list_widget = QListWidget()
        self.folder_list_widget.setFixedWidth(250)
        self.folder_list_widget.setIconSize(QSize(20, 20))
        self.folder_list_widget.currentItemChanged.connect(self._on_folder_selected)
        container_layout.addWidget(self.folder_list_widget)

        # Right Panel: File Tree View
        right_panel_layout = QVBoxLayout()
        self.file_system_model = QFileSystemModel()
        self.file_system_model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_system_model)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)
        self.tree_view.setColumnWidth(0, 350)  # Make name column wider
        right_panel_layout.addWidget(self.tree_view)

        container_layout.addLayout(right_panel_layout)

    def _show_context_menu(self, position):
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl

        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return

        file_path = self.file_system_model.filePath(index)
        is_dir = self.file_system_model.isDir(index)

        menu = QMenu()
        open_action = menu.addAction("Open")
        open_folder_action = menu.addAction("Open Containing Folder")
        delete_action = menu.addAction("Delete")
        action = menu.exec(self.tree_view.viewport().mapToGlobal(position))

        if action == open_action:
            if os.path.exists(file_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        elif action == open_folder_action:
            folder = os.path.dirname(file_path) if not is_dir else file_path
            if os.path.exists(folder):
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        elif action == delete_action:
            confirm = QMessageBox.question(self, "Confirm Delete",
                                           f"Are you sure you want to delete '{os.path.basename(file_path)}'?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                try:
                    if is_dir:
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                    gui_logger.info(f"Deleted: {file_path}")
                except Exception as e:
                    gui_logger.error(f"Error deleting {file_path}: {e}")
                    QMessageBox.critical(self, "Delete Error", f"Could not delete {file_path}: {e}")

    def _get_folder_icon(self):
        return qta.icon('fa5s.folder', color='#f59e0b') if QTA_INSTALLED else QIcon()

    def load_paths_into_manager(self):
        self.folder_list_widget.clear()

        self.paths_map = {
            "Source Files": self.config.get('Settings', 'SourcePath'),
            "Translated Output": self.config.get('Settings', 'OutputPath'),
            "Cleaned Files": self.config.get('Settings', 'CleanedOutputPath'),
            "HTML Versions": self.config.get('Settings', 'HtmlOutputPath'),
            "DOCX Versions": self.config.get('Settings', 'DocxOutputPath'),
            "Sorted Volumes": self.config.get('Settings', 'VolumeSortPath'),
            "Merged Files": self.config.get('MergeSettings', 'OutputPath'),
            "Glossaries": self.config.get('Settings', 'GlossaryPath')
        }

        for name in self.paths_map.keys():
            item = QListWidgetItem(name)
            item.setIcon(self._get_folder_icon())
            self.folder_list_widget.addItem(item)

        self.folder_list_widget.setCurrentRow(0)
        gui_logger.info("File manager folders loaded.")

    def _on_folder_selected(self, current_item, previous_item):
        if not current_item:
            return

        folder_name = current_item.text()
        path = self.paths_map.get(folder_name, "")

        if path and os.path.isdir(path):
            self.tree_view.setRootIndex(self.file_system_model.setRootPath(path))
        else:
            gui_logger.warning(f"Path for '{folder_name}' not found: {path}. Clearing view.")
            # Clear the view by setting an invalid path
            self.file_system_model.setRootPath("")