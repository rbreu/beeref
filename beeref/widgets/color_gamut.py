# This file is part of BeeRef.
#
# BeeRef is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BeeRef is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BeeRef.  If not, see <https://www.gnu.org/licenses/>.

import logging
import math

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt


logger = logging.getLogger(__name__)


class GamutPainterThread(QtCore.QThread):
    """Dedicated thread for drawing the gamut image."""

    finished = QtCore.pyqtSignal(QtGui.QImage)
    radius = 250

    def __init__(self, parent, item):
        super().__init__()
        self.item = item
        self.parent = parent

    def draw_color_wheel_gradient(self, painter, center, radius):
        """Draw a circular HSV color wheel gradient."""
        # Draw gradient by iterating through pixels
        for y in range(2 * radius):
            for x in range(2 * radius):
                # Calculate distance from center
                dx = x - center.x()
                dy = y - center.y()
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Only draw inside the circle
                if distance <= radius:
                    # Calculate angle in radians (same coordinate system as points)
                    angle_rad = math.atan2(dx, dy)
                    
                    # Convert to hue using the same transformation as points
                    # Points use: angle = math.radians(-90 - hue)
                    # So for gradient: hue = -90 - math.degrees(angle_rad)
                    angle_deg = math.degrees(angle_rad)
                    hue = int(-90 - angle_deg) % 360
                    
                    # Calculate saturation based on distance from center
                    # At center (distance=0): saturation=0 (white)
                    # At edge (distance=radius): saturation=255 (full color)
                    saturation = int((distance / radius) * 255)
                    saturation = min(255, max(0, saturation))
                    
                    # Value is always maximum for bright colors
                    value = 255
                    
                    # Create color from HSV
                    color = QtGui.QColor()
                    color.setHsv(hue, saturation, value)
                    
                    # Draw pixel
                    painter.setPen(QtGui.QPen(color, 1))
                    painter.drawPoint(x, y)

    def run(self):
        logger.debug('Start drawing gamut image...')
        self.image = QtGui.QImage(
            QtCore.QSize(2 * self.radius, 2 * self.radius),
            QtGui.QImage.Format.Format_ARGB32)
        self.image.fill(QtGui.QColor(0, 0, 0, 0))

        painter = QtGui.QPainter(self.image)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        center = QtCore.QPoint(self.radius, self.radius)
        
        # Draw color wheel gradient if enabled
        if self.parent.show_color_gamut:
            logger.debug('Drawing color wheel gradient...')
            self.draw_color_wheel_gradient(painter, center, self.radius)
        else:
            # Draw black circle background
            painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, self.radius, self.radius)
        
        logger.debug(f'Threshold: {self.parent.threshold}')

        for (hue, saturation), count in self.item.color_gamut.items():
            if count < self.parent.threshold:
                continue
            hypotenuse = saturation / 255 * self.radius
            angle = math.radians(-90 - hue)
            x = int(math.sin(angle) * hypotenuse) + center.x()
            y = int(math.cos(angle) * hypotenuse) + center.y()
            color = QtGui.QColor()
            color.setHsv(hue, saturation, 255)
            painter.setBrush(QtGui.QBrush(color))
            painter.drawEllipse(QtCore.QPoint(x, y), 3, 3)

        logger.debug('Finished drawing gamut image.')
        self.finished.emit(self.image)


class GamutWidget(QtWidgets.QWidget):

    def __init__(self, parent, item):
        super().__init__(parent)
        self.item = item
        self.image = None
        self.show_color_gamut = False  # Default: gradient disabled
        self.worker = GamutPainterThread(self, item)
        self.worker.finished.connect(self.on_gamut_finished)
        self.worker.start()

    @property
    def threshold(self):
        return self.parent().threshold_input.value()

    def on_gamut_finished(self, image):
        logger.debug('Gamut image update received')
        self.image = image
        self.update()

    def minimumSizeHint(self):
        return QtCore.QSize(200, 200)

    def update_values(self):
        self.worker.start()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(painter.RenderHint.SmoothPixmapTransform)
        if self.image:
            size = min(self.size().width(), self.size().height())
            x = max((self.size().width() - size) / 2, 0)
            y = max((self.size().height() - size) / 2, 0)
            painter.drawImage(QtCore.QRectF(x, y, size, size), self.image)
        else:
            painter.drawText(10, 20, 'Counting pixels...')


class GamutDialog(QtWidgets.QDialog):
    def __init__(self, parent, item):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle('Color Gamut')

        # The input controls on the right
        controls_layout = QtWidgets.QVBoxLayout()

        # Add "View color gamut" checkbox
        self.view_gamut_checkbox = QtWidgets.QCheckBox('View color gamut', self)
        self.view_gamut_checkbox.setChecked(False)
        self.view_gamut_checkbox.stateChanged.connect(self.on_gamut_checkbox_changed)
        controls_layout.addWidget(self.view_gamut_checkbox)

        label = QtWidgets.QLabel('Threshold:', self)
        controls_layout.addWidget(label)
        self.threshold_input = QtWidgets.QSlider(self)
        self.threshold_input.setRange(0, 500)
        self.threshold_input.setValue(20)
        self.threshold_input.setTracking(False)
        self.threshold_input.valueChanged.connect(self.on_value_changed)
        controls_layout.addWidget(
            self.threshold_input, alignment=Qt.AlignmentFlag.AlignHCenter)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        controls_layout.addWidget(buttons)

        # The gamut display
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        self.gamut_widget = GamutWidget(self, item)
        layout.addWidget(self.gamut_widget, stretch=1)

        layout.addLayout(controls_layout, stretch=0)
        self.show()

    def on_gamut_checkbox_changed(self, state):
        """Handle checkbox state change."""
        self.gamut_widget.show_color_gamut = self.view_gamut_checkbox.isChecked()
        self.gamut_widget.update_values()

    def on_value_changed(self, value):
        self.gamut_widget.update_values()
