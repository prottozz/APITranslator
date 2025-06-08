# worker_thread.py
from PyQt6.QtCore import QThread, pyqtSignal
import asyncio
import traceback

# Assuming Project.py is accessible
try:
    from Project import main_async as project_main_async
    from Project import main_sequential as project_main_sequential
    from Project import sort_files_into_volumes, extract_glossary_and_clean_files
    from Project import convert_cleaned_to_html, convert_cleaned_to_docx
    from Project import find_chapters_without_glossary_marker, merge_cleaned_files
    PROJECT_AVAILABLE = True
except ImportError:
    PROJECT_AVAILABLE = False
    print("Project.py not found, some worker functionalities will be disabled.")

from project_config import get_config
from gui_logger import gui_logger


class WorkerThread(QThread):
    task_finished = pyqtSignal(object)  # Emits result or exception
    task_progress = pyqtSignal(str)     # Emits progress messages

    def __init__(self, task_name, *args, **kwargs):
        super().__init__()
        self.task_name = task_name
        self.args = args
        self.kwargs = kwargs
        self.config = get_config() # Get the shared config instance

    def run(self):
        if not PROJECT_AVAILABLE:
            self.task_finished.emit(ImportError("Project.py module not found."))
            return

        try:
            gui_logger.info(f"Starting task: {self.task_name}...")
            result = None
            if self.task_name == "translate_async":
                # Ensure config is up-to-date before running
                self.config.data = self.config._load_config() # Reload fresh config
                asyncio.run(project_main_async(self.config))
                result = "Async translation completed."
            elif self.task_name == "translate_sequential":
                self.config.data = self.config._load_config()
                asyncio.run(project_main_sequential(self.config))
                result = "Sequential translation completed."
            elif self.task_name == "sort_volumes":
                sort_files_into_volumes(self.config)
                result = "Volume sorting completed."
            elif self.task_name == "extract_glossary":
                asyncio.run(extract_glossary_and_clean_files(self.config))
                result = "Glossary extraction and cleaning completed."
            elif self.task_name == "convert_html":
                asyncio.run(convert_cleaned_to_html(self.config))
                result = "HTML conversion completed."
            elif self.task_name == "convert_docx":
                asyncio.run(convert_cleaned_to_docx(self.config))
                result = "DOCX conversion completed."
            elif self.task_name == "find_missing_markers":
                asyncio.run(find_chapters_without_glossary_marker(self.config))
                result = "Missing glossary marker check completed."
            elif self.task_name == "merge_cleaned":
                asyncio.run(merge_cleaned_files(self.config))
                result = "Merging cleaned files completed."
            # Add more tasks as needed
            else:
                result = ValueError(f"Unknown task: {self.task_name}")

            gui_logger.info(f"Task '{self.task_name}' finished successfully.")
            self.task_finished.emit(result)
        except Exception as e:
            detailed_error = f"Error in task '{self.task_name}': {e}\n{traceback.format_exc()}"
            gui_logger.error(detailed_error)
            self.task_finished.emit(e)