# views/utility_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QGroupBox, QMessageBox
from PyQt6.QtCore import Qt
from worker_thread import WorkerThread
from gui_logger import gui_logger


class UtilityView(QWidget):
    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        utilities = [
            ("Sort into Volumes", "sort_volumes", "Sorts translated files from OutputPath into VolumeSortPath."),
            ("Extract Glossary & Clean Files", "extract_glossary",
             "Extracts glossaries, cleans files, saves to CleanedOutputPath & GlossaryPath."),
            ("Convert to HTML", "convert_html", "Converts cleaned text files to HTML in HtmlOutputPath."),
            ("Convert to DOCX", "convert_docx", "Converts cleaned text files to DOCX in DocxOutputPath."),
            ("Find Missing Glossary Markers", "find_missing_markers",
             "Scans OutputPath for chapters missing the glossary separator."),
            ("Merge Cleaned Files", "merge_cleaned", "Merges cleaned files (txt, html, docx) based on MergeSettings.")
        ]

        for name, task_id, tooltip in utilities:
            group = QGroupBox(name)
            group_layout = QVBoxLayout()

            btn = QPushButton(f"Run {name}")
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda _, t=task_id, n=name: self._run_utility(t, n))
            group_layout.addWidget(btn)

            group.setLayout(group_layout)
            main_layout.addWidget(group)

        main_layout.addStretch()  # Push utilities to the top

    def _run_utility(self, task_id, task_name_display):
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Busy", "Another utility or task is already running.")
            return

        gui_logger.info(f"Initiating utility: {task_name_display}")
        # You might want to disable all utility buttons while one is running

        self.worker_thread = WorkerThread(task_id)
        self.worker_thread.task_finished.connect(
            lambda result, name=task_name_display: self._on_utility_finished(result, name))
        self.worker_thread.start()

    def _on_utility_finished(self, result, task_name_display):
        # Re-enable buttons
        if isinstance(result, Exception):
            gui_logger.error(f"Utility '{task_name_display}' failed: {result}")
            QMessageBox.critical(self, "Error", f"Utility '{task_name_display}' encountered an error: {result}")
        else:
            gui_logger.info(f"Utility '{task_name_display}' completed: {result}")
            QMessageBox.information(self, "Success", f"Utility '{task_name_display}' completed successfully.")