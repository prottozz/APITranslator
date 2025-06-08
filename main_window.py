# main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QStackedWidget, QStatusBar, QLabel,
                             QListWidgetItem, QApplication)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize

from views.dashboard_view import DashboardView
from views.settings_view import SettingsView
from views.utility_view import UtilityView
from views.file_manager_view import FileManagerView
from views.logs_view import LogsView

from gui_logger import gui_logger, qt_handler
from project_config import get_config

try:
    import qtawesome as qta

    QTA_INSTALLED = True
except ImportError:
    QTA_INSTALLED = False
    print("qtawesome not found. Icons will be text-based or default.")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.setWindowTitle("AI File Translator - Novel Edition")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        gui_logger.info("Application MainWindow initialized.")

        # Sidebar
        sidebar_widget = self._create_sidebar()
        main_layout.addWidget(sidebar_widget)

        # Right side wrapper (for content and status bar)
        right_side_wrapper = QWidget()
        right_layout = QVBoxLayout(right_side_wrapper)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        main_layout.addWidget(right_side_wrapper, 1)  # Add stretch factor

        # Content Area
        self.stacked_widget = QStackedWidget()
        right_layout.addWidget(self.stacked_widget)

        self._add_views()

        # Status Bar
        self.status_bar = QStatusBar()
        right_layout.addWidget(self.status_bar)

        # Initial status message
        config_path = self.config.config_path
        self.status_config_label = QLabel(f"Config: {config_path}")
        self.status_bar.addPermanentWidget(self.status_config_label)

        self.status_bar.showMessage("Status: Idle")
        qt_handler.new_log_record.connect(self._update_status_bar)

        self.nav_list.setCurrentRow(0)

    def _create_sidebar(self):
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(10)
        sidebar_widget.setFixedWidth(240)
        sidebar_widget.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e5e7eb;")

        # App Title in Sidebar
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(10, 20, 10, 20)
        app_title = QLabel("AI Translator")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #4f46e5;")
        app_subtitle = QLabel("Novel Edition")
        app_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_subtitle.setStyleSheet("font-size: 11px; color: #6b7280;")
        title_layout.addWidget(app_title)
        title_layout.addWidget(app_subtitle)
        sidebar_layout.addWidget(title_container)

        # Navigation List
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("sidebarNav")
        self.nav_list.setSpacing(5)
        self.nav_list.currentRowChanged.connect(self.display_view)
        sidebar_layout.addWidget(self.nav_list)

        sidebar_layout.addStretch()

        return sidebar_widget

    def _update_status_bar(self, html_log_message):
        from PyQt6.QtGui import QTextDocument
        doc = QTextDocument()
        doc.setHtml(html_log_message)
        plain_text = doc.toPlainText().split("]:", 1)[-1].strip()
        self.status_bar.showMessage(f"Status: {plain_text}", 5000)

    def _get_icon(self, icon_name_fa, color='#374151'):
        if QTA_INSTALLED:
            try:
                return qta.icon(icon_name_fa, color=color, color_active='#ffffff')
            except Exception as e:
                gui_logger.warning(f"qtawesome icon error: {e}")
        return QIcon()

    def _add_views(self):
        views_data = [
            {"name": "Translate", "widget": DashboardView(), "icon": "fa5s.magic"},
            {"name": "File Manager", "widget": FileManagerView(), "icon": "fa5s.folder-open"},
            {"name": "Utilities", "widget": UtilityView(), "icon": "fa5s.tools"},
            {"name": "Settings", "widget": SettingsView(), "icon": "fa5s.cog"},
            {"name": "Logs", "widget": LogsView(), "icon": "fa5s.align-left"}
        ]

        for view_info in views_data:
            item = QListWidgetItem(view_info["name"])
            item.setIcon(self._get_icon(view_info["icon"]))
            item.setSizeHint(QSize(0, 45))
            item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.nav_list.addItem(item)
            self.stacked_widget.addWidget(view_info["widget"])

    def display_view(self, index):
        self.stacked_widget.setCurrentIndex(index)
        # Update icon colors on selection
        for i in range(self.nav_list.count()):
            item = self.nav_list.item(i)
            view_info = self._get_icon(views_data[i]["icon"])  # Re-get default icon
            if i == index:
                view_info = self._get_icon(views_data[i]["icon"], color='#ffffff')  # Get active icon
            item.setIcon(view_info)

    def closeEvent(self, event):
        gui_logger.info("Application closing.")
        event.accept()


# Dummy views_data for display_view logic
views_data = [
    {"icon": "fa5s.magic"}, {"icon": "fa5s.folder-open"}, {"icon": "fa5s.tools"},
    {"icon": "fa5s.cog"}, {"icon": "fa5s.align-left"}
]