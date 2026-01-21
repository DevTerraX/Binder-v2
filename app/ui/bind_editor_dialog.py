from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.pages.common import card_container, card_layout


# ----------------------------
# Helpers
# ----------------------------

def _apply_editor_local_style(dialog: QDialog) -> None:
    """
    Локальный стиль только для этого диалога.
    Он специально "перебивает" возможные глобальные правила типа:
      QFrame#Card QWidget { background: transparent; }
    чтобы инпуты/комбобоксы в карточках не пропадали.
    """
    dialog.setStyleSheet(
        """
        /* Точечно для этого диалога */
        QWidget#BindEditorDialogRoot {
            background: transparent;
        }

        /* Инпуты внутри карточек - всегда видимые */
        QFrame#Card QLineEdit,
        QFrame#Card QComboBox,
        QFrame#Card QPlainTextEdit {
            background: #0E0E10;
            border: 1px solid rgba(255, 255, 255, 18);
            border-radius: 14px;
            padding: 8px 12px;
            color: #eaeaea;
            selection-background-color: rgba(160, 26, 26, 90);
        }

        QFrame#Card QLineEdit:focus,
        QFrame#Card QComboBox:focus,
        QFrame#Card QPlainTextEdit:focus {
            border: 1px solid rgba(160, 26, 26, 140);
        }

        QFrame#Card QLineEdit::placeholder,
        QFrame#Card QPlainTextEdit::placeholder {
            color: rgba(230, 230, 230, 110);
        }

        /* Segmented buttons */
        QPushButton#SegBtn {
            background: #0E0E10;
            border: 1px solid rgba(255, 255, 255, 16);
            border-radius: 12px;
            padding: 8px 12px;
            text-align: center;
        }
        QPushButton#SegBtn:hover {
            border: 1px solid rgba(255, 255, 255, 26);
            background: #111114;
        }
        QPushButton#SegBtn:checked {
            background: rgba(160, 26, 26, 22);
            border: 1px solid rgba(160, 26, 26, 90);
            color: #ffffff;
        }

        /* Маленькие подписи */
        QLabel#FieldLabel {
            color: #e8e8e8;
            font-size: 12px;
            font-weight: 500;
        }
        QLabel#HintText {
            color: #a7a7a7;
            font-size: 11px;
        }
        """
    )


def _field_row(label_text: str, field: QWidget) -> QWidget:
    row = QWidget()
    lay = QVBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)

    label = QLabel(label_text)
    label.setObjectName("FieldLabel")
    label.setMinimumHeight(18)

    lay.addWidget(label)
    lay.addWidget(field)
    return row


