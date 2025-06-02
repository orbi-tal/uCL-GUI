from PyQt6.QtWidgets import QPushButton, QApplication, QSizePolicy
from PyQt6.QtCore import QEvent, QObject
from PyQt6.QtGui import QPalette
from typing import Optional, cast
from src.ui.style.style import StyleSystem


class AnimatedButton(QPushButton):
    """
    QPushButton subclass with hover and click color effects.
    Includes shadow management and theme-aware styling.
    """
    def __init__(self, *args, fill_width=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self.installEventFilter(self)
        self._hovered: bool = False

        # Set size policy to expand if needed
        if fill_width:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._apply_style()

    def _apply_style(self) -> None:
        """Apply QSS colors from StyleSystem based on app palette with improved dark mode detection"""
        app = cast(QApplication, QApplication.instance())
        theme = "light"  # Default theme
        
        if app:
            # Try multiple methods to detect dark mode
            palette = app.palette()
            bg_color = palette.color(QPalette.ColorRole.Window)
            text_color = palette.color(QPalette.ColorRole.WindowText)
            
            # Method 1: Compare text and background brightness
            bg_luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()) / 255
            text_luminance = (0.299 * text_color.red() + 0.587 * text_color.green() + 0.114 * text_color.blue()) / 255
            
            # Method 2: Check if background is dark
            is_bg_dark = bg_luminance < 0.5
            
            # Method 3: Check contrast between text and background
            has_light_on_dark_contrast = text_luminance > bg_luminance
            
            # Combine methods for more accurate detection
            if is_bg_dark or (has_light_on_dark_contrast and bg_luminance < 0.7):
                theme = "dark"

        colors = StyleSystem.get_colors(theme)

        # Use change profile colors if property is set, else default button colors
        change_profile = self.property("changeProfile")
        if change_profile in (True, "true", "True"):
            # Use specific colors for Change Profile button
            if theme == "light":
                bg = "#E6E4D7"  # Specific light mode color
            else:
                bg = "#363636"  # Specific dark mode color
            fg = colors['change_profile_text']
        else:
            bg = colors['button']
            fg = colors['button_text']
        
        # Use the centralized styling from StyleSystem
        self.setStyleSheet(StyleSystem.get_animated_button_style(bg, fg, theme))
        
    def _adjust_color_brightness(self, color: str, factor: float) -> str:
        """Adjust color brightness by multiplying RGB values by factor"""
        if color.startswith('#'):
            # Convert hex to RGB
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            
            # For extreme brightness increases (factor > 1.3), 
            # blend with white to create better highlights
            if factor > 1.3:
                white_blend = (factor - 1.0) * 0.7  # How much white to blend in
                r = int(r * (1 - white_blend) + 255 * white_blend)
                g = int(g * (1 - white_blend) + 255 * white_blend)
                b = int(b * (1 - white_blend) + 255 * white_blend)
            else:
                # HSL-like adjustment (preserve saturation better than direct RGB multiplication)
                # Find the max value to preserve color character
                max_val = max(r, g, b)
            
                # Calculate the relative ratios of each color component
                r_ratio = r / max_val if max_val > 0 else 0
                g_ratio = g / max_val if max_val > 0 else 0
                b_ratio = b / max_val if max_val > 0 else 0
                
                # Apply factor to the max value
                new_max = min(255, int(max_val * factor))
                
                # Recalculate RGB values preserving their ratios
                r = min(255, int(new_max * r_ratio))
                g = min(255, int(new_max * g_ratio))
                b = min(255, int(new_max * b_ratio))
            
            # Convert back to hex
            return f'#{r:02x}{g:02x}{b:02x}'
        return color

    # This method overrides QObject.eventFilter
    def eventFilter(self, a0: Optional[QObject], a1: Optional[QEvent]) -> bool:
        if a0 is self and a1 is not None:
            if a1.type() == QEvent.Type.Enter and not self._hovered:
                self._hovered = True
                self.update()
            elif a1.type() == QEvent.Type.Leave and self._hovered:
                self._hovered = False
                self.update()
        return super().eventFilter(a0, a1)


# Alias for backwards compatibility
DialogAnimatedButton = AnimatedButton
