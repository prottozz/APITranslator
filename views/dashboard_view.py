# views/dashboard_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
                             QLabel, QLineEdit, QFileDialog, QComboBox, QSpinBox,
                             QListWidget, QProgressBar, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt
from project_config import get_config
from gui_logger import gui_logger
from worker_thread import WorkerThread
import re
import os


class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.worker_thread = None
        self._init_ui()
        self.load_settings()

        

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Dashboard & Translation")
        title.setObjectName("h2_heading")
        main_layout.addWidget(title)

        # --- Project Setup Card ---
        project_card = QGroupBox("Project Setup")
        project_card.setProperty("class", "card")
        project_card_layout = QGridLayout(project_card)
        project_card_layout.setSpacing(10)

        # Source Folder
        source_label = QLabel("Source Folder")
        source_label.setProperty("class", "input-label")
        self.source_folder_edit = QLineEdit()
        source_btn = QPushButton("Browse")
        source_btn.clicked.connect(self._select_source_folder)
        project_card_layout.addWidget(source_label, 0, 0)
        project_card_layout.addWidget(self.source_folder_edit, 0, 1)
        project_card_layout.addWidget(source_btn, 0, 2)

        # Output Folder
        output_label = QLabel("Output Folder")
        output_label.setProperty("class", "input-label")
        self.output_folder_edit = QLineEdit()
        output_btn = QPushButton("Browse")
        output_btn.clicked.connect(self._select_output_folder)
        project_card_layout.addWidget(output_label, 1, 0)
        project_card_layout.addWidget(self.output_folder_edit, 1, 1)
        project_card_layout.addWidget(output_btn, 1, 2)

        project_card_layout.setColumnStretch(1, 1)
        main_layout.addWidget(project_card)

        # --- Translation Actions Card ---
        actions_card = QGroupBox("Translation Actions")
        actions_card.setProperty("class", "card")
        actions_card_layout = QHBoxLayout(actions_card)
        actions_card_layout.setSpacing(20)
        # Let the layout align items vertically centered by default
        actions_card_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Start Button
        self.start_button = QPushButton("Start Translation")
        self.start_button.setObjectName("btn_primary")
        self.start_button.clicked.connect(self._start_translation)

        # Run Mode
        self.run_mode_combo = QComboBox()
        self.run_mode_combo.addItems(["Async (Recommended)", "Sequential"])

        # --- FIX: Set button's minimum height to match the combo box's hint ---
        self.start_button.setMinimumHeight(self.run_mode_combo.sizeHint().height())

        run_mode_group = self._create_input_group("Run Mode", self.run_mode_combo)

        # Files Per Run
        self.files_per_run_spin = QSpinBox()
        self.files_per_run_spin.setRange(-1, 10000)
        self.files_per_run_spin.setToolTip("-1 for all available files")
        files_per_run_group = self._create_input_group("Files Per Run", self.files_per_run_spin)

        actions_card_layout.addWidget(self.start_button)
        actions_card_layout.addLayout(run_mode_group)
        actions_card_layout.addLayout(files_per_run_group)
        actions_card_layout.addStretch()
        main_layout.addWidget(actions_card)

        # --- Status & Files Layout ---
        status_grid_layout = QGridLayout()
        status_grid_layout.setSpacing(20)
        main_layout.addLayout(status_grid_layout)

        # Left Card: Chapters to Translate
        chapters_card = QGroupBox("Chapters to Translate")
        chapters_card.setProperty("class", "card")
        chapters_card_layout = QVBoxLayout(chapters_card)
        self.file_list_widget = QListWidget()
        self.last_successful_label = QLabel("Last successful chapter processed: N/A")
        self.last_successful_label.setStyleSheet("font-size: 11px; color: #6b7280;")
        chapters_card_layout.addWidget(self.file_list_widget)
        chapters_card_layout.addWidget(self.last_successful_label)
        status_grid_layout.addWidget(chapters_card, 0, 0)

        # Right Card: Progress
        progress_card = QGroupBox("Overall Progress")
        progress_card.setProperty("class", "card")
        progress_card_layout = QVBoxLayout(progress_card)
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setTextVisible(True)
        self.overall_progress_bar.setFormat("%p%")
        progress_card_layout.addWidget(self.overall_progress_bar)
        progress_card_layout.addStretch()
        status_grid_layout.addWidget(progress_card, 0, 1)

        main_layout.addStretch()

    def _create_input_group(self, label_text, widget):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        label = QLabel(label_text)
        label.setProperty("class", "input-label")
        layout.addWidget(label, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(widget)
        return layout

    def load_settings(self):
        self.source_folder_edit.setText(self.config.get('Settings', 'SourcePath', default=''))
        self.output_folder_edit.setText(self.config.get('Settings', 'OutputPath', default=''))
        run_mode_config = self.config.get('Settings', 'RunMode', default='async').lower()
        self.run_mode_combo.setCurrentText("Async (Recommended)" if run_mode_config == 'async' else "Sequential")
        self.files_per_run_spin.setValue(self.config.get('Settings', 'FilesPerRun', default=-1))
        last_chap = self.config.get('State', 'LastSuccessfulChapter', default='N/A')
        self.last_successful_label.setText(f"Last successful chapter processed: {last_chap}")
        self._populate_file_list(self.source_folder_edit.text())

    def _select_source_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.source_folder_edit.setText(folder)
            self._populate_file_list(folder)

    def _select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder_edit.setText(folder)

    def _populate_file_list(self, folder_path_str):
        self.file_list_widget.clear()
        if not folder_path_str or not os.path.isdir(folder_path_str):
            self.file_list_widget.addItem("Source folder not set or not found.")
            return
        try:
            from pathlib import Path
            folder_path = Path(folder_path_str)
            files = [f.name for f in folder_path.glob("*.txt") if re.match(r'^\d{4}.*', f.name)]
            files.sort()
            if files:
                self.file_list_widget.addItems(files)
            else:
                self.file_list_widget.addItem("No matching chapter files found in source.")
        except Exception as e:
            self.file_list_widget.addItem(f"Error listing files: {e}")
            gui_logger.error(f"Error populating file list: {e}")

    def _start_translation(self):
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Busy", "A task is already running.")
            return

        self.config.set(self.source_folder_edit.text(), 'Settings', 'SourcePath')
        self.config.set(self.output_folder_edit.text(), 'Settings', 'OutputPath')
        selected_mode = "async" if "async" in self.run_mode_combo.currentText().lower() else "sequential"
        self.config.set(selected_mode, 'Settings', 'RunMode')
        self.config.set(self.files_per_run_spin.value(), 'Settings', 'FilesPerRun')
        self.config.save()
        gui_logger.info("Configuration saved before starting translation.")

        task_name = "translate_async" if selected_mode == "async" else "translate_sequential"
        self.overall_progress_bar.setValue(0)
        self.start_button.setEnabled(False)
        self.start_button.setText("Translating...")

        self.worker_thread = WorkerThread(task_name)
        self.worker_thread.task_finished.connect(self._on_translation_finished)
        self.worker_thread.start()
        gui_logger.info(f"Starting {selected_mode} translation task...")

    def _on_translation_finished(self, result):
        self.start_button.setEnabled(True)
        self.start_button.setText("Start Translation")
        self.overall_progress_bar.setValue(100)
        if isinstance(result, Exception):
            gui_logger.error(f"Translation task failed: {result}")
            QMessageBox.critical(self, "Error", f"Translation task encountered an error:\n{result}")
        else:
            gui_logger.info(f"Translation task completed: {result}")
            QMessageBox.information(self, "Success", f"Translation task completed successfully.")

        self.config.data = self.config._load_config()
        last_chap = self.config.get('State', 'LastSuccessfulChapter', default='N/A')
        self.last_successful_label.setText(f"Last successful chapter processed: {last_chap}")