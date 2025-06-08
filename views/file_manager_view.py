# views/file_manager_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QListWidget, QPushButton, QFileDialog, QHBoxLayout, \
    QMessageBox, QTreeView
from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QFileSystemModel
from project_config import get_config
from gui_logger import gui_logger
import os
import shutil  # For delete operations


class FileManagerView(QWidget):
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self._init_ui()
        self.load_paths_into_tabs()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

    def _create_file_browser_tab(self, folder_path_str, tab_name):
        tab_content_widget = QWidget()
        layout = QVBoxLayout(tab_content_widget)

        model = QFileSystemModel()
        model.setRootPath(
            folder_path_str if folder_path_str and os.path.exists(folder_path_str) else QDir.currentPath())

        tree_view = QTreeView()
        tree_view.setModel(model)
        if folder_path_str and os.path.exists(folder_path_str):
            tree_view.setRootIndex(model.index(folder_path_str))
        else:
            tree_view.setRootIndex(model.index(QDir.currentPath()))
            gui_logger.warning(
                f"Path for '{tab_name}' ('{folder_path_str}') not found or not set. Displaying current dir.")

        tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree_view.customContextMenuRequested.connect(lambda pos: self._show_context_menu(tree_view, pos))

        layout.addWidget(tree_view)
        return tab_content_widget

    def _show_context_menu(self, tree_view, position):
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QDesktopServices  # For opening files/folders
        from PyQt6.QtCore import QUrl

        index = tree_view.indexAt(position)
        if not index.isValid():
            return

        file_system_model = tree_view.model()
        file_path = file_system_model.filePath(index)
        is_dir = file_system_model.isDir(index)

        menu = QMenu()

        open_action = menu.addAction("Open")
        open_folder_action = menu.addAction("Open Containing Folder")
        delete_action = menu.addAction("Delete")

        action = menu.exec(tree_view.viewport().mapToGlobal(position))

        if action == open_action:
            if os.path.exists(file_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            else:
                QMessageBox.warning(self, "Not Found", f"Path not found: {file_path}")
        elif action == open_folder_action:
            containing_folder = os.path.dirname(file_path) if not is_dir else file_path
            if os.path.exists(containing_folder):
                QDesktopServices.openUrl(QUrl.fromLocalFile(containing_folder))
            else:
                QMessageBox.warning(self, "Not Found", f"Folder not found: {containing_folder}")
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
                    # Model should update automatically, or you might need to refresh
                except Exception as e:
                    gui_logger.error(f"Error deleting {file_path}: {e}")
                    QMessageBox.critical(self, "Delete Error", f"Could not delete {file_path}: {e}")

    def load_paths_into_tabs(self):
        self.tab_widget.clear()  # Clear existing tabs before reloading

        paths_to_manage = {
            "Source Files": self.config.get('Settings', 'SourcePath'),
            "Translated Output": self.config.get('Settings', 'OutputPath'),
            "Cleaned Files": self.config.get('Settings', 'CleanedOutputPath'),
            "HTML Versions": self.config.get('Settings', 'HtmlOutputPath'),
            "DOCX Versions": self.config.get('Settings', 'DocxOutputPath'),
            "Sorted Volumes": self.config.get('Settings', 'VolumeSortPath'),
            "Merged Files": self.config.get('MergeSettings', 'OutputPath'),
            "Glossaries": self.config.get('Settings', 'GlossaryPath')
        }

        for tab_name, path_str in paths_to_manage.items():
            if not path_str:  # Handle cases where path might not be in config
                path_str = ""  # Default to empty or current dir
                gui_logger.debug(f"Path for '{tab_name}' not found in config. Using default for browser.")

            tab_ui = self._create_file_browser_tab(path_str, tab_name)
            self.tab_widget.addTab(tab_ui, tab_name)
        gui_logger.info("File manager tabs loaded/reloaded.")