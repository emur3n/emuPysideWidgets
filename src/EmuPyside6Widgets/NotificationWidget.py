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
    QFrame,
    QGraphicsOpacityEffect,
    QSizePolicy,
)
from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QEvent,
    QRect,
    QTimer,
    Signal,
    QParallelAnimationGroup,
    QPoint,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPalette, QEnterEvent
from enum import Enum


class NotificationZone(Enum):
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


class NotificationSeverity(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SeverityStyle:
    """
    Style configuration for a notification severity level.
    
    Allows customization of background color, border color, text color, and duration.
    
    Usage:
        # Get default style
        style = SeverityStyle.default(NotificationSeverity.INFO)
        
        # Create custom style
        style = SeverityStyle(bg="#ff0000", border="#cc0000", text="#ffffff", duration=5000)
    """
    
    # Default configurations
    _DEFAULTS = {
        NotificationSeverity.INFO: {"bg": "#3498db", "border": "#2980b9", "text": "#ffffff", "duration": 3000},
        NotificationSeverity.SUCCESS: {"bg": "#27ae60", "border": "#1e8449", "text": "#ffffff", "duration": 3000},
        NotificationSeverity.WARNING: {"bg": "#f39c12", "border": "#d68910", "text": "#ffffff", "duration": 5000},
        NotificationSeverity.ERROR: {"bg": "#e74c3c", "border": "#c0392b", "text": "#ffffff", "duration": 7000},
        NotificationSeverity.CRITICAL: {"bg": "#8e44ad", "border": "#6c3483", "text": "#ffffff", "duration": 0},
    }
    
    def __init__(self, bg="#3498db", border="#2980b9", text="#ffffff", duration=3000):
        """
        Initialize a severity style.
        
        Args:
            bg: Background color (CSS color string)
            border: Border color (CSS color string)
            text: Text color (CSS color string)
            duration: Auto-dismiss duration in ms (0 = no auto-dismiss)
        """
        self.bg = bg
        self.border = border
        self.text = text
        self.duration = duration
    
    @classmethod
    def default(cls, severity):
        """Get the default style for a severity level"""
        config = cls._DEFAULTS.get(severity, cls._DEFAULTS[NotificationSeverity.INFO])
        return cls(**config)
    
    def copy(self):
        """Create a copy of this style"""
        return SeverityStyle(self.bg, self.border, self.text, self.duration)
    
    def to_dict(self):
        """Convert to dictionary format"""
        return {"bg": self.bg, "border": self.border, "text": self.text}


# Default durations (for backwards compatibility)
SEVERITY_DURATIONS = {
    NotificationSeverity.INFO: 3000,
    NotificationSeverity.SUCCESS: 3000,
    NotificationSeverity.WARNING: 5000,
    NotificationSeverity.ERROR: 7000,
    NotificationSeverity.CRITICAL: 0,  # 0 = no auto-dismiss
}

# Default colors (for backwards compatibility)
SEVERITY_COLORS = {
    NotificationSeverity.INFO: {"bg": "#3498db", "border": "#2980b9", "text": "#ffffff"},
    NotificationSeverity.SUCCESS: {"bg": "#27ae60", "border": "#1e8449", "text": "#ffffff"},
    NotificationSeverity.WARNING: {"bg": "#f39c12", "border": "#d68910", "text": "#ffffff"},
    NotificationSeverity.ERROR: {"bg": "#e74c3c", "border": "#c0392b", "text": "#ffffff"},
    NotificationSeverity.CRITICAL: {"bg": "#8e44ad", "border": "#6c3483", "text": "#ffffff"},
}


class _NotificationManager:
    """Manages notifications per parent and zone for proper stacking"""
    _instances = {}  # parent_id -> {zone: [notifications]}
    
    @classmethod
    def register(cls, parent, notification, zone):
        """Register a notification"""
        parent_id = id(parent)
        if parent_id not in cls._instances:
            cls._instances[parent_id] = {z: [] for z in NotificationZone}
        cls._instances[parent_id][zone].append(notification)
    
    @classmethod
    def unregister(cls, parent, notification, zone):
        """Unregister a notification"""
        parent_id = id(parent)
        if parent_id in cls._instances and zone in cls._instances[parent_id]:
            if notification in cls._instances[parent_id][zone]:
                cls._instances[parent_id][zone].remove(notification)
    
    @classmethod
    def get_notifications(cls, parent, zone):
        """Get all notifications for a zone"""
        parent_id = id(parent)
        if parent_id in cls._instances:
            return cls._instances[parent_id].get(zone, [])
        return []
    
    @classmethod
    def get_index(cls, parent, notification, zone):
        """Get index of notification in its zone"""
        notifications = cls.get_notifications(parent, zone)
        if notification in notifications:
            return notifications.index(notification)
        return -1


class NotificationItem(QFrame):
    """Individual notification item"""
    
    closed = Signal(object)  # Emits self when closed
    
    def __init__(
        self,
        parent,
        message="",
        title="",
        severity=NotificationSeverity.INFO,
        zone=NotificationZone.TOP_RIGHT,
        duration=None,
        width=320,
        custom_widget=None,
        style=None,
    ):
        super().__init__(parent)
        self._message = message
        self._title = title
        self._severity = severity
        self._zone = zone
        self._width = width
        self._custom_widget = custom_widget
        self._closing = False
        self._hovered = False
        self._paused = False
        
        # Use provided style or default for severity
        self._style = style if style is not None else SeverityStyle.default(severity)
        
        # Duration: use provided, or style's duration, or global default
        if duration is not None:
            self._duration = duration
        elif style is not None:
            self._duration = style.duration
        else:
            self._duration = SEVERITY_DURATIONS[severity]
        self._remaining_time = self._duration
        
        # Animation references
        self._slide_animation = None
        self._position_animation = None
        self._opacity_animation = None
        
        # Timer for auto-dismiss
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._start_dismiss)
        
        # Timer for tracking elapsed time (for pause/resume)
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(100)
        self._elapsed_timer.timeout.connect(self._tick)
        
        self.setup_ui()
        
        # Track mouse enter/leave
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
    
    def setup_ui(self):
        """Setup the notification UI"""
        # Use instance style for colors
        colors = self._style.to_dict()
        
        self.setStyleSheet(f"""
            NotificationItem {{
                background-color: {colors['bg']};
                border: 2px solid {colors['border']};
                border-radius: 8px;
            }}
        """)
        
        # Set fixed width, height will be determined by content
        self.setFixedWidth(self._width)
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 8, 10)
        main_layout.setSpacing(8)
        
        # Content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        if self._custom_widget:
            # Use custom widget
            content_layout.addWidget(self._custom_widget)
        else:
            # Title (if provided)
            if self._title:
                title_label = QLabel(self._title)
                title_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors['text']};
                        font-weight: bold;
                        font-size: 13px;
                        background: transparent;
                    }}
                """)
                title_label.setWordWrap(True)
                content_layout.addWidget(title_label)
            
            # Message
            if self._message:
                message_label = QLabel(self._message)
                message_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors['text']};
                        font-size: 12px;
                        background: transparent;
                    }}
                """)
                message_label.setWordWrap(True)
                content_layout.addWidget(message_label)
        
        main_layout.addLayout(content_layout, 1)
        
        # Close button
        self.close_button = QPushButton("✕", self)
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet(f"""
            QPushButton {{
                color: {colors['text']};
                font-size: 12px;
                border: none;
                background: transparent;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.3);
            }}
        """)
        self.close_button.clicked.connect(self._start_dismiss)
        main_layout.addWidget(self.close_button, 0, Qt.AlignTop)
        
        # Adjust size to content
        self.adjustSize()
        
        # Create opacity effect
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
    
    def show_notification(self):
        """Show the notification with animation"""
        if not self.parent():
            return
        
        # Register with manager
        _NotificationManager.register(self.parent(), self, self._zone)
        
        # Install event filter on parent for resize
        self.parent().installEventFilter(self)
        
        # Calculate initial position (off-screen)
        self._update_position(animate=False, off_screen=True)
        
        # Show widget
        self.show()
        self.raise_()
        
        # Animate in
        self._animate_in()
        
        # Start auto-dismiss timer if duration > 0
        if self._duration > 0:
            self._dismiss_timer.start(self._duration)
            self._elapsed_timer.start()
    
    def _calculate_target_position(self):
        """Calculate the target position for this notification"""
        if not self.parent():
            return QPoint(0, 0)
        
        parent_rect = self.parent().rect()
        margin = 15
        spacing = 10
        
        # Get index in stack
        index = _NotificationManager.get_index(self.parent(), self, self._zone)
        if index < 0:
            index = 0
        
        # Calculate cumulative height of notifications above/below
        notifications = _NotificationManager.get_notifications(self.parent(), self._zone)
        cumulative_height = 0
        for i, notif in enumerate(notifications):
            if i < index:
                cumulative_height += notif.height() + spacing
        
        # Calculate position based on zone
        if self._zone == NotificationZone.TOP_RIGHT:
            x = parent_rect.width() - self._width - margin
            y = margin + cumulative_height
        elif self._zone == NotificationZone.TOP_LEFT:
            x = margin
            y = margin + cumulative_height
        elif self._zone == NotificationZone.BOTTOM_RIGHT:
            x = parent_rect.width() - self._width - margin
            y = parent_rect.height() - margin - self.height() - cumulative_height
        elif self._zone == NotificationZone.BOTTOM_LEFT:
            x = margin
            y = parent_rect.height() - margin - self.height() - cumulative_height
        else:
            x, y = margin, margin
        
        return QPoint(x, y)
    
    def _calculate_off_screen_position(self):
        """Calculate off-screen position for slide animation"""
        if not self.parent():
            return QPoint(0, 0)
        
        parent_rect = self.parent().rect()
        target = self._calculate_target_position()
        
        # Slide direction based on zone (left zones slide left, right zones slide right)
        if self._zone in [NotificationZone.TOP_RIGHT, NotificationZone.BOTTOM_RIGHT]:
            return QPoint(parent_rect.width() + 10, target.y())
        else:
            return QPoint(-self._width - 10, target.y())
    
    def _update_position(self, animate=True, off_screen=False):
        """Update position, optionally with animation"""
        if off_screen:
            pos = self._calculate_off_screen_position()
            self.move(pos)
        elif animate:
            self._animate_to_position(self._calculate_target_position())
        else:
            self.move(self._calculate_target_position())
    
    def _animate_in(self):
        """Animate notification sliding in"""
        target_pos = self._calculate_target_position()
        
        # Slide animation
        self._slide_animation = QPropertyAnimation(self, b"pos")
        self._slide_animation.setDuration(300)
        self._slide_animation.setStartValue(self.pos())
        self._slide_animation.setEndValue(target_pos)
        self._slide_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Fade in
        self._opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self._opacity_animation.setDuration(300)
        self._opacity_animation.setStartValue(0)
        self._opacity_animation.setEndValue(1)
        self._opacity_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self._slide_animation.start()
        self._opacity_animation.start()
    
    def _animate_to_position(self, target_pos):
        """Animate to a new position (for stacking adjustment)"""
        if self._position_animation and self._position_animation.state() == QPropertyAnimation.Running:
            self._position_animation.stop()
        
        self._position_animation = QPropertyAnimation(self, b"pos")
        self._position_animation.setDuration(250)
        self._position_animation.setStartValue(self.pos())
        self._position_animation.setEndValue(target_pos)
        self._position_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._position_animation.start()
    
    def _start_dismiss(self):
        """Start the dismiss animation"""
        if self._closing:
            return
        self._closing = True
        
        # Stop timers
        self._dismiss_timer.stop()
        self._elapsed_timer.stop()
        
        # Calculate off-screen position
        off_screen_pos = self._calculate_off_screen_position()
        
        # Slide out animation
        self._slide_animation = QPropertyAnimation(self, b"pos")
        self._slide_animation.setDuration(250)
        self._slide_animation.setStartValue(self.pos())
        self._slide_animation.setEndValue(off_screen_pos)
        self._slide_animation.setEasingCurve(QEasingCurve.InCubic)
        
        # Fade out
        self._opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self._opacity_animation.setDuration(250)
        self._opacity_animation.setStartValue(1)
        self._opacity_animation.setEndValue(0)
        self._opacity_animation.setEasingCurve(QEasingCurve.InCubic)
        
        self._slide_animation.finished.connect(self._cleanup)
        self._slide_animation.start()
        self._opacity_animation.start()
    
    def _cleanup(self):
        """Clean up after dismiss"""
        # Unregister first (before emitting signal)
        if self.parent():
            _NotificationManager.unregister(self.parent(), self, self._zone)
            self.parent().removeEventFilter(self)
            
            # Update positions of remaining notifications
            self._reposition_siblings()
        
        # Emit closed signal
        self.closed.emit(self)
        self.deleteLater()
    
    def _reposition_siblings(self):
        """Reposition sibling notifications after this one is removed"""
        if not self.parent():
            return
        
        notifications = _NotificationManager.get_notifications(self.parent(), self._zone)
        for notif in notifications:
            if notif != self and not notif._closing:
                notif._update_position(animate=True)
    
    def _tick(self):
        """Called periodically to track elapsed time"""
        if not self._paused and self._duration > 0:
            self._remaining_time -= 100
    
    def enterEvent(self, event):
        """Mouse entered - pause auto-dismiss"""
        self._hovered = True
        if self._duration > 0 and not self._closing:
            self._paused = True
            self._dismiss_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse left - resume auto-dismiss"""
        self._hovered = False
        if self._duration > 0 and not self._closing and self._paused:
            self._paused = False
            # Resume with remaining time
            if self._remaining_time > 0:
                self._dismiss_timer.start(self._remaining_time)
            else:
                self._start_dismiss()
        super().leaveEvent(event)
    
    def eventFilter(self, obj, event):
        """Handle parent resize"""
        if obj == self.parent() and event.type() == QEvent.Resize:
            if not self._closing:
                self._update_position(animate=True)
        return super().eventFilter(obj, event)


class NotificationManager(QWidget):
    """
    Manager widget for showing notifications in a parent window.
    
    Usage:
        notification_mgr = NotificationManager(main_window)
        notification_mgr.show_notification(
            message="File saved successfully!",
            severity=NotificationSeverity.SUCCESS,
            zone=NotificationZone.TOP_RIGHT
        )
        
        # Customize styles
        notification_mgr.set_style(NotificationSeverity.CRITICAL, SeverityStyle(
            bg="#ff0000",
            border="#cc0000", 
            text="#ffffff",
            duration=0
        ))
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        # This widget is invisible, just used as a manager
        self.hide()
        self._notifications = []
        
        # Initialize styles with defaults (can be customized)
        self._styles = {
            severity: SeverityStyle.default(severity)
            for severity in NotificationSeverity
        }
    
    def set_style(self, severity, style):
        """
        Set custom style for a severity level.
        
        Args:
            severity: NotificationSeverity enum value
            style: SeverityStyle instance
        
        Usage:
            manager.set_style(NotificationSeverity.CRITICAL, SeverityStyle(
                bg="#ff0000",
                border="#cc0000",
                text="#ffffff",
                duration=0
            ))
        """
        if isinstance(style, SeverityStyle):
            self._styles[severity] = style
        elif isinstance(style, dict):
            # Allow dict format for convenience
            self._styles[severity] = SeverityStyle(**style)
    
    def get_style(self, severity):
        """
        Get the style for a severity level.
        
        Args:
            severity: NotificationSeverity enum value
        
        Returns:
            SeverityStyle instance
        """
        return self._styles.get(severity, SeverityStyle.default(severity))
    
    def reset_style(self, severity=None):
        """
        Reset style(s) to defaults.
        
        Args:
            severity: Specific severity to reset, or None to reset all
        """
        if severity is None:
            for sev in NotificationSeverity:
                self._styles[sev] = SeverityStyle.default(sev)
        else:
            self._styles[severity] = SeverityStyle.default(severity)
    
    def show_notification(
        self,
        message="",
        title="",
        severity=NotificationSeverity.INFO,
        zone=NotificationZone.TOP_RIGHT,
        duration=None,
        width=320,
        custom_widget=None,
    ):
        """
        Show a notification.
        
        Args:
            message: The notification message text
            title: Optional title text
            severity: NotificationSeverity enum value
            zone: NotificationZone enum value for positioning
            duration: Auto-dismiss duration in ms (None = use style's default)
            width: Width of the notification widget
            custom_widget: Optional custom widget to display instead of text
        
        Returns:
            The NotificationItem instance
        """
        # Get style for this severity
        style = self.get_style(severity)
        
        # Use style's duration if not explicitly provided
        if duration is None:
            duration = style.duration
        
        notification = NotificationItem(
            parent=self.parent(),
            message=message,
            title=title,
            severity=severity,
            zone=zone,
            duration=duration,
            width=width,
            custom_widget=custom_widget,
            style=style,  # Pass custom style
        )
        
        self._notifications.append(notification)
        notification.closed.connect(self._on_notification_closed)
        notification.show_notification()
        
        return notification
    
    def _on_notification_closed(self, notification):
        """Handle notification closed"""
        if notification in self._notifications:
            self._notifications.remove(notification)
    
    def close_all(self, zone=None):
        """Close all notifications, optionally filtered by zone"""
        notifications_to_close = self._notifications.copy()
        for notif in notifications_to_close:
            if zone is None or notif._zone == zone:
                notif._start_dismiss()


