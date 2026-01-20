from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QLabel, QVBoxLayout, QWidget


def section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("SectionTitle")
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    return label


def card_container() -> QFrame:
    frame = QFrame()
    frame.setObjectName("Card")
    shadow = QGraphicsDropShadowEffect(frame)
    shadow.setBlurRadius(18)
    shadow.setOffset(0, 6)
    shadow.setColor(QColor(0, 0, 0, 110))
    frame.setGraphicsEffect(shadow)
    return frame


def card_layout(card: QWidget, spacing: int = 12) -> QVBoxLayout:
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(spacing)
    return layout


def badge(text: str, kind: str = "category") -> QLabel:
    label = QLabel(text)
    label.setObjectName("Badge")
    label.setProperty("badge", kind)
    label.setAlignment(Qt.AlignCenter)
    return label
