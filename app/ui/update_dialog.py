from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton

from app.config import APP_VERSION, ASSET_NAME, GITHUB_OWNER, GITHUB_REPO


class UpdateDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Обновление Binder")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        title = QLabel("Проверка обновлений")
        title.setStyleSheet("font-size: 15px; color: #ffffff;")
        layout.addWidget(title)

        repo_label = QLabel(f"GitHub: {GITHUB_OWNER}/{GITHUB_REPO}")
        version_label = QLabel(f"Текущая версия: {APP_VERSION}")
        asset_label = QLabel(f"Asset: {ASSET_NAME}")

        hint = QLabel("Логика обновления подключится через GitHub Releases.")
        hint.setStyleSheet("color: #bfb0b0;")

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)

        layout.addWidget(repo_label)
        layout.addWidget(version_label)
        layout.addWidget(asset_label)
        layout.addWidget(hint)
        layout.addStretch(1)
        layout.addWidget(close_btn)
