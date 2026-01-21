from PySide6.QtGui import QFont


ACCENT_DARK_RED = "#7a1212"
ACCENT_DARK_RED_LIGHT = "#a01a1a"
ACCENT_DARK_RED_SOFT = "#3a1414"


def app_font() -> QFont:
    return QFont("Copperplate", 10)


APP_QSS = f"""
QWidget {{
    background: #0B0B0C;
    color: #dcdcdc;
    font-size: 13px;
}}
QFrame#Sidebar {{
    background: transparent;
    border: none;
}}
QFrame#Sidebar QPushButton {{
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 10);
}}
QFrame#Sidebar QPushButton:checked {{
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 12);
    border-left: 2px solid rgba(160, 26, 26, 80);
    color: #ffffff;
}}
QWidget#DialogRoot {{
    background: #0B0B0C;
}}
QStackedWidget {{
    background: transparent;
}}
QFrame#Header {{
    background: #0B0B0C;
    border-bottom: none;
}}
QFrame#Header QLabel {{
    background: transparent;
}}
QLabel#SectionTitle {{
    color: #ffffff;
    font-size: 17px;
    font-weight: 600;
}}
QPushButton {{
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 18);
    border-radius: 12px;
    padding: 6px 10px;
    text-align: left;
}}
QPushButton:hover {{
    border: 1px solid rgba(255, 255, 255, 28);
    background: #111114;
}}
QPushButton:pressed {{
    background: #0C0C0E;
}}
QPushButton:checked {{
    background: transparent;
    color: #ffffff;
    border: 1px solid rgba(160, 26, 26, 70);
}}
QPushButton#Primary {{
    background: transparent;
    color: #ffffff;
    text-align: center;
    border: 1px solid rgba(160, 26, 26, 70);
}}
QPushButton#Primary:hover {{
    background: #111114;
    border: 1px solid rgba(160, 26, 26, 110);
}}
QPushButton#Secondary {{
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 18);
}}
QPushButton#Destructive {{
    background: transparent;
    border: 1px solid rgba(160, 26, 26, 60);
    color: #e0bcbc;
}}
QPushButton#Ghost {{
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 14);
}}
QPushButton#Ghost:hover {{
    background: #111114;
}}
QPushButton#HelpTab {{
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 12);
    color: #d6d6d6;
    padding: 6px 12px;
}}
QPushButton#HelpTab:hover {{
    border: 1px solid rgba(255, 255, 255, 28);
    background: #111114;
    color: #ffffff;
}}
QPushButton#HelpTab:checked {{
    border: 1px solid rgba(160, 26, 26, 70);
    color: #ffffff;
}}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
    background: #0B0B0C;
    border: 1px solid rgba(255, 255, 255, 10);
    border-radius: 12px;
    padding: 6px 10px;
    color: #e6e6e6;
}}
QLineEdit::placeholder, QTextEdit::placeholder, QPlainTextEdit::placeholder {{
    color: rgba(230, 230, 230, 120);
}}
QLineEdit, QComboBox {{
    min-height: 32px;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: 1px solid rgba(255, 255, 255, 18);
}}
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
}}
QCheckBox::indicator:unchecked {{
    border: 1px solid #3a3a3a;
    background: #141414;
}}
QCheckBox::indicator:checked {{
    background: #141414;
    border: 1px solid rgba(160, 26, 26, 90);
}}
QRadioButton {{
    spacing: 8px;
}}
QTableWidget {{
    background: #0E0E10;
    border: 1px solid rgba(255, 255, 255, 10);
    border-radius: 12px;
    gridline-color: rgba(255, 255, 255, 8);
}}
QHeaderView::section {{
    background: #0E0E10;
    color: #cfcfcf;
    border: none;
    padding: 6px;
}}
QScrollBar:vertical {{
    background: #171717;
    width: 10px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: #2a2a2a;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QFrame#Card {{
    background: #0B0B0C;
    border: 1px solid rgba(255, 255, 255, 8);
    border-radius: 16px;
}}
QFrame#Card QWidget {{
    background: transparent;
}}

QFrame#Card QLineEdit,
QFrame#Card QComboBox {{
    background: #0B0B0C;
    border: 1px solid rgba(255, 255, 255, 10);
    color: #e6e6e6;

    /* вот это делает тонко и красиво */
    border-radius: 10px;
    padding: 5px 10px;
    min-height: 32px;
    max-height: 32px;
    font-size: 13px;
}}

QFrame#Card QPlainTextEdit,
QFrame#Card QTextEdit {{
    background: #0B0B0C;
    border: 1px solid rgba(255, 255, 255, 10);
    color: #e6e6e6;
    border-radius: 10px;
    padding: 8px 10px;
    font-size: 13px;
}}


QFrame#CardDivider {{
    background: rgba(255, 255, 255, 6);
    max-height: 1px;
    min-height: 1px;
}}
QLabel#Badge {{
    background: transparent;
    color: #bdbdbd;
    border-radius: 8px;
    padding: 1px 8px;
    border: 1px solid rgba(255, 255, 255, 10);
}}
QLabel {{
    background: transparent;
}}
QLabel[badge="type"] {{
    background: transparent;
    color: #d8b8b8;
    border: 1px solid rgba(160, 26, 26, 40);
}}
QLabel[badge="category"] {{
    background: transparent;
    color: #bdbdbd;
    border: 1px solid rgba(255, 255, 255, 10);
}}
QCheckBox#Toggle {{
    spacing: 10px;
}}
QCheckBox#Toggle::indicator {{
    width: 40px;
    height: 20px;
    border-radius: 10px;
    background: #141414;
    border: 1px solid rgba(255, 255, 255, 12);
}}
QCheckBox#Toggle::indicator:checked {{
    background: #141414;
    border: 1px solid rgba(160, 26, 26, 90);
}}
QToolButton#ActionIcon {{
    background: transparent;
    border: none;
    padding: 2px;
}}
QToolButton#ActionDelete {{
    background: transparent;
    border: none;
    padding: 2px;
}}
QToolButton#ActionIcon:hover {{
    background: #1f1f1f;
    border-radius: 8px;
}}
QToolButton#ActionDelete:hover {{
    background: #2a1616;
}}
"""
