from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .common import card_container, card_layout, section_title


class HelpSection(QWidget):
    def __init__(self, title: str, items: list[dict]) -> None:
        super().__init__()
        self._items = items

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        header = QLabel(title)
        header.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 600;")

        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск")
        self.filter = QComboBox()
        self.filter.addItem("Все")
        self._rebuild_categories(items)

        controls_layout.addWidget(self.search, 1)
        controls_layout.addWidget(self.filter)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)

        layout.addWidget(header)
        layout.addWidget(controls)
        layout.addWidget(self.list_container)
        layout.addStretch(1)

        self.search.textChanged.connect(self.refresh)
        self.filter.currentIndexChanged.connect(self.refresh)

        self.refresh()

    def set_items(self, items: list[dict]) -> None:
        current = self.filter.currentText()
        self._items = items
        self._rebuild_categories(items)
        index = self.filter.findText(current)
        self.filter.setCurrentIndex(index if index != -1 else 0)
        self.refresh()

    def refresh(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        query = self.search.text().strip().lower()
        category = self.filter.currentText()

        for item in self._items:
            if category != "Все" and item.get("category") != category:
                continue
            title = item.get("title", "")
            body = item.get("body", "")
            haystack = f"{title} {body}".lower()
            if query and query not in haystack:
                continue

            card = card_container()
            card_layout(card, spacing=6)
            title_label = QLabel(title)
            title_label.setStyleSheet("color: #f0f0f0; font-weight: 600;")
            body_label = QLabel(body)
            body_label.setStyleSheet("color: #bfb0b0;")
            body_label.setWordWrap(True)
            card.layout().addWidget(title_label)
            card.layout().addWidget(body_label)
            self.list_layout.addWidget(card)

        if self.list_layout.count() == 0:
            empty = QLabel("Ничего не найдено")
            empty.setStyleSheet("color: #9a9a9a;")
            empty.setAlignment(Qt.AlignLeft)
            self.list_layout.addWidget(empty)

    def _rebuild_categories(self, items: list[dict]) -> None:
        self.filter.blockSignals(True)
        self.filter.clear()
        self.filter.addItem("Все")
        categories = sorted({item.get("category", "Другое") for item in items})
        for category in categories:
            self.filter.addItem(category)
        self.filter.blockSignals(False)


class HelpPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(section_title("Помощь / Changelog"))

        nav_row = QWidget()
        nav_layout = QHBoxLayout(nav_row)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(8)

        buttons = [
            "Подсказки",
            "Телепорты",
            "Новости",
            "Журнал изменений",
        ]

        self.stack = QStackedWidget()
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        for idx, label in enumerate(buttons):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setObjectName("HelpTab")
            if idx == 0:
                btn.setChecked(True)
            self.nav_group.addButton(btn, idx)
            nav_layout.addWidget(btn)

        nav_layout.addStretch(1)

        self.nav_group.buttonClicked.connect(
            lambda button: self.stack.setCurrentIndex(self.nav_group.id(button))
        )

        content_card = card_container()
        content_layout = card_layout(content_card)
        content_layout.setSpacing(12)

        data = _load_help_content()
        self._base_items = {
            "tips": data.get("tips", []),
            "teleports": data.get("teleports", []),
            "news": data.get("news", []),
            "changelog": data.get("changelog", []),
        }

        self.tips_section = HelpSection("Подсказки", self._base_items["tips"])
        self.teleports_section = HelpSection("Телепорты", self._base_items["teleports"])
        self.news_section = HelpSection("Новости", self._base_items["news"])
        self.changelog_section = HelpSection("Журнал изменений", self._base_items["changelog"])

        self.stack.addWidget(self.tips_section)
        self.stack.addWidget(self.teleports_section)
        self.stack.addWidget(self.news_section)
        self.stack.addWidget(self.changelog_section)

        content_layout.addWidget(self.stack)

        update_btn = QPushButton("Проверить обновления")
        update_btn.setObjectName("Primary")

        layout.addWidget(nav_row)
        layout.addWidget(content_card)
        layout.addWidget(update_btn)
        layout.addStretch(1)

        self.update_btn = update_btn

    def set_dynamic_items(self, dynamic: dict[str, list[dict]]) -> None:
        merged = {
            "tips": self._base_items["tips"] + dynamic.get("tips", []),
            "teleports": self._base_items["teleports"] + dynamic.get("teleports", []),
            "news": self._base_items["news"] + dynamic.get("news", []),
            "changelog": self._base_items["changelog"] + dynamic.get("changelog", []),
        }
        self.tips_section.set_items(merged["tips"])
        self.teleports_section.set_items(merged["teleports"])
        self.news_section.set_items(merged["news"])
        self.changelog_section.set_items(merged["changelog"])


def build_page() -> tuple[QWidget, QPushButton]:
    page = HelpPage()
    return page, page.update_btn


def _load_help_content() -> dict:
    defaults = {
        "tips": [
            {
                "title": "Как добавить бинд",
                "category": "Бинды",
                "body": "Откройте вкладку 'Бинды' и нажмите 'Добавить бинд'.",
            },
            {
                "title": "Горячие клавиши",
                "category": "Настройки",
                "body": "В разделе настроек можно задать хоткеи для открытия и переключения.",
            },
        ],
        "teleports": [
            {"title": "Телепорт к игроку", "category": "Команды", "body": "Используйте шаблон /tp {id}."},
            {"title": "Телепорт к месту", "category": "Команды", "body": "Сохраните координаты в шаблон бинда."},
        ],
        "news": [
            {"title": "Новая версия UI", "category": "Обновления", "body": "Обновлён редактор биндов и список карточек."},
        ],
        "changelog": [
            {"title": "0.1.0", "category": "Релиз", "body": "Базовый функционал профилей, биндов и логов."},
        ],
    }

    path = Path(__file__).resolve().parents[2] / "assets" / "help_content.json"
    if not path.exists():
        return defaults
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return defaults
    except json.JSONDecodeError:
        return defaults

    merged = defaults.copy()
    for key in defaults:
        if isinstance(data.get(key), list):
            merged[key] = data[key]
    return merged
