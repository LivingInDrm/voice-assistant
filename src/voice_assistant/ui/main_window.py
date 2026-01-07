"""Main application window - Studio Noir Edition."""

import math
from PyQt6.QtCore import (
    Qt, pyqtSignal, pyqtSlot, QTimer, QPropertyAnimation,
    QEasingCurve, pyqtProperty, QSize, QRectF, QPointF
)
from PyQt6.QtGui import (
    QAction, QCloseEvent, QIcon, QPixmap, QPainter, QColor,
    QFont, QFontDatabase, QLinearGradient, QRadialGradient,
    QPen, QBrush, QPainterPath
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QProgressBar,
    QPushButton,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QFrame,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)

from ..config.settings import WhisperModel


# === Color Palette ===
class Colors:
    """Studio Noir color palette."""
    # Backgrounds
    BG_DARK = "#0a0a0f"
    BG_CARD = "#12121a"
    BG_ELEVATED = "#1a1a24"

    # Accent - Electric Cyan
    ACCENT = "#00d4ff"
    ACCENT_DIM = "#0099cc"
    ACCENT_GLOW = "#00d4ff40"

    # Recording state - Warm Red
    RECORDING = "#ff3b5c"
    RECORDING_GLOW = "#ff3b5c50"

    # Text
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#8a8a9a"
    TEXT_MUTED = "#4a4a5a"

    # Borders
    BORDER = "#2a2a3a"
    BORDER_ACCENT = "#00d4ff30"


