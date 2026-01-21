from __future__ import annotations

from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.hotkeys import format_hotkey
from .common import card_container, card_layout, section_title


class HotkeysPage(QWidget):
    add_requested = Signal()
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    test_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._hotkeys: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(section_title("Hotkeys / Макросы"))

        action_row = QWidget()
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(10)
        add_btn = QPushButton("Добавить макрос")
        add_btn.setObjectName("Primary")
        add_btn.clicked.connect(self.add_requested.emit)
        action_layout.addWidget(add_btn)
        action_layout.addStretch(1)

        layout.addWidget(action_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        container = QWidget()
        self.container_layout = QVBoxLayout(container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(12)
        self.container_layout.addStretch(1)

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def set_hotkeys(self, hotkeys: list[dict]) -> None:
        self._hotkeys = hotkeys
        self.refresh()

    def refresh(self) -> None:
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for hotkey in self._hotkeys:
            card = self._hotkey_card(hotkey)
            self.container_layout.addWidget(card)
        self.container_layout.addStretch(1)

    def _hotkey_card(self, hotkey: dict) -> QWidget:
        card = card_container()
        layout = card_layout(card, spacing=12)

        title = hotkey.get("title") or "Без названия"
        hotkey_text = format_hotkey(str(hotkey.get("hotkey", "")))
        steps_count = len(hotkey.get("steps", []) or [])

        header_row = QWidget()
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 600;")
        hotkey_label = QLabel(hotkey_text or "(не задан)" )
        hotkey_label.setStyleSheet("color: #cfa3a3; font-size: 13px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(hotkey_label)

        divider = QFrame()
        divider.setObjectName("CardDivider")
        divider.setFrameShape(QFrame.HLine)

        bottom_row = QWidget()
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(12)

        steps_label = QLabel(f"Шагов: {steps_count}")
        steps_label.setStyleSheet("color: #a89d9d;")

        actions = QWidget()
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        edit_btn = QToolButton()
        edit_btn.setObjectName("ActionIcon")
        edit_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        edit_btn.setIconSize(QSize(16, 16))
        edit_btn.setToolTip("Редактировать")
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(hotkey.get("id", "")))

        test_btn = QToolButton()
        test_btn.setObjectName("ActionIcon")
        test_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        test_btn.setIconSize(QSize(16, 16))
        test_btn.setToolTip("Тест")
        test_btn.clicked.connect(lambda: self.test_requested.emit(hotkey.get("id", "")))

        delete_btn = QToolButton()
        delete_btn.setObjectName("ActionDelete")
        delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        delete_btn.setIconSize(QSize(16, 16))
        delete_btn.setToolTip("Удалить")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(hotkey.get("id", "")))

        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(test_btn)
        actions_layout.addWidget(delete_btn)

        bottom_layout.addWidget(steps_label)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(actions)

        layout.addWidget(header_row)
        layout.addWidget(divider)
        layout.addWidget(bottom_row)

        return card
