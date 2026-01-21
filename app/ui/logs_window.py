from __future__ import annotations

from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.log_store import read_events


TYPE_LABELS = {
    "bind_added": "Добавлено",
    "bind_edited": "Изменено",
    "bind_deleted": "Удалено",
    "profile_switched": "Профиль активирован",
    "profile_created": "Создан профиль",
    "profile_renamed": "Переименован профиль",
    "profile_deleted": "Удалён профиль",
    "import": "Импорт",
    "export": "Экспорт",
    "settings_changed": "Настройки",
    "personalization_changed": "Персонализация",
    "macro_created": "Создан макрос",
    "macro_edited": "Изменён макрос",
    "macro_deleted": "Удалён макрос",
    "macro_run": "Запущен макрос",
    "macro_error": "Ошибка макроса",
    "update_check": "Обновление",
    "update_download": "Обновление",
    "engine_debug": "Отладка",
}

TYPE_COLORS = {
    "bind_added": "#23361f",
    "bind_edited": "#2a2a1a",
    "bind_deleted": "#3a1f1f",
    "profile_switched": "#1f2a36",
    "profile_created": "#1f2a36",
    "profile_renamed": "#1f2a36",
    "profile_deleted": "#2a1f36",
    "import": "#1f2a36",
    "export": "#2a1f36",
    "settings_changed": "#2a241a",
    "personalization_changed": "#2a1f1f",
    "macro_created": "#1f2a36",
    "macro_edited": "#2a2a1a",
    "macro_deleted": "#3a1f1f",
    "macro_run": "#1f2630",
    "macro_error": "#3a1f1f",
    "update_check": "#1f2630",
    "update_download": "#1f2630",
    "engine_debug": "#2a1f1f",
}


class LogsWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Логи")
        self.setMinimumSize(820, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(12)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по логам")
        self.filter = QComboBox()
        self.filter.addItems(
            [
                "Все",
                "Добавлено",
                "Изменено",
                "Удалено",
                "Импорт",
                "Экспорт",
                "Создан профиль",
                "Переименован профиль",
                "Удалён профиль",
                "Профиль активирован",
                "Настройки",
                "Персонализация",
                "Создан макрос",
                "Изменён макрос",
                "Удалён макрос",
                "Запущен макрос",
                "Ошибка макроса",
                "Обновление",
                "Отладка",
            ]
        )
        controls_layout.addWidget(self.search, 1)
        controls_layout.addWidget(self.filter)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Время", "Тип", "Профиль", "Что изменилось"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setShowGrid(False)
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(3, 420)

        layout.addWidget(controls)
        layout.addWidget(self.table)

        self.search.textChanged.connect(self.refresh)
        self.filter.currentIndexChanged.connect(self.refresh)

        self._events: list[dict] = []
        self.load_events()

    def load_events(self) -> None:
        self._events = read_events()
        self.refresh()

    def refresh(self) -> None:
        query = self.search.text().strip().lower()
        filter_label = self.filter.currentText()

        filtered = []
        for event in self._events:
            label = TYPE_LABELS.get(event.get("type", ""), "Другое")
            if filter_label != "Все" and label != filter_label:
                continue
            if query:
                haystack = " ".join(
                    [
                        str(event.get("ts", "")),
                        str(event.get("type", "")),
                        str(event.get("profile_name", "")),
                        str(event.get("meta", "")),
                    ]
                ).lower()
                if query not in haystack:
                    continue
            filtered.append(event)

        self.table.setRowCount(len(filtered) if filtered else 1)
        if not filtered:
            item = QTableWidgetItem("Логов пока нет")
            item.setForeground(QBrush(QColor("#9a9a9a")))
            self.table.setItem(0, 0, item)
            return

        for row, event in enumerate(filtered):
            ts_item = QTableWidgetItem(str(event.get("ts", "")))
            type_key = event.get("type", "")
            type_label = TYPE_LABELS.get(type_key, "Other")
            type_item = QTableWidgetItem(type_label)
            color = TYPE_COLORS.get(type_key, "#1f1f1f")
            type_item.setBackground(QBrush(QColor(color)))
            profile_item = QTableWidgetItem(str(event.get("profile_name", "-")))
            meta_item = QTableWidgetItem(str(event.get("meta", "")))

            self.table.setItem(row, 0, ts_item)
            self.table.setItem(row, 1, type_item)
            self.table.setItem(row, 2, profile_item)
            self.table.setItem(row, 3, meta_item)
