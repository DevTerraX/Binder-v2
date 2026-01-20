from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .common import badge, card_container, card_layout, section_title


class BindsPage(QWidget):
    add_requested = Signal()
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    copy_requested = Signal(str)
    import_requested = Signal()
    binder_toggled = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.prefix = "."
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(section_title("Бинды"))

        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)
        search = QLineEdit()
        search.setPlaceholderText("Поиск по trigger / названию / тексту")
        category = QComboBox()
        category.addItems(["Все категории", "Телепорты", "Ответы", "Наказания"])
        self.toggle = QCheckBox("Binder ON")
        self.toggle.setObjectName("Toggle")
        self.toggle.setChecked(True)
        self.toggle.stateChanged.connect(lambda: self.binder_toggled.emit(self.toggle.isChecked()))
        top_layout.addWidget(search, 1)
        top_layout.addWidget(category)
        top_layout.addWidget(self.toggle)

        layout.addWidget(top_bar)

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

        action_row = QWidget()
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(10)
        add_btn = QPushButton("Добавить бинд")
        add_btn.setObjectName("Primary")
        import_btn = QPushButton("Импорт биндов в профиль")
        import_btn.clicked.connect(self.import_requested.emit)
        add_btn.clicked.connect(self.add_requested.emit)
        action_layout.addWidget(add_btn)
        action_layout.addWidget(import_btn)
        action_layout.addStretch(1)

        layout.addWidget(action_row)

    def set_binds(self, binds: list[dict]) -> None:
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for bind in binds:
            card = self._bind_card(
                self.prefix,
                bind.get("trigger", ""),
                bind.get("title", ""),
                bind.get("category", "Без категории"),
                bind.get("content", ""),
                bind.get("type", "Text"),
                bind.get("id", ""),
            )
            self.container_layout.addWidget(card)
        self.container_layout.addStretch(1)

    def set_binder_enabled(self, enabled: bool) -> None:
        self.toggle.blockSignals(True)
        self.toggle.setChecked(enabled)
        self.toggle.blockSignals(False)

    def set_prefix(self, prefix: str) -> None:
        self.prefix = prefix or "."

    def _bind_card(
        self,
        prefix: str,
        trigger: str,
        title: str,
        category: str,
        preview: str,
        bind_type: str,
        bind_id: str,
    ) -> QWidget:
        card = card_container()
        layout = card_layout(card, spacing=14)

        top_row = QWidget()
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)

        trigger_wrap = QWidget()
        trigger_layout = QHBoxLayout(trigger_wrap)
        trigger_layout.setContentsMargins(0, 0, 0, 0)
        trigger_layout.setSpacing(6)
        prefix_label = QLabel(prefix)
        prefix_label.setStyleSheet("color: #cfa3a3; font-size: 14px;")
        trigger_label = QLabel(trigger)
        trigger_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 600;")
        trigger_layout.addWidget(prefix_label)
        trigger_layout.addWidget(trigger_label)

        badges_row = QWidget()
        badges_layout = QHBoxLayout(badges_row)
        badges_layout.setContentsMargins(0, 0, 0, 0)
        badges_layout.setSpacing(6)
        type_badge = badge(bind_type, "type")
        category_badge = badge(category, "category")
        badges_layout.addWidget(type_badge)
        badges_layout.addWidget(category_badge)
        badges_layout.addStretch(1)

        top_layout.addWidget(trigger_wrap)
        top_layout.addStretch(1)
        top_layout.addWidget(badges_row)

        divider = QFrame()
        divider.setObjectName("CardDivider")
        divider.setFrameShape(QFrame.HLine)

        bottom_row = QWidget()
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(16)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #c9c9c9; font-size: 13px;")

        preview_text = preview if len(preview) <= 120 else f"{preview[:117]}..."
        preview_label = QLabel(preview_text)
        preview_label.setWordWrap(True)
        preview_label.setStyleSheet("color: #a89d9d;")
        preview_label.setMaximumHeight(36)

        left_layout.addWidget(title_label)
        left_layout.addWidget(preview_label)

        actions = QWidget()
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 8, 0)
        actions_layout.setSpacing(14)

        edit_btn = QToolButton()
        edit_btn.setObjectName("ActionIcon")
        edit_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        edit_btn.setIconSize(QSize(16, 16))
        edit_btn.setToolTip("Редактировать")
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(bind_id))
        copy_btn = QToolButton()
        copy_btn.setObjectName("ActionIcon")
        copy_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        copy_btn.setIconSize(QSize(16, 16))
        copy_btn.setToolTip("Скопировать")
        copy_btn.clicked.connect(lambda: self.copy_requested.emit(bind_id))
        delete_btn = QToolButton()
        delete_btn.setObjectName("ActionDelete")
        delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        delete_btn.setIconSize(QSize(16, 16))
        delete_btn.setToolTip("Удалить")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(bind_id))

        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(copy_btn)
        actions_layout.addWidget(delete_btn)

        bottom_layout.addWidget(left, 1)
        bottom_layout.addWidget(actions)

        layout.addWidget(top_row)
        layout.addWidget(divider)
        layout.addWidget(bottom_row)
        return card
