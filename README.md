# EmuPyside6Widgets

A collection of modern, animated UI widgets for PySide6 applications. These widgets provide common UI patterns like drawers, overlays, and notifications with smooth animations and flexible APIs.

## Installation

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

## Widgets Overview

| Widget | Description |
|--------|-------------|
| **DrawerWidget** | Slide-in panels from any edge (left, right, top, bottom) |
| **OverlayWidget** | Centered modal dialogs with dimmed background |
| **NotificationWidget** | Toast-style notifications with stacking and auto-dismiss |

## Utilities Overview

| Utility | Description |
|---------|-------------|
| **LookAndFeel** | Dark/light mode detection, Qt styles, system colors |
| **IconTheme** | Icon theme management, icon resolution by name |

---

## DrawerWidget

Slide-in drawer panels that can appear from any edge of the parent widget. Supports sticky mode for multi-drawer scenarios.

### Basic Usage

```python
from EmuPyside6Widgets import DrawerManager, DrawerSide

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.drawer_manager = DrawerManager(self)
    
    def show_settings(self):
        settings_widget = SettingsPanel()
        self.drawer_manager.show_drawer(
            settings_widget,
            side=DrawerSide.RIGHT,
            size=400
        )
```

### API Reference

#### DrawerManager

```python
DrawerManager(parent: QWidget)
```

| Method | Description |
|--------|-------------|
| `show_drawer(widget, side, size, sticky, show_close_button)` | Show a drawer with the given widget |
| `close_all(side=None, sticky_only=False)` | Close all drawers with optional filters |
| `get_open_drawers(side=None)` | Get list of currently open drawers |

#### show_drawer() Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `widget` | QWidget | required | Widget to display in the drawer |
| `side` | DrawerSide | `RIGHT` | Edge to slide from (`LEFT`, `RIGHT`, `TOP`, `BOTTOM`) |
| `size` | int | `400` | Width (left/right) or height (top/bottom) in pixels |
| `sticky` | bool | `False` | If `True`, no overlay and doesn't close on outside click |
| `show_close_button` | bool | `True` | Show the X close button |

### Examples

#### Standard Drawer
```python
# Right drawer with overlay - closes on outside click
widget = MyWidget()
drawer = self.drawer_manager.show_drawer(widget, DrawerSide.RIGHT, size=350)
```

#### Sticky Drawer (No Overlay)
```python
# Drawer without overlay - allows interaction with main content
drawer = self.drawer_manager.show_drawer(
    widget,
    side=DrawerSide.LEFT,
    size=280,
    sticky=True
)
```

#### Multiple Simultaneous Drawers
```python
# Open drawers on both sides (requires sticky=True)
self.drawer_manager.show_drawer(left_panel, DrawerSide.LEFT, sticky=True)
self.drawer_manager.show_drawer(right_panel, DrawerSide.RIGHT, sticky=True)
```

---

## OverlayWidget

Centered modal overlays with dimmed backgrounds. Perfect for dialogs, forms, and confirmation prompts.

### Basic Usage

```python
from EmuPyside6Widgets import OverlayManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.overlay_manager = OverlayManager(self)
    
    def show_dialog(self):
        dialog = ConfirmDialog()
        dialog.setFixedSize(400, 300)
        self.overlay_manager.show_overlay(dialog)
```

### API Reference

#### OverlayManager

```python
OverlayManager(parent: QWidget)
```

| Method | Description |
|--------|-------------|
| `show_overlay(widget, sticky, nobackground)` | Show an overlay with the given widget |
| `close_all(nobackground_only=False)` | Close all overlays |
| `get_open_overlays()` | Get list of currently open overlays |

#### show_overlay() Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `widget` | QWidget | required | Widget to display (should have fixed size) |
| `sticky` | bool | `False` | If `True`, doesn't close on outside click |
| `nobackground` | bool | `False` | If `True`, no dark overlay background |

### Examples

#### Standard Modal
```python
widget = FormWidget()
widget.setFixedSize(400, 300)
overlay = self.overlay_manager.show_overlay(widget)

# Close programmatically
overlay._close_overlay()
```

#### Sticky Modal (Must Close via Button)
```python
confirm_dialog = ConfirmWidget()
confirm_dialog.setFixedSize(350, 200)
overlay = self.overlay_manager.show_overlay(confirm_dialog, sticky=True)

# Connect close button
confirm_dialog.close_btn.clicked.connect(overlay._close_overlay)
```

#### Stacked Modals
```python
# Multiple modals can be stacked - later ones appear on top
self.overlay_manager.show_overlay(first_modal)
self.overlay_manager.show_overlay(second_modal)  # Appears on top
```

---

## NotificationWidget

Toast-style notifications with severity levels, auto-dismiss, stacking, and smooth animations.

