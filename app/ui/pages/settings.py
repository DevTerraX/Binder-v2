from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .common import card_container, card_layout, section_title


class SettingsPage(QWidget):
    settings_changed = Signal(dict)
    logs_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(section_title("Настройки"))

        triggers_card = card_container()
        triggers_layout = card_layout(triggers_card)
        triggers_layout.addWidget(QLabel("Префиксы триггера"))
        self.prefixes_input = QLineEdit()
        self.allow_no_prefix = QCheckBox("Разрешить триггер без префикса")
        self.auto_layout = QCheckBox("Авто-конверсия RU↔EN, если триггер не найден")
        self.prefixes_input.editingFinished.connect(self.emit_change)
        self.allow_no_prefix.stateChanged.connect(self.emit_change)
        self.auto_layout.stateChanged.connect(self.emit_change)
        triggers_layout.addWidget(self.prefixes_input)
        triggers_layout.addWidget(self.allow_no_prefix)
        triggers_layout.addWidget(self.auto_layout)

        commits_card = card_container()
        commits_layout = card_layout(commits_card)
        commits_layout.addWidget(QLabel("Клавиши подтверждения"))
        commits_row = QWidget()
        commits_row_layout = QHBoxLayout(commits_row)
        commits_row_layout.setContentsMargins(0, 0, 0, 0)
        commits_row_layout.setSpacing(10)
        self.space_cb = QCheckBox("Space")
        self.enter_cb = QCheckBox("Enter")
        self.tab_cb = QCheckBox("Tab")
        for cb in (self.space_cb, self.enter_cb, self.tab_cb):
            cb.stateChanged.connect(self.emit_change)
        commits_row_layout.addWidget(self.space_cb)
        commits_row_layout.addWidget(self.enter_cb)
        commits_row_layout.addWidget(self.tab_cb)
        commits_row_layout.addStretch(1)
        commits_layout.addWidget(commits_row)

        hotkeys_card = card_container()
        hotkeys_layout = card_layout(hotkeys_card)
        hotkeys_layout.addWidget(QLabel("Горячие клавиши"))
        form = QFormLayout()
        self.toggle_hotkey = QLineEdit()
        self.open_hotkey = QLineEdit()
        self.profile_hotkey = QLineEdit()
        for field in (self.toggle_hotkey, self.open_hotkey, self.profile_hotkey):
            field.editingFinished.connect(self.emit_change)
        form.addRow("Вкл/выкл binder:", self.toggle_hotkey)
        form.addRow("Открыть окно:", self.open_hotkey)
        form.addRow("Быстрое переключение профиля:", self.profile_hotkey)
        hotkeys_layout.addLayout(form)

        filter_card = card_container()
        filter_layout = card_layout(filter_card)
        filter_layout.addWidget(QLabel("Фильтр по приложениям"))
        self.only_apps = QLineEdit()
        self.exclude_apps = QLineEdit()
        self.only_apps.editingFinished.connect(self.emit_change)
        self.exclude_apps.editingFinished.connect(self.emit_change)
        filter_layout.addWidget(self.only_apps)
        filter_layout.addWidget(self.exclude_apps)

        service_card = card_container()
        service_layout = card_layout(service_card)
        service_layout.addWidget(QLabel("Сервис"))
        logs_btn = QPushButton("Логи")
        logs_btn.clicked.connect(self.logs_requested.emit)
        service_layout.addWidget(logs_btn)

        layout.addWidget(triggers_card)
        layout.addWidget(commits_card)
        layout.addWidget(hotkeys_card)
        layout.addWidget(filter_card)
        layout.addWidget(service_card)
        layout.addStretch(1)

    def set_settings(self, settings: dict) -> None:
        prefixes = settings.get("trigger_prefixes", ["."])
        self.prefixes_input.setText(",".join(prefixes))
        self.allow_no_prefix.blockSignals(True)
        self.allow_no_prefix.setChecked(settings.get("allow_no_prefix", False))
        self.allow_no_prefix.blockSignals(False)
        self.auto_layout.blockSignals(True)
        self.auto_layout.setChecked(settings.get("auto_layout", True))
        self.auto_layout.blockSignals(False)
        commit_keys = set(settings.get("commit_keys", []))
        for cb, key in (
            (self.space_cb, "space"),
            (self.enter_cb, "enter"),
            (self.tab_cb, "tab"),
        ):
            cb.blockSignals(True)
            cb.setChecked(key in commit_keys)
            cb.blockSignals(False)
        hotkeys = settings.get("hotkeys", {})
        self.toggle_hotkey.setText(hotkeys.get("toggle", ""))
        self.open_hotkey.setText(hotkeys.get("open", ""))
        self.profile_hotkey.setText(hotkeys.get("profile_switch", ""))
        apps = settings.get("apps_filter", {})
        self.only_apps.setText(apps.get("only", ""))
        self.exclude_apps.setText(apps.get("exclude", ""))

    def emit_change(self) -> None:
        prefixes = [p.strip() for p in self.prefixes_input.text().split(",") if p.strip()]
        commit_keys = []
        if self.space_cb.isChecked():
            commit_keys.append("space")
        if self.enter_cb.isChecked():
            commit_keys.append("enter")
        if self.tab_cb.isChecked():
            commit_keys.append("tab")

        payload = {
            "trigger_prefixes": prefixes or ["."],
            "allow_no_prefix": self.allow_no_prefix.isChecked(),
            "auto_layout": self.auto_layout.isChecked(),
            "commit_keys": commit_keys,
            "hotkeys": {
                "toggle": self.toggle_hotkey.text().strip(),
                "open": self.open_hotkey.text().strip(),
                "profile_switch": self.profile_hotkey.text().strip(),
            },
            "apps_filter": {
                "only": self.only_apps.text().strip(),
                "exclude": self.exclude_apps.text().strip(),
            },
        }
        self.settings_changed.emit(payload)
