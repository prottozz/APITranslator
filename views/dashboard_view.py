# views/dashboard_view.py
import os
import re
import uuid
from pathlib import Path
from datetime import datetime

# ИЗМЕНЕНО: Добавляем QTimer
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
                             QLabel, QLineEdit, QFileDialog, QComboBox, QSpinBox,
                             QListWidget, QProgressBar, QGroupBox, QMessageBox,
                             QGraphicsDropShadowEffect, QListWidgetItem, QScrollArea)

from project_config import get_config
from gui_logger import gui_logger
from worker_thread import WorkerThread
from ui_helper import create_svg_icon


class TaskStatusWidget(QWidget):
    def __init__(self, task_id, description, start_time):
        super().__init__()
        self.task_id = task_id
        self.start_time = start_time
        self.is_finished = False

        # Иконки
        self.in_progress_icon = create_svg_icon("icons/cogs_colored.svg", "#3b82f6")
        self.completed_icon = create_svg_icon("icons/check-circle_colored.svg", "#10b981")
        self.error_icon = create_svg_icon("icons/exclamation-triangle_colored.svg", "#ef4444")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setPixmap(self.in_progress_icon.pixmap(QSize(16, 16)))

        self.desc_label = QLabel(description)
        self.desc_label.setStyleSheet("color: #374151;")

        self.time_label = QLabel(f"Started at: {self.start_time.strftime('%H:%M:%S')}")
        self.time_label.setStyleSheet("color: #6b7280; font-size: 11px;")

        self.elapsed_label = QLabel("Elapsed time: 00:00")
        self.elapsed_label.setStyleSheet("color: #6b7280; font-size: 11px;")

        layout.addWidget(self.icon_label)
        layout.addWidget(self.desc_label)
        layout.addStretch()
        layout.addWidget(self.time_label)
        layout.addWidget(self.elapsed_label)

        self.setStyleSheet("border-bottom: 1px solid #e5e7eb;")

    def update_elapsed_time(self):
        if self.is_finished:
            return

        delta = datetime.now() - self.start_time
        minutes, seconds = divmod(int(delta.total_seconds()), 60)
        self.elapsed_label.setText(f"Elapsed: {minutes:02}:{seconds:02}")

    def set_succeeded(self):
        self.is_finished = True
        self.icon_label.setPixmap(self.completed_icon.pixmap(QSize(16, 16)))
        self.desc_label.setStyleSheet("color: #10b981;")  # Green

    def set_failed(self):
        self.is_finished = True
        self.icon_label.setPixmap(self.error_icon.pixmap(QSize(16, 16)))
        self.desc_label.setStyleSheet("color: #ef4444;")  # Red

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.worker_thread = None

        self.folder_icon = QIcon("icons/folder-plus.svg")
        self.pending_icon = create_svg_icon("icons/hourglass-start_colored.svg", "#f59e0b")
        self.completed_icon = create_svg_icon("icons/check-circle_colored.svg", "#10b981")
        self.error_icon = create_svg_icon("icons/exclamation-triangle_colored.svg", "#ef4444")
        self.play_icon = QIcon("icons/play.svg")

        self._init_ui()
        self.load_settings()

        self.task_widgets = {}
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(1000)  # Обновление каждую секунду
        self.update_timer.timeout.connect(self._update_task_timers)
        self.update_timer.start()

    def _create_input_group(self, label_text, widget):
        layout = QVBoxLayout()
        layout.setSpacing(4)
        label = QLabel(label_text)
        layout.addWidget(label)
        layout.addWidget(widget)
        return layout

    def _apply_shadow_effect(self, widget):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        widget.setGraphicsEffect(shadow)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Dashboard & Translation")
        title.setObjectName("h2_heading")
        main_layout.addWidget(title)

        # --- Project Setup Card ---
        project_card = QGroupBox()
        project_card.setProperty("class", "card")
        self._apply_shadow_effect(project_card)
        project_card_layout = QVBoxLayout(project_card)
        card_title_1 = QLabel("Project Setup")
        card_title_1.setObjectName("h3_heading")
        project_card_layout.addWidget(card_title_1)
        setup_fields_layout = QHBoxLayout()
        project_card_layout.addLayout(setup_fields_layout)
        source_group_layout = QVBoxLayout()
        source_group_layout.addWidget(QLabel("Source Folder"))
        source_input_layout = QHBoxLayout()
        self.source_folder_edit = QLineEdit()
        self.source_folder_edit.setFixedHeight(40)
        source_input_layout.addWidget(self.source_folder_edit)
        source_btn = QPushButton()
        source_btn.setIcon(self.folder_icon)
        source_btn.setIconSize(QSize(20, 20))
        source_btn.setFixedSize(40, 40)
        source_btn.clicked.connect(self._select_source_folder)
        source_input_layout.addWidget(source_btn)
        source_group_layout.addLayout(source_input_layout)
        setup_fields_layout.addLayout(source_group_layout)
        output_group_layout = QVBoxLayout()
        output_group_layout.addWidget(QLabel("Output Folder"))
        output_input_layout = QHBoxLayout()
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setFixedHeight(40)
        output_input_layout.addWidget(self.output_folder_edit)
        output_btn = QPushButton()
        output_btn.setIcon(self.folder_icon)
        output_btn.setIconSize(QSize(20, 20))
        output_btn.setFixedSize(40, 40)
        output_btn.clicked.connect(self._select_output_folder)
        output_input_layout.addWidget(output_btn)
        output_group_layout.addLayout(output_input_layout)
        setup_fields_layout.addLayout(output_group_layout)
        main_layout.addWidget(project_card)

        # --- Translation Actions Card ---
        actions_card = QGroupBox()
        actions_card.setProperty("class", "card")
        self._apply_shadow_effect(actions_card)
        actions_card_layout = QVBoxLayout(actions_card)
        card_title_2 = QLabel("Translation Actions")
        card_title_2.setObjectName("h3_heading")
        actions_card_layout.addWidget(card_title_2)
        actions_row_layout = QHBoxLayout()
        actions_row_layout.setSpacing(20)
        actions_card_layout.addLayout(actions_row_layout)
        self.start_button = QPushButton("Start Translation")
        self.start_button.setProperty("class", "btn_primary")
        self.start_button.setFixedHeight(40)
        self.start_button.setIcon(self.play_icon)
        self.start_button.setIconSize(QSize(18, 18))
        self.start_button.clicked.connect(self._start_translation)
        start_button_layout = QVBoxLayout()
        start_button_layout.addWidget(self.start_button)
        start_button_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        actions_row_layout.addLayout(start_button_layout)
        self.run_mode_combo = QComboBox()
        self.run_mode_combo.addItems(["Async (Recommended)", "Sequential"])
        self.run_mode_combo.setFixedWidth(200)
        self.run_mode_combo.setFixedHeight(40)
        actions_row_layout.addLayout(self._create_input_group("Run Mode", self.run_mode_combo))
        self.files_per_run_spin = QSpinBox()
        self.files_per_run_spin.setRange(-1, 10000)
        self.files_per_run_spin.setToolTip("-1 for all available files")
        self.files_per_run_spin.setFixedWidth(120)
        self.files_per_run_spin.setFixedHeight(40)
        actions_row_layout.addLayout(self._create_input_group("Files Per Run", self.files_per_run_spin))
        actions_row_layout.addStretch(1)
        main_layout.addWidget(actions_card)

        # --- Status & Files Layout ---
        bottom_section_layout = QHBoxLayout()
        bottom_section_layout.setSpacing(20)
        main_layout.addLayout(bottom_section_layout, 1)
        chapters_card = QGroupBox()
        chapters_card.setProperty("class", "card")
        self._apply_shadow_effect(chapters_card)
        chapters_card_layout = QVBoxLayout(chapters_card)
        chapters_title = QLabel("Chapters to Translate")
        chapters_title.setObjectName("h3_heading")
        chapters_card_layout.addWidget(chapters_title)
        self.file_list_widget = QListWidget()
        self.file_list_widget.setIconSize(QSize(16, 16))
        chapters_card_layout.addWidget(self.file_list_widget)
        self.last_successful_label = QLabel("Last successful chapter processed: N/A")
        self.last_successful_label.setStyleSheet("font-size: 11px; color: #6b7280;")
        chapters_card_layout.addWidget(self.last_successful_label)
        bottom_section_layout.addWidget(chapters_card, 1)

        # --- Active & Queued Tasks ---
        progress_card = QGroupBox()
        progress_card.setProperty("class", "card")
        self._apply_shadow_effect(progress_card)
        progress_card_layout = QVBoxLayout(progress_card)
        progress_card_layout.setContentsMargins(15, 15, 15, 15)
        progress_title = QLabel("Active & Queued Tasks")
        progress_title.setObjectName("h3_heading")
        progress_card_layout.addWidget(progress_title)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("taskScrollArea")
        self.tasks_container_widget = QWidget()
        self.active_tasks_layout = QVBoxLayout(self.tasks_container_widget)
        self.active_tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.active_tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.active_tasks_layout.setSpacing(0)
        scroll_area.setWidget(self.tasks_container_widget)
        progress_card_layout.addWidget(scroll_area)

        bottom_section_layout.addWidget(progress_card, 1)

    # --- Методы ---

    def load_settings(self):
        self.source_folder_edit.setText(self.config.get('Settings', 'SourcePath', default=''))
        self.output_folder_edit.setText(self.config.get('Settings', 'OutputPath', default=''))
        run_mode_config = self.config.get('Settings', 'RunMode', default='async').lower()
        self.run_mode_combo.setCurrentText("Async (Recommended)" if run_mode_config == 'async' else "Sequential")
        self.files_per_run_spin.setValue(self.config.get('Settings', 'FilesPerRun', default=-1))
        last_chap = self.config.get('State', 'LastSuccessfulChapter', default='N/A')
        self.last_successful_label.setText(f"Last successful chapter processed: {last_chap}")
        self._populate_file_list()

    def _select_source_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.source_folder_edit.setText(folder)
            self._populate_file_list()

    def _select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder_edit.setText(folder)
            # ИЗМЕНЕНО: Обновляем список, т.к. статус глав мог измениться
            self._populate_file_list()

    def _populate_file_list(self):
        """
        ИЗМЕНЕНО: Полностью переработанный метод.
        Заполняет список глав, сравнивая папки Source и Output для определения статуса.
        """
        self.file_list_widget.clear()

        source_path_str = self.source_folder_edit.text()
        output_path_str = self.output_folder_edit.text()

        # Проверка исходной папки
        if not source_path_str or not os.path.isdir(source_path_str):
            self.file_list_widget.addItem("Source folder not set or not found.")
            return

        # 1. Получаем номера уже переведенных глав для быстрой проверки
        translated_chapters = set()
        if output_path_str and os.path.isdir(output_path_str):
            try:
                output_path = Path(output_path_str)
                for f in output_path.glob("*.txt"):
                    match = re.match(r'^(\d{4})', f.name)
                    if match:
                        translated_chapters.add(match.group(1))
            except Exception as e:
                gui_logger.warning(f"Could not read output directory {output_path_str}: {e}")

        # 2. Проходим по исходным файлам и определяем их статус
        try:
            source_path = Path(source_path_str)
            files = sorted([f.name for f in source_path.glob("*.txt") if re.match(r'^\d{4}.*', f.name)])

            if not files:
                self.file_list_widget.addItem("No matching chapter files found in source.")
                return

            for filename in files:
                item = QListWidgetItem(filename)

                # Определяем статус
                match = re.match(r'^(\d{4})', filename)
                if match and match.group(1) in translated_chapters:
                    item.setIcon(self.completed_icon)
                else:
                    item.setIcon(self.pending_icon)

                self.file_list_widget.addItem(item)

        except Exception as e:
            item = QListWidgetItem(f"Error listing files: {e}")
            item.setIcon(self.error_icon)
            self.file_list_widget.addItem(item)
            gui_logger.error(f"Error populating file list: {e}")

    def _start_translation(self):
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Busy", "A task is already running.")
            return

            # ... (сохранение конфига без изменений)
        self.config.set(self.source_folder_edit.text(), 'Settings', 'SourcePath')
        self.config.set(self.output_folder_edit.text(), 'Settings', 'OutputPath')
        selected_mode = "async" if "async" in self.run_mode_combo.currentText().lower() else "sequential"
        self.config.set(selected_mode, 'Settings', 'RunMode')
        self.config.set(self.files_per_run_spin.value(), 'Settings', 'FilesPerRun')
        self.config.save()
        gui_logger.info("Configuration saved before starting translation.")

        task_name = "translate_async"  # Имя для воркера

        self.start_button.setEnabled(False)
        self.start_button.setText("Translating...")

        while self.active_tasks_layout.count():
            child = self.active_tasks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.task_widgets.clear()

        # Запуск потока
        self.worker_thread = WorkerThread(task_name)
        # ИЗМЕНЕНО: Подключаем новые сигналы
        self.worker_thread.task_started.connect(self._on_task_started)
        self.worker_thread.task_retrying.connect(self._on_task_retrying)
        self.worker_thread.task_succeeded.connect(self._on_task_succeeded)
        self.worker_thread.task_failed.connect(self._on_task_failed)
        self.worker_thread.all_tasks_finished.connect(self._on_all_tasks_finished)

        self.worker_thread.start()
        gui_logger.info(f"Starting translation task...")

    def _on_task_started(self, task_id, description, start_time):
        widget = TaskStatusWidget(task_id, description, start_time)
        self.active_tasks_layout.addWidget(widget)
        self.task_widgets[task_id] = widget

    def _on_task_retrying(self, task_id, message):
        retry_label = QLabel(f"└─ {message}")
        retry_label.setStyleSheet("color: #f59e0b; font-size: 11px; padding-left: 25px;")
        self.active_tasks_layout.addWidget(retry_label)

    def _on_task_succeeded(self, task_id):
        if task_id in self.task_widgets:
            self.task_widgets[task_id].set_succeeded()

    def _on_task_failed(self, task_id, error_message):
        if task_id in self.task_widgets:
            self.task_widgets[task_id].set_failed()
        gui_logger.error(f"Task {task_id} failed: {error_message}")
        QMessageBox.critical(self, "Task Error", f"A task failed after all retries:\n{error_message}")

    def _on_all_tasks_finished(self):
        """Срабатывает, когда весь цикл в потоке завершен."""
        self.start_button.setEnabled(True)
        self.start_button.setText("Start Translation")
        gui_logger.info("All translation tasks have been processed.")
        self._populate_file_list() # Обновляем список глав

    def _update_task_timers(self):
        """Вызывается каждую секунду для обновления таймеров."""
        for widget in self.task_widgets.values():
            widget.update_elapsed_time()