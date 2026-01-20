import sys

from PySide6.QtWidgets import QApplication

from app.styles import APP_QSS, app_font
from app.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)
    app.setFont(app_font())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
