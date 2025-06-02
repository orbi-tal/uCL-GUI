from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

def create_shadow(
    blur: int = 12,
    color: QColor = QColor(0, 0, 0, 10),
    offset_x: int = 0,
    offset_y: int = 2
) -> QGraphicsDropShadowEffect:
    """
    Create a QGraphicsDropShadowEffect with consistent styling.

    Args:
        blur (int): Blur radius for the shadow.
        color (QColor): Shadow color (with alpha for transparency).
        offset_x (int): Horizontal offset.
        offset_y (int): Vertical offset.

    Returns:
        QGraphicsDropShadowEffect: Configured drop shadow effect.
    """
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setColor(color)
    shadow.setOffset(offset_x, offset_y)
    return shadow
