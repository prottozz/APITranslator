# gui_logger.py
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from project_config import get_backend_logger


class QtLoggingHandler(logging.Handler, QObject):
    new_log_record = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)
        self.log_colors = {
            'DEBUG': '#6b7280',  # Gray
            'INFO': '#3b82f6',  # Blue
            'WARNING': '#f59e0b',  # Amber
            'ERROR': '#ef4444',  # Red
            'CRITICAL': '#b91c1c',  # Darker Red
        }

    def emit(self, record):
        # FIX: Manually format the timestamp using the handler's formatter
        # This creates the timestamp string instead of trying to access a non-existent attribute
        try:
            asctime = self.formatter.formatTime(record, self.formatter.datefmt)
        except Exception:
            asctime = record.created  # Fallback to unix timestamp if formatting fails

        log_level = record.levelname
        color = self.log_colors.get(log_level, '#374151')

        # Basic HTML escaping for the message itself
        message = record.getMessage().replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        log_html = (
            f"<p style='white-space: pre-wrap; margin: 0; font-family:\"Courier New\",monospace;'>"
            f"<span style='color:{color};'>[{asctime}] [{log_level}]: {message}</span>"
            f"</p>"
        )
        self.new_log_record.emit(log_html)


# --- The rest of the file remains the same ---

gui_logger = logging.getLogger("GUILogger")
gui_logger.setLevel(logging.INFO)

backend_project_logger = get_backend_logger()

if backend_project_logger:
    backend_project_logger.propagate = False

qt_handler = QtLoggingHandler()
# This formatter is now used by our custom emit method via self.formatter
formatter = logging.Formatter('%(asctime)s', datefmt='%Y-%m-%d %H:%M:%S')
qt_handler.setFormatter(formatter)

gui_logger.addHandler(qt_handler)

if backend_project_logger:
    backend_project_logger.addHandler(qt_handler)
    backend_project_logger.setLevel(logging.INFO)