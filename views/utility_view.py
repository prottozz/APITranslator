# views/utility_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QGroupBox,
                             QMessageBox, QGridLayout, QLabel, QTextBrowser)
from PyQt6.QtCore import Qt
from worker_thread import WorkerThread
from gui_logger import gui_logger


class UtilityView(QWidget):
    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.buttons = {}
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Utilities")
        title.setObjectName("h2_heading")
        main_layout.addWidget(title)

        description = QLabel(
            "Run post-translation processing tasks. These correspond to the different `RunMode` settings.")
        description.setWordWrap(True)
        main_layout.addWidget(description)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        main_layout.addLayout(grid_layout)

        utilities = [
            ("Sort into Volumes", "sort_volumes",
             "Sorts raw translated files from `OutputPath` into subdirectories based on volume titles."),
            ("Extract Glossary & Clean", "extract_glossary",
             "Separates text from glossaries and saves to `CleanedOutputPath`."),
            ("Convert to HTML", "convert_html",
             "Converts cleaned text files into individual HTML files in `HtmlOutputPath`."),
            ("Convert to DOCX", "convert_docx",
             "Converts cleaned text files into individual DOCX files in `DocxOutputPath`."),
            ("Merge Cleaned Files", "merge_cleaned",
             "Merges cleaned files into larger documents based on `MergeSettings`."),
            ("Find Missing Markers", "find_missing_markers",
             "Scans `OutputPath` to find chapters missing the glossary separator.")
        ]

        row, col = 0, 0
        for name, task_id, tooltip in utilities:
            card = QGroupBox(name)
            card.setProperty("class", "card")
            card_layout = QVBoxLayout(card)

            desc_label = QLabel(tooltip)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #4b5563;")

            btn = QPushButton(f"Run {name}")
            btn.setObjectName("btn_primary")
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda _, t=task_id, n=name: self._run_utility(t, n))

            card_layout.addWidget(desc_label)
            card_layout.addStretch()
            card_layout.addWidget(btn)

            self.buttons[task_id] = btn
            grid_layout.addWidget(card, row, col)

            col += 1
            if col > 2:
                col = 0
                row += 1

        main_layout.addStretch()

    def _run_utility(self, task_id, task_name_display):
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Busy", "Another utility or task is already running.")
            return

        gui_logger.info(f"Initiating utility: {task_name_display}")
        self._set_buttons_enabled(False)

        self.worker_thread = WorkerThread(task_id)
        self.worker_thread.task_finished.connect(
            lambda result, name=task_name_display: self._on_utility_finished(result, name))
        self.worker_thread.start()

    def _on_utility_finished(self, result, task_name_display):
        self._set_buttons_enabled(True)
        if isinstance(result, Exception):
            gui_logger.error(f"Utility '{task_name_display}' failed: {result}")
            QMessageBox.critical(self, "Error", f"Utility '{task_name_display}' encountered an error:\n{result}")
        else:
            gui_logger.info(f"Utility '{task_name_display}' completed: {result}")
            QMessageBox.information(self, "Success", f"Utility '{task_name_display}' completed successfully.")

    def _set_buttons_enabled(self, enabled):
        for btn in self.buttons.values():
            btn.setEnabled(enabled)