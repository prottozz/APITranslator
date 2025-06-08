# views/logs_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QFileDialog, QLabel
from gui_logger import qt_handler


class LogsView(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        qt_handler.new_log_record.connect(self.log_text_edit.append)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(15)

        title = QLabel("Logs")
        title.setObjectName("h2_heading")
        main_layout.addWidget(title)

        description = QLabel("Real-time log output from the application backend and UI.")
        main_layout.addWidget(description)

        self.log_text_edit = QTextEdit()
        self.log_text_edit.setObjectName("log_box")
        self.log_text_edit.setReadOnly(True)
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

    def _save_log(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Log File", "", "Log Files (*.log);;Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text_edit.toPlainText())
                self.log_text_edit.append("<p style='color:#10b981;'>Log saved successfully.</p>")
            except Exception as e:
                self.log_text_edit.append(f"<p style='color:#ef4444;'>ERROR: Could not save log: {e}</p>")