# ui_helper.py
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer

def create_svg_icon(icon_path: str, color: str | QColor) -> QIcon:
    """
    Создает иконку из SVG-файла, раскрашивая ее в указанный цвет.

    :param icon_path: Путь к SVG-файлу.
    :param color: Цвет в виде строки (e.g., "#ff0000") или объекта QColor.
    :return: QIcon с раскрашенной иконкой.
    """
    # 1. Читаем SVG-файл
    with open(icon_path, 'r', encoding='utf-8') as f:
        svg_data = f.read()

    # 2. Заменяем цвет-заполнитель на новый
    color_str = color if isinstance(color, str) else color.name()
    # Ищем 'currentColor' или стандартный черный цвет для замены
    modified_svg_data = svg_data.replace('currentColor', color_str)
    modified_svg_data = modified_svg_data.replace('#000000', color_str)
    modified_svg_data = modified_svg_data.replace('black', color_str)

    # 3. Отрисовываем измененный SVG
    renderer = QSvgRenderer(modified_svg_data.encode('utf-8'))

    # Определяем размер для отрисовки (можно сделать параметром)
    pixmap_size = QSize(256, 256)  # Берем с запасом для качества
    pixmap = QPixmap(pixmap_size)
    pixmap.fill(Qt.GlobalColor.transparent)  # Прозрачный фон

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)