# ----------------------------
# Dialog
# ----------------------------

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

        # Корневой контейнер диалога (на него повесим локальные стили)
        dialog_root = QWidget()
        dialog_root.setObjectName("BindEditorDialogRoot")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)
        outer.addWidget(dialog_root, 1)

        _apply_editor_local_style(self)

        # Внутренний layout
        root = QVBoxLayout(dialog_root)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # Header
        header = QWidget()
        header_l = QVBoxLayout(header)
        header_l.setContentsMargins(8, 8, 8, 0)
        header_l.setSpacing(6)

        title = QLabel("Редактор бинда")
        title.setStyleSheet("color:#ffffff;font-size:18px;font-weight:700;")
        subtitle = QLabel("Создание и настройка триггеров для быстрого ввода.")
        subtitle.setStyleSheet("color:#bfb0b0;")

        header_l.addWidget(title)
        header_l.addWidget(subtitle)

        root.addWidget(header)

        # Content area with scroll (чтобы ничего не ломалось на маленьких экранах)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content_wrap = QWidget()
        scroll.setWidget(content_wrap)

        content_l = QHBoxLayout(content_wrap)
        content_l.setContentsMargins(0, 0, 0, 0)
        content_l.setSpacing(14)

        # LEFT CARD
        left_card = card_container()
        left_card.setMinimumWidth(520)  # чтобы форма не сжималась
        left = card_layout(left_card, spacing=12)

        left_title = QLabel("Основные поля")
        left_title.setStyleSheet("color:#ffffff;font-size:15px;font-weight:600;")

        # Inputs
        self.name_input = QLineEdit()
        self.name_input.setMinimumHeight(40)
        self.name_input.setPlaceholderText("Например: Приветствие")

        self.category_input = QComboBox()
        self.category_input.setMinimumHeight(40)
        self.category_input.addItems(["Ответы", "Телепорты", "Наказания", "Без категории"])

        self.trigger_input = QLineEdit()
        self.trigger_input.setMinimumHeight(40)
        self.trigger_input.setPlaceholderText("ку")

        # Hints
        trigger_hint = QLabel("Префикс берется из настроек. Триггер хранится без префикса.")
        trigger_hint.setObjectName("HintText")
        trigger_hint.setWordWrap(True)

        layout_hint = QLabel("Можно писать триггер на русском — авто-конверсия найдёт соответствие.")
        layout_hint.setObjectName("HintText")
        layout_hint.setWordWrap(True)

        # Form block
        form_block = QWidget()
        form_l = QVBoxLayout(form_block)
        form_l.setContentsMargins(0, 2, 0, 0)
        form_l.setSpacing(10)

        form_l.addWidget(_field_row("Название", self.name_input))
        form_l.addWidget(_field_row("Категория", self.category_input))
        form_l.addWidget(_field_row("Триггер", self.trigger_input))

        # Type segmented buttons
        type_label = QLabel("Тип")
        type_label.setObjectName("FieldLabel")

        type_row = QWidget()
        type_l = QHBoxLayout(type_row)
        type_l.setContentsMargins(0, 0, 0, 0)
        type_l.setSpacing(8)

        self.type_group = QButtonGroup(self)
        self.type_group.setExclusive(True)

        self.type_text = QPushButton("Text")
        self.type_command = QPushButton("Command")
        self.type_multi = QPushButton("Multi")

        for b in (self.type_text, self.type_command, self.type_multi):
            b.setCheckable(True)
            b.setObjectName("SegBtn")
            b.setMinimumHeight(38)
            b.setMinimumWidth(120)
            self.type_group.addButton(b)
            type_l.addWidget(b)

        type_l.addStretch(1)
        self.type_text.setChecked(True)
        self.type_group.buttonClicked.connect(self._on_type_changed)

        # Content
        content_label = QLabel("Контент")
        content_label.setObjectName("FieldLabel")

        self.content_input = QPlainTextEdit()
        self.content_input.setMinimumHeight(220)
        self.content_input.setPlaceholderText(
            "Введите текст или команды. Для Multi каждая строка = отдельная команда."
        )

        # Options
        options_title = QLabel("Опции")
        options_title.setStyleSheet("color:#ffffff;font-size:14px;font-weight:600;")

        self.delete_trigger = QCheckBox("Удалять введенный триггер")
        self.delete_trigger.setObjectName("Toggle")
        self.delete_trigger.setChecked(True)

        self.case_sensitive = QCheckBox("Чувствителен к регистру")
        self.case_sensitive.setObjectName("Toggle")

        self.only_prefix = QCheckBox("Только с префиксом")
        self.only_prefix.setObjectName("Toggle")
        self.only_prefix.setChecked(True)

        left.addWidget(left_title)
        left.addWidget(form_block)
        left.addWidget(trigger_hint)
        left.addWidget(layout_hint)
        left.addSpacing(6)
        left.addWidget(type_label)
        left.addWidget(type_row)
        left.addSpacing(6)
        left.addWidget(content_label)
        left.addWidget(self.content_input, 1)
        left.addWidget(options_title)
        left.addWidget(self.delete_trigger)
        left.addWidget(self.case_sensitive)
        left.addWidget(self.only_prefix)

        # RIGHT COLUMN
        right_col = QWidget()
        right_l = QVBoxLayout(right_col)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.setSpacing(12)
        right_col.setMinimumWidth(330)

        # Templates card
        templates_card = card_container()
        templates = card_layout(templates_card, spacing=10)

        templates_title = QLabel("Шаблоны")
        templates_title.setStyleSheet("color:#ffffff;font-size:15px;font-weight:600;")

        templates.addWidget(templates_title)
        templates.addWidget(self._templates_row(["{discord_me}", "{discord_zga}", "{discord_ga}"]))
        templates.addWidget(self._templates_row(["{me_name}", "{time}", "{date}"]))
        templates.addWidget(self._templates_row(["{g:мог|могла}", "{g:сделал|сделала}", "{g:обратился|обратилась}"]))

        gender_hint = QLabel("{g:муж|жен} выбирается по полу из персонализации.")
        gender_hint.setObjectName("HintText")
        gender_hint.setWordWrap(True)
        templates.addWidget(gender_hint)

        # Test card
        test_card = card_container()
        test = card_layout(test_card, spacing=10)

        test_title = QLabel("Тест")
        test_title.setStyleSheet("color:#ffffff;font-size:15px;font-weight:600;")

        self.test_input = QLineEdit()
        self.test_input.setMinimumHeight(38)
        self.test_input.setPlaceholderText(".ку")

        test_btn = QPushButton("Проверить")
        test_btn.setObjectName("Primary")
        test_btn.setMinimumHeight(38)
        test_btn.clicked.connect(self.run_test)

        test_row = QWidget()
        test_row_l = QHBoxLayout(test_row)
        test_row_l.setContentsMargins(0, 0, 0, 0)
        test_row_l.setSpacing(8)
        test_row_l.addWidget(self.test_input, 1)
        test_row_l.addWidget(test_btn)

        result_label = QLabel("Результат")
        result_label.setStyleSheet("color:#ffffff;font-size:14px;font-weight:600;")

        self.result_box = QPlainTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setMinimumHeight(160)
        self.result_box.setPlaceholderText("Найдено: нет\nМетод: точный\nВыходной текст: ...")

        test.addWidget(test_title)
        test.addWidget(test_row)
        test.addWidget(result_label)
        test.addWidget(self.result_box, 1)

        right_l.addWidget(templates_card)
        right_l.addWidget(test_card, 1)

        # Put columns in content layout
        content_l.addWidget(left_card, 3)
        content_l.addWidget(right_col, 2)

        root.addWidget(scroll, 1)

        # Bottom buttons
        buttons_row = QWidget()
        btn_l = QHBoxLayout(buttons_row)
        btn_l.setContentsMargins(0, 0, 0, 0)
        btn_l.setSpacing(10)

        delete_btn = QPushButton("Удалить")
        delete_btn.setObjectName("Destructive")
        delete_btn.setMinimumHeight(40)
        delete_btn.clicked.connect(self.handle_delete)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("Secondary")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("Primary")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.handle_save)

        if self.mode == "edit":
            btn_l.addWidget(delete_btn)

        btn_l.addStretch(1)
        btn_l.addWidget(cancel_btn)
        btn_l.addWidget(save_btn)

        root.addWidget(buttons_row)

        # Load existing bind
        self._load_bind()
        self._on_type_changed()  # подстроить подсказку сразу

    # ----------------------------
    # UI blocks
    # ----------------------------

    def _templates_row(self, texts: list[str]) -> QWidget:
        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        for t in texts:
            b = QPushButton(t)
            b.setMinimumHeight(34)
            b.clicked.connect(lambda checked=False, text=t: self.insert_template(text))
            lay.addWidget(b)
        return row

    def _on_type_changed(self) -> None:
        t = self._current_type()
        if t == "Multi":
            self.content_input.setPlaceholderText(
                "Multi: каждая строка = отдельная команда/строка.\n"
                "Пример:\n"
                "/re Привет\n"
                "/me сделал что-то"
            )
        elif t == "Command":
            self.content_input.setPlaceholderText("Command: одна команда или несколько команд одной строкой.")
        else:
            self.content_input.setPlaceholderText("Text: обычный текст, который будет вставлен/введён.")

    # ----------------------------
    # Actions
    # ----------------------------

    def insert_template(self, text: str) -> None:
        cursor = self.content_input.textCursor()
        cursor.insertText(text)
        self.content_input.setTextCursor(cursor)

    def handle_save(self) -> None:
        trigger = self.trigger_input.text().strip()
        if not trigger:
            QMessageBox.warning(self, "Ошибка", "Триггер не может быть пустым.")
            return

        # Нормализуем category
        if not self.category_input.currentText().strip():
            self.category_input.setCurrentText("Без категории")

        # Конфликт триггера
        replace = False
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
            self.result_box.setPlainText("Найдено: нет\nМетод: -\nВыходной текст: ")
            return

        raw_trigger = raw[1:] if raw.startswith(".") else raw
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

    # ----------------------------
    # Data
    # ----------------------------

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
        self.delete_trigger.setChecked(options.get("delete_trigger", True))
        self.case_sensitive.setChecked(options.get("case_sensitive", False))
        self.only_prefix.setChecked(options.get("only_prefix", True))

    def _current_type(self) -> str:
        if self.type_command.isChecked():
            return "Command"
        if self.type_multi.isChecked():
            return "Multi"
        return "Text"


# ----------------------------
# Layout convert
# ----------------------------

def convert_layout(text: str) -> str:
    mapping = {
        "ф": "a", "и": "b", "с": "c", "в": "d", "у": "e", "а": "f",
        "п": "g", "р": "h", "ш": "i", "о": "j", "л": "k", "д": "l",
        "ь": "m", "т": "n", "щ": "o", "з": "p", "й": "q", "к": "r",
        "ы": "s", "е": "t", "г": "u", "м": "v", "ц": "w", "ч": "x",
        "н": "y", "я": "z",
    }
    reverse = {v: k for k, v in mapping.items()}

    out: list[str] = []
    for ch in text:
        lower = ch.lower()
        if lower in mapping:
            out.append(mapping[lower])
        elif lower in reverse:
            out.append(reverse[lower])
        else:
            out.append(ch)
    return "".join(out)
