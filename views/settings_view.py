# views/settings_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QPushButton,
                             QLabel, QLineEdit, QFileDialog, QSpinBox, QCheckBox,
                             QGroupBox, QMessageBox, QScrollArea, QTabWidget)
from PyQt6.QtCore import Qt
from project_config import get_config
from gui_logger import gui_logger
import re  # For path validation (optional)


class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self._init_ui()
        self.load_settings()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        settings_layout = QVBoxLayout(content_widget)
        settings_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- General Paths Group ---
        paths_group = QGroupBox("General Paths")
        paths_grid = QGridLayout()
        self.path_edits = {}  # Store QLineEdits for paths

        # FIX: Added 'False' to each tuple that represents a folder path.
        path_keys = [
            ("SourcePath", "Source Novel Folder:", False),
            ("OutputPath", "Initial Output Folder:", False),
            ("CleanedOutputPath", "Cleaned Output Folder:", False),
            ("GlossaryPath", "Glossaries Folder:", False),
            ("HtmlOutputPath", "HTML Output Folder:", False),
            ("DocxOutputPath", "DOCX Output Folder:", False),
            ("VolumeSortPath", "Sorted Volumes Folder:", False),
            ("PromptPath", "Prompt File:", True)  # True indicates it's a file
        ]

        for i, (key, label_text, is_file) in enumerate(path_keys):
            lbl = QLabel(label_text)
            edit = QLineEdit()
            btn = QPushButton("Browse")
            if is_file:
                btn.clicked.connect(lambda _, k=key, e=edit: self._select_file_path(k, e))
            else:
                btn.clicked.connect(lambda _, k=key, e=edit: self._select_folder_path(k, e))

            self.path_edits[key] = edit
            paths_grid.addWidget(lbl, i, 0)
            paths_grid.addWidget(edit, i, 1)
            paths_grid.addWidget(btn, i, 2)

        paths_group.setLayout(paths_grid)
        settings_layout.addWidget(paths_group)

        # --- Translation Parameters Group ---
        trans_params_group = QGroupBox("Translation Parameters")
        trans_params_layout = QGridLayout()

        self.end_chapter_spin = QSpinBox()
        self.end_chapter_spin.setRange(1, 100000)
        trans_params_layout.addWidget(QLabel("End Chapter:"), 0, 0)
        trans_params_layout.addWidget(self.end_chapter_spin, 0, 1)

        self.files_per_run_spin = QSpinBox()
        self.files_per_run_spin.setRange(-1, 1000)
        trans_params_layout.addWidget(QLabel("Files Per Run (-1 for all):"), 1, 0)
        trans_params_layout.addWidget(self.files_per_run_spin, 1, 1)

        self.use_last_successful_check = QCheckBox("Use Last Successful Chapter")
        trans_params_layout.addWidget(self.use_last_successful_check, 2, 0, 1, 2)

        # Add more settings as needed (MergeChunkSize, DefaultEncoding, etc.)
        self.model_name_edit = QLineEdit()
        trans_params_layout.addWidget(QLabel("Model Name:"), 3, 0)
        trans_params_layout.addWidget(self.model_name_edit, 3, 1)

        trans_params_group.setLayout(trans_params_layout)
        settings_layout.addWidget(trans_params_group)

        # --- API Key Management (Placeholder) ---
        api_group = QGroupBox("API Key Management (Simplified)")
        api_layout = QVBoxLayout()
        api_layout.addWidget(QLabel("API Key configuration is managed in config.yml directly for this example."))
        api_layout.addWidget(QLabel("Refer to Project.py and config.yml for APIKey structure."))
        self.api_key_placeholder_label = QLabel("API Keys: (Load from config)")
        api_layout.addWidget(self.api_key_placeholder_label)
        api_group.setLayout(api_layout)
        settings_layout.addWidget(api_group)

        # --- Save Button ---
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        settings_layout.addWidget(save_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def _select_folder_path(self, config_key, line_edit_widget):
        folder = QFileDialog.getExistingDirectory(self, f"Select {config_key} Folder", line_edit_widget.text())
        if folder:
            line_edit_widget.setText(folder)

    def _select_file_path(self, config_key, line_edit_widget):
        # For prompt.txt, it's a text file
        current_path = line_edit_widget.text()
        file_path, _ = QFileDialog.getOpenFileName(self, f"Select {config_key} File", current_path,
                                                   "Text files (*.txt);;All files (*)")
        if file_path:
            line_edit_widget.setText(file_path)

    def load_settings(self):
        gui_logger.info("Loading settings into Settings View...")
        for key, widget in self.path_edits.items():
            widget.setText(self.config.get('Settings', key, default=''))

        self.end_chapter_spin.setValue(self.config.get('Settings', 'EndChapter', default=1000))
        self.files_per_run_spin.setValue(self.config.get('Settings', 'FilesPerRun', default=-1))
        self.use_last_successful_check.setChecked(self.config.get('Settings', 'UseLastSuccessfulChapter', default=True))
        self.model_name_edit.setText(self.config.get('Settings', 'ModelName', default="gemini-1.5-pro-latest"))

        # API Keys display (simplified)
        api_keys_data = self.config.get('APIKeys', default={})
        if api_keys_data:
            display_text = "Loaded API Keys:\n"
            for name, data in api_keys_data.items():
                acc = data.get('account', 'N/A')
                key_part = str(data.get('key', ''))[:4] + "..."  # Masked
                display_text += f"- {name} (Account: {acc}, Key: {key_part})\n"
            self.api_key_placeholder_label.setText(display_text)
        else:
            self.api_key_placeholder_label.setText("No API Keys found in config or config is empty.")

    def save_settings(self):
        gui_logger.info("Saving settings from Settings View...")
        try:
            for key, widget in self.path_edits.items():
                self.config.set(widget.text(), 'Settings', key)

            self.config.set(self.end_chapter_spin.value(), 'Settings', 'EndChapter')
            self.config.set(self.files_per_run_spin.value(), 'Settings', 'FilesPerRun')
            self.config.set(self.use_last_successful_check.isChecked(), 'Settings', 'UseLastSuccessfulChapter')
            self.config.set(self.model_name_edit.text(), 'Settings', 'ModelName')
            # Add saving for other parameters here

            self.config.save()
            gui_logger.info("Settings saved successfully to config.yml.")
            QMessageBox.information(self, "Success", "Settings saved successfully.")
        except Exception as e:
            gui_logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")