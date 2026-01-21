from __future__ import annotations

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.hotkeys import format_hotkey, get_keyboard, keyboard_available, normalize_hotkey
from app.ui.pages.common import card_container, card_layout


class HotkeyRecorderWorker(QThread):
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


class HotkeyEditorDialog(QDialog):
    saved = Signal(dict)
    test_requested = Signal(list)

    def __init__(
        self,
        parent=None,
        mode: str = "create",
        hotkey_data: dict | None = None,
        commit_keys: set[str] | None = None,
        triggers: set[str] | None = None,
        settings_hotkeys: dict | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Редактор макроса")
        self.setMinimumSize(860, 620)
        self.setModal(True)

        self.mode = mode
        self.hotkey_data = hotkey_data or {}
        self.hotkey_id = self.hotkey_data.get("id", "")
        self._hotkey_value = str(self.hotkey_data.get("hotkey", "")).strip()
        self._steps: list[dict] = list(self.hotkey_data.get("steps", []) or [])
        self._edit_index: int | None = None
        self._commit_keys = commit_keys or set()
        self._triggers = triggers or set()
        self._settings_hotkeys = settings_hotkeys or {}

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QLabel("Горячие клавиши / Макросы")
        header.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: 700;")
        root.addWidget(header)

        main_card = card_container()
        main_layout = card_layout(main_card, spacing=12)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setVerticalSpacing(10)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Например: Admin macro")
        self.title_input.setText(self.hotkey_data.get("title", ""))

        self.hotkey_display = QLineEdit()
        self.hotkey_display.setReadOnly(True)
        self.hotkey_display.setPlaceholderText("Нажмите 'Записать хоткей'")
        if self._hotkey_value:
            self.hotkey_display.setText(format_hotkey(self._hotkey_value))

        record_row = QWidget()
        record_layout = QHBoxLayout(record_row)
        record_layout.setContentsMargins(0, 0, 0, 0)
        record_layout.setSpacing(8)

        self.record_btn = QPushButton("Записать хоткей")
        self.clear_btn = QPushButton("Очистить")
        self.record_btn.clicked.connect(self.start_recording)
        self.clear_btn.clicked.connect(self.clear_hotkey)

        record_layout.addWidget(self.hotkey_display, 1)
        record_layout.addWidget(self.record_btn)
        record_layout.addWidget(self.clear_btn)

        form.addRow("Название:", self.title_input)
        form.addRow("Хоткей:", record_row)

        main_layout.addLayout(form)

        self.conflict_hint = QLabel()
        self.conflict_hint.setStyleSheet("color: #cfa3a3; font-size: 11px;")
        self.conflict_hint.setWordWrap(True)
        self.conflict_hint.setVisible(False)
        main_layout.addWidget(self.conflict_hint)

        steps_label = QLabel("Шаги макроса")
        steps_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 600;")
        main_layout.addWidget(steps_label)

        self.steps_table = QTableWidget(0, 5)
        self.steps_table.setHorizontalHeaderLabels(["#", "Тип", "Значение", "Задержка (с)", "Действия"])
        self.steps_table.verticalHeader().setVisible(False)
        self.steps_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.steps_table.setSelectionMode(QTableWidget.NoSelection)
        self.steps_table.setShowGrid(False)
        self.steps_table.setColumnWidth(0, 40)
        self.steps_table.setColumnWidth(1, 120)
        self.steps_table.setColumnWidth(2, 260)
        self.steps_table.setColumnWidth(3, 100)
        self.steps_table.setColumnWidth(4, 140)

        main_layout.addWidget(self.steps_table)

        step_card = card_container()
        step_layout = card_layout(step_card, spacing=10)

        step_title = QLabel("Добавить шаг")
        step_title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 600;")

        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)

        self.step_type = QComboBox()
        self.step_type.addItems(["Press key", "Type text", "Press Enter", "Delay"])
        self.step_type.currentIndexChanged.connect(self._update_step_controls)

        self.step_value = QLineEdit()
        self.step_value.setPlaceholderText("Например: T или /chide")

        self.step_enter = QCheckBox("Enter")
        self.step_enter.setChecked(True)

        self.step_delay = QDoubleSpinBox()
        self.step_delay.setRange(0, 60)
        self.step_delay.setDecimals(2)
        self.step_delay.setSingleStep(0.25)
        self.step_delay.setSuffix(" c")

        self.add_step_btn = QPushButton("Добавить шаг")
        self.add_step_btn.setObjectName("Primary")
        self.add_step_btn.clicked.connect(self.add_step)

        controls_layout.addWidget(self.step_type)
        controls_layout.addWidget(self.step_value, 1)
        controls_layout.addWidget(self.step_enter)
        controls_layout.addWidget(self.step_delay)
        controls_layout.addWidget(self.add_step_btn)

        step_layout.addWidget(step_title)
        step_layout.addWidget(controls)

        main_layout.addWidget(step_card)

        root.addWidget(main_card, 1)

        buttons_row = QWidget()
        buttons_layout = QHBoxLayout(buttons_row)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)

        test_btn = QPushButton("Тест макрос")
        test_btn.clicked.connect(self._emit_test)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("Secondary")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("Primary")
        save_btn.clicked.connect(self.handle_save)

        buttons_layout.addWidget(test_btn)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)

        root.addWidget(buttons_row)

        self._update_step_controls()
        self._refresh_steps()
        self._update_conflict_warning()

    def start_recording(self) -> None:
        if not keyboard_available():
            QMessageBox.information(self, "Запись хоткея", "Доступно только на Windows.")
            return
        self.record_btn.setEnabled(False)
        self.record_btn.setText("Ожидание...")
        self._recorder = HotkeyRecorderWorker()
        self._recorder.recorded.connect(self._set_hotkey)
        self._recorder.finished.connect(self._recording_finished)
        self._recorder.start()

    def _set_hotkey(self, value: str) -> None:
        self._hotkey_value = normalize_hotkey(value)
        self.hotkey_display.setText(format_hotkey(self._hotkey_value))
        self.record_btn.setEnabled(True)
        self.record_btn.setText("Записать хоткей")
        self._update_conflict_warning()

    def _recording_finished(self) -> None:
        if self.record_btn.isEnabled():
            return
        self.record_btn.setEnabled(True)
        self.record_btn.setText("Записать хоткей")

    def clear_hotkey(self) -> None:
        self._hotkey_value = ""
        self.hotkey_display.clear()
        self._update_conflict_warning()

    def _update_step_controls(self) -> None:
        step_type = self.step_type.currentText()
        needs_value = step_type in {"Press key", "Type text"}
        needs_enter = step_type == "Type text"
        self.step_value.setEnabled(needs_value)
        self.step_enter.setEnabled(needs_enter)
        if not needs_value:
            self.step_value.clear()
        if not needs_enter:
            self.step_enter.setChecked(False)

    def add_step(self) -> None:
        step_type = self.step_type.currentText()
        value = self.step_value.text().strip()
        delay = float(self.step_delay.value())

        if step_type in {"Press key", "Type text"} and not value:
            QMessageBox.warning(self, "Шаг макроса", "Введите значение для шага.")
            return

        payload: dict = {"delay": delay}
        if step_type == "Press key":
            payload.update({"type": "press_key", "value": value})
        elif step_type == "Type text":
            payload.update({"type": "type_text", "value": value, "enter": self.step_enter.isChecked()})
        elif step_type == "Press Enter":
            payload.update({"type": "press_enter"})
        elif step_type == "Delay":
            payload.update({"type": "delay"})
        else:
            return

        if self._edit_index is None:
            self._steps.append(payload)
        else:
            self._steps[self._edit_index] = payload
            self._edit_index = None
            self.add_step_btn.setText("Добавить шаг")
        self._refresh_steps()

    def _refresh_steps(self) -> None:
        self.steps_table.setRowCount(len(self._steps) if self._steps else 1)
        if not self._steps:
            item = QTableWidgetItem("Шагов пока нет")
            item.setForeground(QBrush(QColor("#9a9a9a")))
            self.steps_table.setItem(0, 0, item)
            return

        for row, step in enumerate(self._steps):
            type_label = step.get("type", "")
            value = step.get("value", "")
            delay = step.get("delay", 0)
            if step.get("enter"):
                value = f"{value} (Enter)"

            self.steps_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.steps_table.setItem(row, 1, QTableWidgetItem(self._label_type(type_label)))
            self.steps_table.setItem(row, 2, QTableWidgetItem(str(value)))
            self.steps_table.setItem(row, 3, QTableWidgetItem(str(delay)))

            actions = self._action_buttons(row)
            self.steps_table.setCellWidget(row, 4, actions)

    def _action_buttons(self, row: int) -> QWidget:
        wrap = QWidget()
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        edit_btn = QToolButton()
        edit_btn.setText("✎")
        edit_btn.clicked.connect(lambda: self._edit_step(row))

        up_btn = QToolButton()
        up_btn.setText("↑")
        up_btn.clicked.connect(lambda: self._move_step(row, -1))

        down_btn = QToolButton()
        down_btn.setText("↓")
        down_btn.clicked.connect(lambda: self._move_step(row, 1))

        del_btn = QToolButton()
        del_btn.setText("×")
        del_btn.clicked.connect(lambda: self._delete_step(row))

        layout.addWidget(edit_btn)
        layout.addWidget(up_btn)
        layout.addWidget(down_btn)
        layout.addWidget(del_btn)
        return wrap

    def _move_step(self, row: int, direction: int) -> None:
        new_index = row + direction
        if new_index < 0 or new_index >= len(self._steps):
            return
        self._steps[row], self._steps[new_index] = self._steps[new_index], self._steps[row]
        self._refresh_steps()

    def _delete_step(self, row: int) -> None:
        if row < 0 or row >= len(self._steps):
            return
        self._steps.pop(row)
        self._refresh_steps()

    def _edit_step(self, row: int) -> None:
        if row < 0 or row >= len(self._steps):
            return
        step = self._steps[row]
        step_type = step.get("type", "")
        if step_type == "press_key":
            self.step_type.setCurrentText("Press key")
            self.step_value.setText(step.get("value", ""))
        elif step_type == "type_text":
            self.step_type.setCurrentText("Type text")
            self.step_value.setText(step.get("value", ""))
            self.step_enter.setChecked(bool(step.get("enter")))
        elif step_type == "press_enter":
            self.step_type.setCurrentText("Press Enter")
        elif step_type == "delay":
            self.step_type.setCurrentText("Delay")
        self.step_delay.setValue(float(step.get("delay", 0)))
        self._edit_index = row
        self.add_step_btn.setText("Сохранить шаг")

    def _label_type(self, key: str) -> str:
        mapping = {
            "press_key": "Press key",
            "type_text": "Type text",
            "press_enter": "Press Enter",
            "delay": "Delay",
        }
        return mapping.get(key, key)

    def _emit_test(self) -> None:
        self.test_requested.emit(list(self._steps))

    def handle_save(self) -> None:
        if not self._hotkey_value:
            QMessageBox.warning(self, "Хоткей", "Запишите хоткей перед сохранением.")
            return
        if not self._steps:
            QMessageBox.warning(self, "Макрос", "Добавьте хотя бы один шаг.")
            return

        payload = {
            "id": self.hotkey_id,
            "title": self.title_input.text().strip() or "Без названия",
            "hotkey": self._hotkey_value,
            "steps": list(self._steps),
        }
        self.saved.emit(payload)
        self.accept()

    def _update_conflict_warning(self) -> None:
        if not self._hotkey_value:
            self.conflict_hint.setVisible(False)
            return
        parts = [p for p in self._hotkey_value.split("+") if p]
        warnings: list[str] = []
        if len(parts) == 1:
            key = parts[0]
            warnings.append("Одиночная клавиша может конфликтовать с вводом текста.")
            if key in self._commit_keys:
                warnings.append("Конфликт с commit-клавишами биндов.")
            if key in self._triggers:
                warnings.append("Совпадает с триггером бинда.")
        for setting_name, value in self._settings_hotkeys.items():
            if normalize_hotkey(str(value)) == self._hotkey_value:
                warnings.append(f"Совпадает с хоткеем настроек: {setting_name}.")
        if warnings:
            self.conflict_hint.setText("Внимание: " + " ".join(warnings))
            self.conflict_hint.setVisible(True)
        else:
            self.conflict_hint.setVisible(False)
