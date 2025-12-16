import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QGraphicsOpacityEffect,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QEvent
from PySide6.QtGui import QColor, QFont, QKeyEvent, QPainter, QPalette


class OverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self._content_widget = None
        self._animation = None

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
        # Make overlay cover parent
        if self.parent():
            self.setGeometry(self.parent().rect())

        # Set window flags and attributes for proper overlay behavior
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Create opacity effect for the entire overlay
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        # Floating close button (top-right corner)
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
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fill the entire overlay with semi-transparent dark color
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        super().paintEvent(event)

    def show_widget(self, widget):
        """Show a widget centered in the overlay"""
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
        if self.parent():
            # Update overlay geometry first
            self.setGeometry(self.parent().rect())

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
        if self._content_widget:
            self._content_widget.setParent(None)
            self._content_widget.deleteLater()
            self._content_widget = None
        self.deleteLater()

    def resizeEvent(self, event):
        """Handle window resize"""
        self._position_content()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse clicks on the overlay background"""
        if event.button() == Qt.LeftButton:
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
        self.setWindowTitle("Overlay with Dimming Effect Demo")
        self.resize(800, 600)

        # Create main content
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Demo buttons
        btn_default = QPushButton("Show Default Styled Widget")
        btn_default.clicked.connect(self.show_default_overlay)

        btn_custom = QPushButton("Show Custom Styled Widget")
        btn_custom.clicked.connect(self.show_custom_overlay)

        btn_transparent = QPushButton("Show Transparent Widget")
        btn_transparent.clicked.connect(self.show_transparent_overlay)

        layout.addWidget(btn_default)
        layout.addWidget(btn_custom)
        layout.addWidget(btn_transparent)
        layout.addStretch()

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

        overlay = OverlayWidget(self)
        overlay.show_widget(widget)
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

        overlay = OverlayWidget(self)
        overlay.show_widget(widget)
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

        overlay = OverlayWidget(self)
        overlay.show_widget(widget)
        button.clicked.connect(overlay._close_overlay)


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
