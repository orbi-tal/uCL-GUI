# Init file to make style a proper package
from .style import StyleSystem
from .icons import IconProvider, install_icons

__all__ = ['StyleSystem', 'IconProvider', 'install_icons']