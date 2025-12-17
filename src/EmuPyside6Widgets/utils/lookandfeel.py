"""
Look and Feel Utilities for PySide6 Applications

This module provides utilities for:
- Dark/light mode detection and forcing
- Qt style listing and switching
- System color scheme access
- Icon theme management and icon resolution

Usage:
    from EmuPyside6Widgets.utils.lookandfeel import LookAndFeel, IconTheme
    
    # Check dark mode
    if LookAndFeel.is_dark_mode():
        print("Dark mode detected")
    
    # Get system colors
    colors = LookAndFeel.get_system_colors()
    print(f"Window background: {colors['window']}")
    
    # Get an icon
    icon = IconTheme.get_icon("document-save")
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from enum import Enum

from PySide6.QtWidgets import QApplication, QStyleFactory, QStyle, QWidget
from PySide6.QtGui import QPalette, QColor, QIcon, QPixmap
from PySide6.QtCore import Qt, QDir, QFile, QSize


class ColorScheme(Enum):
    """Color scheme modes"""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class LookAndFeel:
    """
    Utilities for managing application look and feel.
    
    Provides methods for:
    - Detecting and forcing dark/light mode
    - Listing and switching Qt styles
    - Accessing system color palette
    """
    
    _forced_scheme: Optional[ColorScheme] = None
    _original_palette: Optional[QPalette] = None
    
    # ==================== Dark/Light Mode ====================
    
    @classmethod
    def is_dark_mode(cls) -> bool:
        """
        Detect if the system/application is in dark mode.
        
        Returns:
            True if dark mode is active, False otherwise
        """
        if cls._forced_scheme == ColorScheme.DARK:
            return True
        elif cls._forced_scheme == ColorScheme.LIGHT:
            return False
        
        # Check system palette
        app = QApplication.instance()
        if app:
            palette = app.palette()
            # Compare window background luminance
            bg_color = palette.color(QPalette.Window)
            # Calculate relative luminance
            luminance = (0.299 * bg_color.red() + 
                        0.587 * bg_color.green() + 
                        0.114 * bg_color.blue()) / 255
            return luminance < 0.5
        return False
    
    @classmethod
    def is_light_mode(cls) -> bool:
        """
        Detect if the system/application is in light mode.
        
        Returns:
            True if light mode is active, False otherwise
        """
        return not cls.is_dark_mode()
    
    @classmethod
    def get_color_scheme(cls) -> ColorScheme:
        """
        Get the current color scheme.
        
        Returns:
            ColorScheme enum value
        """
        if cls._forced_scheme and cls._forced_scheme != ColorScheme.SYSTEM:
            return cls._forced_scheme
        return ColorScheme.DARK if cls.is_dark_mode() else ColorScheme.LIGHT
    
    @classmethod
    def force_dark_mode(cls):
        """
        Force the application into dark mode.
        
        Creates a dark palette and applies it to the application.
        """
        app = QApplication.instance()
        if not app:
            return
        
        # Store original palette if not already stored
        if cls._original_palette is None:
            cls._original_palette = app.palette()
        
        cls._forced_scheme = ColorScheme.DARK
        
        # Create dark palette
        dark_palette = QPalette()
        
        # Window colors
        dark_palette.setColor(QPalette.Window, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
        
        # Base colors (for text inputs, lists, etc.)
        dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(50, 50, 50))
        
        # Text colors
        dark_palette.setColor(QPalette.Text, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
        
        # Button colors
        dark_palette.setColor(QPalette.Button, QColor(55, 55, 55))
        dark_palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
        
        # Highlight colors
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # Link colors
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.LinkVisited, QColor(165, 122, 255))
        
        # Disabled colors
        dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
        dark_palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
        
        # Tooltip colors
        dark_palette.setColor(QPalette.ToolTipBase, QColor(60, 60, 60))
        dark_palette.setColor(QPalette.ToolTipText, QColor(220, 220, 220))
        
        # Placeholder text
        dark_palette.setColor(QPalette.PlaceholderText, QColor(127, 127, 127))
        
        app.setPalette(dark_palette)
        
        # Apply stylesheet and refresh
        cls.apply_palette_stylesheet()
        cls.refresh_widgets()
    
    @classmethod
    def force_light_mode(cls):
        """
        Force the application into light mode.
        
        Creates a light palette and applies it to the application.
        """
        app = QApplication.instance()
        if not app:
            return
        
        # Store original palette if not already stored
        if cls._original_palette is None:
            cls._original_palette = app.palette()
        
        cls._forced_scheme = ColorScheme.LIGHT
        
        # Create light palette
        light_palette = QPalette()
        
        # Window colors
        light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
        light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        
        # Base colors
        light_palette.setColor(QPalette.Base, QColor(255, 255, 255))
        light_palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        
        # Text colors
        light_palette.setColor(QPalette.Text, QColor(0, 0, 0))
        light_palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
        
        # Button colors
        light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
        light_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        
        # Highlight colors
        light_palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        light_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # Link colors
        light_palette.setColor(QPalette.Link, QColor(0, 102, 204))
        light_palette.setColor(QPalette.LinkVisited, QColor(128, 0, 128))
        
        # Disabled colors
        light_palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
        light_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
        light_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
        light_palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(200, 200, 200))
        light_palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
        
        # Tooltip colors
        light_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
        light_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        
        # Placeholder text
        light_palette.setColor(QPalette.PlaceholderText, QColor(127, 127, 127))
        
        app.setPalette(light_palette)
        
        # Apply stylesheet and refresh
        cls.apply_palette_stylesheet()
        cls.refresh_widgets()
    
    @classmethod
    def reset_color_scheme(cls):
        """
        Reset to system default color scheme.
        
        Restores the original palette if one was stored.
        """
        cls._forced_scheme = ColorScheme.SYSTEM
        
        app = QApplication.instance()
        if app and cls._original_palette:
            app.setPalette(cls._original_palette)
            # Clear stylesheet
            app.setStyleSheet("")
            cls.refresh_widgets()
    
    @classmethod
    def refresh_widgets(cls, widget=None):
        """
        Refresh widget styles after palette change.
        
        This forces widgets to update their appearance based on the new palette.
        Call this after applying a color scheme to update custom-styled widgets.
        
        Args:
            widget: Specific widget to refresh, or None for all top-level widgets
        """
        app = QApplication.instance()
        if not app:
            return
        
        if widget:
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()
            # Refresh all children
            for child in widget.findChildren(QWidget):
                child.style().unpolish(child)
                child.style().polish(child)
                child.update()
        else:
            # Refresh all top-level widgets
            for window in app.topLevelWidgets():
                cls.refresh_widgets(window)
    
    @classmethod
    def get_palette_stylesheet(cls, minimal: bool = True) -> str:
        """
        Generate a CSS stylesheet with current palette colors.
        
        Args:
            minimal: If True (default), only sets text colors to preserve native 
                     Qt/KDE widget styling. If False, includes background colors too.
        
        Returns a stylesheet string that can be applied to widgets.
        This is designed to work WITH the native Qt style, not override it.
        
        Returns:
            CSS stylesheet string with color definitions
        """
        colors = cls.get_system_colors()
        
        if minimal:
            # Minimal stylesheet - only set text colors on widgets that need it
            # This preserves native Qt/KDE button styles, icons, etc.
            return f"""
                QLabel {{
                    color: {colors.get('window_text', '#000000')};
                }}
                QGroupBox {{
                    color: {colors.get('window_text', '#000000')};
                }}
                QGroupBox::title {{
                    color: {colors.get('window_text', '#000000')};
                }}
                QCheckBox {{
                    color: {colors.get('window_text', '#000000')};
                }}
                QRadioButton {{
                    color: {colors.get('window_text', '#000000')};
                }}
            """
        else:
            # Full stylesheet - sets all colors (may override native styling)
            return f"""
                QWidget {{
                    background-color: {colors.get('window', '#ffffff')};
                    color: {colors.get('window_text', '#000000')};
                }}
                QLabel {{
                    background-color: transparent;
                    color: {colors.get('window_text', '#000000')};
                }}
                QGroupBox {{
                    color: {colors.get('window_text', '#000000')};
                }}
                QGroupBox::title {{
                    color: {colors.get('window_text', '#000000')};
                }}
                QLineEdit, QTextEdit, QPlainTextEdit {{
                    background-color: {colors.get('base', '#ffffff')};
                    color: {colors.get('text', '#000000')};
                }}
                QComboBox QAbstractItemView {{
                    background-color: {colors.get('base', '#ffffff')};
                    color: {colors.get('text', '#000000')};
                    selection-background-color: {colors.get('highlight', '#308cc6')};
                    selection-color: {colors.get('highlighted_text', '#ffffff')};
                }}
            """
    
    @classmethod
    def apply_palette_stylesheet(cls, widget=None, minimal: bool = True):
        """
        Apply a palette-based stylesheet to widgets.
        
        This ensures widgets follow the current palette colors even with
        custom styling. Call this after changing the color scheme.
        
        Args:
            widget: Specific widget, or None to apply to the application
            minimal: If True (default), only sets text colors to preserve native
                     Qt/KDE widget styling (buttons, dropdowns, etc.)
        """
        stylesheet = cls.get_palette_stylesheet(minimal=minimal)
        
        app = QApplication.instance()
        if not app:
            return
        
        if widget:
            widget.setStyleSheet(stylesheet)
        else:
            app.setStyleSheet(stylesheet)
    
    @classmethod  
    def get_color_css_vars(cls) -> Dict[str, str]:
        """
        Get current palette colors formatted for use in stylesheets.
        
        Returns:
            Dictionary with color names and hex values for use in CSS
        
        Example:
            colors = LookAndFeel.get_color_css_vars()
            widget.setStyleSheet(f'''
                background: {colors['window']};
                color: {colors['text']};
            ''')
        """
        return cls.get_system_colors()
    
    # ==================== Qt Styles ====================
    
    @classmethod
    def list_styles(cls) -> List[str]:
        """
        List all available Qt styles.
        
        Returns:
            List of style names
        """
        return QStyleFactory.keys()
    
    @classmethod
    def get_current_style(cls) -> Optional[str]:
        """
        Get the name of the current Qt style.
        
        Returns:
            Style name or None if no application exists
        """
        app = QApplication.instance()
        if app and app.style():
            return app.style().objectName()
        return None
    
    @classmethod
    def set_style(cls, style_name: str) -> bool:
        """
        Set the Qt application style.
        
        Args:
            style_name: Name of the style (use list_styles() to see available)
        
        Returns:
            True if successful, False otherwise
        """
        app = QApplication.instance()
        if not app:
            return False
        
        style = QStyleFactory.create(style_name)
        if style:
            app.setStyle(style)
            return True
        return False
    
    # ==================== System Colors ====================
    
    @classmethod
    def get_system_colors(cls) -> Dict[str, str]:
        """
        Get current system color palette as a dictionary.
        
        Returns:
            Dictionary with color role names and hex color values
        """
        app = QApplication.instance()
        if not app:
            return {}
        
        palette = app.palette()
        
        colors = {
            # Window colors
            "window": palette.color(QPalette.Window).name(),
            "window_text": palette.color(QPalette.WindowText).name(),
            
            # Base colors (inputs, lists)
            "base": palette.color(QPalette.Base).name(),
            "alternate_base": palette.color(QPalette.AlternateBase).name(),
            
            # Text colors
            "text": palette.color(QPalette.Text).name(),
            "bright_text": palette.color(QPalette.BrightText).name(),
            "placeholder_text": palette.color(QPalette.PlaceholderText).name(),
            
            # Button colors
            "button": palette.color(QPalette.Button).name(),
            "button_text": palette.color(QPalette.ButtonText).name(),
            
            # Highlight/Selection colors
            "highlight": palette.color(QPalette.Highlight).name(),
            "highlighted_text": palette.color(QPalette.HighlightedText).name(),
            
            # Link colors
            "link": palette.color(QPalette.Link).name(),
            "link_visited": palette.color(QPalette.LinkVisited).name(),
            
            # Tooltip colors
            "tooltip_base": palette.color(QPalette.ToolTipBase).name(),
            "tooltip_text": palette.color(QPalette.ToolTipText).name(),
            
            # Other
            "light": palette.color(QPalette.Light).name(),
            "midlight": palette.color(QPalette.Midlight).name(),
            "mid": palette.color(QPalette.Mid).name(),
            "dark": palette.color(QPalette.Dark).name(),
            "shadow": palette.color(QPalette.Shadow).name(),
        }
        
        return colors
    
    @classmethod
    def get_system_colors_extended(cls) -> Dict[str, Dict[str, str]]:
        """
        Get extended system colors including disabled and inactive states.
        
        Returns:
            Dictionary with color groups containing role names and hex values
        """
        app = QApplication.instance()
        if not app:
            return {}
        
        palette = app.palette()
        
        def get_colors_for_group(group: QPalette.ColorGroup) -> Dict[str, str]:
            return {
                "window": palette.color(group, QPalette.Window).name(),
                "window_text": palette.color(group, QPalette.WindowText).name(),
                "base": palette.color(group, QPalette.Base).name(),
                "alternate_base": palette.color(group, QPalette.AlternateBase).name(),
                "text": palette.color(group, QPalette.Text).name(),
                "bright_text": palette.color(group, QPalette.BrightText).name(),
                "button": palette.color(group, QPalette.Button).name(),
                "button_text": palette.color(group, QPalette.ButtonText).name(),
                "highlight": palette.color(group, QPalette.Highlight).name(),
                "highlighted_text": palette.color(group, QPalette.HighlightedText).name(),
                "link": palette.color(group, QPalette.Link).name(),
                "link_visited": palette.color(group, QPalette.LinkVisited).name(),
            }
        
        return {
            "active": get_colors_for_group(QPalette.Active),
            "inactive": get_colors_for_group(QPalette.Inactive),
            "disabled": get_colors_for_group(QPalette.Disabled),
        }
    
    @classmethod
    def get_semantic_colors(cls) -> Dict[str, str]:
        """
        Get semantic color suggestions based on the current theme.
        
        Returns colors commonly used for success, warning, error, info states.
        Each semantic color includes:
        - Base color (e.g., 'success')
        - Light variant ('success_light')
        - Dark variant ('success_dark')
        - Text color for that background ('success_text')
        
        The _text variants are automatically calculated to ensure readable
        contrast against the base color.
        
        Returns:
            Dictionary with semantic color names and hex values
        
        Example:
            colors = LookAndFeel.get_semantic_colors()
            button.setStyleSheet(f'''
                background: {colors['success']};
                color: {colors['success_text']};
            ''')
        """
        is_dark = cls.is_dark_mode()
        
        if is_dark:
            base_colors = {
                "success": "#27ae60",          # Green
                "success_light": "#2ecc71",
                "success_dark": "#1e8449",
                
                "warning": "#f39c12",          # Orange
                "warning_light": "#f1c40f",
                "warning_dark": "#d68910",
                
                "error": "#e74c3c",            # Red
                "error_light": "#ec7063",
                "error_dark": "#c0392b",
                
                "info": "#3498db",             # Blue
                "info_light": "#5dade2",
                "info_dark": "#2980b9",
                
                "critical": "#8e44ad",         # Purple
                "critical_light": "#a569bd",
                "critical_dark": "#6c3483",
                
                "neutral": "#95a5a6",          # Gray
                "neutral_light": "#bdc3c7",
                "neutral_dark": "#7f8c8d",
            }
        else:
            base_colors = {
                "success": "#28a745",
                "success_light": "#48c774",
                "success_dark": "#1e7e34",
                
                "warning": "#ffc107",
                "warning_light": "#ffdb4d",
                "warning_dark": "#d39e00",
                
                "error": "#dc3545",
                "error_light": "#f17a85",
                "error_dark": "#bd2130",
                
                "info": "#17a2b8",
                "info_light": "#4fc3dc",
                "info_dark": "#117a8b",
                
                "critical": "#6f42c1",
                "critical_light": "#9775d9",
                "critical_dark": "#5a32a3",
                
                "neutral": "#6c757d",
                "neutral_light": "#adb5bd",
                "neutral_dark": "#495057",
            }
        
        # Add text color variants for each semantic color
        colors_with_text = dict(base_colors)
        
        # Define the semantic color types
        semantic_types = ["success", "warning", "error", "info", "critical", "neutral"]
        
        for sem_type in semantic_types:
            # Text color for base
            colors_with_text[f"{sem_type}_text"] = cls.get_contrasting_color(base_colors[sem_type])
            # Text color for light variant
            colors_with_text[f"{sem_type}_light_text"] = cls.get_contrasting_color(base_colors[f"{sem_type}_light"])
            # Text color for dark variant
            colors_with_text[f"{sem_type}_dark_text"] = cls.get_contrasting_color(base_colors[f"{sem_type}_dark"])
        
        return colors_with_text
    
    @classmethod
    def get_color(cls, role: str) -> Optional[QColor]:
        """
        Get a specific color from the current palette.
        
        Args:
            role: Color role name (e.g., 'window', 'text', 'highlight')
        
        Returns:
            QColor object or None if role not found
        """
        colors = cls.get_system_colors()
        if role in colors:
            return QColor(colors[role])
        return None
    
    # ==================== Contrast Utilities ====================
    
    @staticmethod
    def get_luminance(color) -> float:
        """
        Calculate the relative luminance of a color.
        
        Uses the WCAG formula for perceived brightness.
        
        Args:
            color: QColor, hex string (e.g., "#ff0000"), or RGB tuple
        
        Returns:
            Luminance value between 0 (black) and 1 (white)
        """
        # Convert to QColor if needed
        if isinstance(color, str):
            color = QColor(color)
        elif isinstance(color, tuple):
            color = QColor(*color)
        
        # Get RGB values normalized to 0-1
        r = color.redF()
        g = color.greenF()
        b = color.blueF()
        
        # Apply gamma correction (sRGB to linear)
        def linearize(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        
        r_lin = linearize(r)
        g_lin = linearize(g)
        b_lin = linearize(b)
        
        # Calculate luminance using WCAG coefficients
        return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
    
    @staticmethod
    def get_contrast_ratio(color1, color2) -> float:
        """
        Calculate the contrast ratio between two colors.
        
        WCAG guidelines:
        - 4.5:1 minimum for normal text
        - 3:1 minimum for large text
        - 7:1 enhanced contrast
        
        Args:
            color1: First color (QColor, hex string, or RGB tuple)
            color2: Second color (QColor, hex string, or RGB tuple)
        
        Returns:
            Contrast ratio (1 to 21)
        """
        lum1 = LookAndFeel.get_luminance(color1)
        lum2 = LookAndFeel.get_luminance(color2)
        
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    @staticmethod
    def get_contrasting_text_color(bg_color, light_text: str = "#ffffff", dark_text: str = "#000000") -> str:
        """
        Get a contrasting text color for the given background.
        
        Uses WCAG luminance calculation to determine whether
        light or dark text provides better contrast.
        
        Args:
            bg_color: Background color (QColor, hex string, or RGB tuple)
            light_text: Color to return for dark backgrounds (default white)
            dark_text: Color to return for light backgrounds (default black)
        
        Returns:
            Hex color string for the text
        """
        luminance = LookAndFeel.get_luminance(bg_color)
        
        # Threshold based on WCAG guidelines
        # 0.179 is roughly where equal contrast would be achieved
        return light_text if luminance < 0.179 else dark_text
    
    @staticmethod
    def get_contrasting_color(bg_color, prefer_tinted: bool = False) -> str:
        """
        Get a contrasting text color for any background color.
        
        This is the main utility for ensuring readable text on any background.
        
        Args:
            bg_color: Background color (QColor, hex string, or RGB tuple)
            prefer_tinted: If True, returns a slightly tinted color instead of pure black/white
        
        Returns:
            Hex color string that will be readable on the background
        
        Example:
            >>> LookAndFeel.get_contrasting_color("#28a745")  # Green
            '#ffffff'  # White text on green
            >>> LookAndFeel.get_contrasting_color("#ffc107")  # Yellow
            '#000000'  # Black text on yellow
        """
        if isinstance(bg_color, str):
            bg_qcolor = QColor(bg_color)
        elif isinstance(bg_color, tuple):
            bg_qcolor = QColor(*bg_color)
        else:
            bg_qcolor = bg_color
        
        luminance = LookAndFeel.get_luminance(bg_qcolor)
        
        if prefer_tinted:
            # Create a tinted version that's harmonious with the background
            h, s, l, a = bg_qcolor.getHslF()
            
            if luminance < 0.179:
                # Dark background - use light tinted text
                # Reduce saturation and increase lightness
                new_s = max(0, s * 0.3)
                new_l = min(1, 0.9 + (1 - l) * 0.1)
            else:
                # Light background - use dark tinted text
                # Reduce saturation and decrease lightness
                new_s = max(0, s * 0.4)
                new_l = max(0, 0.1 + l * 0.1)
            
            result = QColor()
            result.setHslF(h, new_s, new_l, a)
            return result.name()
        else:
            return "#ffffff" if luminance < 0.179 else "#000000"
    
    @classmethod
    def ensure_contrast(cls, fg_color, bg_color, min_ratio: float = 4.5) -> str:
        """
        Ensure a foreground color has sufficient contrast against a background.
        
        If the contrast is insufficient, returns an adjusted color that meets
        the minimum contrast ratio.
        
        Args:
            fg_color: Foreground/text color
            bg_color: Background color
            min_ratio: Minimum contrast ratio (4.5 for WCAG AA, 7 for AAA)
        
        Returns:
            Hex color string with sufficient contrast
        """
        ratio = cls.get_contrast_ratio(fg_color, bg_color)
        
        if ratio >= min_ratio:
            # Already sufficient contrast
            if isinstance(fg_color, str):
                return fg_color
            elif isinstance(fg_color, QColor):
                return fg_color.name()
            else:
                return QColor(*fg_color).name()
        
        # Insufficient contrast - return appropriate black or white
        return cls.get_contrasting_text_color(bg_color)


class KDEColorScheme:
    """
    Utilities for managing KDE/Plasma color schemes.
    
    KDE stores color schemes in ~/.local/share/color-schemes/ as INI-like files.
    This class provides methods to:
    - List installed color schemes
    - Parse and apply color schemes
    - Detect if a scheme is dark or light
    
    Example:
        # List available schemes
        schemes = KDEColorScheme.list_schemes()
        
        # Apply a scheme
        KDEColorScheme.apply_scheme("Breeze Dark")
        
        # Check if scheme is dark
        if KDEColorScheme.is_scheme_dark("Breeze Dark"):
            print("Dark scheme")
    """
    
    _current_scheme: Optional[str] = None
    _scheme_cache: Dict[str, Dict] = {}
    
    # Standard KDE color scheme directories
    _SCHEME_DIRS = [
        Path.home() / ".local/share/color-schemes",
        Path("/usr/share/color-schemes"),
        Path("/usr/local/share/color-schemes"),
    ]
    
    # Color role mapping from KDE to QPalette
    _KDE_TO_QPALETTE = {
        # Window colors
        ("Colors:Window", "BackgroundNormal"): (QPalette.Window,),
        ("Colors:Window", "ForegroundNormal"): (QPalette.WindowText,),
        
        # View colors (for lists, text inputs)
        ("Colors:View", "BackgroundNormal"): (QPalette.Base,),
        ("Colors:View", "BackgroundAlternate"): (QPalette.AlternateBase,),
        ("Colors:View", "ForegroundNormal"): (QPalette.Text,),
        ("Colors:View", "ForegroundInactive"): (QPalette.PlaceholderText,),
        ("Colors:View", "ForegroundLink"): (QPalette.Link,),
        ("Colors:View", "ForegroundVisited"): (QPalette.LinkVisited,),
        
        # Button colors
        ("Colors:Button", "BackgroundNormal"): (QPalette.Button,),
        ("Colors:Button", "ForegroundNormal"): (QPalette.ButtonText,),
        
        # Selection colors
        ("Colors:Selection", "BackgroundNormal"): (QPalette.Highlight,),
        ("Colors:Selection", "ForegroundNormal"): (QPalette.HighlightedText,),
        
        # Tooltip colors
        ("Colors:Tooltip", "BackgroundNormal"): (QPalette.ToolTipBase,),
        ("Colors:Tooltip", "ForegroundNormal"): (QPalette.ToolTipText,),
    }
    
    @classmethod
    def list_schemes(cls) -> List[str]:
        """
        List all installed KDE color schemes.
        
        Returns:
            List of color scheme names
        """
        schemes = []
        
        for scheme_dir in cls._SCHEME_DIRS:
            if scheme_dir.exists() and scheme_dir.is_dir():
                for item in scheme_dir.iterdir():
                    if item.is_file() and item.suffix == ".colors":
                        # Parse to get the actual name
                        parsed = cls._parse_scheme_file(item)
                        if parsed and "General" in parsed and "Name" in parsed["General"]:
                            schemes.append(parsed["General"]["Name"])
                        else:
                            # Use filename without extension
                            schemes.append(item.stem)
        
        return sorted(set(schemes))
    
    @classmethod
    def get_scheme_path(cls, name: str) -> Optional[Path]:
        """
        Get the file path for a color scheme by name.
        
        Args:
            name: Color scheme name
        
        Returns:
            Path to the scheme file or None if not found
        """
        for scheme_dir in cls._SCHEME_DIRS:
            if scheme_dir.exists():
                for item in scheme_dir.iterdir():
                    if item.is_file() and item.suffix == ".colors":
                        # Check by filename
                        if item.stem.lower() == name.lower():
                            return item
                        # Check by internal name
                        parsed = cls._parse_scheme_file(item)
                        if parsed and "General" in parsed:
                            if parsed["General"].get("Name", "").lower() == name.lower():
                                return item
        return None
    
    @classmethod
    def _parse_scheme_file(cls, path: Path) -> Optional[Dict[str, Dict[str, str]]]:
        """
        Parse a KDE color scheme file.
        
        Args:
            path: Path to the .colors file
        
        Returns:
            Dictionary with sections and their key-value pairs
        """
        if not path.exists():
            return None
        
        # Check cache
        cache_key = str(path)
        if cache_key in cls._scheme_cache:
            return cls._scheme_cache[cache_key]
        
        result = {}
        current_section = None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue
                    
                    # Section header
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                        if current_section not in result:
                            result[current_section] = {}
                    elif '=' in line and current_section:
                        key, _, value = line.partition('=')
                        result[current_section][key.strip()] = value.strip()
            
            cls._scheme_cache[cache_key] = result
            return result
            
        except Exception as e:
            print(f"Error parsing color scheme {path}: {e}")
            return None
    
    @classmethod
    def get_scheme_colors(cls, name: str) -> Optional[Dict[str, Dict[str, str]]]:
        """
        Get the parsed color data for a scheme.
        
        Args:
            name: Color scheme name
        
        Returns:
            Dictionary with color sections and values, or None if not found
        """
        path = cls.get_scheme_path(name)
        if path:
            return cls._parse_scheme_file(path)
        return None
    
    @classmethod
    def _parse_color(cls, color_str: str) -> Optional[QColor]:
        """
        Parse a KDE color string (R,G,B or R,G,B,A) to QColor.
        
        Args:
            color_str: Color string like "255,255,255" or "255,255,255,128"
        
        Returns:
            QColor object or None if invalid
        """
        try:
            parts = [int(p.strip()) for p in color_str.split(',')]
            if len(parts) == 3:
                return QColor(parts[0], parts[1], parts[2])
            elif len(parts) == 4:
                return QColor(parts[0], parts[1], parts[2], parts[3])
        except (ValueError, IndexError):
            pass
        return None
    
    @classmethod
    def is_scheme_dark(cls, name: str) -> bool:
        """
        Determine if a color scheme is dark or light.
        
        Uses the window background color luminance to determine.
        
        Args:
            name: Color scheme name
        
        Returns:
            True if the scheme is dark, False if light
        """
        colors = cls.get_scheme_colors(name)
        if not colors:
            return False
        
        # Check Window or View background
        bg_str = None
        if "Colors:Window" in colors:
            bg_str = colors["Colors:Window"].get("BackgroundNormal")
        if not bg_str and "Colors:View" in colors:
            bg_str = colors["Colors:View"].get("BackgroundNormal")
        
        if bg_str:
            color = cls._parse_color(bg_str)
            if color:
                luminance = LookAndFeel.get_luminance(color)
                return luminance < 0.5
        
        return False
    
    @classmethod
    def get_current_scheme(cls) -> Optional[str]:
        """
        Get the currently applied KDE color scheme name.
        
        Returns:
            Scheme name or None if no KDE scheme is applied
        """
        return cls._current_scheme
    
    @classmethod
    def apply_scheme(cls, name: str) -> bool:
        """
        Apply a KDE color scheme to the application.
        
        This parses the scheme file and sets the application palette accordingly.
        
        Args:
            name: Color scheme name
        
        Returns:
            True if successful, False otherwise
        """
        colors = cls.get_scheme_colors(name)
        if not colors:
            return False
        
        app = QApplication.instance()
        if not app:
            return False
        
        # Store original palette if not already stored
        if LookAndFeel._original_palette is None:
            LookAndFeel._original_palette = app.palette()
        
        palette = QPalette()
        
        # Apply mapped colors
        for (section, key), roles in cls._KDE_TO_QPALETTE.items():
            if section in colors and key in colors[section]:
                color = cls._parse_color(colors[section][key])
                if color:
                    for role in roles:
                        palette.setColor(role, color)
        
        # Additional derived colors
        if "Colors:View" in colors:
            view = colors["Colors:View"]
            
            # BrightText - use ForegroundActive or derive from normal
            if "ForegroundActive" in view:
                color = cls._parse_color(view["ForegroundActive"])
                if color:
                    palette.setColor(QPalette.BrightText, color)
        
        # Set light/mid/dark from Window colors
        if "Colors:Window" in colors:
            window = colors["Colors:Window"]
            bg = cls._parse_color(window.get("BackgroundNormal", "255,255,255"))
            if bg:
                palette.setColor(QPalette.Light, bg.lighter(150))
                palette.setColor(QPalette.Midlight, bg.lighter(125))
                palette.setColor(QPalette.Mid, bg.darker(125))
                palette.setColor(QPalette.Dark, bg.darker(150))
                palette.setColor(QPalette.Shadow, bg.darker(200))
        
        # Apply disabled state colors
        if "ColorEffects:Disabled" in colors:
            disabled = colors["ColorEffects:Disabled"]
            disabled_color_str = disabled.get("Color", "120,120,120")
            disabled_color = cls._parse_color(disabled_color_str)
            if disabled_color:
                # Disabled text
                palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_color)
                palette.setColor(QPalette.Disabled, QPalette.Text, disabled_color)
                palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_color)
        
        app.setPalette(palette)
        cls._current_scheme = name
        
        # Update LookAndFeel forced scheme based on darkness
        if cls.is_scheme_dark(name):
            LookAndFeel._forced_scheme = ColorScheme.DARK
        else:
            LookAndFeel._forced_scheme = ColorScheme.LIGHT
        
        # Apply stylesheet to ensure all widgets update properly
        LookAndFeel.apply_palette_stylesheet()
        
        # Refresh all widgets
        LookAndFeel.refresh_widgets()
        
        return True
    
    @classmethod
    def reset_scheme(cls):
        """
        Reset to the original system palette.
        """
        app = QApplication.instance()
        if app and LookAndFeel._original_palette:
            app.setPalette(LookAndFeel._original_palette)
            # Clear stylesheet
            app.setStyleSheet("")
        
        cls._current_scheme = None
        LookAndFeel._forced_scheme = None
        
        # Refresh widgets
        LookAndFeel.refresh_widgets()
    
    @classmethod
    def get_scheme_info(cls, name: str) -> Dict[str, any]:
        """
        Get detailed information about a color scheme.
        
        Args:
            name: Color scheme name
        
        Returns:
            Dictionary with scheme metadata and preview colors
        """
        colors = cls.get_scheme_colors(name)
        if not colors:
            return {}
        
        info = {
            "name": name,
            "is_dark": cls.is_scheme_dark(name),
            "path": str(cls.get_scheme_path(name)),
        }
        
        # Extract preview colors
        preview = {}
        
        if "Colors:Window" in colors:
            w = colors["Colors:Window"]
            preview["window_bg"] = w.get("BackgroundNormal")
            preview["window_fg"] = w.get("ForegroundNormal")
        
        if "Colors:View" in colors:
            v = colors["Colors:View"]
            preview["view_bg"] = v.get("BackgroundNormal")
            preview["view_fg"] = v.get("ForegroundNormal")
            preview["link"] = v.get("ForegroundLink")
            preview["positive"] = v.get("ForegroundPositive")
            preview["negative"] = v.get("ForegroundNegative")
            preview["neutral"] = v.get("ForegroundNeutral")
        
        if "Colors:Selection" in colors:
            s = colors["Colors:Selection"]
            preview["selection_bg"] = s.get("BackgroundNormal")
            preview["selection_fg"] = s.get("ForegroundNormal")
        
        if "Colors:Button" in colors:
            b = colors["Colors:Button"]
            preview["button_bg"] = b.get("BackgroundNormal")
            preview["button_fg"] = b.get("ForegroundNormal")
        
        info["preview"] = preview
        
        # General info
        if "General" in colors:
            info["display_name"] = colors["General"].get("Name", name)
            info["color_scheme_id"] = colors["General"].get("ColorScheme")
        
        return info
    
    @classmethod
    def get_semantic_colors_from_scheme(cls, name: str) -> Dict[str, str]:
        """
        Extract semantic colors from a KDE color scheme.
        
        KDE schemes include ForegroundPositive (success), ForegroundNegative (error),
        ForegroundNeutral (warning), and ForegroundLink (info).
        
        Args:
            name: Color scheme name
        
        Returns:
            Dictionary with semantic color hex values
        """
        colors = cls.get_scheme_colors(name)
        if not colors:
            return {}
        
        semantic = {}
        
        # Extract from View colors (most complete)
        view = colors.get("Colors:View", {})
        
        # Success (Positive)
        if "ForegroundPositive" in view:
            color = cls._parse_color(view["ForegroundPositive"])
            if color:
                semantic["success"] = color.name()
                semantic["success_text"] = LookAndFeel.get_contrasting_color(color)
        
        # Error (Negative)
        if "ForegroundNegative" in view:
            color = cls._parse_color(view["ForegroundNegative"])
            if color:
                semantic["error"] = color.name()
                semantic["error_text"] = LookAndFeel.get_contrasting_color(color)
        
        # Warning (Neutral)
        if "ForegroundNeutral" in view:
            color = cls._parse_color(view["ForegroundNeutral"])
            if color:
                semantic["warning"] = color.name()
                semantic["warning_text"] = LookAndFeel.get_contrasting_color(color)
        
        # Info (Link)
        if "ForegroundLink" in view:
            color = cls._parse_color(view["ForegroundLink"])
            if color:
                semantic["info"] = color.name()
                semantic["info_text"] = LookAndFeel.get_contrasting_color(color)
        
        # Active (could be used for critical/accent)
        if "ForegroundActive" in view:
            color = cls._parse_color(view["ForegroundActive"])
            if color:
                semantic["critical"] = color.name()
                semantic["critical_text"] = LookAndFeel.get_contrasting_color(color)
        
        return semantic
    
    @classmethod
    def add_scheme_search_path(cls, path: str):
        """
        Add a custom directory to search for color schemes.
        
        Args:
            path: Directory path containing .colors files
        """
        p = Path(path)
        if p.exists() and p.is_dir() and p not in cls._SCHEME_DIRS:
            cls._SCHEME_DIRS.append(p)
            cls._scheme_cache.clear()  # Clear cache to pick up new schemes


class IconTheme:
    """
    Utilities for managing icon themes and resolving icons.
    
    Provides methods for:
    - Listing installed icon themes
    - Getting icons by name
    - Setting custom icon theme paths
    - Resolving icon file paths
    """
    
    _custom_theme_paths: List[Path] = []
    _custom_theme_name: Optional[str] = None
    
    # Standard icon theme directories on Linux
    _LINUX_ICON_DIRS = [
        Path.home() / ".local/share/icons",
        Path.home() / ".icons",
        Path("/usr/share/icons"),
        Path("/usr/local/share/icons"),
        Path("/usr/share/pixmaps"),
    ]
    
    # Standard icon sizes to search
    _ICON_SIZES = [48, 32, 24, 22, 16, "scalable"]
    
    # Standard icon contexts/categories
    _ICON_CONTEXTS = [
        "actions", "apps", "categories", "devices", "emblems",
        "emotes", "mimetypes", "places", "status", "stock",
    ]
    
    # ==================== Icon Theme Management ====================
    
    @classmethod
    def list_icon_themes(cls) -> List[str]:
        """
        List all installed icon themes.
        
        Returns:
            List of icon theme names
        """
        themes = set()
        
        # Search system directories
        search_dirs = cls._LINUX_ICON_DIRS + cls._custom_theme_paths
        
        for icon_dir in search_dirs:
            if icon_dir.exists() and icon_dir.is_dir():
                for item in icon_dir.iterdir():
                    if item.is_dir():
                        # Check if it has an index.theme file (valid icon theme)
                        index_file = item / "index.theme"
                        if index_file.exists():
                            themes.add(item.name)
        
        return sorted(list(themes))
    
    @classmethod
    def get_current_theme(cls) -> str:
        """
        Get the current icon theme name.
        
        Returns:
            Current theme name
        """
        if cls._custom_theme_name:
            return cls._custom_theme_name
        return QIcon.themeName() or "hicolor"
    
    @classmethod
    def set_theme(cls, theme_name: str) -> bool:
        """
        Set the icon theme by name.
        
        Args:
            theme_name: Name of an installed icon theme
        
        Returns:
            True if successful
        """
        cls._custom_theme_name = theme_name
        QIcon.setThemeName(theme_name)
        return True
    
    @classmethod
    def add_theme_search_path(cls, path: str):
        """
        Add a custom directory to search for icon themes.
        
        Args:
            path: Directory path containing icon themes
        """
        path_obj = Path(path)
        if path_obj.exists() and path_obj.is_dir():
            cls._custom_theme_paths.append(path_obj)
            # Also add to Qt's search paths
            QIcon.setThemeSearchPaths(
                QIcon.themeSearchPaths() + [str(path_obj)]
            )
    
    @classmethod
    def get_theme_search_paths(cls) -> List[str]:
        """
        Get all icon theme search paths.
        
        Returns:
            List of directory paths
        """
        return QIcon.themeSearchPaths()
    
    # ==================== Icon Access ====================
    
    @classmethod
    def get_icon(cls, name: str, fallback: Optional[str] = None, theme: Optional[str] = None, size: int = 48) -> QIcon:
        """
        Get an icon by its freedesktop.org standard name.
        
        Args:
            name: Icon name (e.g., "document-save", "edit-copy")
            fallback: Fallback icon name if primary not found
            theme: Optional icon theme to use for this call only.
                   If provided, uses get_icon_path() to find the icon file directly.
            size: Preferred icon size when using theme override (default 48)
        
        Returns:
            QIcon object (may be null if not found)
        
        Common icon names:
            - document-new, document-open, document-save, document-save-as
            - edit-copy, edit-cut, edit-paste, edit-delete, edit-undo, edit-redo
            - view-refresh, view-fullscreen
            - go-home, go-up, go-down, go-previous, go-next
            - list-add, list-remove
            - window-close, window-maximize, window-minimize
            - application-exit
            - dialog-information, dialog-warning, dialog-error, dialog-question
            - folder, folder-open, user-home, user-trash
        
        Example:
            # Use current theme
            icon = IconTheme.get_icon("folder")
            
            # Override with specific theme for this call only
            icon = IconTheme.get_icon("folder", theme="Papirus")
            icon = IconTheme.get_icon("folder", theme="breeze-dark")
        """
        if theme:
            # Use get_icon_path to find icon in specific theme (no global state change)
            path = cls.get_icon_path(name, size=size, theme=theme)
            if path:
                return QIcon(path)
            
            # Try fallback
            if fallback:
                path = cls.get_icon_path(fallback, size=size, theme=theme)
                if path:
                    return QIcon(path)
            
            return QIcon()  # Return null icon
        else:
            # Use Qt's built-in theme lookup for current theme
            icon = QIcon.fromTheme(name)
            
            if icon.isNull() and fallback:
                icon = QIcon.fromTheme(fallback)
            
            return icon
    
    @classmethod
    def get_icon_path(cls, name: str, size: int = 48, context: str = None, theme: Optional[str] = None) -> Optional[str]:
        """
        Resolve the file path for an icon.
        
        Args:
            name: Icon name
            size: Preferred icon size in pixels
            context: Icon context/category (e.g., "actions", "apps", "places")
            theme: Optional icon theme to search in. If not provided, uses current theme.
        
        Returns:
            File path to the icon or None if not found
        
        Example:
            # Use current theme
            path = IconTheme.get_icon_path("folder")
            
            # Search in specific theme
            path = IconTheme.get_icon_path("folder", theme="Papirus")
            
            # Non-Qt usage (e.g., GTK, web, etc.)
            path = IconTheme.get_icon_path("document-save", size=24, theme="breeze-dark")
        """
        theme_name = theme if theme else cls.get_current_theme()
        search_dirs = cls._LINUX_ICON_DIRS + cls._custom_theme_paths
        
        # Extensions to try (prefer svg)
        extensions = [".svg", ".png", ".xpm"]
        
        # Sizes to try (starting with requested size)
        int_sizes = [s for s in cls._ICON_SIZES if isinstance(s, int)]
        sizes_to_try = [size] + [s for s in int_sizes if s != size] + ["scalable"]
        
        # Contexts to try - expanded list
        contexts_to_try = [context] if context else [
            "actions", "apps", "categories", "devices", "emblems",
            "emotes", "mimetypes", "places", "status", "stock",
            "animations", "intl", "filesystems"
        ]
        
        def search_in_theme(theme_dir: Path) -> Optional[str]:
            """Search for icon in a theme directory"""
            if not theme_dir.exists():
                return None
            
            for sz in sizes_to_try:
                for ctx in contexts_to_try:
                    if ctx is None:
                        continue
                    
                    for ext in extensions:
                        # Structure 1: {context}/{size}/{name}.ext (Breeze, Papirus)
                        if isinstance(sz, int):
                            icon_path = theme_dir / ctx / str(sz) / f"{name}{ext}"
                            if icon_path.exists():
                                return str(icon_path)
                        
                        # Structure 2: {size}x{size}/{context}/{name}.ext (hicolor, some themes)
                        size_dir = f"{sz}x{sz}" if isinstance(sz, int) else sz
                        icon_path = theme_dir / size_dir / ctx / f"{name}{ext}"
                        if icon_path.exists():
                            return str(icon_path)
                        
                        # Structure 3: {context}/{size}x{size}/{name}.ext
                        icon_path = theme_dir / ctx / size_dir / f"{name}{ext}"
                        if icon_path.exists():
                            return str(icon_path)
                        
                        # Structure 4: scalable/{context}/{name}.ext
                        if sz == "scalable":
                            icon_path = theme_dir / "scalable" / ctx / f"{name}{ext}"
                            if icon_path.exists():
                                return str(icon_path)
            
            return None
        
        # Search in specified theme
        for icon_dir in search_dirs:
            theme_dir = icon_dir / theme_name
            result = search_in_theme(theme_dir)
            if result:
                return result
        
        # Try hicolor as fallback
        if theme_name != "hicolor":
            for icon_dir in search_dirs:
                theme_dir = icon_dir / "hicolor"
                result = search_in_theme(theme_dir)
                if result:
                    return result
        
        return None
    
    @classmethod
    def get_icon_from_file(cls, path: str) -> QIcon:
        """
        Load an icon from a specific file path.
        
        Args:
            path: Path to the icon file
        
        Returns:
            QIcon object
        """
        return QIcon(path)
    
    @classmethod
    def has_icon(cls, name: str, theme: Optional[str] = None) -> bool:
        """
        Check if an icon exists in the current or specified theme.
        
        Args:
            name: Icon name
            theme: Optional icon theme to check. If not provided, uses current theme.
        
        Returns:
            True if icon exists
        
        Example:
            # Check in current theme
            exists = IconTheme.has_icon("folder")
            
            # Check in specific theme
            exists = IconTheme.has_icon("folder", theme="Papirus")
        """
        if theme:
            original_theme = QIcon.themeName()
            QIcon.setThemeName(theme)
            result = QIcon.hasThemeIcon(name)
            QIcon.setThemeName(original_theme)
            return result
        else:
            return QIcon.hasThemeIcon(name)
    
    @classmethod
    def list_standard_icons(cls) -> Dict[str, List[str]]:
        """
        Get a dictionary of standard freedesktop.org icon names by category.
        
        Returns:
            Dictionary with categories as keys and icon name lists as values
        """
        return {
            "actions": [
                "document-new", "document-open", "document-open-recent",
                "document-save", "document-save-as", "document-save-all",
                "document-close", "document-print", "document-print-preview",
                "document-properties", "document-revert",
                "edit-copy", "edit-cut", "edit-paste", "edit-delete",
                "edit-undo", "edit-redo", "edit-select-all", "edit-clear",
                "edit-find", "edit-find-replace",
                "view-refresh", "view-fullscreen", "view-restore",
                "view-sort-ascending", "view-sort-descending",
                "go-home", "go-up", "go-down", "go-previous", "go-next",
                "go-first", "go-last", "go-jump",
                "list-add", "list-remove",
                "format-text-bold", "format-text-italic", "format-text-underline",
                "format-indent-more", "format-indent-less",
                "format-justify-left", "format-justify-center",
                "format-justify-right", "format-justify-fill",
                "window-close", "window-new",
                "application-exit",
                "help-about", "help-contents", "help-faq",
                "system-search", "system-run", "system-shutdown",
                "system-lock-screen", "system-log-out",
                "zoom-in", "zoom-out", "zoom-fit-best", "zoom-original",
                "media-playback-start", "media-playback-pause",
                "media-playback-stop", "media-record",
                "media-seek-backward", "media-seek-forward",
                "media-skip-backward", "media-skip-forward",
                "media-eject",
                "process-stop", "call-start", "call-stop",
                "bookmark-new", "contact-new", "mail-send",
            ],
            "apps": [
                "accessories-calculator", "accessories-text-editor",
                "help-browser", "multimedia-volume-control",
                "preferences-desktop", "preferences-system",
                "system-file-manager", "system-software-install",
                "utilities-terminal", "utilities-system-monitor",
            ],
            "categories": [
                "applications-accessories", "applications-development",
                "applications-games", "applications-graphics",
                "applications-internet", "applications-multimedia",
                "applications-office", "applications-system",
                "applications-utilities", "preferences-desktop",
                "preferences-system",
            ],
            "devices": [
                "audio-card", "audio-input-microphone",
                "battery", "camera-photo", "camera-video",
                "computer", "drive-harddisk", "drive-optical",
                "drive-removable-media", "input-keyboard",
                "input-mouse", "media-flash", "media-optical",
                "multimedia-player", "network-wired", "network-wireless",
                "phone", "printer", "scanner", "video-display",
            ],
            "emblems": [
                "emblem-default", "emblem-documents", "emblem-downloads",
                "emblem-favorite", "emblem-important", "emblem-mail",
                "emblem-photos", "emblem-readonly", "emblem-shared",
                "emblem-symbolic-link", "emblem-synchronized",
                "emblem-system", "emblem-unreadable",
            ],
            "mimetypes": [
                "application-x-executable", "audio-x-generic",
                "font-x-generic", "image-x-generic",
                "package-x-generic", "text-html", "text-x-generic",
                "text-x-script", "video-x-generic",
                "x-office-address-book", "x-office-calendar",
                "x-office-document", "x-office-presentation",
                "x-office-spreadsheet",
            ],
            "places": [
                "folder", "folder-documents", "folder-download",
                "folder-music", "folder-pictures", "folder-remote",
                "folder-saved-search", "folder-templates",
                "folder-videos", "network-server", "network-workgroup",
                "start-here", "user-bookmarks", "user-desktop",
                "user-home", "user-trash",
            ],
            "status": [
                "appointment-missed", "appointment-soon",
                "audio-volume-high", "audio-volume-low",
                "audio-volume-medium", "audio-volume-muted",
                "battery-caution", "battery-low",
                "dialog-error", "dialog-information",
                "dialog-password", "dialog-question", "dialog-warning",
                "folder-drag-accept", "folder-open", "folder-visiting",
                "image-loading", "image-missing",
                "mail-attachment", "mail-read", "mail-unread",
                "network-error", "network-idle", "network-offline",
                "network-receive", "network-transmit",
                "network-transmit-receive",
                "printer-error", "printer-printing",
                "security-high", "security-medium", "security-low",
                "software-update-available", "software-update-urgent",
                "task-due", "task-past-due",
                "user-available", "user-away", "user-idle", "user-offline",
                "weather-clear", "weather-few-clouds", "weather-overcast",
                "weather-showers", "weather-snow", "weather-storm",
            ],
        }
    
    @classmethod
    def get_standard_icon(cls, standard_icon: QStyle.StandardPixmap) -> QIcon:
        """
        Get a Qt standard icon.
        
        Args:
            standard_icon: QStyle.StandardPixmap enum value
        
        Returns:
            QIcon object
        
        Example:
            icon = IconTheme.get_standard_icon(QStyle.SP_DialogSaveButton)
        """
        app = QApplication.instance()
        if app and app.style():
            return app.style().standardIcon(standard_icon)
        return QIcon()
    
    @classmethod
    def list_qt_standard_icons(cls) -> Dict[str, int]:
        """
        List all Qt standard icons.
        
        Returns:
            Dictionary of icon names to QStyle.StandardPixmap values
        """
        return {
            "SP_TitleBarMenuButton": QStyle.SP_TitleBarMenuButton,
            "SP_TitleBarMinButton": QStyle.SP_TitleBarMinButton,
            "SP_TitleBarMaxButton": QStyle.SP_TitleBarMaxButton,
            "SP_TitleBarCloseButton": QStyle.SP_TitleBarCloseButton,
            "SP_TitleBarNormalButton": QStyle.SP_TitleBarNormalButton,
            "SP_TitleBarShadeButton": QStyle.SP_TitleBarShadeButton,
            "SP_TitleBarUnshadeButton": QStyle.SP_TitleBarUnshadeButton,
            "SP_TitleBarContextHelpButton": QStyle.SP_TitleBarContextHelpButton,
            "SP_DockWidgetCloseButton": QStyle.SP_DockWidgetCloseButton,
            "SP_MessageBoxInformation": QStyle.SP_MessageBoxInformation,
            "SP_MessageBoxWarning": QStyle.SP_MessageBoxWarning,
            "SP_MessageBoxCritical": QStyle.SP_MessageBoxCritical,
            "SP_MessageBoxQuestion": QStyle.SP_MessageBoxQuestion,
            "SP_DesktopIcon": QStyle.SP_DesktopIcon,
            "SP_TrashIcon": QStyle.SP_TrashIcon,
            "SP_ComputerIcon": QStyle.SP_ComputerIcon,
            "SP_DriveFDIcon": QStyle.SP_DriveFDIcon,
            "SP_DriveHDIcon": QStyle.SP_DriveHDIcon,
            "SP_DriveCDIcon": QStyle.SP_DriveCDIcon,
            "SP_DriveDVDIcon": QStyle.SP_DriveDVDIcon,
            "SP_DriveNetIcon": QStyle.SP_DriveNetIcon,
            "SP_DirOpenIcon": QStyle.SP_DirOpenIcon,
            "SP_DirClosedIcon": QStyle.SP_DirClosedIcon,
            "SP_DirLinkIcon": QStyle.SP_DirLinkIcon,
            "SP_DirLinkOpenIcon": QStyle.SP_DirLinkOpenIcon,
            "SP_FileIcon": QStyle.SP_FileIcon,
            "SP_FileLinkIcon": QStyle.SP_FileLinkIcon,
            "SP_FileDialogStart": QStyle.SP_FileDialogStart,
            "SP_FileDialogEnd": QStyle.SP_FileDialogEnd,
            "SP_FileDialogToParent": QStyle.SP_FileDialogToParent,
            "SP_FileDialogNewFolder": QStyle.SP_FileDialogNewFolder,
            "SP_FileDialogDetailedView": QStyle.SP_FileDialogDetailedView,
            "SP_FileDialogInfoView": QStyle.SP_FileDialogInfoView,
            "SP_FileDialogContentsView": QStyle.SP_FileDialogContentsView,
            "SP_FileDialogListView": QStyle.SP_FileDialogListView,
            "SP_FileDialogBack": QStyle.SP_FileDialogBack,
            "SP_DirIcon": QStyle.SP_DirIcon,
            "SP_DialogOkButton": QStyle.SP_DialogOkButton,
            "SP_DialogCancelButton": QStyle.SP_DialogCancelButton,
            "SP_DialogHelpButton": QStyle.SP_DialogHelpButton,
            "SP_DialogOpenButton": QStyle.SP_DialogOpenButton,
            "SP_DialogSaveButton": QStyle.SP_DialogSaveButton,
            "SP_DialogCloseButton": QStyle.SP_DialogCloseButton,
            "SP_DialogApplyButton": QStyle.SP_DialogApplyButton,
            "SP_DialogResetButton": QStyle.SP_DialogResetButton,
            "SP_DialogDiscardButton": QStyle.SP_DialogDiscardButton,
            "SP_DialogYesButton": QStyle.SP_DialogYesButton,
            "SP_DialogNoButton": QStyle.SP_DialogNoButton,
            "SP_ArrowUp": QStyle.SP_ArrowUp,
            "SP_ArrowDown": QStyle.SP_ArrowDown,
            "SP_ArrowLeft": QStyle.SP_ArrowLeft,
            "SP_ArrowRight": QStyle.SP_ArrowRight,
            "SP_ArrowBack": QStyle.SP_ArrowBack,
            "SP_ArrowForward": QStyle.SP_ArrowForward,
            "SP_DirHomeIcon": QStyle.SP_DirHomeIcon,
            "SP_CommandLink": QStyle.SP_CommandLink,
            "SP_VistaShield": QStyle.SP_VistaShield,
            "SP_BrowserReload": QStyle.SP_BrowserReload,
            "SP_BrowserStop": QStyle.SP_BrowserStop,
            "SP_MediaPlay": QStyle.SP_MediaPlay,
            "SP_MediaStop": QStyle.SP_MediaStop,
            "SP_MediaPause": QStyle.SP_MediaPause,
            "SP_MediaSkipForward": QStyle.SP_MediaSkipForward,
            "SP_MediaSkipBackward": QStyle.SP_MediaSkipBackward,
            "SP_MediaSeekForward": QStyle.SP_MediaSeekForward,
            "SP_MediaSeekBackward": QStyle.SP_MediaSeekBackward,
            "SP_MediaVolume": QStyle.SP_MediaVolume,
            "SP_MediaVolumeMuted": QStyle.SP_MediaVolumeMuted,
            "SP_LineEditClearButton": QStyle.SP_LineEditClearButton,
            "SP_RestoreDefaultsButton": QStyle.SP_RestoreDefaultsButton,
        }


# ==================== Demo Application ====================

if __name__ == "__main__":
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QComboBox, QListWidget, QListWidgetItem,
        QGroupBox, QGridLayout, QScrollArea, QFrame, QLineEdit,
        QFileDialog, QSizePolicy
    )
    from PySide6.QtGui import QFont
    
    class DemoWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Look and Feel Utilities Demo")
            self.resize(1000, 800)
            
            # Sample icons list for the grid
            self.sample_icons = [
                "document-new", "document-save", "edit-copy", "edit-paste",
                "folder", "folder-open", "go-home", "go-previous", "go-next",
                "dialog-information", "dialog-warning", "dialog-error",
                "application-exit", "help-about", "system-search",
                "media-playback-start", "media-playback-pause", "media-playback-stop",
            ]
            
            # Store icon labels for refresh
            self.icon_labels = {}
            
            # Main widget with scroll
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            self.setCentralWidget(scroll)
            
            main_widget = QWidget()
            scroll.setWidget(main_widget)
            layout = QVBoxLayout(main_widget)
            
            # Title
            title = QLabel("Look and Feel Utilities Demo")
            title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
            layout.addWidget(title)
            
            # Color Scheme Section
            scheme_group = QGroupBox("Color Scheme")
            scheme_layout = QVBoxLayout(scheme_group)
            
            scheme_btns = QHBoxLayout()
            
            self.scheme_label = QLabel(f"Current: {LookAndFeel.get_color_scheme().value}")
            scheme_btns.addWidget(self.scheme_label)
            
            btn_dark = QPushButton("Force Dark Mode")
            btn_dark.clicked.connect(self.force_dark)
            scheme_btns.addWidget(btn_dark)
            
            btn_light = QPushButton("Force Light Mode")
            btn_light.clicked.connect(self.force_light)
            scheme_btns.addWidget(btn_light)
            
            btn_reset = QPushButton("Reset to System")
            btn_reset.clicked.connect(self.reset_scheme)
            scheme_btns.addWidget(btn_reset)
            
            scheme_layout.addLayout(scheme_btns)
            layout.addWidget(scheme_group)
            
            # Qt Styles Section
            style_group = QGroupBox("Qt Styles")
            style_layout = QHBoxLayout(style_group)
            
            style_layout.addWidget(QLabel("Available Styles:"))
            
            self.style_combo = QComboBox()
            self.style_combo.addItems(LookAndFeel.list_styles())
            current_style = LookAndFeel.get_current_style()
            if current_style:
                index = self.style_combo.findText(current_style, Qt.MatchFixedString)
                if index >= 0:
                    self.style_combo.setCurrentIndex(index)
            style_layout.addWidget(self.style_combo)
            
            btn_apply_style = QPushButton("Apply Style")
            btn_apply_style.clicked.connect(self.apply_style)
            style_layout.addWidget(btn_apply_style)
            
            style_layout.addStretch()
            layout.addWidget(style_group)
            
            # KDE Color Schemes Section
            kde_group = QGroupBox("KDE/Plasma Color Schemes")
            kde_layout = QVBoxLayout(kde_group)
            
            # Current scheme and selection
            kde_row1 = QHBoxLayout()
            self.kde_scheme_label = QLabel(f"Current KDE Scheme: {KDEColorScheme.get_current_scheme() or '(none)'}")
            kde_row1.addWidget(self.kde_scheme_label)
            kde_row1.addStretch()
            kde_layout.addLayout(kde_row1)
            
            kde_row2 = QHBoxLayout()
            kde_row2.addWidget(QLabel("Available Schemes:"))
            
            self.kde_scheme_combo = QComboBox()
            self.kde_scheme_combo.setMinimumWidth(200)
            kde_schemes = KDEColorScheme.list_schemes()
            self.kde_scheme_combo.addItems(kde_schemes if kde_schemes else ["(no KDE schemes found)"])
            self.kde_scheme_combo.currentTextChanged.connect(self.preview_kde_scheme)
            kde_row2.addWidget(self.kde_scheme_combo)
            
            btn_apply_kde = QPushButton("Apply Scheme")
            btn_apply_kde.clicked.connect(self.apply_kde_scheme)
            kde_row2.addWidget(btn_apply_kde)
            
            btn_reset_kde = QPushButton("Reset to System")
            btn_reset_kde.clicked.connect(self.reset_kde_scheme)
            kde_row2.addWidget(btn_reset_kde)
            
            kde_row2.addStretch()
            kde_layout.addLayout(kde_row2)
            
            # Scheme preview
            self.kde_preview_frame = QFrame()
            self.kde_preview_frame.setMinimumHeight(100)
            self.kde_preview_frame.setStyleSheet("background: #f0f0f0; border-radius: 8px; padding: 10px;")
            
            kde_preview_layout = QVBoxLayout(self.kde_preview_frame)
            
            self.kde_preview_info = QLabel("Select a scheme to preview")
            self.kde_preview_info.setStyleSheet("font-weight: bold;")
            kde_preview_layout.addWidget(self.kde_preview_info)
            
            # Color swatches row
            self.kde_swatches_layout = QHBoxLayout()
            kde_preview_layout.addLayout(self.kde_swatches_layout)
            
            # Semantic colors from scheme
            self.kde_semantic_layout = QHBoxLayout()
            kde_preview_layout.addLayout(self.kde_semantic_layout)
            
            kde_layout.addWidget(self.kde_preview_frame)
            
            # Add custom path
            kde_path_row = QHBoxLayout()
            kde_path_row.addWidget(QLabel("Add Custom Schemes Path:"))
            
            self.kde_path_input = QLineEdit()
            self.kde_path_input.setPlaceholderText("/path/to/color-schemes/folder")
            kde_path_row.addWidget(self.kde_path_input)
            
            btn_browse_kde = QPushButton("Browse...")
            btn_browse_kde.clicked.connect(self.browse_kde_path)
            kde_path_row.addWidget(btn_browse_kde)
            
            btn_add_kde_path = QPushButton("Add Path")
            btn_add_kde_path.clicked.connect(self.add_kde_path)
            kde_path_row.addWidget(btn_add_kde_path)
            
            kde_layout.addLayout(kde_path_row)
            
            layout.addWidget(kde_group)
            
            # System Colors Section
            colors_group = QGroupBox("System Colors")
            colors_layout = QGridLayout(colors_group)
            
            colors = LookAndFeel.get_system_colors()
            row = 0
            col = 0
            for name, hex_color in colors.items():
                color_frame = QFrame()
                color_frame.setFixedSize(30, 30)
                color_frame.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #666;")
                
                label = QLabel(f"{name}: {hex_color}")
                label.setStyleSheet("font-size: 11px;")
                
                colors_layout.addWidget(color_frame, row, col * 2)
                colors_layout.addWidget(label, row, col * 2 + 1)
                
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
            
            layout.addWidget(colors_group)
            
            # Semantic Colors Section with Text Colors
            semantic_group = QGroupBox("Semantic Colors with Contrast-Aware Text")
            semantic_layout = QVBoxLayout(semantic_group)
            
            semantic_colors = LookAndFeel.get_semantic_colors()
            
            # Show semantic buttons with proper text colors
            semantic_types = ["success", "warning", "error", "info", "critical", "neutral"]
            
            buttons_row = QHBoxLayout()
            for sem_type in semantic_types:
                bg_color = semantic_colors[sem_type]
                text_color = semantic_colors[f"{sem_type}_text"]
                
                btn = QPushButton(f"{sem_type.title()}\n{bg_color}")
                btn.setFixedSize(100, 60)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {bg_color};
                        color: {text_color};
                        border: none;
                        border-radius: 6px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {semantic_colors[f'{sem_type}_light']};
                        color: {semantic_colors[f'{sem_type}_light_text']};
                    }}
                """)
                buttons_row.addWidget(btn)
            
            buttons_row.addStretch()
            semantic_layout.addLayout(buttons_row)
            
            # Show variants
            variants_label = QLabel("Variants (base, light, dark with auto text colors):")
            variants_label.setStyleSheet("font-size: 11px; margin-top: 10px;")
            semantic_layout.addWidget(variants_label)
            
            variants_grid = QGridLayout()
            row = 0
            for sem_type in semantic_types:
                col = 0
                for variant in ["", "_light", "_dark"]:
                    bg_key = f"{sem_type}{variant}"
                    text_key = f"{sem_type}{variant}_text"
                    
                    bg_color = semantic_colors[bg_key]
                    text_color = semantic_colors[text_key]
                    
                    label = QLabel(f" {bg_key} ")
                    label.setAlignment(Qt.AlignCenter)
                    label.setStyleSheet(f"""
                        background-color: {bg_color};
                        color: {text_color};
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 10px;
                    """)
                    variants_grid.addWidget(label, row, col)
                    col += 1
                row += 1
            
            semantic_layout.addLayout(variants_grid)
            layout.addWidget(semantic_group)
            
            # Contrast Utilities Section
            contrast_group = QGroupBox("Contrast Utilities - Get Text Color for Any Background")
            contrast_layout = QVBoxLayout(contrast_group)
            
            contrast_input_row = QHBoxLayout()
            contrast_input_row.addWidget(QLabel("Background Color:"))
            
            self.contrast_input = QLineEdit()
            self.contrast_input.setPlaceholderText("#28a745 or any hex color")
            self.contrast_input.setText("#28a745")
            self.contrast_input.returnPressed.connect(self.test_contrast)
            contrast_input_row.addWidget(self.contrast_input)
            
            btn_test_contrast = QPushButton("Get Contrasting Text Color")
            btn_test_contrast.clicked.connect(self.test_contrast)
            contrast_input_row.addWidget(btn_test_contrast)
            
            contrast_input_row.addStretch()
            contrast_layout.addLayout(contrast_input_row)
            
            # Result display
            self.contrast_result_frame = QFrame()
            self.contrast_result_frame.setFixedHeight(80)
            self.contrast_result_frame.setStyleSheet("background: #28a745; border-radius: 8px;")
            
            result_layout = QVBoxLayout(self.contrast_result_frame)
            self.contrast_result_label = QLabel("Sample Text on This Background")
            self.contrast_result_label.setAlignment(Qt.AlignCenter)
            self.contrast_result_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
            result_layout.addWidget(self.contrast_result_label)
            
            self.contrast_info_label = QLabel("Text color: #ffffff | Contrast ratio: 4.57:1 | WCAG AA: ✓")
            self.contrast_info_label.setAlignment(Qt.AlignCenter)
            self.contrast_info_label.setStyleSheet("color: #ffffff; font-size: 11px;")
            result_layout.addWidget(self.contrast_info_label)
            
            contrast_layout.addWidget(self.contrast_result_frame)
            
            # Tinted option
            tint_row = QHBoxLayout()
            btn_test_tinted = QPushButton("Try Tinted Text (Harmonious)")
            btn_test_tinted.clicked.connect(self.test_contrast_tinted)
            tint_row.addWidget(btn_test_tinted)
            
            tint_row.addWidget(QLabel("Tinted text uses a color that harmonizes with the background"))
            tint_row.addStretch()
            contrast_layout.addLayout(tint_row)
            
            layout.addWidget(contrast_group)
            
            # Icon Themes Section
            icon_theme_group = QGroupBox("Icon Themes")
            icon_theme_layout = QVBoxLayout(icon_theme_group)
            
            # Current theme and selection row
            theme_row = QHBoxLayout()
            self.theme_label = QLabel(f"Current Theme: {IconTheme.get_current_theme()}")
            theme_row.addWidget(self.theme_label)
            
            self.theme_combo = QComboBox()
            self.theme_combo.setMinimumWidth(200)
            themes = IconTheme.list_icon_themes()
            self.theme_combo.addItems(themes if themes else ["(no themes found)"])
            theme_row.addWidget(self.theme_combo)
            
            btn_apply_theme = QPushButton("Apply Theme")
            btn_apply_theme.clicked.connect(self.apply_icon_theme)
            theme_row.addWidget(btn_apply_theme)
            
            btn_refresh_themes = QPushButton("Refresh List")
            btn_refresh_themes.clicked.connect(self.refresh_theme_list)
            theme_row.addWidget(btn_refresh_themes)
            
            theme_row.addStretch()
            icon_theme_layout.addLayout(theme_row)
            
            # Custom theme path row
            path_row = QHBoxLayout()
            path_row.addWidget(QLabel("Add Custom Theme Path:"))
            
            self.theme_path_input = QLineEdit()
            self.theme_path_input.setPlaceholderText("/path/to/icons/folder")
            path_row.addWidget(self.theme_path_input)
            
            btn_browse = QPushButton("Browse...")
            btn_browse.clicked.connect(self.browse_theme_path)
            path_row.addWidget(btn_browse)
            
            btn_add_path = QPushButton("Add Path")
            btn_add_path.clicked.connect(self.add_theme_path)
            path_row.addWidget(btn_add_path)
            
            icon_theme_layout.addLayout(path_row)
            
            # Current search paths
            self.paths_label = QLabel(f"Search Paths: {', '.join(IconTheme.get_theme_search_paths()[:3])}...")
            self.paths_label.setStyleSheet("font-size: 10px; color: #666;")
            self.paths_label.setWordWrap(True)
            icon_theme_layout.addWidget(self.paths_label)
            
            layout.addWidget(icon_theme_group)
            
            # Get Icon by Name Section
            lookup_group = QGroupBox("Get Icon by Name")
            lookup_layout = QVBoxLayout(lookup_group)
            
            lookup_row = QHBoxLayout()
            lookup_row.addWidget(QLabel("Icon Name:"))
            
            self.icon_name_input = QLineEdit()
            self.icon_name_input.setPlaceholderText("e.g., document-save, folder, edit-copy")
            self.icon_name_input.returnPressed.connect(self.lookup_icon)
            lookup_row.addWidget(self.icon_name_input)
            
            btn_lookup = QPushButton("Get Icon")
            btn_lookup.clicked.connect(self.lookup_icon)
            lookup_row.addWidget(btn_lookup)
            
            lookup_layout.addLayout(lookup_row)
            
            # Icon result display
            result_row = QHBoxLayout()
            
            self.lookup_icon_label = QLabel()
            self.lookup_icon_label.setFixedSize(48, 48)
            self.lookup_icon_label.setStyleSheet("border: 1px solid #666; background: #f0f0f0;")
            self.lookup_icon_label.setAlignment(Qt.AlignCenter)
            result_row.addWidget(self.lookup_icon_label)
            
            self.lookup_result_label = QLabel("Enter an icon name and click 'Get Icon'")
            self.lookup_result_label.setStyleSheet("font-size: 12px; margin-left: 10px;")
            result_row.addWidget(self.lookup_result_label)
            
            result_row.addStretch()
            lookup_layout.addLayout(result_row)
            
            layout.addWidget(lookup_group)
            
            # Sample Icons Section
            self.icons_group = QGroupBox(f"Sample Icons (from {IconTheme.get_current_theme()})")
            self.icons_layout = QGridLayout(self.icons_group)
            
            self._populate_icons_grid()
            
            layout.addWidget(self.icons_group)
            
            # Qt Standard Icons Section
            qt_icons_group = QGroupBox("Qt Standard Icons")
            qt_icons_layout = QGridLayout(qt_icons_group)
            
            qt_sample_icons = [
                ("SP_DialogSaveButton", QStyle.SP_DialogSaveButton),
                ("SP_DialogOpenButton", QStyle.SP_DialogOpenButton),
                ("SP_DialogCloseButton", QStyle.SP_DialogCloseButton),
                ("SP_MessageBoxInformation", QStyle.SP_MessageBoxInformation),
                ("SP_MessageBoxWarning", QStyle.SP_MessageBoxWarning),
                ("SP_MessageBoxCritical", QStyle.SP_MessageBoxCritical),
                ("SP_TrashIcon", QStyle.SP_TrashIcon),
                ("SP_ComputerIcon", QStyle.SP_ComputerIcon),
                ("SP_DirHomeIcon", QStyle.SP_DirHomeIcon),
                ("SP_ArrowUp", QStyle.SP_ArrowUp),
                ("SP_ArrowDown", QStyle.SP_ArrowDown),
                ("SP_MediaPlay", QStyle.SP_MediaPlay),
            ]
            
            row = 0
            col = 0
            for name, sp in qt_sample_icons:
                icon = IconTheme.get_standard_icon(sp)
                
                icon_label = QLabel()
                if not icon.isNull():
                    icon_label.setPixmap(icon.pixmap(24, 24))
                else:
                    icon_label.setText("?")
                icon_label.setFixedSize(24, 24)
                
                name_label = QLabel(name.replace("SP_", ""))
                name_label.setStyleSheet("font-size: 10px;")
                
                qt_icons_layout.addWidget(icon_label, row, col * 2)
                qt_icons_layout.addWidget(name_label, row, col * 2 + 1)
                
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
            
            layout.addWidget(qt_icons_group)
            
            layout.addStretch()
        
        def _populate_icons_grid(self):
            """Populate the sample icons grid"""
            # Clear existing widgets
            while self.icons_layout.count():
                item = self.icons_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            self.icon_labels.clear()
            
            row = 0
            col = 0
            for icon_name in self.sample_icons:
                icon = IconTheme.get_icon(icon_name)
                
                icon_label = QLabel()
                if not icon.isNull():
                    icon_label.setPixmap(icon.pixmap(24, 24))
                else:
                    icon_label.setText("?")
                    icon_label.setStyleSheet("color: #999;")
                icon_label.setFixedSize(24, 24)
                
                # Store for later refresh
                self.icon_labels[icon_name] = icon_label
                
                name_label = QLabel(icon_name)
                name_label.setStyleSheet("font-size: 10px;")
                
                self.icons_layout.addWidget(icon_label, row, col * 2)
                self.icons_layout.addWidget(name_label, row, col * 2 + 1)
                
                col += 1
                if col >= 4:
                    col = 0
                    row += 1
        
        def _refresh_icons_grid(self):
            """Refresh icons in the grid with current theme"""
            for icon_name, icon_label in self.icon_labels.items():
                icon = IconTheme.get_icon(icon_name)
                if not icon.isNull():
                    icon_label.setPixmap(icon.pixmap(24, 24))
                    icon_label.setText("")
                    icon_label.setStyleSheet("")
                else:
                    icon_label.setPixmap(QPixmap())
                    icon_label.setText("?")
                    icon_label.setStyleSheet("color: #999;")
            
            # Update group title
            self.icons_group.setTitle(f"Sample Icons (from {IconTheme.get_current_theme()})")
        
        def force_dark(self):
            LookAndFeel.force_dark_mode()
            self.scheme_label.setText(f"Current: {LookAndFeel.get_color_scheme().value}")
        
        def force_light(self):
            LookAndFeel.force_light_mode()
            self.scheme_label.setText(f"Current: {LookAndFeel.get_color_scheme().value}")
        
        def reset_scheme(self):
            LookAndFeel.reset_color_scheme()
            self.scheme_label.setText(f"Current: {LookAndFeel.get_color_scheme().value}")
        
        def apply_style(self):
            style_name = self.style_combo.currentText()
            LookAndFeel.set_style(style_name)
        
        def apply_icon_theme(self):
            """Apply selected icon theme and refresh the icons grid"""
            theme_name = self.theme_combo.currentText()
            if theme_name and theme_name != "(no themes found)":
                IconTheme.set_theme(theme_name)
                self.theme_label.setText(f"Current Theme: {theme_name}")
                self._refresh_icons_grid()
        
        def refresh_theme_list(self):
            """Refresh the list of available themes"""
            self.theme_combo.clear()
            themes = IconTheme.list_icon_themes()
            self.theme_combo.addItems(themes if themes else ["(no themes found)"])
        
        def browse_theme_path(self):
            """Browse for a custom theme directory"""
            path = QFileDialog.getExistingDirectory(
                self, "Select Icon Theme Directory",
                str(Path.home()),
                QFileDialog.ShowDirsOnly
            )
            if path:
                self.theme_path_input.setText(path)
        
        def add_theme_path(self):
            """Add a custom theme search path"""
            path = self.theme_path_input.text().strip()
            if path:
                IconTheme.add_theme_search_path(path)
                self.theme_path_input.clear()
                self.refresh_theme_list()
                paths = IconTheme.get_theme_search_paths()
                self.paths_label.setText(f"Search Paths: {', '.join(paths[:3])}{'...' if len(paths) > 3 else ''}")
        
        def lookup_icon(self):
            """Look up an icon by name"""
            icon_name = self.icon_name_input.text().strip()
            if not icon_name:
                self.lookup_result_label.setText("Please enter an icon name")
                return
            
            icon = IconTheme.get_icon(icon_name)
            icon_path = IconTheme.get_icon_path(icon_name)
            has_icon = IconTheme.has_icon(icon_name)
            
            if not icon.isNull():
                self.lookup_icon_label.setPixmap(icon.pixmap(48, 48))
                self.lookup_icon_label.setText("")
                
                if icon_path:
                    self.lookup_result_label.setText(
                        f"✓ Found: {icon_name}\n"
                        f"Path: {icon_path}\n"
                        f"Has theme icon: {has_icon}"
                    )
                else:
                    self.lookup_result_label.setText(
                        f"✓ Found: {icon_name}\n"
                        f"Path: (resolved by Qt)\n"
                        f"Has theme icon: {has_icon}"
                    )
            else:
                self.lookup_icon_label.setPixmap(QPixmap())
                self.lookup_icon_label.setText("✗")
                self.lookup_icon_label.setStyleSheet("border: 1px solid #666; background: #f0f0f0; color: #c00; font-size: 24px;")
                self.lookup_result_label.setText(
                    f"✗ Not found: {icon_name}\n"
                    f"Has theme icon: {has_icon}"
                )
        
        def test_contrast(self, tinted: bool = False):
            """Test contrast color for a given background"""
            bg_color = self.contrast_input.text().strip()
            if not bg_color:
                return
            
            # Ensure it starts with #
            if not bg_color.startswith("#"):
                bg_color = f"#{bg_color}"
            
            try:
                # Validate color
                qcolor = QColor(bg_color)
                if not qcolor.isValid():
                    self.contrast_info_label.setText("Invalid color! Use hex format like #28a745")
                    return
                
                # Get contrasting text color
                text_color = LookAndFeel.get_contrasting_color(bg_color, prefer_tinted=tinted)
                contrast_ratio = LookAndFeel.get_contrast_ratio(bg_color, text_color)
                
                # Check WCAG compliance
                wcag_aa = "✓" if contrast_ratio >= 4.5 else "✗"
                wcag_aaa = "✓" if contrast_ratio >= 7.0 else "✗"
                
                # Update display
                self.contrast_result_frame.setStyleSheet(f"background: {bg_color}; border-radius: 8px;")
                self.contrast_result_label.setStyleSheet(f"color: {text_color}; font-size: 16px; font-weight: bold;")
                self.contrast_info_label.setStyleSheet(f"color: {text_color}; font-size: 11px;")
                
                mode = "tinted" if tinted else "standard"
                self.contrast_info_label.setText(
                    f"Text: {text_color} ({mode}) | Ratio: {contrast_ratio:.2f}:1 | "
                    f"WCAG AA: {wcag_aa} | WCAG AAA: {wcag_aaa}"
                )
                
            except Exception as e:
                self.contrast_info_label.setText(f"Error: {str(e)}")
        
        def test_contrast_tinted(self):
            """Test tinted contrast color"""
            self.test_contrast(tinted=True)
        
        def preview_kde_scheme(self, scheme_name: str):
            """Preview a KDE color scheme"""
            if not scheme_name or scheme_name == "(no KDE schemes found)":
                return
            
            info = KDEColorScheme.get_scheme_info(scheme_name)
            if not info:
                self.kde_preview_info.setText(f"Could not load scheme: {scheme_name}")
                return
            
            # Update info label
            is_dark = "Dark" if info.get("is_dark") else "Light"
            display_name = info.get("display_name", scheme_name)
            self.kde_preview_info.setText(f"{display_name} ({is_dark} scheme)")
            
            # Clear previous swatches
            while self.kde_swatches_layout.count():
                item = self.kde_swatches_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            while self.kde_semantic_layout.count():
                item = self.kde_semantic_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            preview = info.get("preview", {})
            
            # Create color swatches
            swatch_pairs = [
                ("Window", "window_bg", "window_fg"),
                ("View", "view_bg", "view_fg"),
                ("Button", "button_bg", "button_fg"),
                ("Selection", "selection_bg", "selection_fg"),
            ]
            
            for label, bg_key, fg_key in swatch_pairs:
                bg_str = preview.get(bg_key)
                fg_str = preview.get(fg_key)
                
                if bg_str:
                    bg_color = KDEColorScheme._parse_color(bg_str)
                    fg_color = KDEColorScheme._parse_color(fg_str) if fg_str else None
                    
                    if bg_color:
                        swatch = QLabel(label)
                        swatch.setFixedSize(80, 40)
                        swatch.setAlignment(Qt.AlignCenter)
                        
                        fg_hex = fg_color.name() if fg_color else LookAndFeel.get_contrasting_color(bg_color)
                        swatch.setStyleSheet(f"""
                            background-color: {bg_color.name()};
                            color: {fg_hex};
                            border-radius: 4px;
                            font-size: 11px;
                            font-weight: bold;
                        """)
                        self.kde_swatches_layout.addWidget(swatch)
            
            self.kde_swatches_layout.addStretch()
            
            # Create semantic color swatches
            semantic_map = [
                ("Positive", "positive", "#28a745"),
                ("Negative", "negative", "#dc3545"),
                ("Neutral", "neutral", "#ffc107"),
                ("Link", "link", "#17a2b8"),
            ]
            
            for label, key, fallback in semantic_map:
                color_str = preview.get(key)
                if color_str:
                    color = KDEColorScheme._parse_color(color_str)
                    if color:
                        swatch = QLabel(label)
                        swatch.setFixedSize(70, 30)
                        swatch.setAlignment(Qt.AlignCenter)
                        
                        text_color = LookAndFeel.get_contrasting_color(color)
                        swatch.setStyleSheet(f"""
                            background-color: {color.name()};
                            color: {text_color};
                            border-radius: 4px;
                            font-size: 10px;
                        """)
                        self.kde_semantic_layout.addWidget(swatch)
            
            self.kde_semantic_layout.addStretch()
            
            # Update preview frame background based on scheme
            window_bg = preview.get("window_bg")
            if window_bg:
                bg_color = KDEColorScheme._parse_color(window_bg)
                if bg_color:
                    fg_color = LookAndFeel.get_contrasting_color(bg_color)
                    self.kde_preview_frame.setStyleSheet(f"""
                        background: {bg_color.name()};
                        border-radius: 8px;
                        padding: 10px;
                    """)
                    self.kde_preview_info.setStyleSheet(f"font-weight: bold; color: {fg_color};")
        
        def apply_kde_scheme(self):
            """Apply the selected KDE color scheme"""
            scheme_name = self.kde_scheme_combo.currentText()
            if scheme_name and scheme_name != "(no KDE schemes found)":
                if KDEColorScheme.apply_scheme(scheme_name):
                    self.kde_scheme_label.setText(f"Current KDE Scheme: {scheme_name}")
                    self.scheme_label.setText(f"Current: {LookAndFeel.get_color_scheme().value}")
                    
                    # Refresh semantic colors display
                    self._refresh_semantic_colors()
        
        def reset_kde_scheme(self):
            """Reset KDE color scheme to system default"""
            KDEColorScheme.reset_scheme()
            self.kde_scheme_label.setText("Current KDE Scheme: (none)")
            self.scheme_label.setText(f"Current: {LookAndFeel.get_color_scheme().value}")
            self._refresh_semantic_colors()
        
        def _refresh_semantic_colors(self):
            """Refresh the semantic colors section after scheme change"""
            # This would require storing references to the semantic buttons
            # For now, just note that the semantic colors are from get_semantic_colors()
            pass
        
        def browse_kde_path(self):
            """Browse for a custom KDE schemes directory"""
            path = QFileDialog.getExistingDirectory(
                self, "Select Color Schemes Directory",
                str(Path.home() / ".local/share/color-schemes"),
                QFileDialog.ShowDirsOnly
            )
            if path:
                self.kde_path_input.setText(path)
        
        def add_kde_path(self):
            """Add a custom KDE schemes search path"""
            path = self.kde_path_input.text().strip()
            if path:
                KDEColorScheme.add_scheme_search_path(path)
                self.kde_path_input.clear()
                
                # Refresh the combo
                self.kde_scheme_combo.clear()
                kde_schemes = KDEColorScheme.list_schemes()
                self.kde_scheme_combo.addItems(kde_schemes if kde_schemes else ["(no KDE schemes found)"])
    
    app = QApplication(sys.argv)
    
    font = QFont()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)
    
    window = DemoWindow()
    window.show()
    sys.exit(app.exec())