# Convenience functions for quick notifications
def show_info(parent, message, title="", zone=NotificationZone.TOP_RIGHT, duration=None):
    """Show an info notification"""
    notif = NotificationItem(parent, message, title, NotificationSeverity.INFO, zone, duration)
    notif.show_notification()
    return notif


def show_success(parent, message, title="", zone=NotificationZone.TOP_RIGHT, duration=None):
    """Show a success notification"""
    notif = NotificationItem(parent, message, title, NotificationSeverity.SUCCESS, zone, duration)
    notif.show_notification()
    return notif


def show_warning(parent, message, title="", zone=NotificationZone.TOP_RIGHT, duration=None):
    """Show a warning notification"""
    notif = NotificationItem(parent, message, title, NotificationSeverity.WARNING, zone, duration)
    notif.show_notification()
    return notif


def show_error(parent, message, title="", zone=NotificationZone.TOP_RIGHT, duration=None):
    """Show an error notification"""
    notif = NotificationItem(parent, message, title, NotificationSeverity.ERROR, zone, duration)
    notif.show_notification()
    return notif


def show_critical(parent, message, title="", zone=NotificationZone.TOP_RIGHT):
    """Show a critical notification (no auto-dismiss)"""
    notif = NotificationItem(parent, message, title, NotificationSeverity.CRITICAL, zone, 0)
    notif.show_notification()
    return notif


