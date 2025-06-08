# utils.py
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

def apply_shadow(widget):
    """Applies a standard card shadow effect to a widget."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(15)
    shadow.setColor(QColor(0, 0, 0, 40)) # Color with transparency
    shadow.setOffset(2, 2)
    widget.setGraphicsEffect(shadow)
    return shadow # Return in case it needs to be managed