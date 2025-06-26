# views/dashboard_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
                             QLabel, QLineEdit, QFileDialog, QComboBox, QSpinBox,
                             QListWidget, QProgressBar, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt
from project_config import get_config
from gui_logger import gui_logger
from worker_thread import WorkerThread
from utils import apply_shadow
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
        # Main layout for the entire view with padding
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Main Title ---
        title = QLabel("Dashboard & Translation")
        title.setObjectName("h2_heading")
        main_layout.addWidget(title)

        # --- Project Setup Card ---
        project_card = QGroupBox()
        project_card.setProperty("class", "card")
        project_card_layout = QVBoxLayout(project_card)

        card_title_1 = QLabel("Project Setup")
        card_title_1.setObjectName("h3_heading")
        project_card_layout.addWidget(card_title_1)

        setup_grid_layout = QGridLayout()
        project_card_layout.addLayout(setup_grid_layout)

        # Source Folder
        setup_grid_layout.addWidget(QLabel("Source Folder"), 0, 0)
        source_folder_layout = QHBoxLayout()
        self.source_folder_edit = QLineEdit()
        source_folder_layout.addWidget(self.source_folder_edit)
        source_btn = QPushButton("Browse")
        source_btn.clicked.connect(self._select_source_folder)
        source_folder_layout.addWidget(source_btn)
        setup_grid_layout.addLayout(source_folder_layout, 0, 1)

        # Output Folder
        setup_grid_layout.addWidget(QLabel("Output Folder"), 1, 0)
        output_folder_layout = QHBoxLayout()
        self.output_folder_edit = QLineEdit()
        output_folder_layout.addWidget(self.output_folder_edit)
        output_btn = QPushButton("Browse")
        output_btn.clicked.connect(self._select_output_folder)
        output_folder_layout.addWidget(output_btn)
        setup_grid_layout.addLayout(output_folder_layout, 1, 1)

        setup_grid_layout.setColumnStretch(1, 1)
        main_layout.addWidget(project_card)

        # --- Translation Actions Card ---
        actions_card = QGroupBox()
        actions_card.setProperty("class", "card")
        actions_card_layout = QVBoxLayout(actions_card)

        card_title_2 = QLabel("Translation Actions")
        card_title_2.setObjectName("h3_heading")
        actions_card_layout.addWidget(card_title_2)

        actions_row_layout = QHBoxLayout()
        actions_row_layout.setSpacing(15)
        actions_card_layout.addLayout(actions_row_layout)

        # This QHBoxLayout will contain the button and have a fixed size
        button_container = QVBoxLayout()
        button_container.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.start_button = QPushButton("Start Translation")
        self.start_button.setObjectName("btn_primary")
        self.start_button.setMinimumHeight(40)  # Match input height
        self.start_button.clicked.connect(self._start_translation)
        button_container.addWidget(self.start_button)
        actions_row_layout.addLayout(button_container)

        # Run Mode
        run_mode_group = QVBoxLayout()
        run_mode_group.addWidget(QLabel("Run Mode"))
        self.run_mode_combo = QComboBox()
        self.run_mode_combo.addItems(["Async (Recommended)", "Sequential"])
        run_mode_group.addWidget(self.run_mode_combo)
        actions_row_layout.addLayout(run_mode_group)

        # Files Per Run
        files_per_run_group = QVBoxLayout()
        files_per_run_group.addWidget(QLabel("Files Per Run"))
        self.files_per_run_spin = QSpinBox()
        self.files_per_run_spin.setRange(-1, 10000)
        self.files_per_run_spin.setToolTip("-1 for all available files")
        files_per_run_group.addWidget(self.files_per_run_spin)
        actions_row_layout.addLayout(files_per_run_group)

        actions_row_layout.addStretch()
        main_layout.addWidget(actions_card)

        # --- Status & Files Layout ---
        status_grid_layout = QGridLayout()
        status_grid_layout.setSpacing(20)
        main_layout.addLayout(status_grid_layout)

        # Left Card: Chapters to Translate
        chapters_card = QGroupBox()
        chapters_card.setProperty("class", "card")
        chapters_card_layout = QVBoxLayout(chapters_card)

        chapters_title = QLabel("Chapters to Translate")
        chapters_title.setObjectName("h3_heading")
        chapters_card_layout.addWidget(chapters_title)

        self.file_list_widget = QListWidget()
        chapters_card_layout.addWidget(self.file_list_widget)

        self.last_successful_label = QLabel("Last successful chapter processed: N/A")
        self.last_successful_label.setStyleSheet("font-size: 11px; color: #6b7280;")
        chapters_card_layout.addWidget(self.last_successful_label)
        status_grid_layout.addWidget(chapters_card, 0, 0)

        # Right Card: Active Tasks & Progress
        progress_card = QGroupBox()
        progress_card.setProperty("class", "card")
        progress_card_layout = QVBoxLayout(progress_card)

        progress_title = QLabel("Overall Progress")
        progress_title.setObjectName("h3_heading")
        progress_card_layout.addWidget(progress_title)

        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setTextVisible(True)
        self.overall_progress_bar.setFormat("%p%")
        progress_card_layout.addWidget(self.overall_progress_bar)

        progress_card_layout.addStretch()  # Pushes progress bar to the top
        status_grid_layout.addWidget(progress_card, 0, 1)

        main_layout.addStretch()

    # --- The rest of the methods (_select_source_folder, etc.) remain unchanged ---
    # ... (paste the rest of the original file's methods here)
    def load_settings(self):
        """Load settings from config and populate the UI fields."""
        self.source_folder_edit.setText(self.config.get('Settings', 'SourcePath', default=''))
        self.output_folder_edit.setText(self.config.get('Settings', 'OutputPath', default=''))

        run_mode_config = self.config.get('Settings', 'RunMode', default='async').lower()
        self.run_mode_combo.setCurrentText("Async (Recommended)" if run_mode_config == 'async' else "Sequential")

        self.files_per_run_spin.setValue(self.config.get('Settings', 'FilesPerRun', default=-1))

        last_chap = self.config.get('State', 'LastSuccessfulChapter', default='N/A')
        self.last_successful_label.setText(f"Last successful chapter processed: {last_chap}")

        # Populate file list from the loaded source path
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
            # This is a visual placeholder. Project.py has the real logic for what to process.
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

        # --- Update config with current UI settings before starting ---
        self.config.set(self.source_folder_edit.text(), 'Settings', 'SourcePath')
        self.config.set(self.output_folder_edit.text(), 'Settings', 'OutputPath')

        selected_mode_text = self.run_mode_combo.currentText()
        selected_mode = "async" if "async" in selected_mode_text.lower() else "sequential"
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

        # A simple way to show completion. A real implementation would
        # track file counts for a more accurate progress bar.
        self.overall_progress_bar.setValue(100)

        if isinstance(result, Exception):
            gui_logger.error(f"Translation task failed: {result}")
            QMessageBox.critical(self, "Error", f"Translation task encountered an error:\n{result}")
        else:
            gui_logger.info(f"Translation task completed: {result}")
            QMessageBox.information(self, "Success", f"Translation task completed successfully.")

        # Refresh last successful chapter from config
        self.config.data = self.config._load_config()
        last_chap = self.config.get('State', 'LastSuccessfulChapter', default='N/A')
        self.last_successful_label.setText(f"Last successful chapter processed: {last_chap}")