# ============== Demo Application ==============

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Notification Widget Demo")
        self.resize(900, 700)
        
        # Create notification manager
        self.notification_mgr = NotificationManager(self)
        
        # Track notification count for demo
        self._notification_count = 0

        # Create main content
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Notification Widget Demo")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Severity section
        severity_label = QLabel("Notification Severities")
        severity_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(severity_label)
        
        severity_layout = QHBoxLayout()
        
        btn_info = QPushButton("Info (3s)")
        btn_info.clicked.connect(lambda: self.show_demo_notification(NotificationSeverity.INFO))
        
        btn_success = QPushButton("Success (3s)")
        btn_success.clicked.connect(lambda: self.show_demo_notification(NotificationSeverity.SUCCESS))
        
        btn_warning = QPushButton("Warning (5s)")
        btn_warning.clicked.connect(lambda: self.show_demo_notification(NotificationSeverity.WARNING))
        
        btn_error = QPushButton("Error (7s)")
        btn_error.clicked.connect(lambda: self.show_demo_notification(NotificationSeverity.ERROR))
        
        btn_critical = QPushButton("Critical (No dismiss)")
        btn_critical.clicked.connect(lambda: self.show_demo_notification(NotificationSeverity.CRITICAL))
        
        severity_layout.addWidget(btn_info)
        severity_layout.addWidget(btn_success)
        severity_layout.addWidget(btn_warning)
        severity_layout.addWidget(btn_error)
        severity_layout.addWidget(btn_critical)
        layout.addLayout(severity_layout)
        
        # Zone section
        zone_label = QLabel("Notification Zones")
        zone_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;")
        layout.addWidget(zone_label)
        
        zone_layout = QHBoxLayout()
        
        btn_top_left = QPushButton("Top Left")
        btn_top_left.clicked.connect(lambda: self.show_zone_notification(NotificationZone.TOP_LEFT))
        
        btn_top_right = QPushButton("Top Right")
        btn_top_right.clicked.connect(lambda: self.show_zone_notification(NotificationZone.TOP_RIGHT))
        
        btn_bottom_left = QPushButton("Bottom Left")
        btn_bottom_left.clicked.connect(lambda: self.show_zone_notification(NotificationZone.BOTTOM_LEFT))
        
        btn_bottom_right = QPushButton("Bottom Right")
        btn_bottom_right.clicked.connect(lambda: self.show_zone_notification(NotificationZone.BOTTOM_RIGHT))
        
        zone_layout.addWidget(btn_top_left)
        zone_layout.addWidget(btn_top_right)
        zone_layout.addWidget(btn_bottom_left)
        zone_layout.addWidget(btn_bottom_right)
        layout.addLayout(zone_layout)
        
        # Stacking demo section
        stack_label = QLabel("Stacking Demo")
        stack_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;")
        layout.addWidget(stack_label)
        
        stack_layout = QHBoxLayout()
        
        btn_stack_3 = QPushButton("Stack 3 Notifications")
        btn_stack_3.clicked.connect(self.show_stacked_notifications)
        
        btn_stack_mixed = QPushButton("Stack Mixed Severities")
        btn_stack_mixed.clicked.connect(self.show_mixed_stack)
        
        btn_all_corners = QPushButton("All Corners")
        btn_all_corners.clicked.connect(self.show_all_corners)
        
        stack_layout.addWidget(btn_stack_3)
        stack_layout.addWidget(btn_stack_mixed)
        stack_layout.addWidget(btn_all_corners)
        layout.addLayout(stack_layout)
        
        # Control section
        control_label = QLabel("Controls")
        control_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 15px;")
        layout.addWidget(control_label)
        
        control_layout = QHBoxLayout()
        
        btn_close_all = QPushButton("Close All")
        btn_close_all.clicked.connect(lambda: self.notification_mgr.close_all())
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
        
        btn_custom = QPushButton("Custom Widget Notification")
        btn_custom.clicked.connect(self.show_custom_widget_notification)
        
        control_layout.addWidget(btn_custom)
        control_layout.addWidget(btn_close_all)
        layout.addLayout(control_layout)
        
        # Info section
        info_label = QLabel(
            "💡 Tips:\n"
            "• Hover over a notification to pause auto-dismiss\n"
            "• CRITICAL notifications don't auto-dismiss\n"
            "• Resize the window to see notifications reposition\n"
            "• Notifications slide out and others fill the gap"
        )
        info_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
                background: #f5f5f5;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
            }
        """)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        # Style buttons
        for btn in [
            btn_info, btn_success, btn_warning, btn_error, btn_critical,
            btn_top_left, btn_top_right, btn_bottom_left, btn_bottom_right,
            btn_stack_3, btn_stack_mixed, btn_all_corners, btn_custom,
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
    
    def show_demo_notification(self, severity):
        """Show a demo notification with given severity"""
        self._notification_count += 1
        
        titles = {
            NotificationSeverity.INFO: "Information",
            NotificationSeverity.SUCCESS: "Success!",
            NotificationSeverity.WARNING: "Warning",
            NotificationSeverity.ERROR: "Error",
            NotificationSeverity.CRITICAL: "Critical Alert",
        }
        
        messages = {
            NotificationSeverity.INFO: f"This is an info notification #{self._notification_count}",
            NotificationSeverity.SUCCESS: f"Operation completed successfully #{self._notification_count}",
            NotificationSeverity.WARNING: f"Please review this warning #{self._notification_count}",
            NotificationSeverity.ERROR: f"An error has occurred #{self._notification_count}",
            NotificationSeverity.CRITICAL: f"Critical issue requires attention #{self._notification_count}",
        }
        
        self.notification_mgr.show_notification(
            message=messages[severity],
            title=titles[severity],
            severity=severity,
            zone=NotificationZone.TOP_RIGHT,
        )
    
    def show_zone_notification(self, zone):
        """Show a notification in the specified zone"""
        self._notification_count += 1
        self.notification_mgr.show_notification(
            message=f"Notification in {zone.value} zone #{self._notification_count}",
            title=f"{zone.value.replace('_', ' ').title()}",
            severity=NotificationSeverity.INFO,
            zone=zone,
        )
    
    def show_stacked_notifications(self):
        """Show multiple notifications to demonstrate stacking"""
        from PySide6.QtCore import QTimer
        
        self._notification_count += 1
        self.notification_mgr.show_notification(
            message="First notification - will disappear first",
            title="Notification 1",
            severity=NotificationSeverity.INFO,
            zone=NotificationZone.TOP_RIGHT,
        )
        
        QTimer.singleShot(200, lambda: self._show_stacked_2())
        QTimer.singleShot(400, lambda: self._show_stacked_3())
    
    def _show_stacked_2(self):
        self._notification_count += 1
        self.notification_mgr.show_notification(
            message="Second notification - watch the animation!",
            title="Notification 2",
            severity=NotificationSeverity.SUCCESS,
            zone=NotificationZone.TOP_RIGHT,
        )
    
    def _show_stacked_3(self):
        self._notification_count += 1
        self.notification_mgr.show_notification(
            message="Third notification - when one closes, others slide into place",
            title="Notification 3",
            severity=NotificationSeverity.WARNING,
            zone=NotificationZone.TOP_RIGHT,
        )
    
    def show_mixed_stack(self):
        """Show mixed severity stack to demonstrate hover pause"""
        self.notification_mgr.show_notification(
            message="Hover over me to pause! Other notifications will still timeout.",
            title="Hover to Pause",
            severity=NotificationSeverity.INFO,
            zone=NotificationZone.TOP_RIGHT,
            duration=10000,  # 10 seconds
        )
        
        from PySide6.QtCore import QTimer
        QTimer.singleShot(200, lambda: self.notification_mgr.show_notification(
            message="I'll dismiss in 3 seconds unless you hover!",
            title="Quick Info",
            severity=NotificationSeverity.SUCCESS,
            zone=NotificationZone.TOP_RIGHT,
        ))
        
        QTimer.singleShot(400, lambda: self.notification_mgr.show_notification(
            message="I won't auto-dismiss. Close me manually!",
            title="Critical",
            severity=NotificationSeverity.CRITICAL,
            zone=NotificationZone.TOP_RIGHT,
        ))
    
    def show_all_corners(self):
        """Show notifications in all corners"""
        self._notification_count += 1
        
        for zone in NotificationZone:
            self.notification_mgr.show_notification(
                message=f"Notification #{self._notification_count}",
                title=zone.value.replace("_", " ").title(),
                severity=NotificationSeverity.INFO,
                zone=zone,
            )
    
    def show_custom_widget_notification(self):
        """Show a notification with a custom widget"""
        # Create custom widget
        custom = QWidget()
        custom_layout = QVBoxLayout(custom)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel("Custom Widget!")
        label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        
        btn_layout = QHBoxLayout()
        
        btn_yes = QPushButton("Accept")
        btn_yes.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid rgba(255,255,255,0.3);
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.3);
            }
        """)
        
        btn_no = QPushButton("Decline")
        btn_no.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: 1px solid rgba(255,255,255,0.3);
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        
        btn_layout.addWidget(btn_yes)
        btn_layout.addWidget(btn_no)
        
        custom_layout.addWidget(label)
        custom_layout.addLayout(btn_layout)
        
        notif = self.notification_mgr.show_notification(
            severity=NotificationSeverity.WARNING,
            zone=NotificationZone.TOP_RIGHT,
            duration=0,  # Don't auto-dismiss
            custom_widget=custom,
        )
        
        # Connect buttons to close
        btn_yes.clicked.connect(notif._start_dismiss)
        btn_no.clicked.connect(notif._start_dismiss)


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

