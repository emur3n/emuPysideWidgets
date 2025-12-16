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
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QEvent, QRect
from PySide6.QtGui import QColor, QPalette, QFont, QKeyEvent, QPainter
from enum import Enum


class DrawerSide(Enum):
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


class DrawerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self._content_widget = None
        self._content_frame = None
        self._animation = None
        self._side = DrawerSide.RIGHT
        self._drawer_size = 400  # Default drawer width/height
        self._closing = False  # Flag to prevent multiple closes
        self._opacity_animation = None  # Store opacity animation reference
        self._show_close_button = True  # Default to showing close button

        # Enable key events and make sure we get focus
        self.setFocusPolicy(Qt.StrongFocus)

    def setup_ui(self):
        # Make drawer cover parent
        if self.parent():
            self.setGeometry(self.parent().rect())

        # Create opacity effect for the entire drawer
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        # Initially hidden
        self.hide()

    def paintEvent(self, event):
        """Custom paint event to draw the dimmed background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fill the entire drawer with semi-transparent dark color
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        super().paintEvent(event)

    def show_widget(
        self, widget, side=DrawerSide.RIGHT, drawer_size=400, show_close_button=True
    ):
        """Show a widget in a drawer sliding from the specified side"""
        self._side = side
        self._drawer_size = drawer_size
        self._show_close_button = show_close_button

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

        # Update drawer geometry first
        self.setGeometry(self.parent().rect())

        if self._content_frame:
            # Calculate drawer size based on parent size and limits
            parent_width = self.width()
            parent_height = self.height()

            # Limit drawer size to reasonable bounds
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

        if self._content_widget:
            self._content_widget.setParent(None)
            self._content_widget.deleteLater()
            self._content_widget = None
        if self._content_frame:
            self._content_frame.setParent(None)
            self._content_frame.deleteLater()
            self._content_frame = None
        self.deleteLater()

    def resizeEvent(self, event):
        """Handle window resize"""
        # Update drawer geometry to match parent
        if self.parent():
            self.setGeometry(self.parent().rect())

        # Reposition and resize content
        self._position_content()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse clicks on the drawer background"""
        if event.button() == Qt.LeftButton:
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

        # Side buttons
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

        button_layout.addLayout(side_layout)
        button_layout.addLayout(content_layout)

        layout.addLayout(button_layout)
        layout.addStretch()

        # Style buttons
        for btn in [
            btn_left,
            btn_right,
            btn_top,
            btn_bottom,
            btn_form,
            btn_text,
            btn_small,
            btn_default,
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

        drawer = DrawerWidget(self)
        drawer.show_widget(label, side, 350, show_close_button=True)

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

        drawer = DrawerWidget(self)
        drawer.show_widget(widget, DrawerSide.RIGHT, 400)

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

        drawer = DrawerWidget(self)
        drawer.show_widget(form, DrawerSide.RIGHT, 400)

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

        drawer = DrawerWidget(self)
        drawer.show_widget(text_widget, DrawerSide.LEFT, 450)

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

        drawer = DrawerWidget(self)
        drawer.show_widget(small_button, DrawerSide.BOTTOM, 300)


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
