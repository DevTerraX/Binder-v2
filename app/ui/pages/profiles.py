from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .common import card_container, card_layout, section_title


class ProfilesPage(QWidget):
    create_requested = Signal()
    activate_requested = Signal(str)
    rename_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._profiles: list[dict] = []
        self._active_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(section_title("Профили"))

        search_row = QWidget()
        search_layout = QHBoxLayout(search_row)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(12)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск профиля")
        self.create_btn = QPushButton("+ Создать профиль")
        self.create_btn.setObjectName("Primary")
        self.create_btn.clicked.connect(self.create_requested.emit)
        search_layout.addWidget(self.search, 1)
        search_layout.addWidget(self.create_btn)

        layout.addWidget(search_row)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(12)
        layout.addWidget(self.list_container)
        layout.addStretch(1)

        self.search.textChanged.connect(self.refresh)

    def set_profiles(self, profiles: list[dict], active_id: str | None) -> None:
        self._profiles = profiles
        self._active_id = active_id
        self.refresh()

    def refresh(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        query = self.search.text().strip().lower()
        for profile in self._profiles:
            name = profile.get("name", "")
            if query and query not in name.lower():
                continue
            card = self._profile_card(profile)
            self.list_layout.addWidget(card)
        self.list_layout.addStretch(1)

    def _profile_card(self, profile: dict) -> QWidget:
        card = card_container()
        layout = card_layout(card, spacing=10)

        name = profile.get("name", "")
        profile_id = profile.get("id", "")
        active = profile_id == self._active_id

        title = QLabel(name)
        status = QLabel("Активный" if active else "Неактивный")
        status.setStyleSheet("color: #a01a1a;" if active else "color: #9a9a9a;")

        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        activate_btn = QPushButton("Активировать")
        rename_btn = QPushButton("Переименовать")
        delete_btn = QPushButton("Удалить")
        delete_btn.setObjectName("Destructive")
        if active:
            activate_btn.setEnabled(False)
        activate_btn.clicked.connect(lambda: self.activate_requested.emit(profile_id))
        rename_btn.clicked.connect(lambda: self.rename_requested.emit(profile_id))
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(profile_id))
        button_layout.addWidget(activate_btn)
        button_layout.addWidget(rename_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch(1)

        layout.addWidget(title)
        layout.addWidget(status)
        layout.addWidget(button_row)
        return card
