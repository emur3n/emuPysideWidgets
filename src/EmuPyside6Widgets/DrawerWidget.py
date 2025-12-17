import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QFrame,
    QGraphicsOpacityEffect,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QEvent, QRect, Signal
from PySide6.QtGui import QColor, QPalette, QFont, QKeyEvent, QPainter
from enum import Enum


class DrawerSide(Enum):
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


# Internal drawer tracker for z-ordering
class _DrawerTracker:
    """Internal tracker for drawer z-ordering and stacking"""
    _instances = {}  # parent_id -> {side: [drawers]}
    _z_counter = {}  # parent_id -> counter
    
    @classmethod
    def register(cls, parent, drawer, side):
        """Register a drawer and get its z-index"""
        parent_id = id(parent)
        if parent_id not in cls._instances:
            cls._instances[parent_id] = {s: [] for s in DrawerSide}
            cls._z_counter[parent_id] = 0
        
        cls._instances[parent_id][side].append(drawer)
        cls._z_counter[parent_id] += 1
        return cls._z_counter[parent_id]
    
    @classmethod
    def unregister(cls, parent, drawer, side):
        """Remove a drawer from tracking"""
        parent_id = id(parent)
        if parent_id in cls._instances and side in cls._instances[parent_id]:
            if drawer in cls._instances[parent_id][side]:
                cls._instances[parent_id][side].remove(drawer)
    
    @classmethod
    def get_drawers_on_side(cls, parent, side):
        """Get all drawers on a specific side"""
        parent_id = id(parent)
        if parent_id in cls._instances:
            return cls._instances[parent_id].get(side, [])
        return []
    
    @classmethod
    def is_topmost_on_side(cls, parent, drawer, side):
        """Check if this drawer is the topmost on its side"""
        drawers = cls.get_drawers_on_side(parent, side)
        return len(drawers) == 0 or drawers[-1] == drawer


class DrawerManager:
    """
    Manager for showing drawers within a parent widget.
    
    Usage:
        class MainWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.drawer_manager = DrawerManager(self)
                
            def show_settings(self):
                widget = SettingsWidget()
                self.drawer_manager.show_drawer(
                    widget,
                    side=DrawerSide.RIGHT,
                    size=400,
                    sticky=False
                )
    """
    
    def __init__(self, parent):
        """
        Initialize the drawer manager.
        
        Args:
            parent: The parent widget where drawers will be shown
        """
        self._parent = parent
        self._drawers = []
    
    def show_drawer(
        self,
        widget,
        side=DrawerSide.RIGHT,
        size=400,
        sticky=False,
        show_close_button=True,
    ):
        """
        Show a widget in a drawer.
        
        Args:
            widget: The widget to display in the drawer
            side: Which side to slide from (DrawerSide enum)
            size: Width for left/right drawers, height for top/bottom
            sticky: If True, drawer won't close on outside click and has no overlay
            show_close_button: Whether to show the X close button
        
        Returns:
            The DrawerWidget instance
        """
        drawer = DrawerWidget(self._parent, sticky=sticky)
        drawer.show_widget(widget, side, size, show_close_button)
        
        self._drawers.append(drawer)
        drawer.closed.connect(lambda: self._on_drawer_closed(drawer))
        
        return drawer
    
    def _on_drawer_closed(self, drawer):
        """Handle drawer closed"""
        if drawer in self._drawers:
            self._drawers.remove(drawer)
    
    def close_all(self, side=None, sticky_only=False):
        """
        Close all drawers, optionally filtered.
        
        Args:
            side: Only close drawers on this side (None = all sides)
            sticky_only: Only close sticky drawers
        """
        drawers_to_close = self._drawers.copy()
        for drawer in drawers_to_close:
            if side is not None and drawer._side != side:
                continue
            if sticky_only and not drawer._sticky:
                continue
            drawer._close_drawer()
    
    def get_open_drawers(self, side=None):
        """
        Get list of open drawers, optionally filtered by side.
        
        Args:
            side: Filter by side (None = all sides)
        
        Returns:
            List of open DrawerWidget instances
        """
        if side is None:
            return self._drawers.copy()
        return [d for d in self._drawers if d._side == side]
    
    @property
    def parent(self):
        """Get the parent widget"""
        return self._parent


