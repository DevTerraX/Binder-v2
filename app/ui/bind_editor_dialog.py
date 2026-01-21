from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.engine import apply_variables
from app.ui.pages.common import card_container, card_layout
from app.ui.widgets.switch import ToggleSwitch


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
            background: #0B0B0C;
            border: 1px solid rgba(255, 255, 255, 12);
            border-radius: 10px;
            padding: 5px 10px;
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
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 14);
            border-radius: 10px;
            padding: 4px 10px;
            text-align: center;
        }
        QPushButton#SegBtn:hover {
            border: 1px solid rgba(255, 255, 255, 26);
            background: #111114;
        }
        QPushButton#SegBtn:checked {
            background: transparent;
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
        allowed_prefixes: list[str] | None = None,
        allow_no_prefix: bool = False,
        variables: dict | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Редактор бинда")
        self.setMinimumSize(920, 640)
        self.setModal(True)

        self.mode = mode
        self.existing_triggers = existing_triggers or set()
        self.bind_data = bind_data or {}
        self.allowed_prefixes = allowed_prefixes or ["."]
        self.allow_no_prefix = allow_no_prefix
        self.variables = variables or {}

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
        self.name_input.setMinimumHeight(32)
        self.name_input.setPlaceholderText("Например: Приветствие")

        self.category_input = QComboBox()
        self.category_input.setMinimumHeight(32)
        self.category_input.addItems(["Ответы", "Телепорты", "Наказания", "Без категории"])

        self.help_section_input = QComboBox()
        self.help_section_input.setMinimumHeight(32)
        self.help_section_input.addItems(
            [
                "Нет",
                "Подсказки",
                "Телепорты",
                "Новости",
                "Журнал изменений",
            ]
        )

        self.trigger_word = QLineEdit()
        self.trigger_word.setMinimumHeight(32)
        self.trigger_word.setPlaceholderText("ku, tp, ajail")
        self.trigger_word.textChanged.connect(self._update_trigger_preview)

        # Trigger block
        trigger_block = QWidget()
        trigger_l = QVBoxLayout(trigger_block)
        trigger_l.setContentsMargins(0, 2, 0, 0)
        trigger_l.setSpacing(8)

        trigger_title = QLabel("Триггер")
        trigger_title.setStyleSheet("color:#ffffff;font-size:14px;font-weight:600;")

        prefix_row = QWidget()
        prefix_l = QHBoxLayout(prefix_row)
        prefix_l.setContentsMargins(0, 0, 0, 0)
        prefix_l.setSpacing(8)

        self.prefix_group = QButtonGroup(self)
        self.prefix_group.setExclusive(True)

        prefixes = self._prefixes()
        for idx, prefix in enumerate(prefixes):
            btn = QPushButton(prefix)
            btn.setCheckable(True)
            btn.setObjectName("SegBtn")
            btn.setMinimumHeight(28)
            btn.setMinimumWidth(28)
            if idx == 0:
                btn.setChecked(True)
            self.prefix_group.addButton(btn)
            prefix_l.addWidget(btn)
        prefix_l.addStretch(1)
        self.prefix_group.buttonClicked.connect(self._update_trigger_preview)

        self.trigger_preview = QLabel()
        self.trigger_preview.setStyleSheet("color:#ffffff;font-size:16px;font-weight:600;")
        self._update_trigger_preview()

        trigger_hint = QLabel("Префикс берется из настроек. Триггер хранится без префикса.")
        trigger_hint.setObjectName("HintText")
        trigger_hint.setWordWrap(True)

        layout_hint = QLabel("Можно писать триггер на русском — авто-конверсия найдёт соответствие.")
        layout_hint.setObjectName("HintText")
        layout_hint.setWordWrap(True)

        trigger_l.addWidget(trigger_title)
        trigger_l.addWidget(prefix_row)
        trigger_l.addWidget(_field_row("Короткое слово", self.trigger_word))
        trigger_l.addWidget(self.trigger_preview)
        trigger_l.addWidget(trigger_hint)
        trigger_l.addWidget(layout_hint)

        # Form block
        form_block = QWidget()
        form_l = QVBoxLayout(form_block)
        form_l.setContentsMargins(0, 2, 0, 0)
        form_l.setSpacing(10)

        form_l.addWidget(_field_row("Название", self.name_input))
        form_l.addWidget(_field_row("Категория", self.category_input))
        form_l.addWidget(_field_row("Раздел Help", self.help_section_input))

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
        self.type_text.setToolTip("Text — вставляет обычный текст.")
        self.type_command.setToolTip("Command — вставляет команду, обычно начинается с /.") 
        self.type_multi.setToolTip("Multi — несколько строк, вводятся последовательно.")

        for b in (self.type_text, self.type_command, self.type_multi):
            b.setCheckable(True)
            b.setObjectName("SegBtn")
            b.setMinimumHeight(28)
            b.setMinimumWidth(90)
            self.type_group.addButton(b)
            type_l.addWidget(b)

        type_l.addStretch(1)
        self.type_text.setChecked(True)
        self.type_group.buttonClicked.connect(self._on_type_changed)

        self.type_hint = QLabel()
        self.type_hint.setObjectName("HintText")

        # Content
        content_label = QLabel("Контент")
        content_label.setObjectName("FieldLabel")

        self.content_input = QPlainTextEdit()
        self.content_input.setMinimumHeight(280)
        self.content_input.setPlaceholderText(
            "Введите текст или команды. Для Multi каждая строка = отдельная команда."
        )

        # Options
        options_title = QLabel("Опции")
        options_title.setStyleSheet("color:#ffffff;font-size:14px;font-weight:600;")

        self.delete_trigger = ToggleSwitch()
        self.delete_trigger.setChecked(True)
        self.case_sensitive = ToggleSwitch()
        self.only_prefix = ToggleSwitch()
        self.only_prefix.setChecked(True)

        def toggle_row(label_text: str, toggle: ToggleSwitch) -> QWidget:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(12)
            label = QLabel(label_text)
            label.setStyleSheet("color: #e0e0e0;")
            row_layout.addWidget(label)
            row_layout.addStretch(1)
            row_layout.addWidget(toggle)
            return row

        left.addWidget(left_title)
        left.addWidget(form_block)
        left.addWidget(trigger_block)
        left.addSpacing(6)
        left.addWidget(type_label)
        left.addWidget(type_row)
        left.addWidget(self.type_hint)
        left.addSpacing(6)
        left.addWidget(content_label)
        left.addWidget(self.content_input, 1)
        left.addWidget(options_title)
        left.addWidget(toggle_row("Удалять введенный триггер", self.delete_trigger))
        left.addWidget(toggle_row("Чувствителен к регистру", self.case_sensitive))
        left.addWidget(toggle_row("Только с префиксом", self.only_prefix))

        # RIGHT COLUMN
        right_col = QWidget()
        right_l = QVBoxLayout(right_col)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.setSpacing(12)
        right_col.setMinimumWidth(330)

        # Templates card
        templates_card = card_container()
        templates = card_layout(templates_card, spacing=10)

        templates_title = QLabel("Вставки (шаблоны)")
        templates_title.setStyleSheet("color:#ffffff;font-size:15px;font-weight:600;")
        templates_hint = QLabel("Нажми — вставится в текст. Можно использовать в любом бинде.")
        templates_hint.setObjectName("HintText")
        templates_hint.setWordWrap(True)

        templates.addWidget(templates_title)
        templates.addWidget(templates_hint)
        templates.addWidget(
            self._templates_row(
                [
                    ("{discord_me}", "Подставит ваш Discord, пример: me#9999"),
                    ("{discord_zga}", "Подставит Discord ЗГА, пример: zga#5678"),
                    ("{discord_ga}", "Подставит Discord ГА, пример: admin#1234"),
                ]
            )
        )
        templates.addWidget(
            self._templates_row(
                [
                    ("{me_name}", "Подставит ваше имя/ник"),
                    ("{time}", "Текущее время, пример: 21:30"),
                    ("{date}", "Текущая дата, пример: 12.03.2025"),
                ]
            )
        )

        extras_btn = QPushButton("Дополнительно")
        extras_btn.setCheckable(True)
        extras_btn.setObjectName("Secondary")

        gender_hint = QLabel("{g:муж|жен} выбирается по полу из персонализации.")
        gender_hint.setObjectName("HintText")
        gender_hint.setWordWrap(True)
        gender_row = self._templates_row(
            [
                ("{g:мог|могла}", "Пример: мог/могла"),
                ("{g:сделал|сделала}", "Пример: сделал/сделала"),
                ("{g:обратился|обратилась}", "Пример: обратился/обратилась"),
            ]
        )
        gender_row.setVisible(False)
        gender_hint.setVisible(False)
        extras_btn.toggled.connect(gender_row.setVisible)
        extras_btn.toggled.connect(gender_hint.setVisible)

        templates.addWidget(extras_btn)
        templates.addWidget(gender_row)
        templates.addWidget(gender_hint)

        # Test card
        test_card = card_container()
        test = card_layout(test_card, spacing=10)
        test_card.setMaximumHeight(220)

        test_title = QLabel("Тест")
        test_title.setStyleSheet("color:#ffffff;font-size:15px;font-weight:600;")

        self.test_input = QLineEdit()
        self.test_input.setMinimumHeight(32)
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

        self.result_found = QLabel("Найдено: -")
        self.result_method = QLabel("Метод: -")
        self.result_output = QLabel("Выход: -")
        for lbl in (self.result_found, self.result_method, self.result_output):
            lbl.setStyleSheet("color:#bfb0b0;")
            lbl.setWordWrap(True)

        test.addWidget(test_title)
        test.addWidget(test_row)
        test.addWidget(result_label)
        test.addWidget(self.result_found)
        test.addWidget(self.result_method)
        test.addWidget(self.result_output)

        test_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        right_l.addWidget(templates_card)
        right_l.addWidget(test_card)
        right_l.addStretch(1)

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

    def _templates_row(self, texts: list[tuple[str, str]]) -> QWidget:
        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        for t, hint in texts:
            b = QPushButton(t)
            b.setMinimumHeight(34)
            b.setToolTip(hint)
            b.clicked.connect(lambda checked=False, text=t: self.insert_template(text))
            lay.addWidget(b)
        return row

    def _prefixes(self) -> list[str]:
        allowed_chars = {".", ",", "/", "\\", "|"}
        prefixes: list[str] = []
        for raw in self.allowed_prefixes:
            if not raw:
                continue
            cleaned = raw.strip()
            if cleaned in allowed_chars:
                prefixes.append(cleaned)
                continue
            for ch in cleaned:
                if ch in allowed_chars and ch not in prefixes:
                    prefixes.append(ch)
        if prefixes == ["."]:
            return [".", ",", "/", "\\", "|"]
        return prefixes or ["."]

    def _selected_prefix(self) -> str:
        button = self.prefix_group.checkedButton()
        if button is None:
            return self._prefixes()[0]
        return button.text()

    def _update_trigger_preview(self) -> None:
        word = self.trigger_word.text().strip()
        prefix = self._selected_prefix()
        self.trigger_preview.setText(f"{prefix}{word}" if word else f"{prefix}…")

    def _on_type_changed(self) -> None:
        t = self._current_type()
        if t == "Multi":
            self.content_input.setPlaceholderText(
                "Multi: каждая строка = отдельная команда/строка.\n"
                "Пример:\n"
                "/re Привет\n"
                "/me сделал что-то"
            )
            self.type_hint.setText("Multi — несколько строк, вводятся последовательно.")
        elif t == "Command":
            self.content_input.setPlaceholderText("Command: одна команда или несколько команд одной строкой.")
            self.type_hint.setText("Command — команда, обычно начинается с /.") 
        else:
            self.content_input.setPlaceholderText("Text: обычный текст, который будет вставлен/введён.")
            self.type_hint.setText("Text — простой текст без команд.")

    # ----------------------------
    # Actions
    # ----------------------------

    def insert_template(self, text: str) -> None:
        cursor = self.content_input.textCursor()
        cursor.insertText(text)
        self.content_input.setTextCursor(cursor)

    def handle_save(self) -> None:
        trigger = self.trigger_word.text().strip()
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
            "help_section": self._help_section_value(),
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
            self.result_found.setText("Найдено: нет")
            self.result_method.setText("Метод: -")
            self.result_output.setText("Выход: -")
            return

        raw_trigger = raw
        used_prefix = ""
        for prefix in self._prefixes():
            if raw.startswith(prefix):
                raw_trigger = raw[len(prefix) :]
                used_prefix = prefix
                break
        if not used_prefix and not self.allow_no_prefix:
            self.result_found.setText("Найдено: нет")
            self.result_method.setText("Метод: -")
            self.result_output.setText("Выход: -")
            return

        current_trigger = self.trigger_word.text().strip()

        method = "exact"
        found = raw_trigger == current_trigger

        if not found:
            converted = convert_layout(raw_trigger)
            if converted == current_trigger:
                found = True
                method = "ru↔en"

        output = ""
        if found:
            output = apply_variables(self.content_input.toPlainText().strip(), self.variables)

        self.result_found.setText(f"Найдено: {'да' if found else 'нет'}")
        self.result_method.setText(f"Метод: {method}")
        self.result_output.setText(f"Выход: {output if output else '-'}")

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

        self.trigger_word.setText(self.bind_data.get("trigger", ""))
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

        help_section = self.bind_data.get("help_section")
        mapping = {
            None: "Нет",
            "": "Нет",
            "hints": "Подсказки",
            "teleports": "Телепорты",
            "news": "Новости",
            "changelog": "Журнал изменений",
        }
        self.help_section_input.setCurrentText(mapping.get(help_section, "Нет"))
        self._update_trigger_preview()

    def _current_type(self) -> str:
        if self.type_command.isChecked():
            return "Command"
        if self.type_multi.isChecked():
            return "Multi"
        return "Text"

    def _help_section_value(self) -> str | None:
        value = self.help_section_input.currentText()
        mapping = {
            "Нет": None,
            "Подсказки": "hints",
            "Телепорты": "teleports",
            "Новости": "news",
            "Журнал изменений": "changelog",
        }
        return mapping.get(value, None)


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