### Basic Usage

```python
from EmuPyside6Widgets import NotificationManager, NotificationSeverity, NotificationZone

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.notification_manager = NotificationManager(self)
    
    def on_save(self):
        self.notification_manager.show_notification(
            message="File saved successfully!",
            title="Success",
            severity=NotificationSeverity.SUCCESS
        )
```

### API Reference

#### NotificationManager

```python
NotificationManager(parent: QWidget)
```

| Method | Description |
|--------|-------------|
| `show_notification(...)` | Show a notification |
| `set_style(severity, style)` | Customize style for a severity level |
| `get_style(severity)` | Get current style for a severity |
| `reset_style(severity=None)` | Reset style(s) to defaults |
| `close_all(zone=None)` | Close all notifications |

#### show_notification() Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | str | `""` | Notification message text |
| `title` | str | `""` | Optional title text |
| `severity` | NotificationSeverity | `INFO` | Severity level |
| `zone` | NotificationZone | `TOP_RIGHT` | Screen position |
| `duration` | int | None | Auto-dismiss time in ms (None = use default) |
| `width` | int | `320` | Notification width in pixels |
| `custom_widget` | QWidget | None | Custom widget instead of text |

#### Severity Levels

| Severity | Default Duration | Default Color |
|----------|-----------------|---------------|
| `INFO` | 3000ms | Blue |
| `SUCCESS` | 3000ms | Green |
| `WARNING` | 5000ms | Orange |
| `ERROR` | 7000ms | Red |
| `CRITICAL` | Never | Purple |

#### Position Zones

| Zone | Description |
|------|-------------|
| `TOP_LEFT` | Top-left corner, stacks downward |
| `TOP_RIGHT` | Top-right corner, stacks downward |
| `BOTTOM_LEFT` | Bottom-left corner, stacks upward |
| `BOTTOM_RIGHT` | Bottom-right corner, stacks upward |

### Examples

#### Simple Notifications
```python
# Info notification (auto-dismisses in 3s)
self.notification_manager.show_notification(
    message="Processing complete",
    severity=NotificationSeverity.INFO
)

# Error notification (auto-dismisses in 7s)
self.notification_manager.show_notification(
    message="Failed to save file",
    title="Error",
    severity=NotificationSeverity.ERROR
)

# Critical notification (never auto-dismisses)
self.notification_manager.show_notification(
    message="Database connection lost!",
    title="Critical",
    severity=NotificationSeverity.CRITICAL
)
```

#### Custom Duration
```python
# Override default duration
self.notification_manager.show_notification(
    message="This will stay for 10 seconds",
    severity=NotificationSeverity.INFO,
    duration=10000
)
```

#### Different Positions
```python
# Bottom-left corner
self.notification_manager.show_notification(
    message="Download complete",
    zone=NotificationZone.BOTTOM_LEFT
)
```

#### Custom Styles
```python
from EmuPyside6Widgets import SeverityStyle

# Customize the CRITICAL style
self.notification_manager.set_style(
    NotificationSeverity.CRITICAL,
    SeverityStyle(
        bg="#ff0000",      # Red background
        border="#cc0000",  # Darker red border
        text="#ffffff",    # White text
        duration=0         # Never auto-dismiss
    )
)

# Reset to defaults
self.notification_manager.reset_style(NotificationSeverity.CRITICAL)
```

#### Custom Widget Notification
```python
# Create custom content
custom = QWidget()
layout = QHBoxLayout(custom)
layout.addWidget(QLabel("Custom content!"))
btn = QPushButton("Action")
layout.addWidget(btn)

notification = self.notification_manager.show_notification(
    severity=NotificationSeverity.WARNING,
    duration=0,  # Don't auto-dismiss
    custom_widget=custom
)

btn.clicked.connect(notification._start_dismiss)
```

### Features

- **Hover to Pause**: Mouse hover pauses auto-dismiss timer
- **Stacking**: Multiple notifications stack without overlapping
- **Gap Fill Animation**: When one closes, others smoothly fill the gap
- **Responsive**: Repositions on window resize
- **Close Button**: Each notification has an X button

---

## Quick Reference Functions

For simple one-off notifications without creating a manager:

```python
from EmuPyside6Widgets import show_info, show_success, show_warning, show_error, show_critical

# These create notifications directly on a parent widget
show_info(parent, "Information message")
show_success(parent, "Operation successful!", title="Done")
show_warning(parent, "Please review", zone=NotificationZone.BOTTOM_RIGHT)
show_error(parent, "Something went wrong")
show_critical(parent, "System failure!")
```

---

## Running Demos

Each widget includes a demo application:

```bash
# Drawer Widget Demo
python -m EmuPyside6Widgets.DrawerWidget

# Overlay Widget Demo  
python -m EmuPyside6Widgets.OverlayWidget

# Notification Widget Demo
python -m EmuPyside6Widgets.NotificationWidget
```

