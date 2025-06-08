# main_app.py
import sys
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow
from gui_logger import gui_logger

def main():
    app = QApplication(sys.argv)

    # Load the stylesheet
    try:
        with open("style.qss", "r") as f:
            app.setStyleSheet(f.read())
        gui_logger.info("Stylesheet 'style.qss' loaded successfully.")
    except FileNotFoundError:
        gui_logger.warning("Stylesheet 'style.qss' not found. Using default styles.")

    main_win = MainWindow()
    main_win.show()
    gui_logger.info("Application started successfully.")
    sys.exit(app.exec())

if __name__ == '__main__':
    main()