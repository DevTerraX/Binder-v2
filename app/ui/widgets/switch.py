from __future__ import annotations

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class ToggleSwitch(QWidget):
    toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._checked = False
        self._offset = 0.0
        self._animation = QPropertyAnimation(self, b"offset", self)
        self._animation.setDuration(140)
        self._animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(42, 22)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, value: bool) -> None:
        if self._checked == value:
            return
        self._checked = value
        self._animate()
        self.toggled.emit(self._checked)
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton and self.isEnabled():
            self.setChecked(not self._checked)
        super().mousePressEvent(event)

    def _animate(self) -> None:
        self._animation.stop()
        self._animation.setStartValue(self._offset)
        self._animation.setEndValue(1.0 if self._checked else 0.0)
        self._animation.start()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height())

        if not self.isEnabled():
            track_color = QColor(28, 28, 28)
            border_color = QColor(60, 60, 60)
        elif self._checked:
            track_color = QColor(27, 58, 37)
            border_color = QColor(47, 122, 63)
        else:
            track_color = QColor(58, 20, 20)
            border_color = QColor(122, 18, 18)

        painter.setPen(border_color)
        painter.setBrush(track_color)
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 11, 11)

        knob_radius = 8
        x_min = 3
        x_max = self.width() - knob_radius * 2 - 3
        x = x_min + (x_max - x_min) * self._offset
        knob_rect = QRectF(x, 3, knob_radius * 2, knob_radius * 2)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(235, 235, 235))
        painter.drawEllipse(knob_rect)

    def getOffset(self) -> float:  # noqa: N802
        return self._offset

    def setOffset(self, value: float) -> None:  # noqa: N802
        self._offset = value
        self.update()

    offset = Property(float, getOffset, setOffset)
