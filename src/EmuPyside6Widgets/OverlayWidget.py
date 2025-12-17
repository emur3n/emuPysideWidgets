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
    QGraphicsOpacityEffect,
    QFrame,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QEvent, Signal
from PySide6.QtGui import QColor, QFont, QKeyEvent, QPainter, QPalette


# Internal tracker for overlay z-ordering
class _OverlayTracker:
    """Internal tracker for overlay z-ordering"""
    _instances = {}  # parent_id -> [overlays]
    _z_counter = {}  # parent_id -> counter
    
    @classmethod
    def register(cls, parent, overlay):
        """Register an overlay and get its z-index"""
        parent_id = id(parent)
        if parent_id not in cls._instances:
            cls._instances[parent_id] = []
            cls._z_counter[parent_id] = 0
        
        cls._instances[parent_id].append(overlay)
        cls._z_counter[parent_id] += 1
        return cls._z_counter[parent_id]
    
    @classmethod
    def unregister(cls, parent, overlay):
        """Remove an overlay from tracking"""
        parent_id = id(parent)
        if parent_id in cls._instances:
            if overlay in cls._instances[parent_id]:
                cls._instances[parent_id].remove(overlay)
    
    @classmethod
    def get_overlays(cls, parent):
        """Get all overlays for a parent"""
        parent_id = id(parent)
        return cls._instances.get(parent_id, [])
    
    @classmethod
    def is_topmost(cls, parent, overlay):
        """Check if this overlay is the topmost"""
        overlays = cls.get_overlays(parent)
        return len(overlays) == 0 or overlays[-1] == overlay


class OverlayManager:
    """
    Manager for showing overlay modals within a parent widget.
    
    Usage:
        class MainWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.overlay_manager = OverlayManager(self)
                
            def show_dialog(self):
                widget = DialogWidget()
                self.overlay_manager.show_overlay(widget, sticky=True)
    """
    
    def __init__(self, parent):
        """
        Initialize the overlay manager.
        
        Args:
            parent: The parent widget where overlays will be shown
        """
        self._parent = parent
        self._overlays = []
    
    def show_overlay(self, widget, sticky=False, nobackground=False):
        """
        Show a widget in a centered overlay.
        
        Args:
            widget: The widget to display in the overlay
            sticky: If True, overlay won't close on outside click
            nobackground: If True, no dark background overlay (allows interaction behind)
        
        Returns:
            The OverlayWidget instance
        """
        overlay = OverlayWidget(self._parent, sticky=sticky, nobackground=nobackground)
        overlay.show_widget(widget)
        
        self._overlays.append(overlay)
        overlay.closed.connect(lambda: self._on_overlay_closed(overlay))
        
        return overlay
    
    def _on_overlay_closed(self, overlay):
        """Handle overlay closed"""
        if overlay in self._overlays:
            self._overlays.remove(overlay)
    
    def close_all(self, nobackground_only=False):
        """
        Close all overlays.
        
        Args:
            nobackground_only: Only close nobackground overlays
        """
        overlays_to_close = self._overlays.copy()
        for overlay in overlays_to_close:
            if nobackground_only and not overlay._nobackground:
                continue
            overlay._close_overlay()
    
    def get_open_overlays(self):
        """
        Get list of open overlays.
        
        Returns:
            List of open OverlayWidget instances
        """
        return self._overlays.copy()
    
    @property
    def parent(self):
        """Get the parent widget"""
        return self._parent