Or run directly:

```bash
python src/EmuPyside6Widgets/DrawerWidget.py
python src/EmuPyside6Widgets/OverlayWidget.py
python src/EmuPyside6Widgets/NotificationWidget.py
```

---

## Utilities

### LookAndFeel

Utilities for managing application appearance, dark/light mode, and system colors.

```python
from EmuPyside6Widgets import LookAndFeel, ColorScheme
```

#### Dark/Light Mode Detection and Forcing

```python
# Check current mode
if LookAndFeel.is_dark_mode():
    print("Dark mode is active")

# Get current scheme
scheme = LookAndFeel.get_color_scheme()  # Returns ColorScheme.DARK or ColorScheme.LIGHT

# Force dark mode
LookAndFeel.force_dark_mode()

# Force light mode
LookAndFeel.force_light_mode()

# Reset to system default
LookAndFeel.reset_color_scheme()
```

#### Qt Styles

```python
# List available styles
styles = LookAndFeel.list_styles()  # ['Breeze', 'Fusion', 'Windows', ...]

# Get current style
current = LookAndFeel.get_current_style()

# Set style
LookAndFeel.set_style("Fusion")
```

#### System Colors

```python
# Get all system palette colors
colors = LookAndFeel.get_system_colors()
print(colors['window'])       # Window background color
print(colors['text'])         # Text color
print(colors['highlight'])    # Selection highlight color

# Get extended colors (including disabled/inactive states)
extended = LookAndFeel.get_system_colors_extended()
print(extended['disabled']['text'])

# Get semantic colors (success, error, warning, etc.)
semantic = LookAndFeel.get_semantic_colors()
print(semantic['success'])    # Green for success states
print(semantic['error'])      # Red for error states
print(semantic['warning'])    # Orange for warnings
print(semantic['info'])       # Blue for info
print(semantic['critical'])   # Purple for critical

# Get a specific color as QColor
color = LookAndFeel.get_color('highlight')
```

### IconTheme

Utilities for working with system icon themes and resolving icons.

```python
from EmuPyside6Widgets import IconTheme
```

#### Icon Theme Management

```python
# List installed icon themes
themes = IconTheme.list_icon_themes()  # ['Adwaita', 'breeze', 'hicolor', ...]

# Get current theme
current = IconTheme.get_current_theme()

# Set icon theme
IconTheme.set_theme("breeze")

# Add custom theme search path
IconTheme.add_theme_search_path("/path/to/custom/icons")
```

#### Getting Icons

```python
# Get icon by freedesktop.org standard name
icon = IconTheme.get_icon("document-save")
icon = IconTheme.get_icon("edit-copy", fallback="edit-paste")

# Check if icon exists
if IconTheme.has_icon("document-save"):
    print("Icon available")

# Get icon file path
path = IconTheme.get_icon_path("document-save", size=48)

# Load icon from specific file
icon = IconTheme.get_icon_from_file("/path/to/icon.png")

# Get Qt standard icon
from PySide6.QtWidgets import QStyle
icon = IconTheme.get_standard_icon(QStyle.SP_DialogSaveButton)
```

#### Common Icon Names

```python
# Get dictionary of standard icon names by category
icons = IconTheme.list_standard_icons()

# Common action icons:
# document-new, document-open, document-save, document-save-as
# edit-copy, edit-cut, edit-paste, edit-delete, edit-undo, edit-redo
# view-refresh, view-fullscreen
# go-home, go-previous, go-next, go-up, go-down
# list-add, list-remove
# dialog-information, dialog-warning, dialog-error, dialog-question
# application-exit, window-close
# folder, folder-open, user-home, user-trash
```

#### Running the Demo

```bash
python src/EmuPyside6Widgets/utils/lookandfeel.py
```

---

## Notes

### Sticky Mode
- **Drawers**: `sticky=True` removes the dark overlay and allows interaction with the main window
- **Overlays**: `sticky=True` prevents closing on outside click; `nobackground=True` removes the dark overlay
- Use sticky mode when you need multiple simultaneous panels/modals

### Z-Ordering
- Later-created widgets appear above earlier ones
- Each manager tracks its own widgets independently
- Closing a widget properly updates the stacking order

### Parent Widget Scope
- Managers are scoped to their parent widget
- You can have different managers for different parts of your UI
- Widgets respect parent boundaries for positioning

### Memory Management
- Widgets are automatically cleaned up when closed
- The `closed` signal is emitted before deletion
- Managers track open widgets and remove closed ones automatically

---

## Requirements

- Python 3.8+
- PySide6 >= 6.0.0

---

## License

MIT License - See LICENSE file for details.

