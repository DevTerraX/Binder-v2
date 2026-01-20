from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .common import card_container, card_layout, section_title


class ImportExportPage(QWidget):
    export_requested = Signal(str)
    import_new_requested = Signal()
    import_merge_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(section_title("Импорт / Экспорт"))

        card = card_container()
        card_layout(card)
        profile_row = QWidget()
        profile_layout = QHBoxLayout(profile_row)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(10)

        self.profile = QComboBox()
        export_btn = QPushButton("Экспорт профиля")
        export_btn.setObjectName("Primary")
        export_btn.clicked.connect(self._emit_export)
        profile_layout.addWidget(self.profile)
        profile_layout.addWidget(export_btn)
        profile_layout.addStretch(1)

        import_row = QWidget()
        import_layout = QHBoxLayout(import_row)
        import_layout.setContentsMargins(0, 0, 0, 0)
        import_layout.setSpacing(10)
        import_new_btn = QPushButton("Импорт в новый профиль")
        import_merge_btn = QPushButton("Импорт в текущий профиль")
        import_new_btn.clicked.connect(self.import_new_requested.emit)
        import_merge_btn.clicked.connect(self._emit_import_merge)
        import_layout.addWidget(import_new_btn)
        import_layout.addWidget(import_merge_btn)
        import_layout.addStretch(1)

        layout.addWidget(card)
        card.layout().addWidget(profile_row)
        card.layout().addWidget(import_row)
        layout.addStretch(1)

    def set_profiles(self, profiles: list[dict], active_id: str | None) -> None:
        self.profile.clear()
        active_index = 0
        for idx, profile in enumerate(profiles):
            self.profile.addItem(profile.get("name", ""), profile.get("id"))
            if profile.get("id") == active_id:
                active_index = idx
        self.profile.setCurrentIndex(active_index)

    def _emit_export(self) -> None:
        profile_id = self.profile.currentData()
        if profile_id:
            self.export_requested.emit(profile_id)

    def _emit_import_merge(self) -> None:
        profile_id = self.profile.currentData()
        if profile_id:
            self.import_merge_requested.emit(profile_id)
