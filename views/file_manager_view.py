# views/file_manager_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QTreeView, QPushButton,
                             QMessageBox, QHBoxLayout, QLabel)
from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QFileSystemModel, QDesktopServices, QIcon
from PyQt6.QtCore import QUrl
from project_config import get_config
from gui_logger import gui_logger
import os
import shutil


class FileManagerView(QWidget):
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self._init_ui()
        self.load_paths_into_tabs()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(15)

        title = QLabel("File Manager")
        title.setObjectName("h2_heading")
        main_layout.addWidget(title)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Add a refresh button
        refresh_layout = QHBoxLayout()
        refresh_button = QPushButton("Refresh Views")
        refresh_button.clicked.connect(self.load_paths_into_tabs)
        refresh_layout.addStretch()
        refresh_layout.addWidget(refresh_button)
        main_layout.addLayout(refresh_layout)

    def _create_file_browser_tab(self, folder_path_str, tab_name):
        tab_content_widget = QWidget()
        layout = QVBoxLayout(tab_content_widget)

        model = QFileSystemModel()
        root_path = folder_path_str if folder_path_str and os.path.exists(folder_path_str) else QDir.currentPath()
        model.setRootPath(root_path)

        tree_view = QTreeView()
        tree_view.setModel(model)
        tree_view.setRootIndex(model.index(root_path))

        # Configure the tree view
        tree_view.setAnimated(True)
        tree_view.setIndentation(20)
        tree_view.setSortingEnabled(True)
        tree_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        tree_view.setColumnWidth(0, 350)

        if not (folder_path_str and os.path.exists(folder_path_str)):
            gui_logger.warning(f"Path for '{tab_name}' ('{folder_path_str}') not found. Displaying current dir.")

        tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree_view.customContextMenuRequested.connect(lambda pos, tv=tree_view: self._show_context_menu(tv, pos))

        layout.addWidget(tree_view)
        return tab_content_widget

    def _show_context_menu(self, tree_view, position):
        from PyQt6.QtWidgets import QMenu
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
        elif action == open_folder_action:
            containing_folder = os.path.dirname(file_path) if not is_dir else file_path
            if os.path.exists(containing_folder):
                QDesktopServices.openUrl(QUrl.fromLocalFile(containing_folder))
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

    def load_paths_into_tabs(self):
        self.tab_widget.clear()

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
            if not path_str:
                path_str = ""
            tab_ui = self._create_file_browser_tab(path_str, tab_name)
            self.tab_widget.addTab(tab_ui, tab_name)
        gui_logger.info("File manager tabs reloaded.")