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

"""Classes for items that are added to the scene by the user (images,
text).
"""

import logging

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsItem

from beeref import commands


logger = logging.getLogger('BeeRef')


class BeePixmapItem(QtWidgets.QGraphicsPixmapItem):
    """Class for images added by the user."""

    select_color = QtGui.QColor(116, 234, 231, 255)
    SELECT_LINE_WIDTH = 4  # line width for the selection box
    SELECT_HANDLE_SIZE = 15  # size of selection handles for scaling
    SELECT_RESIZE_SIZE = 30  # size of hover area for scaling
    SELECT_ROTATE_SIZE = 30  # size of hover area for rotating
    select_debug = False  # Draw debug shapes

    def __init__(self, image, filename=None):
        super().__init__(QtGui.QPixmap.fromImage(image))
        self.save_id = None
        self.filename = filename
        logger.debug(f'Initialized {self}')

        self.setAcceptHoverEvents(True)
        self.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsMovable
            | QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsSelectable)

        self.single_select_mode = False
        self.scale_active = False
        self.viewport_scale = 1

    def __str__(self):
        return (f'Image "{self.filename}" '
                f'with dimensions {self.width} x {self.height}')

    def setScale(self, factor):
        if factor <= 0:
            return

        logger.debug(f'Setting scale for image "{self.filename}" to {factor}')
        self.prepareGeometryChange()
        super().setScale(factor)

    def setZValue(self, value):
        logger.debug(f'Setting z-value for image "{self.filename}" to {value}')
        super().setZValue(value)
        self.scene().max_z = max(self.scene().max_z, value)

    def bring_to_front(self):
        self.setZValue(self.scene().max_z + 0.001)

    def set_pos_center(self, x, y):
        """Sets the position using the item's center as the origin point."""

        self.setPos(x - self.width * self.scale() / 2,
                    y - self.height * self.scale() / 2)

    @property
    def width(self):
        return self.pixmap().size().width()

    @property
    def height(self):
        return self.pixmap().size().height()

    def itemChange(self, change, value):
        if (change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange
                and value
                and self.scene()
                and not self.scene().has_selection()):
            self.bring_to_front()
        return super().itemChange(change, value)

    def pixmap_to_bytes(self):
        """Convert the pixmap data to PNG bytestring."""
        barray = QtCore.QByteArray()
        buffer = QtCore.QBuffer(barray)
        buffer.open(QtCore.QIODevice.OpenMode.WriteOnly)
        img = self.pixmap().toImage()
        img.save(buffer, 'PNG')
        return barray.data()

    def pixmap_from_bytes(self, data):
        """Set image pimap from a bytestring."""
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(data)
        self.setPixmap(pixmap)

    def fixed_length_for_viewport(self, value):
        """The interactable areas need to stay the same size on the
        screen so we need to adjust the values according to the scale
        factor sof the view and the item."""

        if self.scene():
            scale = self.scene().views()[0].get_scale()
            return value / scale / self.scale()
        else:
            # This can happen when the item is already removed from
            # the scene but its boundingRect is still needed. Use the
            # last known scaling factor instead
            return value * self.viewport_scale

    @property
    def select_resize_size(self):
        return self.fixed_length_for_viewport(self.SELECT_RESIZE_SIZE)

    @property
    def select_rotate_size(self):
        return self.fixed_length_for_viewport(self.SELECT_ROTATE_SIZE)

    def draw_debug_shape(self, painter, shape, r, g, b):
        color = QtGui.QColor(r, g, b, 50)
        if isinstance(shape, QtCore.QRectF):
            painter.fillRect(shape, color)
        else:
            painter.fillPath(shape, color)

    def paint(self, painter, option, widget):
        painter.drawPixmap(0, 0, self.pixmap())

        if self.select_debug:
            self.draw_debug_shape(painter, self.boundingRect(), 0, 255, 0)
            self.draw_debug_shape(painter, self.shape(), 255, 0, 0)

        if not self.isSelected():
            return

        pen = QtGui.QPen(self.select_color)
        pen.setWidth(self.SELECT_LINE_WIDTH)
        pen.setCosmetic(True)
        painter.setPen(pen)

        # Draw the main selection rectangle
        painter.drawRect(0, 0, self.width, self.height)

        single_select_mode = self.scene().has_single_selection()

        # If it's a single selection, draw the handles:
        if single_select_mode:
            pen.setWidth(self.SELECT_HANDLE_SIZE)
            painter.setPen(pen)
            painter.drawPoint(self.width, self.height)

    @property
    def bottom_right_scale_bounds(self):
        """The interactable shape of the bottom right scale handle"""
        return QtCore.QRectF(
            self.width - self.select_resize_size/2,
            self.height - self.select_resize_size/2,
            self.select_resize_size,
            self.select_resize_size)

    @property
    def bottom_right_rotate_bounds(self):
        """The interactable shape of the bottom right rotate handle"""
        return QtCore.QRectF(
            self.width + self.select_resize_size / 2,
            self.height + self.select_resize_size / 2,
            self.select_rotate_size, self.select_rotate_size)

    def boundingRect(self):
        bounds = super().boundingRect()
        if not self.isSelected():
            return bounds
        margin = self.select_resize_size / 2 + self.select_rotate_size
        return QtCore.QRectF(
            bounds.topLeft().x() - margin,
            bounds.topLeft().y() - margin,
            bounds.bottomRight().x() + 2 * margin,
            bounds.bottomRight().y() + 2 * margin)

    def shape(self):
        shape_ = super().shape()
        if self.isSelected():
            path = QtGui.QPainterPath()
            path.addRect(self.bottom_right_scale_bounds)
            path.addRect(self.bottom_right_rotate_bounds)
            shape_ = shape_ + path
        return shape_

    def update_selection(self):
        new_scale = self.fixed_length_for_viewport(1)
        if new_scale != self.viewport_scale:
            logger.debug('Selection geometry changed')
            self.prepareGeometryChange()
            self.viewport_scale = new_scale

    def hoverMoveEvent(self, event):
        if not self.isSelected():
            return
        if self.bottom_right_scale_bounds.contains(event.pos()):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif self.bottom_right_rotate_bounds.contains(event.pos()):
            self.setCursor(Qt.CursorShape.ForbiddenCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def hoverEnterEvent(self, event):
        if not self.isSelected():
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if (event.button() == Qt.MouseButtons.LeftButton
                and self.bottom_right_scale_bounds.contains(event.pos())
                and self.isSelected()):
            self.scale_active = True
            self.orig_scale_factor = self.scale()
            self.scale_start = event.scenePos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def get_scale_delta(self, event):
        imgsize = self.width + self.height
        p = event.scenePos() - self.scale_start
        return (p.x() + p.y()) / imgsize

    def mouseMoveEvent(self, event):
        if self.scale_active:
            delta = self.get_scale_delta(event)
            self.setScale(self.orig_scale_factor + delta)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.scale_active:
            self.scene().undo_stack.push(
                commands.ScaleItemsBy([self],
                                      self.get_scale_delta(event),
                                      ignore_first_redo=True))
            self.scale_active = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
