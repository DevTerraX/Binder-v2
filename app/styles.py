from PySide6.QtGui import QFont


ACCENT_DARK_RED = "#7a1212"
ACCENT_DARK_RED_LIGHT = "#a01a1a"
ACCENT_DARK_RED_SOFT = "#3a1414"


def app_font() -> QFont:
    return QFont("Copperplate", 10)


APP_QSS = f"""
QWidget {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #0B0B0C, stop: 1 #140607
    );
    color: #dcdcdc;
    font-size: 13px;
}}
QFrame#Sidebar {{
    background: transparent;
    border: none;
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
    background: #0E0E10;
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
    background: rgba(160, 26, 26, 18);
    color: #ffffff;
    border: 1px solid rgba(160, 26, 26, 70);
}}
QPushButton#Primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_DARK_RED}, stop:1 {ACCENT_DARK_RED_LIGHT});
    color: #ffffff;
    text-align: center;
}}
QPushButton#Primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_DARK_RED_LIGHT}, stop:1 #b02020);
}}
QPushButton#Secondary {{
    background: #0E0E10;
    border: 1px solid rgba(255, 255, 255, 18);
}}
QPushButton#Destructive {{
    background: rgba(122, 18, 18, 18);
    border: 1px solid rgba(160, 26, 26, 80);
    color: #f4caca;
}}
QPushButton#Ghost {{
    background: #0E0E10;
    border: 1px solid rgba(255, 255, 255, 14);
}}
QPushButton#Ghost:hover {{
    background: #111114;
}}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
    background: #0E0E10;
    border: 1px solid rgba(255, 255, 255, 10);
    border-radius: 12px;
    padding: 6px 10px;
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
    background: #1f1f1f;
}}
QCheckBox::indicator:checked {{
    background: {ACCENT_DARK_RED_LIGHT};
    border: 1px solid {ACCENT_DARK_RED_LIGHT};
}}
QRadioButton {{
    spacing: 8px;
}}
QTableWidget {{
    background: #1c1c1c;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    gridline-color: #2a2a2a;
}}
QHeaderView::section {{
    background: #1f1f1f;
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
    background: #0E0E10;
    border: 1px solid rgba(255, 255, 255, 14);
    border-radius: 16px;
}}
QFrame#Card QWidget {{
    background: transparent;
}}
QFrame#CardDivider {{
    background: rgba(255, 255, 255, 10);
    max-height: 1px;
    min-height: 1px;
}}
QLabel#Badge {{
    background: #111114;
    color: #bdbdbd;
    border-radius: 8px;
    padding: 1px 8px;
}}
QLabel {{
    background: transparent;
}}
QLabel[badge="type"] {{
    background: rgba(160, 26, 26, 18);
    color: #d8b8b8;
}}
QLabel[badge="category"] {{
    background: #111114;
    color: #bdbdbd;
}}
QCheckBox#Toggle {{
    spacing: 10px;
}}
QCheckBox#Toggle::indicator {{
    width: 40px;
    height: 20px;
    border-radius: 10px;
    background: #2a2a2a;
    border: 1px solid #3a2a2a;
}}
QCheckBox#Toggle::indicator:checked {{
    background: {ACCENT_DARK_RED};
    border: 1px solid {ACCENT_DARK_RED_LIGHT};
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
