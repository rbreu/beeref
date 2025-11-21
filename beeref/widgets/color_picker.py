from __future__ import annotations

import math
from typing import Optional

from PyQt6 import QtCore, QtGui, QtWidgets


class HSVColorWheel(QtWidgets.QWidget):
    """Interactive HSV color wheel for selecting hue and saturation."""

    colorChanged = QtCore.pyqtSignal(int, int)  # hue, saturation

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self._hue = 0
        self._saturation = 0
        self._value = 255
        self._wheel_image: Optional[QtGui.QImage] = None
        self._wheel_side = 0
        self._highlight_radius = 8

    def sizeHint(self) -> QtCore.QSize:  # noqa: D401
        return QtCore.QSize(260, 260)

    def setValue(self, value: int) -> None:
        value = max(0, min(255, value))
        if self._value != value:
            self._value = value
            self.update()

    def setHueSaturation(self, hue: int, saturation: int, emit: bool = False) -> None:
        hue = int(hue) % 360
        saturation = max(0, min(255, int(saturation)))
        if self._hue == hue and self._saturation == saturation:
            return
        self._hue = hue
        self._saturation = saturation
        if emit:
            self.colorChanged.emit(self._hue, self._saturation)
        self.update()

    def setColor(self, color: QtGui.QColor) -> None:
        hue, saturation, value, _ = color.getHsv()
        if hue == -1:  # grayscale
            hue = self._hue
        self.setHueSaturation(hue, saturation)
        self.setValue(value)

    def hue(self) -> int:
        return self._hue

    def saturation(self) -> int:
        return self._saturation

    def color(self) -> QtGui.QColor:
        return QtGui.QColor.fromHsv(self._hue, self._saturation, self._value)

    def _generate_wheel_image(self, side: int) -> QtGui.QImage:
        image = QtGui.QImage(side, side, QtGui.QImage.Format.Format_ARGB32)
        image.fill(QtGui.QColor(0, 0, 0, 0))

        center = side / 2.0
        radius = side / 2.0

        for y in range(side):
            for x in range(side):
                dx = x - center + 0.5
                dy = y - center + 0.5
                distance = math.hypot(dx, dy)
                if distance > radius:
                    continue

                hue = int(math.degrees(math.atan2(-dy, dx))) % 360
                saturation = int(min(1.0, distance / radius) * 255)
                color = QtGui.QColor()
                color.setHsv(hue, saturation, 255)
                image.setPixelColor(x, y, color)

        return image

    def _ensure_wheel_image(self) -> None:
        side = min(self.width(), self.height())
        if side <= 0:
            return
        if self._wheel_image is None or self._wheel_side != side:
            self._wheel_side = side
            self._wheel_image = self._generate_wheel_image(side)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # noqa: D401
        super().resizeEvent(event)
        self._wheel_image = None
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:  # noqa: D401
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        self._ensure_wheel_image()
        if not self._wheel_image:
            return

        side = self._wheel_side
        rect_side = min(self.width(), self.height())
        x = (self.width() - rect_side) / 2
        y = (self.height() - rect_side) / 2
        target_rect = QtCore.QRectF(x, y, rect_side, rect_side)
        painter.drawImage(target_rect, self._wheel_image)

        # Draw marker representing the selected color
        radius = rect_side / 2.0
        center = QtCore.QPointF(target_rect.center())
        angle_rad = math.radians(self._hue)
        distance = (self._saturation / 255.0) * radius
        marker_x = center.x() + math.cos(angle_rad) * distance
        marker_y = center.y() - math.sin(angle_rad) * distance
        marker_center = QtCore.QPointF(marker_x, marker_y)

        marker_color = QtGui.QColor.fromHsv(self._hue, self._saturation, self._value)
        marker_radius = self._highlight_radius

        painter.setPen(QtGui.QPen(self.palette().window(), marker_radius / 2))
        painter.setBrush(self.palette().window())
        painter.drawEllipse(marker_center, marker_radius + 2, marker_radius + 2)

        painter.setPen(QtGui.QPen(self.palette().windowText(), 1.5))
        painter.setBrush(QtGui.QBrush(marker_color))
        painter.drawEllipse(marker_center, marker_radius, marker_radius)

    # Interaction utilities
    def _set_from_position(self, pos: QtCore.QPointF) -> None:
        rect_side = min(self.width(), self.height())
        x = (self.width() - rect_side) / 2
        y = (self.height() - rect_side) / 2
        center = QtCore.QPointF(x + rect_side / 2.0, y + rect_side / 2.0)
        dx = pos.x() - center.x()
        dy = center.y() - pos.y()
        angle_deg = (math.degrees(math.atan2(dy, dx)) + 360) % 360
        distance = math.hypot(dx, dy)
        radius = rect_side / 2.0
        distance = min(distance, radius)
        saturation = int((distance / radius) * 255)

        hue_changed = (self._hue != int(angle_deg))
        sat_changed = (self._saturation != saturation)
        if hue_changed or sat_changed:
            self.setHueSaturation(int(angle_deg), saturation, emit=True)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: D401
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._set_from_position(event.position())
            self.setCursor(QtCore.Qt.CursorShape.CrossCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: D401
        if event.buttons() & QtCore.Qt.MouseButton.LeftButton:
            self._set_from_position(event.position())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: D401
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.unsetCursor()
        super().mouseReleaseEvent(event)


class BrightnessSlider(QtWidgets.QWidget):
    """Horizontal brightness selector with gradient background."""

    valueChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self._value = 255
        self._hue = 0
        self._saturation = 0
        self._handle_radius = 8

    def sizeHint(self) -> QtCore.QSize:  # noqa: D401
        return QtCore.QSize(260, 36)

    def minimumSizeHint(self) -> QtCore.QSize:  # noqa: D401
        return QtCore.QSize(180, 32)

    def setHueSaturation(self, hue: int, saturation: int) -> None:
        if self._hue != hue or self._saturation != saturation:
            self._hue = hue
            self._saturation = saturation
            self.update()

    def setValue(self, value: int) -> None:
        value = max(0, min(255, value))
        if self._value != value:
            self._value = value
            self.valueChanged.emit(self._value)
            self.update()

    def value(self) -> int:
        return self._value

    def _color_for_value(self, value: int) -> QtGui.QColor:
        return QtGui.QColor.fromHsv(self._hue, self._saturation, value)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:  # noqa: D401
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        margin = 10
        rect = self.rect().adjusted(margin, margin // 2, -margin, -margin // 2)
        rect = rect.normalized()

        gradient = QtGui.QLinearGradient(rect.left(), rect.center().y(), rect.right(), rect.center().y())
        gradient.setColorAt(0.0, self._color_for_value(0))
        gradient.setColorAt(0.5, self._color_for_value(128))
        gradient.setColorAt(1.0, self._color_for_value(255))

        painter.setPen(QtGui.QPen(self.palette().mid(), 1))
        painter.setBrush(QtGui.QBrush(gradient))
        radius = rect.height() / 2
        painter.drawRoundedRect(rect, radius, radius)

        handle_x = rect.left() + (self._value / 255.0) * rect.width()
        handle_center = QtCore.QPointF(handle_x, rect.center().y())
        handle_color = self._color_for_value(self._value)

        painter.setPen(QtGui.QPen(self.palette().window(), self._handle_radius / 2))
        painter.setBrush(self.palette().window())
        painter.drawEllipse(handle_center, self._handle_radius + 2, self._handle_radius + 2)

        painter.setPen(QtGui.QPen(self.palette().windowText(), 1.5))
        painter.setBrush(QtGui.QBrush(handle_color))
        painter.drawEllipse(handle_center, self._handle_radius, self._handle_radius)

    def _set_from_position(self, pos: QtCore.QPointF) -> None:
        margin = 10
        rect = self.rect().adjusted(margin, margin // 2, -margin, -margin // 2)
        rect = rect.normalized()
        if rect.width() <= 0:
            return
        x = min(rect.right(), max(rect.left(), pos.x()))
        ratio = (x - rect.left()) / rect.width()
        value = int(ratio * 255)
        if value != self._value:
            self._value = value
            self.valueChanged.emit(self._value)
            self.update()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: D401
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._set_from_position(event.position())
            self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: D401
        if event.buttons() & QtCore.Qt.MouseButton.LeftButton:
            self._set_from_position(event.position())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: D401
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.unsetCursor()
        super().mouseReleaseEvent(event)


class ColorPreview(QtWidgets.QFrame):
    """Simple frame showing the currently selected color."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setFixedHeight(36)
        self.setAutoFillBackground(True)

    def setColor(self, color: QtGui.QColor) -> None:
        palette = self.palette()
        palette.setColor(QtGui.QPalette.ColorRole.Window, color)
        self.setPalette(palette)


class ColorPickerDialog(QtWidgets.QDialog):
    """Dialog for choosing a color via HSV color wheel and brightness slider."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None, initial: Optional[QtGui.QColor] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Color Picker")
        self.setModal(True)

        self._wheel = HSVColorWheel(self)
        self._slider = BrightnessSlider(self)
        self._preview = ColorPreview(self)
        self._current_color = QtGui.QColor.fromHsv(0, 0, 255)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._wheel, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._slider)
        layout.addWidget(self._preview)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._wheel.colorChanged.connect(self._on_wheel_changed)
        self._slider.valueChanged.connect(self._on_value_changed)

        if initial is not None:
            self.setColor(initial)
        else:
            self._update_preview()

    def selectedColor(self) -> QtGui.QColor:
        return self._current_color

    def setColor(self, color: QtGui.QColor) -> None:
        color = QtGui.QColor(color)
        hue, saturation, value, _ = color.getHsv()
        if hue == -1:
            hue = 0
        self._wheel.setHueSaturation(hue, saturation)
        self._wheel.setValue(value)
        self._slider.setHueSaturation(hue, saturation)
        self._slider.setValue(value)
        self._current_color = QtGui.QColor.fromHsv(hue, saturation, value)
        self._update_preview()

    def _on_wheel_changed(self, hue: int, saturation: int) -> None:
        self._slider.setHueSaturation(hue, saturation)
        self._wheel.setHueSaturation(hue, saturation)
        value = self._slider.value()
        self._wheel.setValue(value)
        self._current_color = QtGui.QColor.fromHsv(hue, saturation, value)
        self._update_preview()

    def _on_value_changed(self, value: int) -> None:
        self._wheel.setValue(value)
        self._current_color = QtGui.QColor.fromHsv(self._wheel.hue(), self._wheel.saturation(), value)
        self._update_preview()

    def _update_preview(self) -> None:
        self._preview.setColor(self._current_color)


__all__ = [
    "ColorPickerDialog",
    "HSVColorWheel",
    "BrightnessSlider",
]
