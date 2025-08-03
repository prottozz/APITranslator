# worker_thread.py
import asyncio
import traceback
import uuid
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

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


class TaskReporter:
    """
    Класс-посредник, который передает вызовы в сигналы WorkerThread.
    Передается в бизнес-логику для обратной связи.
    """

    def __init__(self, worker_thread):
        self.worker = worker_thread

    def start(self, task_id, description):
        # Отправляет сигнал через воркер
        self.worker.task_started.emit(task_id, description, datetime.now())

    def success(self, task_id):
        self.worker.task_succeeded.emit(task_id)

    def failure(self, task_id, error_message):
        self.worker.task_failed.emit(task_id, error_message)

    def retry(self, task_id, retry_message):
        self.worker.task_retrying.emit(task_id, retry_message)


class WorkerThread(QThread):
    # --- ИЗМЕНЕНО: Новые, более детальные сигналы ---
    task_started = pyqtSignal(str, str, object)
    task_retrying = pyqtSignal(str, str)
    task_succeeded = pyqtSignal(str)
    task_failed = pyqtSignal(str, str)
    all_tasks_finished = pyqtSignal(object)  # Заменяет старый task_finished

    def __init__(self, task_name, *args, **kwargs):
        super().__init__()
        self.task_name = task_name
        self.args = args
        self.kwargs = kwargs
        self.config = get_config()

    def run(self):
        if not PROJECT_AVAILABLE:
            self.all_tasks_finished.emit(ImportError("Project.py module not found."))
            return

        # Создаем репортер, который будет использовать наши сигналы
        reporter = TaskReporter(self)

        try:
            gui_logger.info(f"Starting task group: {self.task_name}...")
            result_message = ""

            # --- Задачи, требующие детальной обратной связи изнутри ---
            if self.task_name in ["translate_async", "translate_sequential", "extract_glossary"]:
                self.config.data = self.config._load_config()

                # Передаем reporter в основную функцию
                if self.task_name == "translate_async":
                    asyncio.run(project_main_async(self.config, reporter=reporter))
                    result_message = "Async translation process finished."
                elif self.task_name == "translate_sequential":
                    asyncio.run(project_main_sequential(self.config, reporter=reporter))
                    result_message = "Sequential translation process finished."
                elif self.task_name == "extract_glossary":
                    asyncio.run(extract_glossary_and_clean_files(self.config, reporter=reporter))
                    result_message = "Glossary extraction process finished."

            # --- Простые, "одноразовые" задачи, для которых мы генерируем отчет сами ---
            else:
                task_id = str(uuid.uuid4())
                task_descriptions = {
                    "sort_volumes": "Sorting files into volumes",
                    "convert_html": "Converting files to HTML",
                    "convert_docx": "Converting files to DOCX",
                    "find_missing_markers": "Finding chapters without glossary marker",
                    "merge_cleaned": "Merging cleaned files"
                }
                description = task_descriptions.get(self.task_name, f"Running utility: {self.task_name}")

                # Вручную вызываем сигналы до и после
                reporter.start(task_id, description)

                if self.task_name == "sort_volumes":
                    sort_files_into_volumes(self.config)
                    result_message = "Volume sorting completed."
                elif self.task_name == "convert_html":
                    asyncio.run(convert_cleaned_to_html(self.config))
                    result_message = "HTML conversion completed."
                elif self.task_name == "convert_docx":
                    asyncio.run(convert_cleaned_to_docx(self.config))
                    result_message = "DOCX conversion completed."
                elif self.task_name == "find_missing_markers":
                    asyncio.run(find_chapters_without_glossary_marker(self.config))
                    result_message = "Missing glossary marker check completed."
                elif self.task_name == "merge_cleaned":
                    asyncio.run(merge_cleaned_files(self.config))
                    result_message = "Merging cleaned files completed."
                else:
                    raise ValueError(f"Unknown task: {self.task_name}")

                reporter.success(task_id)  # Сообщаем об успехе простой задачи

            gui_logger.info(f"Task group '{self.task_name}' finished successfully.")
            self.all_tasks_finished.emit(result_message)

        except Exception as e:
            detailed_error = f"Error in task group '{self.task_name}': {e}\n{traceback.format_exc()}"
            gui_logger.error(detailed_error)
            # Отправляем исключение в главный поток
            self.all_tasks_finished.emit(e)