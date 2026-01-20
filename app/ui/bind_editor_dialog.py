from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from app.ui.pages.common import card_container, card_layout


class BindEditorDialog(QDialog):
    saved = Signal(dict)
    deleted = Signal(str)

    def __init__(
        self,
        parent=None,
        mode: str = "create",
        existing_triggers: set[str] | None = None,
        bind_data: dict | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Редактор бинда")
        self.setMinimumSize(920, 640)
        self.setModal(True)
        self.mode = mode
        self.existing_triggers = existing_triggers or set()
        self.bind_data = bind_data or {}
        self.bind_id = self.bind_data.get("id", "")
        self.original_trigger = self.bind_data.get("trigger", "")

        dialog_root = QWidget()
        dialog_root.setObjectName("DialogRoot")
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)
        root.addWidget(dialog_root, 1)

        dialog_layout = QVBoxLayout(dialog_root)
        dialog_layout.setContentsMargins(24, 24, 24, 24)
        dialog_layout.setSpacing(16)

        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        title_label = QLabel("Редактор бинда")
        title_label.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: 700;")
        subtitle_label = QLabel("Создание и настройка триггеров для быстрого ввода.")
        subtitle_label.setStyleSheet("color: #bfb0b0;")
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)

        content_row = QWidget()
        content_layout = QHBoxLayout(content_row)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        left_card = card_container()
        left_layout = card_layout(left_card, spacing=12)

        title = QLabel("Основные поля")
        title.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 600;")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        self.name_input = QLineEdit()
        self.category_input = QComboBox()
        self.category_input.addItems(["Ответы", "Телепорты", "Наказания", "Без категории"])
        self.trigger_input = QLineEdit()
        self.trigger_input.setPlaceholderText("ку")

        trigger_hint = QLabel("Префикс берется из настроек. Триггер хранится без префикса.")
        trigger_hint.setStyleSheet("color: #a7a7a7;")

        form.addRow("Название:", self.name_input)
        form.addRow("Категория:", self.category_input)
        form.addRow("Триггер:", self.trigger_input)

        type_row = QWidget()
        type_layout = QHBoxLayout(type_row)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(8)

        self.type_group = QButtonGroup(type_row)
        self.type_text = QPushButton("Text")
        self.type_command = QPushButton("Command")
        self.type_multi = QPushButton("Multi")
        for btn in (self.type_text, self.type_command, self.type_multi):
            btn.setCheckable(True)
            self.type_group.addButton(btn)
            type_layout.addWidget(btn)
        self.type_text.setChecked(True)

        self.content_input = QPlainTextEdit()
        self.content_input.setPlaceholderText("Введите текст или команды. Для Multi каждая строка = отдельная команда.")

        options_title = QLabel("Опции")
        options_title.setStyleSheet("color: #ffffff; font-size: 14px;")

        self.delete_trigger = QCheckBox("Удалять введенный триггер")
        self.delete_trigger.setObjectName("Toggle")
        self.delete_trigger.setChecked(True)
        self.case_sensitive = QCheckBox("Чувствителен к регистру")
        self.case_sensitive.setObjectName("Toggle")
        self.only_prefix = QCheckBox("Только с префиксом")
        self.only_prefix.setObjectName("Toggle")
        self.only_prefix.setChecked(True)

        left_layout.addWidget(title)
        left_layout.addLayout(form)
        left_layout.addWidget(trigger_hint)
        left_layout.addWidget(QLabel("Тип:"))
        left_layout.addWidget(type_row)
        left_layout.addWidget(QLabel("Контент:"))
        left_layout.addWidget(self.content_input, 1)
        left_layout.addWidget(options_title)
        left_layout.addWidget(self.delete_trigger)
        left_layout.addWidget(self.case_sensitive)
        left_layout.addWidget(self.only_prefix)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        templates_card = card_container()
        templates_layout = card_layout(templates_card, spacing=10)
        templates_title = QLabel("Шаблоны")
        templates_title.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 600;")

        template_row = QWidget()
        template_layout = QHBoxLayout(template_row)
        template_layout.setContentsMargins(0, 0, 0, 0)
        template_layout.setSpacing(8)

        for text in ("{discord_me}", "{discord_zga}", "{discord_ga}"):
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, t=text: self.insert_template(t))
            template_layout.addWidget(btn)

        template_row_2 = QWidget()
        template_layout_2 = QHBoxLayout(template_row_2)
        template_layout_2.setContentsMargins(0, 0, 0, 0)
        template_layout_2.setSpacing(8)
        for text in ("{me_name}", "{time}", "{date}"):
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, t=text: self.insert_template(t))
            template_layout_2.addWidget(btn)

        gender_row = QWidget()
        gender_layout = QHBoxLayout(gender_row)
        gender_layout.setContentsMargins(0, 0, 0, 0)
        gender_layout.setSpacing(8)
        gender_templates = [
            "{g:мог|могла}",
            "{g:сделал|сделала}",
            "{g:обратился|обратилась}",
        ]
        for text in gender_templates:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, t=text: self.insert_template(t))
            gender_layout.addWidget(btn)

        gender_hint = QLabel("{g:муж|жен} выбирается по полу из персонализации.")
        gender_hint.setStyleSheet("color: #a7a7a7;")

        test_card = card_container()
        test_layout_wrap = card_layout(test_card, spacing=10)
        test_title = QLabel("Тест")
        test_title.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 600;")

        self.test_input = QLineEdit()
        self.test_input.setPlaceholderText(".ку")
        test_button = QPushButton("Проверить")
        test_button.setObjectName("Primary")
        test_button.clicked.connect(self.run_test)

        test_row = QWidget()
        test_layout = QHBoxLayout(test_row)
        test_layout.setContentsMargins(0, 0, 0, 0)
        test_layout.setSpacing(8)
        test_layout.addWidget(self.test_input, 1)
        test_layout.addWidget(test_button)

        result_label = QLabel("Результат")
        result_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        self.result_box = QPlainTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setPlaceholderText(
            "Найдено: нет\nМетод: точный\nВыходной текст: ..."
        )

        templates_layout.addWidget(templates_title)
        templates_layout.addWidget(template_row)
        templates_layout.addWidget(template_row_2)
        templates_layout.addWidget(gender_row)
        templates_layout.addWidget(gender_hint)

        test_layout_wrap.addWidget(test_title)
        test_layout_wrap.addWidget(test_row)
        test_layout_wrap.addWidget(result_label)
        test_layout_wrap.addWidget(self.result_box, 1)

        right_layout.addWidget(templates_card)
        right_layout.addWidget(test_card, 1)

        buttons_row = QWidget()
        buttons_layout = QHBoxLayout(buttons_row)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("Primary")
        save_btn.clicked.connect(self.handle_save)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("Secondary")
        cancel_btn.clicked.connect(self.reject)
        delete_btn = QPushButton("Удалить")
        delete_btn.setObjectName("Destructive")
        delete_btn.clicked.connect(self.handle_delete)
        if self.mode == "edit":
            buttons_layout.addWidget(delete_btn)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)

        content_layout.addWidget(left_card, 3)
        content_layout.addWidget(right, 2)

        dialog_layout.addWidget(header)
        dialog_layout.addWidget(content_row, 1)
        dialog_layout.addWidget(buttons_row)

        self._load_bind()

    def insert_template(self, text: str) -> None:
        cursor = self.content_input.textCursor()
        cursor.insertText(text)
        self.content_input.setTextCursor(cursor)

    def handle_save(self) -> None:
        trigger = self.trigger_input.text().strip()
        if not trigger:
            QMessageBox.warning(self, "Ошибка", "Триггер не может быть пустым.")
            return
        if trigger in self.existing_triggers and trigger != self.original_trigger:
            result = QMessageBox.question(
                self,
                "Конфликт триггера",
                "Триггер уже существует. Заменить?",
                QMessageBox.Yes | QMessageBox.Cancel,
            )
            if result != QMessageBox.Yes:
                return
            replace = True
        else:
            replace = False
        if not self.category_input.currentText().strip():
            self.category_input.setCurrentText("Без категории")

        payload = {
            "id": self.bind_id,
            "title": self.name_input.text().strip(),
            "category": self.category_input.currentText(),
            "trigger": trigger,
            "type": self._current_type(),
            "content": self.content_input.toPlainText(),
            "options": {
                "delete_trigger": self.delete_trigger.isChecked(),
                "case_sensitive": self.case_sensitive.isChecked(),
                "only_prefix": self.only_prefix.isChecked(),
            },
            "replace_existing": replace,
        }
        self.saved.emit(payload)
        self.accept()

    def handle_delete(self) -> None:
        if self.mode != "edit":
            return
        result = QMessageBox.question(
            self,
            "Удалить бинд",
            "Удалить этот бинд?",
            QMessageBox.Yes | QMessageBox.Cancel,
        )
        if result != QMessageBox.Yes:
            return
        if self.bind_id:
            self.deleted.emit(self.bind_id)
        self.accept()

    def run_test(self) -> None:
        raw = self.test_input.text().strip()
        if not raw:
            self.result_box.setPlainText("Найдено: нет\nМетод: точный\nВыходной текст: ")
            return
        if raw.startswith("."):
            raw_trigger = raw[1:]
        else:
            raw_trigger = raw
        current_trigger = self.trigger_input.text().strip()
        method = "точный"
        found = raw_trigger == current_trigger
        if not found:
            converted = convert_layout(raw_trigger)
            if converted == current_trigger:
                found = True
                method = "конверсия RU↔EN"
        output = self.content_input.toPlainText().strip() if found else ""
        self.result_box.setPlainText(
            f"Найдено: {'да' if found else 'нет'}\n"
            f"Метод: {method}\n"
            f"Выходной текст: {output}"
        )

    def _load_bind(self) -> None:
        if not self.bind_data:
            return
        self.name_input.setText(self.bind_data.get("title", ""))
        category = self.bind_data.get("category", "Без категории")
        if category and self.category_input.findText(category) == -1:
            self.category_input.addItem(category)
        self.category_input.setCurrentText(category)
        self.trigger_input.setText(self.bind_data.get("trigger", ""))
        self.content_input.setPlainText(self.bind_data.get("content", ""))
        bind_type = self.bind_data.get("type", "Text")
        if bind_type == "Command":
            self.type_command.setChecked(True)
        elif bind_type == "Multi":
            self.type_multi.setChecked(True)
        else:
            self.type_text.setChecked(True)

        options = self.bind_data.get("options", {})
        if options:
            self.delete_trigger.setChecked(options.get("delete_trigger", True))
            self.case_sensitive.setChecked(options.get("case_sensitive", False))
            self.only_prefix.setChecked(options.get("only_prefix", True))

    def _current_type(self) -> str:
        if self.type_command.isChecked():
            return "Command"
        if self.type_multi.isChecked():
            return "Multi"
        return "Text"


def convert_layout(text: str) -> str:
    mapping = {
        "ф": "a",
        "и": "b",
        "с": "c",
        "в": "d",
        "у": "e",
        "а": "f",
        "п": "g",
        "р": "h",
        "ш": "i",
        "о": "j",
        "л": "k",
        "д": "l",
        "ь": "m",
        "т": "n",
        "щ": "o",
        "з": "p",
        "й": "q",
        "к": "r",
        "ы": "s",
        "е": "t",
        "г": "u",
        "м": "v",
        "ц": "w",
        "ч": "x",
        "н": "y",
        "я": "z",
    }
    reverse = {v: k for k, v in mapping.items()}
    converted = []
    for ch in text:
        lower = ch.lower()
        if lower in mapping:
            converted.append(mapping[lower])
        elif lower in reverse:
            converted.append(reverse[lower])
        else:
            converted.append(ch)
    return "".join(converted)
