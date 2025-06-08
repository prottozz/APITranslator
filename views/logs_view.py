# views/logs_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QFileDialog
from gui_logger import qt_handler

class LogsView(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        qt_handler.new_log_record.connect(self.log_text_edit.append) # Directly append HTML

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        title = QPushButton("Logs") # Using QPushButton as a styled title example
        title.setObjectName("h2_heading")
        main_layout.addWidget(title)

        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        # Style the log box specifically
        self.log_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1f2937; /* Dark background */
                color: #d1d5db; /* Light gray text */
                border-radius: 8px;
            }
        """)
        main_layout.addWidget(self.log_text_edit)

        button_layout = QHBoxLayout()
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.log_text_edit.clear)
        button_layout.addWidget(clear_button)

        save_button = QPushButton("Save Log")
        save_button.clicked.connect(self._save_log)
        button_layout.addWidget(save_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

    def append_log_message(self, message):
        self.log_text_edit.append(message)
        # self.log_text_edit.verticalScrollBar().setValue(self.log_text_edit.verticalScrollBar().maximum())

    def _save_log(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Log File", "", "Log Files (*.log);;Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text_edit.toPlainText())
            except Exception as e:
                # Log this error to the UI log itself, or a status bar
                self.append_log_message(f"ERROR: Could not save log: {e}")