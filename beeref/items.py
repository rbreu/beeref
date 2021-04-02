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
from beeref.config import CommandlineArgs


commandline_args = CommandlineArgs()
logger = logging.getLogger('BeeRef')


class BeePixmapItem(QtWidgets.QGraphicsPixmapItem):
    """Class for images added by the user."""

    select_color = QtGui.QColor(116, 234, 231, 255)
    SELECT_LINE_WIDTH = 4  # line width for the selection box
    SELECT_HANDLE_SIZE = 15  # size of selection handles for scaling
    SELECT_RESIZE_SIZE = 20  # size of hover area for scaling
    SELECT_ROTATE_SIZE = 20  # size of hover area for rotating

    def __init__(self, image, filename=None):
        super().__init__(QtGui.QPixmap.fromImage(image))
        self.save_id = None
        self.filename = filename
        logger.debug(f'Initialized {self}')

        self.setAcceptHoverEvents(True)
        self.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsMovable
            | QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsSelectable)

        self.scale_active_corner = None
        self.viewport_scale = 1
        self.conf_debug_shapes = commandline_args.draw_debug_shapes

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
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self.prepareGeometryChange()
            if(value and self.scene() and not self.scene().has_selection()):
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
            self._view_scale = scale

        # It can happen that the item is already removed from
        # the scene but its boundingRect is still needed. Keep the
        # last known scaling factor for that case
        return value / getattr(self, '_view_scale', 1) / self.scale()

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

        if self.conf_debug_shapes:
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
            for corner in self.corners:
                painter.drawPoint(*corner)

    @property
    def corners(self):
        """The corners of the items. Used for scale and rotate handles."""
        return ((0, 0),
                (0, self.height),
                (self.width, 0),
                (self.width, self.height))

    def get_scale_bounds(self, center):
        """The interactable shape of the scale handles."""
        return QtCore.QRectF(
            center[0] - self.select_resize_size/2,
            center[1] - self.select_resize_size/2,
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

        # Add extra space for scale and rotate interactive areas
        margin = self.select_resize_size / 2 + self.select_rotate_size
        return QtCore.QRectF(
            bounds.topLeft().x() - margin,
            bounds.topLeft().y() - margin,
            bounds.bottomRight().x() + 2 * margin,
            bounds.bottomRight().y() + 2 * margin)

    def shape(self):
        shape_ = super().shape()
        if self.isSelected():
            # Add extra space for scale and rotate interactive areas
            path = QtGui.QPainterPath()
            for corner in self.corners:
                path.addRect(self.get_scale_bounds(corner))
            path.addRect(self.bottom_right_rotate_bounds)
            shape_ = shape_ + path
        return shape_

    def hoverMoveEvent(self, event):
        if not self.isSelected() or not self.scene().has_single_selection():
            return

        for corner in self.corners:
            # See if we need to change the cursor for scale areas
            if self.get_scale_bounds(corner).contains(event.pos()):
                direction = self.get_scale_direction(corner)
                if direction[0] == direction[1]:
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                else:
                    self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                return

        if self.bottom_right_rotate_bounds.contains(event.pos()):
            self.setCursor(Qt.CursorShape.ForbiddenCursor)
            return

        self.setCursor(Qt.CursorShape.ArrowCursor)

    def hoverEnterEvent(self, event):
        # Always return regular cursor when item isn't selected
        if not self.isSelected() or not self.scene().has_single_selection():
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if (event.button() == Qt.MouseButtons.LeftButton
                and self.isSelected() and self.scene().has_single_selection()):
            for corner in self.corners:
                # Check if we are in one of the corner's scale areas
                if self.get_scale_bounds(corner).contains(event.pos()):
                    # Start scale action for this corner
                    self.scale_active_corner = corner
                    self.scale_start = event.scenePos()
                    self.scale_orig_factor = self.scale()
                    self.scale_orig_pos = self.pos()
                    event.accept()
                    return

        super().mousePressEvent(event)

    def get_scale_delta(self, event, corner):
        imgsize = self.width + self.height
        p = event.scenePos() - self.scale_start
        direction = self.get_scale_direction(corner)
        return (direction[0] * p.x() + direction[1] * p.y()) / imgsize

    def get_scale_anchor(self, corner):
        """Get the anchor around which the scale for this corner operates."""
        return(self.width - corner[0], self.height - corner[1])

    def get_scale_direction(self, corner):
        """Get the direction in which the scale for this corner increases"""
        x = 1 if corner[0] > 0 else -1
        y = 1 if corner[1] > 0 else -1
        return (x, y)

    def translate_for_scale_anchor(self, orig_pos, scale_delta, anchor):
        """Adjust the item's position so that a scale with the given scale
        delta appears to operate around the given anchor. ``setScale`` needs
        to be called separately with delta *added* to the current item's scale
        factor."""

        self.setPos(
            orig_pos.x() - anchor[0] * scale_delta,
            orig_pos.y() - anchor[1] * scale_delta,
        )

    def mouseMoveEvent(self, event):
        if self.scale_active_corner:
            delta = self.get_scale_delta(event, self.scale_active_corner)
            self.setScale(self.scale_orig_factor + delta)
            self.translate_for_scale_anchor(
                self.scale_orig_pos,
                delta,
                self.get_scale_anchor(self.scale_active_corner))
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.scale_active_corner:
            self.scene().undo_stack.push(
                commands.ScaleItemsByDelta(
                    [self],
                    self.get_scale_delta(event, self.scale_active_corner),
                    self.get_scale_anchor(self.scale_active_corner),
                    ignore_first_redo=True))
            self.scale_active_corner = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def on_view_scale_change(self):
        self.prepareGeometryChange()
