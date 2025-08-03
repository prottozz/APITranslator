# views/utility_view.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGridLayout,
                             QPushButton, QGroupBox, QMessageBox, QGraphicsDropShadowEffect)

from worker_thread import WorkerThread
from gui_logger import gui_logger


class UtilityView(QWidget):
    def __init__(self):
        super().__init__()
        self.worker_thread = None
        # --- ИЗМЕНЕНО: Список для хранения всех кнопок утилит ---
        self.utility_buttons = []
        self._init_ui()

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

        title = QLabel("Utilities")
        title.setObjectName("h2_heading")
        main_layout.addWidget(title)

        description = QLabel(
            "Run post-translation processing tasks. These correspond to the different `RunMode` settings.")
        description.setStyleSheet("color: #4b5563; padding-bottom: 10px;")
        main_layout.addWidget(description)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        main_layout.addLayout(grid_layout)

        utilities = [
            ("Sort Into Volumes", "Organizes raw translated files into volume subdirectories.", "sort_volumes"),
            (
            "Extract Glossary & Clean", "Separates main text from glossaries and removes markers.", "extract_glossary"),
            ("Convert to HTML", "Converts cleaned text files into individual HTML files.", "convert_html"),
            ("Convert to DOCX", "Converts cleaned text files into individual DOCX files.", "convert_docx"),
            ("Merge Cleaned Files", "Merges cleaned TXT, HTML, or DOCX files into larger documents.", "merge_cleaned"),
            ("Find Missing Glossaries", "Scans for translated chapters missing the glossary marker.",
             "find_missing_markers"),
        ]

        row, col = 0, 0
        for name, desc, task_id in utilities:
            card = QGroupBox()
            card.setProperty("class", "card")
            self._apply_shadow_effect(card)

            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(10)

            name_label = QLabel(name)
            name_label.setObjectName("h3_heading")
            name_label.setStyleSheet("padding-bottom: 0px;")  # Убираем лишний отступ

            desc_label = QLabel(desc)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #6b7280; font-size: 12px;")

            btn = QPushButton(f"Run {name.split(' ')[0]}")
            btn.setProperty("class", "btn_primary")
            btn.setFixedHeight(36)
            btn.clicked.connect(lambda _, t=task_id, n=name: self._run_utility(t, n))

            # --- ИЗМЕНЕНО: Добавляем кнопку в список для управления ее состоянием ---
            self.utility_buttons.append(btn)

            card_layout.addWidget(name_label)
            card_layout.addWidget(desc_label)
            card_layout.addStretch()
            card_layout.addWidget(btn)

            grid_layout.addWidget(card, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

        main_layout.addStretch()

    def _run_utility(self, task_name, friendly_name):
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Busy", "Another task is already running.")
            return

        # --- ИЗМЕНЕНО: Блокируем ВСЕ кнопки утилит ---
        for btn in self.utility_buttons:
            btn.setEnabled(False)

        gui_logger.info(f"Starting utility task: {friendly_name} ({task_name})")

        self.worker_thread = WorkerThread(task_name)

        # --- ИЗМЕНЕНО: Подключаемся к правильному сигналу ---
        self.worker_thread.all_tasks_finished.connect(self._on_utility_finished)

        self.worker_thread.start()

    # --- ИЗМЕНЕНО: Функция теперь принимает 'result' и обрабатывает его ---
    def _on_utility_finished(self, result):
        # --- ИЗМЕНЕНО: Разблокируем ВСЕ кнопки утилит ---
        for btn in self.utility_buttons:
            btn.setEnabled(True)

        if isinstance(result, Exception):
            gui_logger.error(f"Utility task failed: {result}")
            QMessageBox.critical(self, "Utility Error", f"The task failed with an error:\n\n{result}")
        else:
            gui_logger.info(f"Utility task finished successfully: {result}")
            QMessageBox.information(self, "Success", f"Utility task completed successfully:\n\n'{result}'")