class OverlayWidget(QWidget):
    """
    An overlay widget that displays content centered with a dimmed background.
    
    Args:
        parent: Parent widget
        sticky: If True, overlay won't close on outside clicks. Must use close button or ESC.
        nobackground: If True, creates only the modal-sized widget without full overlay.
                     Allows interaction with overlays behind. Useful for multi-modal scenarios.
    """
    
    closed = Signal()  # Emitted when overlay is closed
    
    def __init__(self, parent=None, sticky=False, nobackground=False):
        super().__init__(parent)
        self._sticky = sticky
        self._nobackground = nobackground
        self._z_index = 0
        self.setup_ui()
        self._content_widget = None
        self._animation = None
        self._closing = False  # Prevent multiple closes

        # Enable key events and make sure we get focus
        self.setFocusPolicy(Qt.StrongFocus)

        # Track parent resize events if parent exists
        if parent:
            parent.installEventFilter(self)

    def eventFilter(self, source, event):
        """Handle parent resize events"""
        if source == self.parent() and event.type() == QEvent.Resize:
            self._position_content()
        return super().eventFilter(source, event)

    def setup_ui(self):
        # For nobackground mode, we don't cover the whole parent initially
        # Geometry will be set when content is shown
        if self.parent() and not self._nobackground:
            self.setGeometry(self.parent().rect())

        # Set window flags and attributes for proper overlay behavior
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Create opacity effect for the entire overlay
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        # Close button - will be positioned based on mode
        self.close_button = QPushButton("✕", self)
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
        self.close_button.clicked.connect(self._close_overlay)

        # Initially hidden
        self.hide()

    def paintEvent(self, event):
        """Custom paint event to draw the dimmed background"""
        # Skip dark overlay for nobackground mode
        if self._nobackground:
            super().paintEvent(event)
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fill the entire overlay with semi-transparent dark color
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        super().paintEvent(event)

    def show_widget(self, widget):
        """Show a widget centered in the overlay"""
        # Register with overlay tracker for z-ordering
        if self.parent():
            self._z_index = _OverlayTracker.register(self.parent(), self)
        
        # Clear previous content
        if self._content_widget:
            self._content_widget.setParent(None)
            self._content_widget.deleteLater()

        # Store and add new widget directly to overlay
        self._content_widget = widget
        self._content_widget.setParent(self)

        # Ensure widget gets proper system background color if it doesn't have one set
        if not widget.styleSheet() or "background" not in widget.styleSheet():
            # Get the system default window background color
            palette = QApplication.palette()
            bg_color = palette.color(QPalette.Window)
            widget.setStyleSheet(f"QWidget {{ background-color: {bg_color.name()}; }}")

        self._content_widget.raise_()  # Ensure it's above the dimmed background

        # Position elements before showing
        self._position_content()

        # Show and animate
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()

        # Start fade-in animation
        self.opacity_effect.setOpacity(0)
        self._animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self._animation.setDuration(250)
        self._animation.setStartValue(0)
        self._animation.setEndValue(1)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.start()

    def keyPressEvent(self, event):
        """Close overlay when ESC is pressed"""
        if event.key() == Qt.Key_Escape:
            self._close_overlay()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _position_content(self):
        """Position the content widget and close button"""
        if not self.parent():
            return
            
        parent_rect = self.parent().rect()
        parent_width = parent_rect.width()
        parent_height = parent_rect.height()
        
        if self._nobackground:
            # In nobackground mode, overlay widget is only the size of the content + close button
            if self._content_widget:
                content_width = self._content_widget.width()
                content_height = self._content_widget.height()
                
                # Calculate centered position in parent
                center_x = (parent_width - content_width) // 2
                center_y = (parent_height - content_height) // 2
                
                # Add padding for close button (top-right of content)
                padding = 30  # Space for close button
                
                # Set overlay geometry to just wrap the content
                self.setGeometry(
                    center_x - padding,
                    center_y - padding,
                    content_width + padding * 2,
                    content_height + padding * 2
                )
                
                # Position content widget centered within the overlay
                self._content_widget.move(padding, padding)
                
                # Position close button at top-right of content
                self.close_button.move(
                    content_width + padding - 5,
                    padding - self.close_button.height() + 5
                )
        else:
            # Standard mode: overlay covers whole parent
            self.setGeometry(parent_rect)

            if self._content_widget:
                # Center the widget
                self._content_widget.move(
                    self.width() // 2 - self._content_widget.width() // 2,
                    self.height() // 2 - self._content_widget.height() // 2,
                )

            # Position close button in top-right with margin
            self.close_button.move(self.width() - self.close_button.width() - 20, 20)
        
        self.close_button.raise_()

    def _close_overlay(self):
        """Close the overlay with animation"""
        # Prevent multiple close calls
        if self._closing:
            return
        self._closing = True
        
        if self._animation and self._animation.state() == QPropertyAnimation.Running:
            self._animation.stop()

        self._animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self._animation.setDuration(200)
        self._animation.setStartValue(1)
        self._animation.setEndValue(0)
        self._animation.setEasingCurve(QEasingCurve.InCubic)
        self._animation.finished.connect(self._cleanup)
        self._animation.start()

    def _cleanup(self):
        """Final cleanup when closing"""
        # Unregister from overlay tracker
        if self.parent():
            _OverlayTracker.unregister(self.parent(), self)
            self.parent().removeEventFilter(self)
        
        if self._content_widget:
            self._content_widget.setParent(None)
            self._content_widget.deleteLater()
            self._content_widget = None
        
        # Emit closed signal before deleting
        self.closed.emit()
        self.deleteLater()

    def resizeEvent(self, event):
        """Handle window resize"""
        self._position_content()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse clicks on the overlay background"""
        if event.button() == Qt.LeftButton:
            # Sticky overlays don't close on outside click
            if self._sticky:
                super().mousePressEvent(event)
                return
            
            # If we clicked outside content (on overlay background), close it
            if (
                self._content_widget
                and not self._content_widget.geometry().contains(event.pos())
                and not self.close_button.geometry().contains(event.pos())
            ):
                self._close_overlay()
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Overlay Widget Demo")
        self.resize(900, 700)
        
        # Create overlay manager for this window
        self.overlay_manager = OverlayManager(self)

        # Create main content
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Overlay Widget Demo")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Regular overlays section
        regular_label = QLabel("Regular Overlays (click outside to close)")
        regular_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(regular_label)

        regular_layout = QHBoxLayout()
        
        btn_default = QPushButton("Default Styled")
        btn_default.clicked.connect(self.show_default_overlay)

        btn_custom = QPushButton("Custom Styled")
        btn_custom.clicked.connect(self.show_custom_overlay)

        btn_transparent = QPushButton("Transparent")
        btn_transparent.clicked.connect(self.show_transparent_overlay)

        regular_layout.addWidget(btn_default)
        regular_layout.addWidget(btn_custom)
        regular_layout.addWidget(btn_transparent)
        layout.addLayout(regular_layout)
        
        # Sticky overlays section
        sticky_label = QLabel("Sticky Overlays (click outside doesn't close)")
        sticky_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;")
        layout.addWidget(sticky_label)
        
        sticky_layout = QHBoxLayout()
        
        btn_sticky = QPushButton("Sticky Modal")
        btn_sticky.clicked.connect(self.show_sticky_overlay)
        
        btn_sticky_custom = QPushButton("Sticky Custom")
        btn_sticky_custom.clicked.connect(self.show_sticky_custom_overlay)
        
        sticky_layout.addWidget(btn_sticky)
        sticky_layout.addWidget(btn_sticky_custom)
        layout.addLayout(sticky_layout)
        
        # Multi-overlay section
        multi_label = QLabel("Multi-Overlay Demos")
        multi_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;")
        layout.addWidget(multi_label)
        
        multi_layout = QHBoxLayout()
        
        btn_multi_regular = QPushButton("Stack Overlays (Regular)")
        btn_multi_regular.clicked.connect(self.show_stacked_overlays_regular)
        
        btn_multi_nobackground = QPushButton("Stack Overlays (No Background)")
        btn_multi_nobackground.clicked.connect(self.show_stacked_overlays_nobackground)
        
        btn_close_all = QPushButton("Close All No-Background")
        btn_close_all.clicked.connect(self.close_all_nobackground_overlays)
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
        
        multi_layout.addWidget(btn_multi_regular)
        multi_layout.addWidget(btn_multi_nobackground)
        multi_layout.addWidget(btn_close_all)
        layout.addLayout(multi_layout)
        
        # Test area
        test_label = QLabel("Test Area (verify clicks pass through with no-background overlays)")
        test_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;")
        layout.addWidget(test_label)
        
        test_layout = QHBoxLayout()
        
        self.test_input = QLineEdit()
        self.test_input.setPlaceholderText("Type here to test input passthrough...")
        self.test_input.setStyleSheet("padding: 10px; font-size: 14px;")
        
        test_btn = QPushButton("Click Me!")
        test_btn.clicked.connect(lambda: self.test_input.setText("Button clicked! ✓"))
        
        test_layout.addWidget(self.test_input)
        test_layout.addWidget(test_btn)
        layout.addLayout(test_layout)
        
        layout.addStretch()
        
        # Style buttons
        for btn in [
            btn_default,
            btn_custom,
            btn_transparent,
            btn_sticky,
            btn_sticky_custom,
            btn_multi_regular,
            btn_multi_nobackground,
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

    def show_default_overlay(self):
        """Shows widget with default OS styling"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("Default OS Styling\n(Background comes from system theme)")
        label.setAlignment(Qt.AlignCenter)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText("Default QLineEdit")

        button = QPushButton("Close")

        layout.addWidget(label)
        layout.addWidget(line_edit)
        layout.addWidget(button)
        widget.setFixedSize(300, 200)

        overlay = self.overlay_manager.show_overlay(widget)
        button.clicked.connect(overlay._close_overlay)

    def show_custom_overlay(self):
        """Shows widget with custom styling"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 8px;
                padding: 15px;
            }
            QLabel {
                color: #333;
                font-weight: bold;
            }
            QLineEdit {
                border: 1px solid #ccc;
                padding: 5px;
            }
            QPushButton {
                background: #4CAF50;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
        """)
        layout = QVBoxLayout(widget)

        label = QLabel("Custom Styled Widget\n(White background)")
        label.setAlignment(Qt.AlignCenter)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText("Custom QLineEdit")

        button = QPushButton("Close")

        layout.addWidget(label)
        layout.addWidget(line_edit)
        layout.addWidget(button)
        widget.setFixedSize(300, 200)

        overlay = self.overlay_manager.show_overlay(widget)
        button.clicked.connect(overlay._close_overlay)

    def show_transparent_overlay(self):
        """Shows widget with transparent background"""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)

        label = QLabel("Transparent Background Widget")
        label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                background: rgba(0, 0, 0, 150);
                padding: 10px;
                border-radius: 4px;
            }
        """)
        label.setAlignment(Qt.AlignCenter)

        button = QPushButton("Close")
        button.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 200);
                color: black;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
        """)

        layout.addWidget(label)
        layout.addWidget(button)
        widget.setFixedSize(300, 150)

        overlay = self.overlay_manager.show_overlay(widget)
        button.clicked.connect(overlay._close_overlay)

    def show_sticky_overlay(self):
        """Shows a sticky overlay that doesn't close on outside click"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("Sticky Modal")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold; color: #28a745;")

        info = QLabel("• Click outside doesn't close\n• Use close button or ESC to close\n• Dark overlay still blocks interaction")
        info.setStyleSheet("font-size: 12px; color: #666; margin: 10px;")

        button = QPushButton("Close Modal")
        button.setStyleSheet("""
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
        layout.addWidget(button)
        widget.setFixedSize(320, 200)

        overlay = self.overlay_manager.show_overlay(widget, sticky=True)
        button.clicked.connect(overlay._close_overlay)

    def show_sticky_custom_overlay(self):
        """Shows a sticky overlay with custom styling"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background: #2d2d2d;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        layout = QVBoxLayout(widget)

        label = QLabel("Dark Sticky Modal")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold; color: #fd7e14;")

        info = QLabel("Custom styled sticky overlay\nwith dark theme")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("font-size: 12px; color: #aaa; margin: 10px;")

        button = QPushButton("Dismiss")
        button.setStyleSheet("""
            QPushButton {
                background: #fd7e14;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background: #e8590c;
            }
        """)

        layout.addWidget(label)
        layout.addWidget(info)
        layout.addWidget(button)
        widget.setFixedSize(300, 180)

        overlay = self.overlay_manager.show_overlay(widget, sticky=True)
        button.clicked.connect(overlay._close_overlay)

    def show_stacked_overlays_regular(self):
        """Demonstrate stacking regular overlays (LIFO close order)"""
        # First overlay
        widget1 = QWidget()
        widget1.setStyleSheet("""
            QWidget {
                background: #6c757d;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        layout1 = QVBoxLayout(widget1)

        label1 = QLabel("First Modal (Behind)")
        label1.setAlignment(Qt.AlignCenter)
        label1.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")

        info1 = QLabel("This modal is blocked by\nthe second modal's overlay.\nClose the second one first!")
        info1.setAlignment(Qt.AlignCenter)
        info1.setStyleSheet("font-size: 12px; color: #ddd; margin: 10px;")

        btn1 = QPushButton("Close First (blocked)")
        btn1.setStyleSheet("""
            QPushButton {
                background: #495057; color: white; padding: 8px;
                border-radius: 4px; border: none;
            }
            QPushButton:hover { background: #343a40; }
        """)

        layout1.addWidget(label1)
        layout1.addWidget(info1)
        layout1.addWidget(btn1)
        widget1.setFixedSize(300, 200)

        overlay1 = self.overlay_manager.show_overlay(widget1)
        btn1.clicked.connect(overlay1._close_overlay)

        # Second overlay (on top) - delayed slightly
        from PySide6.QtCore import QTimer
        QTimer.singleShot(300, lambda: self._show_second_regular_overlay())

    def _show_second_regular_overlay(self):
        """Helper for second regular overlay"""
        widget2 = QWidget()
        widget2.setStyleSheet("""
            QWidget {
                background: #dc3545;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        layout2 = QVBoxLayout(widget2)

        label2 = QLabel("Second Modal (On Top)")
        label2.setAlignment(Qt.AlignCenter)
        label2.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")

        info2 = QLabel("Close this first!\nIts overlay blocks the first modal.")
        info2.setAlignment(Qt.AlignCenter)
        info2.setStyleSheet("font-size: 12px; color: #ffcccb; margin: 10px;")

        btn2 = QPushButton("Close Second")
        btn2.setStyleSheet("""
            QPushButton {
                background: #c82333; color: white; padding: 8px;
                border-radius: 4px; border: none;
            }
            QPushButton:hover { background: #bd2130; }
        """)

        layout2.addWidget(label2)
        layout2.addWidget(info2)
        layout2.addWidget(btn2)
        widget2.setFixedSize(280, 180)

        overlay2 = self.overlay_manager.show_overlay(widget2)
        btn2.clicked.connect(overlay2._close_overlay)

    def show_stacked_overlays_nobackground(self):
        """Demonstrate stacking overlays with nobackground (can close in any order)"""
        # First overlay (larger)
        widget1 = QWidget()
        widget1.setStyleSheet("""
            QWidget {
                background: #17a2b8;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        layout1 = QVBoxLayout(widget1)

        label1 = QLabel("First Modal")
        label1.setAlignment(Qt.AlignCenter)
        label1.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")

        info1 = QLabel("No background mode!\nYou CAN close this even\nwith the second modal open.")
        info1.setAlignment(Qt.AlignCenter)
        info1.setStyleSheet("font-size: 12px; color: #d1ecf1; margin: 10px;")

        btn1 = QPushButton("Close First")
        btn1.setStyleSheet("""
            QPushButton {
                background: #138496; color: white; padding: 8px;
                border-radius: 4px; border: none;
            }
            QPushButton:hover { background: #117a8b; }
        """)

        layout1.addWidget(label1)
        layout1.addWidget(info1)
        layout1.addWidget(btn1)
        widget1.setFixedSize(320, 200)

        overlay1 = self.overlay_manager.show_overlay(widget1, sticky=True, nobackground=True)
        btn1.clicked.connect(overlay1._close_overlay)

        # Second overlay (smaller, positioned differently)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(300, lambda: self._show_second_nobackground_overlay())

    def _show_second_nobackground_overlay(self):
        """Helper for second nobackground overlay"""
        widget2 = QWidget()
        widget2.setStyleSheet("""
            QWidget {
                background: #28a745;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        layout2 = QVBoxLayout(widget2)

        label2 = QLabel("Second Modal")
        label2.setAlignment(Qt.AlignCenter)
        label2.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")

        info2 = QLabel("Close in any order!\nTry the test area below too.")
        info2.setAlignment(Qt.AlignCenter)
        info2.setStyleSheet("font-size: 12px; color: #d4edda; margin: 10px;")

        btn2 = QPushButton("Close Second")
        btn2.setStyleSheet("""
            QPushButton {
                background: #218838; color: white; padding: 8px;
                border-radius: 4px; border: none;
            }
            QPushButton:hover { background: #1e7e34; }
        """)

        layout2.addWidget(label2)
        layout2.addWidget(info2)
        layout2.addWidget(btn2)
        widget2.setFixedSize(260, 160)

        overlay2 = self.overlay_manager.show_overlay(widget2, sticky=True, nobackground=True)
        btn2.clicked.connect(overlay2._close_overlay)

    def close_all_nobackground_overlays(self):
        """Close all open no-background overlays"""
        self.overlay_manager.close_all(nobackground_only=True)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set nice font for the application
    font = QFont()
    font.setFamily("Arial")
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
