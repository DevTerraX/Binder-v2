from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from .common import card_container, card_layout, section_title


def build_page() -> tuple[QWidget, QPushButton]:
    root = QWidget()
    layout = QVBoxLayout(root)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(16)

    layout.addWidget(section_title("Помощь / Changelog"))

    card = card_container()
    card_layout(card)
    card.layout().addWidget(QPushButton("Подсказки"))
    card.layout().addWidget(QPushButton("Телепорты"))
    card.layout().addWidget(QPushButton("Новости"))
    card.layout().addWidget(QPushButton("Журнал изменений"))
    update_btn = QPushButton("Проверить обновления")
    update_btn.setObjectName("Primary")
    card.layout().addWidget(update_btn)

    layout.addWidget(card)
    layout.addStretch(1)
    return root, update_btn