class DrawerWidget(QWidget):
    """
    A drawer widget that slides in from any edge of the parent widget.
    
    Args:
        parent: Parent widget
        sticky: If True, drawer won't close on outside clicks and won't block
                interaction with the rest of the UI (no full overlay).
                Useful for multi-drawer scenarios.
    """
    
    closed = Signal()  # Emitted when drawer is closed
    
    def __init__(self, parent=None, sticky=False):
        super().__init__(parent)
        self._sticky = sticky
        self.setup_ui()
        self._content_widget = None
        self._content_frame = None
        self._animation = None
        self._side = DrawerSide.RIGHT
        self._drawer_size = 400  # Default drawer width/height
        self._closing = False  # Flag to prevent multiple closes
        self._opacity_animation = None  # Store opacity animation reference
        self._show_close_button = True  # Default to showing close button
        self._z_index = 0  # For stacking order

        # Enable key events and make sure we get focus
        self.setFocusPolicy(Qt.StrongFocus)

    def setup_ui(self):
        # For sticky mode, we don't cover the whole parent
        # For non-sticky, we cover parent with overlay
        if self.parent() and not self._sticky:
            self.setGeometry(self.parent().rect())

        # Create opacity effect for the entire drawer
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        # For sticky mode, make the widget transparent to mouse events outside drawer
        if self._sticky:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        # Initially hidden
        self.hide()

    def paintEvent(self, event):
        """Custom paint event to draw the dimmed background"""
        # Skip dark overlay for sticky drawers
        if self._sticky:
            super().paintEvent(event)
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fill the entire drawer with semi-transparent dark color
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        super().paintEvent(event)

    def show_widget(
        self, widget, side=DrawerSide.RIGHT, drawer_size=400, show_close_button=True
    ):
        """Show a widget in a drawer sliding from the specified side
        
        Args:
            widget: The widget to display in the drawer
            side: Which side to slide from (DrawerSide enum)
            drawer_size: Width for left/right drawers, height for top/bottom
            show_close_button: Whether to show the X close button
        """
        self._side = side
        self._drawer_size = drawer_size
        self._show_close_button = show_close_button

        # Register with drawer tracker for z-ordering
        if self.parent():
            self._z_index = _DrawerTracker.register(self.parent(), self, side)

        # Clear previous content
        if self._content_widget:
            self._content_widget.setParent(None)
            self._content_widget.deleteLater()
        if self._content_frame:
            self._content_frame.setParent(None)
            self._content_frame.deleteLater()

        # Create content frame that fills the drawer
        self._content_frame = QFrame(self)

        # Use system default window background color
        palette = QApplication.palette()
        bg_color = palette.color(QPalette.Window)
        self._content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color.name()};
                border: none;
            }}
        """)

        # Create the close button inside the content frame if requested
        if self._show_close_button:
            self.close_button = QPushButton("✕", self._content_frame)
            self.close_button.setStyleSheet("""
                QPushButton {
                    color: white;
                    font-size: 16px;
                    border: none;
                    background: rgba(60, 60, 60, 200);
                    border-radius: 12px;
                    min-width: 24px;
                    max-width: 24px;
                    min-height: 24px;
                    max-height: 24px;
                }
                QPushButton:hover {
                    background: rgba(80, 80, 80, 220);
                }
                QPushButton:pressed {
                    background: rgba(100, 100, 100, 240);
                }
            """)
            self.close_button.clicked.connect(self._close_drawer)
        else:
            self.close_button = None

        # Create layout for the frame
        if side in [DrawerSide.LEFT, DrawerSide.RIGHT]:
            layout = QVBoxLayout(self._content_frame)
        else:
            layout = QHBoxLayout(self._content_frame)

        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Store and add new widget to frame
        self._content_widget = widget
        self._content_widget.setParent(self._content_frame)
        layout.addWidget(self._content_widget)

        # Add stretch to center small widgets
        layout.addStretch()

        # Position elements before showing
        self._position_content()

        # Show and animate
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()

        # Connect to parent resize event if parent exists
        if self.parent():
            self.parent().installEventFilter(self)

        # Start slide-in animation
        self._animate_in()

    def _position_content(self):
        """Position the content frame and close button based on side"""
        if not self.parent():
            return

        parent_rect = self.parent().rect()
        parent_width = parent_rect.width()
        parent_height = parent_rect.height()
        
        # Calculate drawer size based on parent size and limits
        if self._side in [DrawerSide.LEFT, DrawerSide.RIGHT]:
            # for side drawers, limit width
            max_width = min(
                parent_width * 0.8, parent_width - 100
            )  # Max 80% or leave 100px margin
            actual_drawer_size = min(self._drawer_size, max_width)
        else:
            # For top/bottom drawers, limit height
            max_height = min(
                parent_height * 0.8, parent_height - 100
            )  # Max 80% or leave 100px margin
            actual_drawer_size = min(self._drawer_size, max_height)

        # For sticky mode, the DrawerWidget is only the size of the drawer panel
        # For non-sticky, it covers the whole parent (to capture outside clicks)
        if self._sticky:
            # Position the DrawerWidget itself to only cover the drawer area
            if self._side == DrawerSide.RIGHT:
                self.setGeometry(
                    parent_width - actual_drawer_size, 0,
                    actual_drawer_size, parent_height
                )
            elif self._side == DrawerSide.LEFT:
                self.setGeometry(0, 0, actual_drawer_size, parent_height)
            elif self._side == DrawerSide.TOP:
                self.setGeometry(0, 0, parent_width, actual_drawer_size)
            elif self._side == DrawerSide.BOTTOM:
                self.setGeometry(
                    0, parent_height - actual_drawer_size,
                    parent_width, actual_drawer_size
                )
            
            # Content frame fills the DrawerWidget in sticky mode
            if self._content_frame:
                self._content_frame.setGeometry(0, 0, self.width(), self.height())
                # Position close button
                if self.close_button:
                    if self._side == DrawerSide.RIGHT:
                        self.close_button.move(5, 5)
                    elif self._side == DrawerSide.LEFT:
                        self.close_button.move(self.width() - self.close_button.width() - 5, 5)
                    elif self._side == DrawerSide.TOP:
                        self.close_button.move(
                            self.width() - self.close_button.width() - 5,
                            self.height() - self.close_button.height() - 5
                        )
                    elif self._side == DrawerSide.BOTTOM:
                        self.close_button.move(self.width() - self.close_button.width() - 5, 5)
        else:
            # Non-sticky: DrawerWidget covers whole parent
            self.setGeometry(parent_rect)
            
            if self._content_frame:
                if self._side == DrawerSide.RIGHT:
                    self._content_frame.setGeometry(
                        parent_width - actual_drawer_size,
                        0,
                        actual_drawer_size,
                        parent_height,
                    )
                    # Close button in top-left of drawer content
                    if self.close_button:
                        self.close_button.move(5, 5)
                elif self._side == DrawerSide.LEFT:
                    self._content_frame.setGeometry(0, 0, actual_drawer_size, parent_height)
                    # Close button
                    if self.close_button:
                        self.close_button.move(
                            actual_drawer_size - self.close_button.width() - 5, 5
                        )
                elif self._side == DrawerSide.TOP:
                    self._content_frame.setGeometry(0, 0, parent_width, actual_drawer_size)
                    # Close button
                    if self.close_button:
                        self.close_button.move(
                            parent_width - self.close_button.width() - 5,  # X: Right-aligned
                            actual_drawer_size
                            - self.close_button.height()
                            - 5,  # Y: Bottom-aligned
                        )
                elif self._side == DrawerSide.BOTTOM:
                    self._content_frame.setGeometry(
                        0,
                        parent_height - actual_drawer_size,
                        parent_width,
                        actual_drawer_size,
                    )
                    # Close button in top-right of drawer content
                    if self.close_button:
                        self.close_button.move(
                            parent_width - self.close_button.width() - 5, 5
                        )

        if self.close_button:
            self.close_button.raise_()

    def _animate_in(self):
        """Animate the drawer sliding in"""
        if not self._content_frame:
            return

        # Set initial position (off-screen)
        start_rect = self._get_start_rect()
        end_rect = self._content_frame.geometry()

        self._content_frame.setGeometry(start_rect)

        # Fade in overlay
        self.opacity_effect.setOpacity(0)
        self._opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self._opacity_animation.setDuration(300)
        self._opacity_animation.setStartValue(0)
        self._opacity_animation.setEndValue(1)
        self._opacity_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._opacity_animation.start()

        # Slide in drawer (with close button inside)
        self._animation = QPropertyAnimation(self._content_frame, b"geometry")
        self._animation.setDuration(300)
        self._animation.setStartValue(start_rect)
        self._animation.setEndValue(end_rect)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.start()

    def _get_start_rect(self):
        """Get the starting rectangle for slide animation"""
        if not self._content_frame:
            return QRect()

        current_rect = self._content_frame.geometry()
        
        # For sticky mode, animation is relative to the drawer widget itself
        if self._sticky:
            if self._side == DrawerSide.RIGHT:
                return QRect(
                    current_rect.width(),  # Start off to the right
                    current_rect.y(),
                    current_rect.width(),
                    current_rect.height(),
                )
            elif self._side == DrawerSide.LEFT:
                return QRect(
                    -current_rect.width(),  # Start off to the left
                    current_rect.y(),
                    current_rect.width(),
                    current_rect.height(),
                )
            elif self._side == DrawerSide.TOP:
                return QRect(
                    current_rect.x(),
                    -current_rect.height(),  # Start above
                    current_rect.width(),
                    current_rect.height(),
                )
            elif self._side == DrawerSide.BOTTOM:
                return QRect(
                    current_rect.x(),
                    current_rect.height(),  # Start below
                    current_rect.width(),
                    current_rect.height(),
                )
        else:
            # Non-sticky: full overlay mode
            if self._side == DrawerSide.RIGHT:
                return QRect(
                    self.width(),
                    current_rect.y(),
                    current_rect.width(),
                    current_rect.height(),
                )
            elif self._side == DrawerSide.LEFT:
                return QRect(
                    -current_rect.width(),
                    current_rect.y(),
                    current_rect.width(),
                    current_rect.height(),
                )
            elif self._side == DrawerSide.TOP:
                return QRect(
                    current_rect.x(),
                    -current_rect.height(),
                    current_rect.width(),
                    current_rect.height(),
                )
            elif self._side == DrawerSide.BOTTOM:
                return QRect(
                    current_rect.x(),
                    self.height(),
                    current_rect.width(),
                    current_rect.height(),
                )

        return current_rect

    def _animate_out(self):
        """Animate the drawer sliding out"""
        if not self._content_frame:
            return

        start_rect = self._content_frame.geometry()
        end_rect = self._get_start_rect()

        # Fade out overlay
        self._opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self._opacity_animation.setDuration(250)
        self._opacity_animation.setStartValue(1)
        self._opacity_animation.setEndValue(0)
        self._opacity_animation.setEasingCurve(QEasingCurve.InCubic)
        self._opacity_animation.start()

        # Slide out drawer (with close button inside)
        self._animation = QPropertyAnimation(self._content_frame, b"geometry")
        self._animation.setDuration(250)
        self._animation.setStartValue(start_rect)
        self._animation.setEndValue(end_rect)
        self._animation.setEasingCurve(QEasingCurve.InCubic)
        self._animation.finished.connect(self._cleanup)
        self._animation.start()

    def eventFilter(self, obj, event):
        """Handle parent window resize events"""
        if obj == self.parent() and event.type() == QEvent.Resize:
            # Update drawer geometry and positioning when parent resizes
            self._position_content()
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """Close drawer when ESC is pressed"""
        if event.key() == Qt.Key_Escape:
            self._close_drawer()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _close_drawer(self):
        """Close the drawer with animation"""
        # Prevent multiple close calls
        if hasattr(self, "_closing") and self._closing:
            return

        self._closing = True

        if self._animation and self._animation.state() == QPropertyAnimation.Running:
            self._animation.stop()

        self._animate_out()

    def _cleanup(self):
        """Final cleanup when closing"""
        # Remove event filter
        if self.parent():
            self.parent().removeEventFilter(self)
            # Unregister from drawer tracker
            _DrawerTracker.unregister(self.parent(), self, self._side)

        if self._content_widget:
            self._content_widget.setParent(None)
            self._content_widget.deleteLater()
            self._content_widget = None
        if self._content_frame:
            self._content_frame.setParent(None)
            self._content_frame.deleteLater()
            self._content_frame = None
        
        # Emit closed signal before deleting
        self.closed.emit()
        self.deleteLater()

    def resizeEvent(self, event):
        """Handle window resize"""
        # Reposition and resize content (this will handle geometry for both modes)
        self._position_content()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse clicks on the drawer background"""
        if event.button() == Qt.LeftButton:
            # Sticky drawers don't close on outside click
            if self._sticky:
                super().mousePressEvent(event)
                return
                
            # Only close if animation is complete and we clicked outside content
            if (
                self._content_frame
                and (
                    not self._animation
                    or self._animation.state() != QPropertyAnimation.Running
                )
                and not self._content_frame.geometry().contains(event.pos())
            ):
                self._close_drawer()
                event.accept()
                return
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drawer Widget Demo")
        self.resize(1000, 700)
        
        # Create drawer manager for this window
        self.drawer_manager = DrawerManager(self)

        # Create main content
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Title
        title = QLabel("Drawer Widget Demo")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)

        # Demo buttons in a grid-like layout
        button_layout = QVBoxLayout()

        # Side buttons - Regular drawers
        side_label = QLabel("Regular Drawers (click outside to close)")
        side_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        button_layout.addWidget(side_label)
        
        side_layout = QHBoxLayout()

        btn_left = QPushButton("Left Drawer")
        btn_left.clicked.connect(lambda: self.show_drawer(DrawerSide.LEFT))

        btn_right = QPushButton("Right Drawer")
        btn_right.clicked.connect(lambda: self.show_drawer(DrawerSide.RIGHT))

        btn_top = QPushButton("Top Drawer")
        btn_top.clicked.connect(lambda: self.show_drawer(DrawerSide.TOP))

        btn_bottom = QPushButton("Bottom Drawer")
        btn_bottom.clicked.connect(lambda: self.show_drawer(DrawerSide.BOTTOM))

        side_layout.addWidget(btn_left)
        side_layout.addWidget(btn_right)
        side_layout.addWidget(btn_top)
        side_layout.addWidget(btn_bottom)

        # Content type buttons
        content_layout = QHBoxLayout()

        btn_form = QPushButton("Form Drawer")
        btn_form.clicked.connect(self.show_form_drawer)

        btn_text = QPushButton("Text Editor Drawer")
        btn_text.clicked.connect(self.show_text_drawer)

        btn_small = QPushButton("Small Widget Drawer")
        btn_small.clicked.connect(self.show_small_widget_drawer)

        btn_default = QPushButton("Default Styled Drawer")
        btn_default.clicked.connect(self.show_default_drawer)

        content_layout.addWidget(btn_form)
        content_layout.addWidget(btn_text)
        content_layout.addWidget(btn_small)
        content_layout.addWidget(btn_default)
        
        # Sticky drawer section
        sticky_label = QLabel("Sticky Drawers (no overlay, click outside doesn't close)")
        sticky_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;")
        button_layout.addWidget(sticky_label)
        
        sticky_layout = QHBoxLayout()
        
        btn_sticky_left = QPushButton("Sticky Left")
        btn_sticky_left.clicked.connect(lambda: self.show_sticky_drawer(DrawerSide.LEFT))
        
        btn_sticky_right = QPushButton("Sticky Right")
        btn_sticky_right.clicked.connect(lambda: self.show_sticky_drawer(DrawerSide.RIGHT))
        
        btn_sticky_top = QPushButton("Sticky Top")
        btn_sticky_top.clicked.connect(lambda: self.show_sticky_drawer(DrawerSide.TOP))
        
        btn_sticky_bottom = QPushButton("Sticky Bottom")
        btn_sticky_bottom.clicked.connect(lambda: self.show_sticky_drawer(DrawerSide.BOTTOM))
        
        sticky_layout.addWidget(btn_sticky_left)
        sticky_layout.addWidget(btn_sticky_right)
        sticky_layout.addWidget(btn_sticky_top)
        sticky_layout.addWidget(btn_sticky_bottom)
        
        # Multi-drawer demo section
        multi_label = QLabel("Multi-Drawer Demos")
        multi_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;")
        button_layout.addWidget(multi_label)
        
        multi_layout = QHBoxLayout()
        
        btn_multi_sticky = QPushButton("Open Both Sides (Sticky)")
        btn_multi_sticky.clicked.connect(self.show_multi_sticky_drawers)
        
        btn_stack_sticky = QPushButton("Stack Same Side (Sticky)")
        btn_stack_sticky.clicked.connect(self.show_stacked_drawers_sticky)
        
        btn_stack_regular = QPushButton("Stack Same Side (Regular)")
        btn_stack_regular.clicked.connect(self.show_stacked_drawers_regular)
        
        btn_close_all = QPushButton("Close All Sticky")
        btn_close_all.clicked.connect(self.close_all_sticky_drawers)
        btn_close_all.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                margin: 5px;
                border-radius: 6px;
                background: #dc3545;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background: #c82333;
            }
            QPushButton:pressed {
                background: #bd2130;
            }
        """)
        
        multi_layout.addWidget(btn_multi_sticky)
        multi_layout.addWidget(btn_stack_sticky)
        multi_layout.addWidget(btn_stack_regular)
        multi_layout.addWidget(btn_close_all)
        
        # Interaction test area
        test_label = QLabel("Test Area (verify clicks pass through with sticky drawers)")
        test_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;")
        button_layout.addWidget(test_label)
        
        test_layout = QHBoxLayout()
        
        self.test_input = QLineEdit()
        self.test_input.setPlaceholderText("Type here to test input passthrough...")
        self.test_input.setStyleSheet("padding: 10px; font-size: 14px;")
        
        test_btn = QPushButton("Click Me!")
        test_btn.clicked.connect(lambda: self.test_input.setText("Button clicked! ✓"))
        
        test_layout.addWidget(self.test_input)
        test_layout.addWidget(test_btn)

        button_layout.addLayout(side_layout)
        button_layout.addLayout(content_layout)
        button_layout.addLayout(sticky_layout)
        button_layout.addLayout(multi_layout)
        button_layout.addLayout(test_layout)

        layout.addLayout(button_layout)
        layout.addStretch()

        # Style buttons (except close all which has custom style)
        for btn in [
            btn_left,
            btn_right,
            btn_top,
            btn_bottom,
            btn_form,
            btn_text,
            btn_small,
            btn_default,
            btn_sticky_left,
            btn_sticky_right,
            btn_sticky_top,
            btn_sticky_bottom,
            btn_multi_sticky,
            btn_stack_sticky,
            btn_stack_regular,
            test_btn,
        ]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 20px;
                    font-size: 14px;
                    margin: 5px;
                    border-radius: 6px;
                    background: #007ACC;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background: #005A9F;
                }
                QPushButton:pressed {
                    background: #004080;
                }
            """)

    def show_drawer(self, side):
        """Show a simple drawer from the specified side"""
        label = QLabel(f"This is a {side.value} drawer!")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            font-size: 18px;
            color: white;
            background: #404040;
            border-radius: 8px;
            padding: 20px;
            margin: 10px;
        """)

        self.drawer_manager.show_drawer(label, side, size=350)

    def show_default_drawer(self):
        """Show a drawer with default system styling"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("Default System Styling")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")

        line_edit = QLineEdit()
        line_edit.setPlaceholderText("This uses system colors")

        button = QPushButton("System Styled Button")

        layout.addWidget(label)
        layout.addWidget(line_edit)
        layout.addWidget(button)

        self.drawer_manager.show_drawer(widget, DrawerSide.RIGHT, size=400)

    def show_form_drawer(self):
        """Show a form in a right drawer"""
        form = QWidget()
        layout = QVBoxLayout(form)

        title = QLabel("User Registration")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")

        name_input = QLineEdit()
        name_input.setPlaceholderText("Full Name")
        name_input.setStyleSheet("padding: 10px; font-size: 14px; border-radius: 4px;")

        email_input = QLineEdit()
        email_input.setPlaceholderText("Email Address")
        email_input.setStyleSheet("padding: 10px; font-size: 14px; border-radius: 4px;")

        phone_input = QLineEdit()
        phone_input.setPlaceholderText("Phone Number")
        phone_input.setStyleSheet("padding: 10px; font-size: 14px; border-radius: 4px;")

        submit_btn = QPushButton("Register")
        submit_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-size: 16px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)

        for widget in [title, name_input, email_input, phone_input, submit_btn]:
            layout.addWidget(widget)

        drawer = self.drawer_manager.show_drawer(form, DrawerSide.RIGHT, size=400)

        # Close drawer when submitted
        submit_btn.clicked.connect(drawer._close_drawer)

    def show_text_drawer(self):
        """Show a text editor in a left drawer"""
        text_widget = QWidget()
        layout = QVBoxLayout(text_widget)

        title = QLabel("Notes")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")

        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Write your notes here...")
        text_edit.setStyleSheet("""
            QTextEdit {
                background: #404040;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }
        """)

        save_btn = QPushButton("Save Notes")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #17a2b8;
                color: white;
                padding: 10px;
                border-radius: 4px;
                font-size: 14px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background: #138496;
            }
        """)

        layout.addWidget(title)
        layout.addWidget(text_edit)
        layout.addWidget(save_btn)

        self.drawer_manager.show_drawer(text_widget, DrawerSide.LEFT, size=450)

    def show_small_widget_drawer(self):
        """Show a small widget in a drawer to demonstrate auto-wrapping"""
        small_button = QPushButton("I'm a small widget!")
        small_button.setStyleSheet("""
            QPushButton {
                background: #fd7e14;
                color: white;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e8590c;
            }
        """)

        self.drawer_manager.show_drawer(small_button, DrawerSide.BOTTOM, size=300)

    def show_sticky_drawer(self, side):
        """Show a sticky drawer that doesn't close on outside click"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel(f"Sticky {side.value.capitalize()} Drawer")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #28a745;
            margin-bottom: 10px;
        """)
        
        info = QLabel("• No dark overlay\n• Click outside doesn't close\n• Use close button or ESC to close")
        info.setStyleSheet("font-size: 12px; color: #666; margin: 10px;")
        
        close_btn = QPushButton("Close This Drawer")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        
        layout.addWidget(label)
        layout.addWidget(info)
        layout.addWidget(close_btn)
        
        drawer = self.drawer_manager.show_drawer(widget, side, size=300, sticky=True)
        close_btn.clicked.connect(drawer._close_drawer)

    def show_multi_sticky_drawers(self):
        """Demonstrate opening multiple sticky drawers simultaneously"""
        # Left drawer
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_label = QLabel("Left Panel")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #17a2b8;")
        
        left_info = QLabel("This is a sticky left drawer.\nYou can interact with the main window\nand open more drawers!")
        left_info.setStyleSheet("font-size: 12px; margin: 10px;")
        
        left_close = QPushButton("Close Left")
        left_close.setStyleSheet("""
            QPushButton {
                background: #17a2b8; color: white; padding: 8px;
                border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background: #138496; }
        """)
        
        left_layout.addWidget(left_label)
        left_layout.addWidget(left_info)
        left_layout.addWidget(left_close)
        
        left_drawer = self.drawer_manager.show_drawer(left_widget, DrawerSide.LEFT, size=280, sticky=True)
        left_close.clicked.connect(left_drawer._close_drawer)
        
        # Right drawer
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        right_label = QLabel("Right Panel")
        right_label.setAlignment(Qt.AlignCenter)
        right_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #fd7e14;")
        
        right_info = QLabel("Both drawers are open!\nNo overlay blocking interaction.\nTry clicking the test area below.")
        right_info.setStyleSheet("font-size: 12px; margin: 10px;")
        
        right_close = QPushButton("Close Right")
        right_close.setStyleSheet("""
            QPushButton {
                background: #fd7e14; color: white; padding: 8px;
                border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background: #e8590c; }
        """)
        
        right_layout.addWidget(right_label)
        right_layout.addWidget(right_info)
        right_layout.addWidget(right_close)
        
        right_drawer = self.drawer_manager.show_drawer(right_widget, DrawerSide.RIGHT, size=280, sticky=True)
        right_close.clicked.connect(right_drawer._close_drawer)

    def show_stacked_drawers_sticky(self):
        """Demonstrate stacking multiple sticky drawers on the same side (can close in any order)"""
        # First drawer (larger, will be behind)
        first_widget = QWidget()
        first_layout = QVBoxLayout(first_widget)
        
        first_label = QLabel("First Drawer (Behind)")
        first_label.setAlignment(Qt.AlignCenter)
        first_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #6c757d;")
        
        first_info = QLabel("Sticky mode - you can close\nthis one even with 2nd open!\nBoth drawers are independent.")
        first_info.setStyleSheet("font-size: 12px; margin: 10px;")
        
        first_close = QPushButton("Close First")
        first_close.setStyleSheet("""
            QPushButton {
                background: #6c757d; color: white; padding: 8px;
                border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background: #545b62; }
        """)
        
        first_layout.addWidget(first_label)
        first_layout.addWidget(first_info)
        first_layout.addWidget(first_close)
        
        first_drawer = self.drawer_manager.show_drawer(first_widget, DrawerSide.RIGHT, size=400, sticky=True)
        first_close.clicked.connect(first_drawer._close_drawer)
        
        # Second drawer (smaller, will be on top) - delayed slightly
        from PySide6.QtCore import QTimer
        QTimer.singleShot(300, lambda: self._show_second_stacked_drawer_sticky())

    def _show_second_stacked_drawer_sticky(self):
        """Helper to show second stacked sticky drawer"""
        second_widget = QWidget()
        second_layout = QVBoxLayout(second_widget)
        
        second_label = QLabel("Second Drawer (On Top)")
        second_label.setAlignment(Qt.AlignCenter)
        second_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #dc3545;")
        
        second_info = QLabel("Sticky: Close in any order!\nYou can close the first drawer\nwhile this one is still open.")
        second_info.setStyleSheet("font-size: 12px; margin: 10px;")
        
        second_close = QPushButton("Close Second")
        second_close.setStyleSheet("""
            QPushButton {
                background: #dc3545; color: white; padding: 8px;
                border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background: #c82333; }
        """)
        
        second_layout.addWidget(second_label)
        second_layout.addWidget(second_info)
        second_layout.addWidget(second_close)
        
        second_drawer = self.drawer_manager.show_drawer(second_widget, DrawerSide.RIGHT, size=250, sticky=True)
        second_close.clicked.connect(second_drawer._close_drawer)

    def show_stacked_drawers_regular(self):
        """Demonstrate stacking multiple regular (non-sticky) drawers - must close in LIFO order"""
        # First drawer (larger, will be behind with its own overlay)
        first_widget = QWidget()
        first_layout = QVBoxLayout(first_widget)
        
        first_label = QLabel("First Drawer (Behind)")
        first_label.setAlignment(Qt.AlignCenter)
        first_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #6c757d;")
        
        first_info = QLabel("Regular drawer with overlay.\nYou cannot interact with this\nuntil the 2nd drawer is closed!")
        first_info.setStyleSheet("font-size: 12px; margin: 10px;")
        
        first_close = QPushButton("Close First (blocked!)")
        first_close.setStyleSheet("""
            QPushButton {
                background: #6c757d; color: white; padding: 8px;
                border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background: #545b62; }
        """)
        
        first_layout.addWidget(first_label)
        first_layout.addWidget(first_info)
        first_layout.addWidget(first_close)
        
        first_drawer = self.drawer_manager.show_drawer(first_widget, DrawerSide.RIGHT, size=400, sticky=False)
        first_close.clicked.connect(first_drawer._close_drawer)
        
        # Second drawer (smaller, will be on top with its own overlay) - delayed slightly
        from PySide6.QtCore import QTimer
        QTimer.singleShot(300, lambda: self._show_second_stacked_drawer_regular())

    def _show_second_stacked_drawer_regular(self):
        """Helper to show second stacked regular drawer"""
        second_widget = QWidget()
        second_layout = QVBoxLayout(second_widget)
        
        second_label = QLabel("Second Drawer (On Top)")
        second_label.setAlignment(Qt.AlignCenter)
        second_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #dc3545;")
        
        second_info = QLabel("This overlay blocks the first!\nClose this first, then you can\ninteract with the drawer behind.")
        second_info.setStyleSheet("font-size: 12px; margin: 10px;")
        
        second_close = QPushButton("Close Second")
        second_close.setStyleSheet("""
            QPushButton {
                background: #dc3545; color: white; padding: 8px;
                border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background: #c82333; }
        """)
        
        second_layout.addWidget(second_label)
        second_layout.addWidget(second_info)
        second_layout.addWidget(second_close)
        
        second_drawer = self.drawer_manager.show_drawer(second_widget, DrawerSide.RIGHT, size=250, sticky=False)
        second_close.clicked.connect(second_drawer._close_drawer)

    def close_all_sticky_drawers(self):
        """Close all open sticky drawers"""
        self.drawer_manager.close_all(sticky_only=True)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set nice font for the application
    font = QFont()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