class WaveformWidget(QWidget):
    """Animated waveform visualization widget."""

    def __init__(self, bar_count: int = 32, parent=None):
        super().__init__(parent)
        self.bar_count = bar_count
        self._levels = [0.0] * bar_count
        self._target_levels = [0.0] * bar_count
        self._is_active = False

        self.setMinimumHeight(60)
        self.setMaximumHeight(60)

        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(30)  # ~33fps

    def set_level(self, level: float) -> None:
        """Set the audio level (0.0 - 1.0)."""
        self._is_active = level > 0.01

        if self._is_active:
            # Generate varied bar heights based on level
            import random
            for i in range(self.bar_count):
                # Create wave-like variation
                wave = math.sin(i * 0.3 + level * 10) * 0.3 + 0.7
                self._target_levels[i] = min(1.0, level * wave * random.uniform(0.7, 1.3))
        else:
            self._target_levels = [0.05] * self.bar_count

    def _animate(self) -> None:
        """Smooth animation towards target levels."""
        changed = False
        for i in range(self.bar_count):
            diff = self._target_levels[i] - self._levels[i]
            if abs(diff) > 0.01:
                # Smooth interpolation
                self._levels[i] += diff * 0.3
                changed = True

        if changed or self._is_active:
            self.update()

    def paintEvent(self, event) -> None:
        """Draw the waveform bars."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        bar_width = max(2, (width - (self.bar_count - 1) * 3) // self.bar_count)
        spacing = 3
        total_width = self.bar_count * bar_width + (self.bar_count - 1) * spacing
        start_x = (width - total_width) // 2

        for i, level in enumerate(self._levels):
            x = start_x + i * (bar_width + spacing)
            bar_height = max(4, int(level * (height - 8)))
            y = (height - bar_height) // 2

            # Gradient based on level
            if self._is_active and level > 0.1:
                gradient = QLinearGradient(x, y, x, y + bar_height)
                gradient.setColorAt(0, QColor(Colors.ACCENT))
                gradient.setColorAt(1, QColor(Colors.ACCENT_DIM))
                painter.setBrush(QBrush(gradient))
            else:
                painter.setBrush(QColor(Colors.BORDER))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, bar_width, bar_height, 2, 2)


class RecordButton(QPushButton):
    """Circular record button with pulsing glow animation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(80, 80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._glow_intensity = 0.0
        self._pulse_phase = 0.0

        # Pulse animation timer
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._update_pulse)

        self.toggled.connect(self._on_toggle)

    def _on_toggle(self, checked: bool) -> None:
        """Handle toggle state change."""
        if checked:
            self._pulse_timer.start(30)
        else:
            self._pulse_timer.stop()
            self._glow_intensity = 0.0
            self.update()

    def _update_pulse(self) -> None:
        """Update pulse animation."""
        self._pulse_phase += 0.15
        self._glow_intensity = (math.sin(self._pulse_phase) + 1) / 2 * 0.5 + 0.5
        self.update()

    def paintEvent(self, event) -> None:
        """Draw the circular button with glow effect."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center = QPointF(self.width() / 2, self.height() / 2)
        radius = min(self.width(), self.height()) / 2 - 8

        is_recording = self.isChecked()
        base_color = QColor(Colors.RECORDING if is_recording else Colors.ACCENT)
        glow_color = QColor(Colors.RECORDING_GLOW if is_recording else Colors.ACCENT_GLOW)

        # Outer glow (when recording)
        if is_recording:
            glow_radius = radius + 12 + self._glow_intensity * 8
            glow = QRadialGradient(center, glow_radius)
            glow.setColorAt(0, glow_color)
            glow.setColorAt(0.5, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 50))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, glow_radius, glow_radius)

        # Button background
        bg_gradient = QRadialGradient(center, radius)
        if is_recording:
            bg_gradient.setColorAt(0, base_color.lighter(120))
            bg_gradient.setColorAt(1, base_color)
        else:
            bg_gradient.setColorAt(0, QColor(Colors.BG_ELEVATED))
            bg_gradient.setColorAt(1, QColor(Colors.BG_CARD))

        painter.setBrush(QBrush(bg_gradient))
        painter.setPen(QPen(base_color, 2))
        painter.drawEllipse(center, radius, radius)

        # Inner icon
        icon_color = QColor(Colors.TEXT_PRIMARY if is_recording else Colors.ACCENT)
        painter.setBrush(icon_color)
        painter.setPen(Qt.PenStyle.NoPen)

        if is_recording:
            # Stop icon (rounded square)
            square_size = radius * 0.5
            painter.drawRoundedRect(
                int(center.x() - square_size / 2),
                int(center.y() - square_size / 2),
                int(square_size),
                int(square_size),
                4, 4
            )
        else:
            # Mic icon
            mic_width = radius * 0.35
            mic_height = radius * 0.6

            # Mic body
            painter.drawRoundedRect(
                int(center.x() - mic_width / 2),
                int(center.y() - mic_height / 2 - 4),
                int(mic_width),
                int(mic_height),
                mic_width / 2,
                mic_width / 2
            )

            # Mic stand arc
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(icon_color, 2))
            arc_rect = QRectF(
                center.x() - mic_width * 0.8,
                center.y() - 4,
                mic_width * 1.6,
                mic_height * 0.7
            )
            painter.drawArc(arc_rect, 0, -180 * 16)

            # Stand line
            painter.drawLine(
                int(center.x()), int(center.y() + mic_height * 0.3),
                int(center.x()), int(center.y() + mic_height * 0.5)
            )


class GlassPanel(QFrame):
    """Glassmorphism-style panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glassPanel")

    def paintEvent(self, event) -> None:
        """Draw glass effect background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background with subtle gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(Colors.BG_CARD))
        gradient.setColorAt(1, QColor(Colors.BG_ELEVATED))

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)

        painter.fillPath(path, gradient)

        # Border
        painter.setPen(QPen(QColor(Colors.BORDER), 1))
        painter.drawPath(path)


class MainWindow(QMainWindow):
    """Main application window - Studio Noir Edition."""

    # Signals
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    model_changed = pyqtSignal(str)
    translation_toggled = pyqtSignal(bool)
    settings_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Assistant")
        self.setMinimumSize(600, 520)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self._is_recording = False
        self._model_downloaded: dict[str, bool] = {}  # Track download status
        self._setup_ui()
        self._setup_tray()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Initialize the user interface."""
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # === Header ===
        header = QHBoxLayout()

        title_label = QLabel("VOICE")
        title_label.setObjectName("titleLabel")
        header.addWidget(title_label)

        title_accent = QLabel("STUDIO")
        title_accent.setObjectName("titleAccent")
        header.addWidget(title_accent)

        header.addStretch()

        # Model selector (minimal style)
        self.model_combo = QComboBox()
        self.model_combo.setObjectName("modelCombo")
        self.model_combo.addItems([m.value for m in WhisperModel])
        self.model_combo.setCurrentText(WhisperModel.SMALL.value)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        header.addWidget(self.model_combo)

        # Settings button
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setObjectName("ghostButton")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.clicked.connect(self._open_settings)
        header.addWidget(self.settings_btn)

        layout.addLayout(header)

        # === Waveform Visualization ===
        self.waveform = WaveformWidget(bar_count=40)
        layout.addWidget(self.waveform)

        # === Record Button Section ===
        record_section = QHBoxLayout()
        record_section.addStretch()

        self.record_btn = RecordButton()
        self.record_btn.clicked.connect(self._on_record_clicked)
        record_section.addWidget(self.record_btn)

        record_section.addStretch()
        layout.addLayout(record_section)

        # === Status Label ===
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Hotkey hint
        hotkey_hint = QLabel("⌘⇧V to toggle recording")
        hotkey_hint.setObjectName("hotkeyHint")
        hotkey_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hotkey_hint)

        # === Transcription Panel ===
        self.transcription_panel = GlassPanel()
        panel_layout = QVBoxLayout(self.transcription_panel)
        panel_layout.setContentsMargins(16, 12, 16, 12)
        panel_layout.setSpacing(8)

        trans_header = QHBoxLayout()
        trans_label = QLabel("TRANSCRIPTION")
        trans_label.setObjectName("panelLabel")
        trans_header.addWidget(trans_label)
        trans_header.addStretch()

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("ghostButton")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy_text)
        trans_header.addWidget(self.copy_btn)

        panel_layout.addLayout(trans_header)

        self.text_display = QTextEdit()
        self.text_display.setObjectName("textDisplay")
        self.text_display.setReadOnly(True)
        self.text_display.setPlaceholderText("Transcribed text will appear here...")
        panel_layout.addWidget(self.text_display)

        layout.addWidget(self.transcription_panel, stretch=2)

        # === Translation Panel (hidden by default) ===
        self.translation_panel = GlassPanel()
        self.translation_panel.setVisible(False)
        trans_panel_layout = QVBoxLayout(self.translation_panel)
        trans_panel_layout.setContentsMargins(16, 12, 16, 12)
        trans_panel_layout.setSpacing(8)

        translation_header = QHBoxLayout()
        translation_label = QLabel("TRANSLATION")
        translation_label.setObjectName("panelLabel")
        translation_header.addWidget(translation_label)
        translation_header.addStretch()

        self.copy_translation_btn = QPushButton("Copy")
        self.copy_translation_btn.setObjectName("ghostButton")
        self.copy_translation_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_translation_btn.clicked.connect(self._copy_translation)
        translation_header.addWidget(self.copy_translation_btn)

        trans_panel_layout.addLayout(translation_header)

        self.translation_display = QTextEdit()
        self.translation_display.setObjectName("textDisplay")
        self.translation_display.setReadOnly(True)
        self.translation_display.setPlaceholderText("English translation...")
        self.translation_display.setMaximumHeight(100)
        trans_panel_layout.addWidget(self.translation_display)

        layout.addWidget(self.translation_panel)

        # === Bottom Bar ===
        bottom_bar = QHBoxLayout()

        self.translate_check = QCheckBox("Translate to English")
        self.translate_check.setObjectName("translateCheck")
        self.translate_check.toggled.connect(self._on_translation_toggled)
        bottom_bar.addWidget(self.translate_check)

        bottom_bar.addStretch()

        self.time_label = QLabel("")
        self.time_label.setObjectName("timeLabel")
        bottom_bar.addWidget(self.time_label)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("ghostButton")
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self._clear_text)
        bottom_bar.addWidget(self.clear_btn)

        layout.addLayout(bottom_bar)

        # Hidden volume bar for compatibility
        self.volume_bar = QProgressBar()
        self.volume_bar.setVisible(False)

    def _setup_tray(self) -> None:
        """Setup system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        icon = self._create_tray_icon()
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Voice Studio")
        self._setup_tray_menu()

    def _create_tray_icon(self) -> QIcon:
        """Create tray icon with accent color."""
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Mic icon in accent color
        accent = QColor(Colors.ACCENT)
        painter.setBrush(accent)
        painter.setPen(accent)
        painter.drawRoundedRect(20, 8, 24, 32, 10, 10)

        painter.setBrush(QColor(0, 0, 0, 0))
        painter.setPen(QPen(accent, 3))
        painter.drawArc(12, 20, 40, 30, 0, -180 * 16)
        painter.drawLine(32, 50, 32, 56)
        painter.drawLine(22, 56, 42, 56)

        painter.end()
        return QIcon(pixmap)

    def _setup_tray_menu(self) -> None:
        """Setup system tray context menu."""
        tray_menu = QMenu()
        tray_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                color: {Colors.TEXT_PRIMARY};
                padding: 8px 24px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {Colors.BG_ELEVATED};
            }}
        """)

        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _apply_styles(self) -> None:
        """Apply Studio Noir stylesheet."""
        self.setStyleSheet(f"""
            /* === Base === */
            QMainWindow {{
                background-color: {Colors.BG_DARK};
            }}

            #centralWidget {{
                background-color: {Colors.BG_DARK};
            }}

            /* === Typography === */
            #titleLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 24px;
                font-weight: 700;
                letter-spacing: 4px;
            }}

            #titleAccent {{
                color: {Colors.ACCENT};
                font-size: 24px;
                font-weight: 300;
                letter-spacing: 4px;
            }}

            #statusLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 15px;
                font-weight: 500;
            }}

            #hotkeyHint {{
                color: {Colors.TEXT_MUTED};
                font-size: 12px;
            }}

            #panelLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 2px;
            }}

            #timeLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: 12px;
            }}

            /* === Text Display === */
            #textDisplay {{
                background-color: transparent;
                border: none;
                color: {Colors.TEXT_PRIMARY};
                font-size: 14px;
                line-height: 1.6;
                selection-background-color: {Colors.ACCENT_DIM};
            }}

            #textDisplay::placeholder {{
                color: {Colors.TEXT_MUTED};
            }}

            /* === Buttons === */
            #ghostButton {{
                background-color: transparent;
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.TEXT_SECONDARY};
                font-size: 12px;
                font-weight: 500;
                padding: 6px 14px;
            }}

            #ghostButton:hover {{
                border-color: {Colors.ACCENT};
                color: {Colors.ACCENT};
            }}

            /* === ComboBox === */
            #modelCombo {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.TEXT_SECONDARY};
                font-size: 12px;
                padding: 6px 12px;
                min-width: 120px;
            }}

            #modelCombo:hover {{
                border-color: {Colors.ACCENT};
            }}

            #modelCombo::drop-down {{
                border: none;
                width: 20px;
            }}

            #modelCombo::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {Colors.TEXT_SECONDARY};
                margin-right: 8px;
            }}

            #modelCombo QAbstractItemView {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.BG_ELEVATED};
                outline: none;
            }}

            /* === Checkbox === */
            #translateCheck {{
                color: {Colors.TEXT_SECONDARY};
                font-size: 13px;
                spacing: 8px;
            }}

            #translateCheck::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: transparent;
            }}

            #translateCheck::indicator:checked {{
                background-color: {Colors.ACCENT};
                border-color: {Colors.ACCENT};
            }}

            #translateCheck::indicator:hover {{
                border-color: {Colors.ACCENT};
            }}

            /* === Scrollbar === */
            QScrollBar:vertical {{
                background-color: transparent;
                width: 8px;
                margin: 0;
            }}

            QScrollBar::handle:vertical {{
                background-color: {Colors.BORDER};
                border-radius: 4px;
                min-height: 30px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {Colors.TEXT_MUTED};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
                height: 0;
            }}
        """)

    # === Event Handlers ===

    def _on_record_clicked(self, checked: bool) -> None:
        """Handle record button click."""
        self._is_recording = checked
        if checked:
            self.status_label.setText("Recording...")
            self.recording_started.emit()
        else:
            self.status_label.setText("Processing...")
            self.recording_stopped.emit()

    def _on_model_changed(self, model: str) -> None:
        """Handle model selection change."""
        # Get the actual model value (without the checkmark)
        current_index = self.model_combo.currentIndex()
        model_value = self.model_combo.itemData(current_index)
        if model_value:
            self.model_changed.emit(model_value)
        else:
            # Fallback: strip the checkmark if present
            clean_model = model.replace(" ✓", "").strip()
            self.model_changed.emit(clean_model)

    def _on_translation_toggled(self, enabled: bool) -> None:
        """Handle translation toggle."""
        self.translation_panel.setVisible(enabled)
        self.translation_toggled.emit(enabled)

    def _open_settings(self) -> None:
        """Open settings dialog."""
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.settings_saved.connect(self.settings_changed.emit)
        dialog.exec()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()

    def _copy_text(self) -> None:
        """Copy transcription to clipboard."""
        clipboard = QApplication.clipboard()
        text = self.text_display.toPlainText()
        if text:
            clipboard.setText(text)
            self.status_label.setText("Copied to clipboard")
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))

    def _copy_translation(self) -> None:
        """Copy translation to clipboard."""
        clipboard = QApplication.clipboard()
        text = self.translation_display.toPlainText()
        if text:
            clipboard.setText(text)
            self.status_label.setText("Translation copied")
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))

    def _clear_text(self) -> None:
        """Clear all text displays."""
        self.text_display.clear()
        self.translation_display.clear()
        self.time_label.clear()
        self.status_label.setText("Ready")

    # === Public Slots ===

    @pyqtSlot(str)
    def set_transcription(self, text: str) -> None:
        """Set the transcription text."""
        self.text_display.setPlainText(text)
        self.status_label.setText("Ready")

    @pyqtSlot(str)
    def append_transcription(self, text: str) -> None:
        """Append to transcription text."""
        current = self.text_display.toPlainText()
        if current:
            self.text_display.setPlainText(current + "\n" + text)
        else:
            self.text_display.setPlainText(text)

    @pyqtSlot(str)
    def set_translation(self, text: str) -> None:
        """Set the translation text."""
        self.translation_display.setPlainText(text)

    @pyqtSlot(str)
    def append_translation(self, text: str) -> None:
        """Append to translation text (for streaming)."""
        current = self.translation_display.toPlainText()
        self.translation_display.setPlainText(current + text)

    @pyqtSlot(int)
    def set_volume(self, level: int) -> None:
        """Update waveform visualization."""
        self.waveform.set_level(level / 100.0)

    @pyqtSlot(str)
    def set_status(self, status: str) -> None:
        """Update status label."""
        self.status_label.setText(status)

    @pyqtSlot(float, float)
    def set_processing_time(self, process_time: float, audio_duration: float) -> None:
        """Display processing time info."""
        ratio = audio_duration / process_time if process_time > 0 else 0
        self.time_label.setText(f"{audio_duration:.1f}s → {process_time:.1f}s ({ratio:.1f}x)")

    @pyqtSlot()
    def reset_recording_state(self) -> None:
        """Reset the recording button state."""
        self._is_recording = False
        self.record_btn.setChecked(False)
        self.waveform.set_level(0)

    def toggle_recording(self) -> None:
        """Toggle recording state (for hotkey)."""
        self.record_btn.click()

    @pyqtSlot(str, bool)
    def set_model_downloaded(self, model: str, downloaded: bool) -> None:
        """
        Update the download status of a model.

        Args:
            model: Model value (e.g., "small", "large")
            downloaded: Whether the model is downloaded
        """
        self._model_downloaded[model] = downloaded
        self._update_model_combo_display()

    def _update_model_combo_display(self) -> None:
        """Update combo box items to show download status."""
        # Get current model value (not display text)
        current_index = self.model_combo.currentIndex()
        current_value = self.model_combo.itemData(current_index) if current_index >= 0 else None

        self.model_combo.blockSignals(True)
        self.model_combo.clear()

        for model in WhisperModel:
            display_text = model.value
            if self._model_downloaded.get(model.value, False):
                display_text = f"{model.value} ✓"
            self.model_combo.addItem(display_text, model.value)

        # Restore selection by matching itemData
        if current_value:
            for i in range(self.model_combo.count()):
                if self.model_combo.itemData(i) == current_value:
                    self.model_combo.setCurrentIndex(i)
                    break

        self.model_combo.blockSignals(False)

    @pyqtSlot(bool)
    def set_record_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the record button.

        Args:
            enabled: Whether recording should be enabled
        """
        self.record_btn.setEnabled(enabled)
        if not enabled:
            self.record_btn.setToolTip("Model not downloaded")
        else:
            self.record_btn.setToolTip("")

    def is_model_downloaded(self, model: str) -> bool:
        """Check if a model is downloaded."""
        return self._model_downloaded.get(model, False)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close - minimize to tray."""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Voice Studio",
            "Running in background",
            QSystemTrayIcon.MessageIcon.Information,
            1500,
        )


# Keep for backward compatibility
class TranslationLabel(QLabel):
    """Compatibility alias."""
    pass
