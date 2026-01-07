"""Settings dialog for API key configuration."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QFrame,
)

from ..config.settings import LLMProvider
from ..config.user_config import get_user_config


class Colors:
    """Studio Noir color palette."""
    BG_DARK = "#0a0a0f"
    BG_CARD = "#12121a"
    BG_ELEVATED = "#1a1a24"
    ACCENT = "#00d4ff"
    ACCENT_DIM = "#0099cc"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#8a8a9a"
    TEXT_MUTED = "#4a4a5a"
    BORDER = "#2a2a3a"


class SettingsDialog(QDialog):
    """Dialog for configuring API keys and translation settings."""

    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 280)
        self.setModal(True)

        self._user_config = get_user_config()
        self._setup_ui()
        self._apply_styles()
        self._load_values()

    def _setup_ui(self) -> None:
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("API Settings")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        layout.addWidget(separator)

        provider_layout = QHBoxLayout()
        provider_label = QLabel("Provider:")
        provider_label.setObjectName("fieldLabel")
        provider_layout.addWidget(provider_label)

        self.provider_combo = QComboBox()
        self.provider_combo.setObjectName("settingsCombo")
        self.provider_combo.addItem("Claude (Anthropic)", LLMProvider.CLAUDE.value)
        self.provider_combo.addItem("OpenAI", LLMProvider.OPENAI.value)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.provider_combo, stretch=1)
        layout.addLayout(provider_layout)

        key_layout = QHBoxLayout()
        self.key_label = QLabel("API Key:")
        self.key_label.setObjectName("fieldLabel")
        key_layout.addWidget(self.key_label)

        self.key_input = QLineEdit()
        self.key_input.setObjectName("keyInput")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("Enter your API key...")
        key_layout.addWidget(self.key_input, stretch=1)

        self.show_key_btn = QPushButton("Show")
        self.show_key_btn.setObjectName("ghostButton")
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.show_key_btn.toggled.connect(self._toggle_key_visibility)
        key_layout.addWidget(self.show_key_btn)

        layout.addLayout(key_layout)

        layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("ghostButton")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _apply_styles(self) -> None:
        """Apply Studio Noir stylesheet."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_DARK};
            }}

            #dialogTitle {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 18px;
                font-weight: 600;
            }}

            #separator {{
                background-color: {Colors.BORDER};
                max-height: 1px;
            }}

            #fieldLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: 13px;
                min-width: 70px;
            }}

            QComboBox {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 13px;
                padding: 8px 12px;
            }}

            QComboBox:hover {{
                border-color: {Colors.ACCENT};
            }}

            QComboBox:focus {{
                border-color: {Colors.ACCENT};
            }}

            QComboBox::drop-down {{
                border: none;
                width: 20px;
                subcontrol-origin: padding;
                subcontrol-position: right center;
            }}

            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {Colors.TEXT_SECONDARY};
                margin-right: 8px;
            }}

            QComboBox::down-arrow:hover {{
                border-top-color: {Colors.ACCENT};
            }}

            QComboBox QAbstractItemView {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.ACCENT_DIM};
                selection-color: {Colors.TEXT_PRIMARY};
                outline: none;
                padding: 4px;
            }}

            QComboBox QAbstractItemView::item {{
                padding: 6px 12px;
                border-radius: 4px;
                min-height: 24px;
            }}

            QComboBox QAbstractItemView::item:hover {{
                background-color: {Colors.BG_ELEVATED};
            }}

            QComboBox QAbstractItemView::item:selected {{
                background-color: {Colors.ACCENT_DIM};
            }}

            #keyInput {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 13px;
                padding: 8px 12px;
            }}

            #keyInput:hover, #keyInput:focus {{
                border-color: {Colors.ACCENT};
            }}

            #keyInput::placeholder {{
                color: {Colors.TEXT_MUTED};
            }}

            #ghostButton {{
                background-color: transparent;
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.TEXT_SECONDARY};
                font-size: 12px;
                font-weight: 500;
                padding: 8px 16px;
            }}

            #ghostButton:hover {{
                border-color: {Colors.ACCENT};
                color: {Colors.ACCENT};
            }}

            #primaryButton {{
                background-color: {Colors.ACCENT};
                border: none;
                border-radius: 6px;
                color: {Colors.BG_DARK};
                font-size: 12px;
                font-weight: 600;
                padding: 8px 20px;
            }}

            #primaryButton:hover {{
                background-color: {Colors.ACCENT_DIM};
            }}
        """)

    def _load_values(self) -> None:
        """Load current values from user config."""
        provider = self._user_config.translation_provider
        index = self.provider_combo.findData(provider)
        if index >= 0:
            self.provider_combo.setCurrentIndex(index)

        self._update_key_input()

    def _on_provider_changed(self, index: int) -> None:
        """Handle provider selection change."""
        self._update_key_input()

    def _update_key_input(self) -> None:
        """Update key input field based on selected provider."""
        provider_value = self.provider_combo.currentData()
        provider = LLMProvider(provider_value)
        key = self._user_config.get_api_key(provider)
        self.key_input.setText(key or "")

    def _toggle_key_visibility(self, checked: bool) -> None:
        """Toggle API key visibility."""
        if checked:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_key_btn.setText("Hide")
        else:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_key_btn.setText("Show")

    def _save_settings(self) -> None:
        """Save settings and close dialog."""
        provider_value = self.provider_combo.currentData()
        provider = LLMProvider(provider_value)
        key = self.key_input.text().strip()

        self._user_config.translation_provider = provider_value
        self._user_config.set_api_key(provider, key if key else None)
        self._user_config.save()

        self.settings_saved.emit()
        self.accept()
