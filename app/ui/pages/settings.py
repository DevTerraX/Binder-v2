from __future__ import annotations

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .common import card_container, card_layout, section_title
from app.hotkeys import format_hotkey, get_keyboard, keyboard_available, normalize_hotkey


ROW_H = 44          # высота строки
FIELD_H = 40        # высота инпута
LABEL_W = 270       # ширина лейбла слева


def _card_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color:#ffffff;font-weight:700;")
    return lbl


def _hint(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color:#a7a7a7;font-size:11px;")
    lbl.setWordWrap(True)
    return lbl


def _make_line_edit(placeholder: str) -> QLineEdit:
    e = QLineEdit()
    e.setMinimumHeight(FIELD_H)
    e.setMaximumHeight(FIELD_H)
    e.setPlaceholderText(placeholder)
    e.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    return e


def _row(label_text: str, field: QWidget, label_width: int = LABEL_W) -> QWidget:
    """
    Аккуратная строка: слева лейбл фикс. ширины, справа поле растягивается.
    Фикс высота строки + вертикальное выравнивание = никаких "наездов".
    """
    w = QWidget()
    w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    w.setMinimumHeight(ROW_H)
    w.setMaximumHeight(ROW_H)

    l = QHBoxLayout(w)
    l.setContentsMargins(0, 0, 0, 0)
    l.setSpacing(14)

    label = QLabel(label_text)
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    label.setFixedWidth(label_width)
    label.setStyleSheet("color:#e8e8e8;font-size:12px;font-weight:600;")

    l.addWidget(label, 0, Qt.AlignVCenter)
    l.addWidget(field, 1, Qt.AlignVCenter)
    return w


class SettingsHotkeyRecorder(QThread):
    recorded = Signal(str)

    def run(self) -> None:
        kb = get_keyboard()
        if kb is None:
            return
        try:
            hotkey = kb.read_hotkey(suppress=False)
        except Exception:
            return
        self.recorded.emit(hotkey)


class SettingsPage(QWidget):
    settings_changed = Signal(dict)
    logs_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._recorders: dict[str, SettingsHotkeyRecorder] = {}
        self._hotkey_fields: dict[str, QLineEdit] = {}
        self._hotkey_buttons: dict[str, QPushButton] = {}

        # ---- ROOT: делаем скролл, чтобы при маленьком окне ничего не сжималось ----
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        scroll.setWidget(content)

        root.addWidget(scroll)

        # ---- CONTENT LAYOUT ----
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(section_title("Настройки"))

        # ---------- Triggers ----------
        triggers_card = card_container()
        triggers_layout = card_layout(triggers_card, spacing=14)  # больше spacing
        triggers_layout.addWidget(_card_title("Префиксы триггера"))

        self.prefixes_input = _make_line_edit("Например: . , ! , /")
        self.prefixes_input.textChanged.connect(self.emit_change)
        triggers_layout.addWidget(_row("Список префиксов:", self.prefixes_input))

        self.allow_no_prefix = QCheckBox("Разрешить триггер без префикса")
        self.auto_layout = QCheckBox("Авто-конверсия RU↔EN, если триггер не найден")
        self.allow_no_prefix.setObjectName("Toggle")
        self.auto_layout.setObjectName("Toggle")

        # stateChanged(int) -> emit_change(*args) (чтобы не падало)
        self.allow_no_prefix.stateChanged.connect(self.emit_change)
        self.auto_layout.stateChanged.connect(self.emit_change)

        triggers_layout.addWidget(self.allow_no_prefix)
        triggers_layout.addWidget(self.auto_layout)
        triggers_layout.addWidget(_hint("Подсказка: триггер хранится без префикса, префиксы задаются здесь."))

        # ---------- Commit keys ----------
        commits_card = card_container()
        commits_layout = card_layout(commits_card, spacing=14)
        commits_layout.addWidget(_card_title("Клавиши подтверждения"))

        commits_row = QWidget()
        commits_row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        commits_row.setMinimumHeight(ROW_H)
        commits_row.setMaximumHeight(ROW_H)

        commits_row_layout = QHBoxLayout(commits_row)
        commits_row_layout.setContentsMargins(0, 0, 0, 0)
        commits_row_layout.setSpacing(14)

        self.space_cb = QCheckBox("Space")
        self.enter_cb = QCheckBox("Enter")
        self.tab_cb = QCheckBox("Tab")

        for cb in (self.space_cb, self.enter_cb, self.tab_cb):
            cb.setObjectName("Toggle")
            cb.stateChanged.connect(self.emit_change)
            commits_row_layout.addWidget(cb, 0, Qt.AlignVCenter)

        commits_row_layout.addStretch(1)
        commits_layout.addWidget(commits_row)

        # ---------- Hotkeys ----------
        hotkeys_card = card_container()
        hotkeys_layout = card_layout(hotkeys_card, spacing=16)
        hotkeys_layout.addWidget(_card_title("Горячие клавиши"))

        self.toggle_hotkey = _make_line_edit("Нажмите «Записать»")
        self.open_hotkey = _make_line_edit("Нажмите «Записать»")
        self.profile_hotkey = _make_line_edit("Нажмите «Записать»")

        for field in (self.toggle_hotkey, self.open_hotkey, self.profile_hotkey):
            field.setReadOnly(True)

        hotkeys_layout.addWidget(
            _row(
                "Вкл/выкл binder:",
                self._hotkey_field("toggle", self.toggle_hotkey),
            )
        )
        hotkeys_layout.addWidget(
            _row(
                "Открыть окно:",
                self._hotkey_field("open", self.open_hotkey),
            )
        )
        hotkeys_layout.addWidget(
            _row(
                "Переключить профиль:",
                self._hotkey_field("profile_switch", self.profile_hotkey),
            )
        )

        # ---------- Apps filter ----------
        filter_card = card_container()
        filter_layout = card_layout(filter_card, spacing=16)
        filter_layout.addWidget(_card_title("Фильтр по приложениям"))

        self.only_apps = _make_line_edit("Через запятую, например: gta5.exe, discord.exe")
        self.exclude_apps = _make_line_edit("Через запятую, например: chrome.exe")

        self.only_apps.textChanged.connect(self.emit_change)
        self.exclude_apps.textChanged.connect(self.emit_change)

        filter_layout.addWidget(_row("Только в приложениях:", self.only_apps))
        filter_layout.addWidget(_row("Исключить приложения:", self.exclude_apps))

        # ---------- Service ----------
        service_card = card_container()
        service_layout = card_layout(service_card, spacing=14)
        service_layout.addWidget(_card_title("Сервис"))

        logs_btn = QPushButton("Логи")
        logs_btn.setObjectName("Primary")
        logs_btn.setMinimumHeight(44)
        logs_btn.clicked.connect(self.logs_requested.emit)
        service_layout.addWidget(logs_btn)

        # Add all cards
        layout.addWidget(triggers_card)
        layout.addWidget(commits_card)
        layout.addWidget(hotkeys_card)
        layout.addWidget(filter_card)
        layout.addWidget(service_card)
        layout.addStretch(1)

    def set_settings(self, settings: dict) -> None:
        prefixes = settings.get("trigger_prefixes", ["."])
        self.prefixes_input.blockSignals(True)
        self.prefixes_input.setText(",".join(prefixes))
        self.prefixes_input.blockSignals(False)

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
        self._set_hotkey_value(self.toggle_hotkey, hotkeys.get("toggle", ""))
        self._set_hotkey_value(self.open_hotkey, hotkeys.get("open", ""))
        self._set_hotkey_value(self.profile_hotkey, hotkeys.get("profile_switch", ""))

        apps = settings.get("apps_filter", {})
        self.only_apps.blockSignals(True)
        self.only_apps.setText(apps.get("only", ""))
        self.only_apps.blockSignals(False)

        self.exclude_apps.blockSignals(True)
        self.exclude_apps.setText(apps.get("exclude", ""))
        self.exclude_apps.blockSignals(False)

    def emit_change(self, *args) -> None:
        prefixes = [p.strip() for p in self.prefixes_input.text().split(",") if p.strip()]

        commit_keys: list[str] = []
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
                "toggle": self._get_hotkey_value(self.toggle_hotkey),
                "open": self._get_hotkey_value(self.open_hotkey),
                "profile_switch": self._get_hotkey_value(self.profile_hotkey),
            },
            "apps_filter": {
                "only": self.only_apps.text().strip(),
                "exclude": self.exclude_apps.text().strip(),
            },
        }
        self.settings_changed.emit(payload)

    def _hotkey_field(self, key: str, field: QLineEdit) -> QWidget:
        wrap = QWidget()
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        record_btn = QPushButton("Записать")
        clear_btn = QPushButton("Очистить")
        record_btn.setMinimumHeight(FIELD_H)
        clear_btn.setMinimumHeight(FIELD_H)
        record_btn.clicked.connect(lambda: self._start_recording(key))
        clear_btn.clicked.connect(lambda: self._clear_hotkey(key))
        if not keyboard_available():
            record_btn.setEnabled(False)

        self._hotkey_fields[key] = field
        self._hotkey_buttons[key] = record_btn

        layout.addWidget(field, 1)
        layout.addWidget(record_btn)
        layout.addWidget(clear_btn)
        return wrap

    def _start_recording(self, key: str) -> None:
        if not keyboard_available():
            return
        record_btn = self._hotkey_buttons.get(key)
        if record_btn:
            record_btn.setEnabled(False)
            record_btn.setText("Ожидание...")
        recorder = SettingsHotkeyRecorder()
        recorder.recorded.connect(lambda value, k=key: self._set_recorded_hotkey(k, value))
        recorder.finished.connect(lambda k=key: self._finish_recording(k))
        self._recorders[key] = recorder
        recorder.start()

    def _finish_recording(self, key: str) -> None:
        record_btn = self._hotkey_buttons.get(key)
        if record_btn:
            record_btn.setEnabled(True)
            record_btn.setText("Записать")

    def _set_recorded_hotkey(self, key: str, value: str) -> None:
        field = self._hotkey_fields.get(key)
        if not field:
            return
        self._set_hotkey_value(field, value)
        self.emit_change()

    def _clear_hotkey(self, key: str) -> None:
        field = self._hotkey_fields.get(key)
        if not field:
            return
        self._set_hotkey_value(field, "")
        self.emit_change()

    def _set_hotkey_value(self, field: QLineEdit, value: str) -> None:
        normalized = normalize_hotkey(str(value).strip())
        field.blockSignals(True)
        field.setProperty("hotkey_value", normalized)
        field.setText(format_hotkey(normalized) if normalized else "")
        field.blockSignals(False)

    def _get_hotkey_value(self, field: QLineEdit) -> str:
        stored = field.property("hotkey_value")
        if isinstance(stored, str) and stored:
            return stored
        return normalize_hotkey(field.text().strip())
