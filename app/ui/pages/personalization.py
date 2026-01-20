from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .common import card_container, card_layout, section_title


class PersonalizationPage(QWidget):
    changed = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(section_title("Персонализация"))

        gender_card = card_container()
        gender_layout = card_layout(gender_card)
        gender_title = QLabel("Пол")

        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        self.gender_group = QButtonGroup(button_row)
        self.male_btn = QPushButton("Мужской")
        self.female_btn = QPushButton("Женский")
        self.male_btn.setCheckable(True)
        self.female_btn.setCheckable(True)
        self.male_btn.setChecked(True)
        self.gender_group.addButton(self.male_btn)
        self.gender_group.addButton(self.female_btn)

        self.male_btn.clicked.connect(self.emit_change)
        self.female_btn.clicked.connect(self.emit_change)

        button_layout.addWidget(self.male_btn)
        button_layout.addWidget(self.female_btn)
        button_layout.addStretch(1)

        preview = QLabel("Пример: {g:мог|могла} помочь вам.")
        preview.setStyleSheet("color: #c2b2b2;")

        gender_layout.addWidget(gender_title)
        gender_layout.addWidget(button_row)
        gender_layout.addWidget(preview)

        discord_card = card_container()
        discord_layout = card_layout(discord_card)
        discord_layout.addWidget(QLabel("Discord"))
        form = QFormLayout()
        self.discord_me = QLineEdit()
        self.discord_zga = QLineEdit()
        self.discord_ga = QLineEdit()
        self.me_name = QLineEdit()
        for field in (self.discord_me, self.discord_zga, self.discord_ga, self.me_name):
            field.editingFinished.connect(self.emit_change)

        form.addRow("Мой Discord:", self.discord_me)
        form.addRow("Discord ЗГА:", self.discord_zga)
        form.addRow("Discord ГА:", self.discord_ga)
        form.addRow("Моё имя/ник:", self.me_name)
        discord_layout.addLayout(form)

        layout.addWidget(gender_card)
        layout.addWidget(discord_card)
        layout.addStretch(1)

    def set_values(self, variables: dict) -> None:
        gender = variables.get("gender", "male")
        self.male_btn.blockSignals(True)
        self.female_btn.blockSignals(True)
        if gender == "female":
            self.female_btn.setChecked(True)
        else:
            self.male_btn.setChecked(True)
        self.male_btn.blockSignals(False)
        self.female_btn.blockSignals(False)
        self.discord_me.setText(variables.get("discord_me", ""))
        self.discord_zga.setText(variables.get("discord_zga", ""))
        self.discord_ga.setText(variables.get("discord_ga", ""))
        self.me_name.setText(variables.get("me_name", ""))

    def emit_change(self) -> None:
        gender = "female" if self.female_btn.isChecked() else "male"
        payload = {
            "gender": gender,
            "discord_me": self.discord_me.text().strip(),
            "discord_zga": self.discord_zga.text().strip(),
            "discord_ga": self.discord_ga.text().strip(),
            "me_name": self.me_name.text().strip(),
        }
        self.changed.emit(payload)
