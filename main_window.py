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

try:
    import qtawesome as qta

    QTA_INSTALLED = True
except ImportError:
    QTA_INSTALLED = False
    print("qtawesome not found. Icons will be text-based or default.")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI File Translator")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        gui_logger.info("Application MainWindow initialized.")

        # Sidebar
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("sidebarNav")  # Set object name for QSS
        self.nav_list.setFixedWidth(240)
        self.nav_list.setIconSize(QSize(20, 20))  # Ensure icons are visible
        self.nav_list.currentRowChanged.connect(self.display_view)
        main_layout.addWidget(self.nav_list)

        # Content Area
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self._add_views()

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        qt_handler.new_log_record.connect(self._update_status_bar)

        # Initial status
        self.status_bar.showMessage("Status: Idle | Config: config.yml")

        font = QFont("Inter", 10)
        QApplication.setFont(font)

        self.nav_list.setCurrentRow(0)

    def _update_status_bar(self, html_log_message):
        # A simple way to get plain text from the HTML for the status bar
        from PyQt6.QtGui import QTextDocument
        doc = QTextDocument()
        doc.setHtml(html_log_message)
        plain_text = doc.toPlainText()
        self.status_bar.showMessage(plain_text, 5000)

    def _get_icon(self, icon_name_fa, color_unselected='#374151', color_selected='white'):
        if QTA_INSTALLED:
            try:
                # The stylesheet will control the color on selection
                return qta.icon(icon_name_fa, color=color_unselected, color_active=color_selected)
            except Exception as e:
                gui_logger.warning(f"qtawesome icon error: {e}")
                return QIcon()
        return QIcon()

    def _add_views(self):
        # Icons updated to match style_example.html
        views_data = [
            {"name": " Translate", "widget": DashboardView(), "icon": "fa5s.magic"},
            {"name": " File Manager", "widget": FileManagerView(), "icon": "fa5s.folder-open"},
            {"name": " Utilities", "widget": UtilityView(), "icon": "fa5s.tools"},
            {"name": " Settings", "widget": SettingsView(), "icon": "fa5s.cog"},
            {"name": " Logs", "widget": LogsView(), "icon": "fa5s.align-left"}
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

    def closeEvent(self, event):
        gui_logger.info("Application closing.")
        event.accept()