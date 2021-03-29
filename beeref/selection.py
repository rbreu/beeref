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

from collections.abc import Iterable
import logging

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref import commands


logger = logging.getLogger('BeeRef')


class SelectionItem(QtWidgets.QGraphicsItem):

    color = QtGui.QColor(116, 234, 231, 255)
    LINE_WIDTH = 4
    HANDLE_SIZE = 15  # scale handles
    RESIZE_SIZE = 30  # area for scale hover events
    ROTATE_SIZE = 30  # area for rotation hover events

    debug = False

    def __init__(self, item):
        super().__init__(parent=item)
        self.single_select_mode = False
        self.setAcceptHoverEvents(True)
        self.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsSelectable
            | QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsMovable)
        self.scale_active = False
        self.previous_scale = None
        self.setZValue(1)

    @property
    def bottom_right_scale_bounds(self):
        """The interactable shape of the bottom right scale handle"""
        return QtCore.QRectF(
            self.parentItem().width - self.resize_size/2,
            self.parentItem().height - self.resize_size/2,
            self.resize_size,
            self.resize_size)

    @property
    def bottom_right_rotate_bounds(self):
        """The interactable shape of the bottom right rotate handle"""
        return QtCore.QRectF(
            self.parentItem().width + self.resize_size / 2,
            self.parentItem().height + self.resize_size / 2,
            self.rotate_size, self.rotate_size)

    def scale_with_view(self, value):
        """The interactable areas should always stay the same size on
        the screen so we need to adjust the values according to the scale
        factor of the view."""

        scale = self.scene().views()[0].get_scale()
        return value / scale / self.parentItem().scale()

    def boundingRect(self):
        bounds = self.parentItem().boundingRect()
        margin = self.resize_size / 2 + self.rotate_size
        return QtCore.QRectF(
            bounds.topLeft().x() - margin,
            bounds.topLeft().y() - margin,
            bounds.bottomRight().x() + 2 * margin,
            bounds.bottomRight().y() + 2 * margin)

    @property
    def resize_size(self):
        return self.scale_with_view(self.RESIZE_SIZE)

    @property
    def rotate_size(self):
        return self.scale_with_view(self.ROTATE_SIZE)

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.bottom_right_scale_bounds)
        path.addRect(self.bottom_right_rotate_bounds)
        return path

    def draw_debug_shape(self, painter, shape):
        color = QtGui.QColor(0, 255, 0, 20)
        if isinstance(shape, QtCore.QRectF):
            painter.fillRect(shape, color)
        else:
            painter.fillPath(shape, color)

    def update_geometry(self):
        current_scale = self.scale_with_view(1)
        if current_scale != self.previous_scale:
            logger.debug('Selection geometry update')
            self.prepareGeometryChange()
            self.update()
            self.previous_scale = current_scale

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.color)
        pen.setWidth(self.LINE_WIDTH)
        pen.setCosmetic(True)
        painter.setPen(pen)

        # Draw the main selection rectangle
        painter.drawRect(
            0, 0, self.parentItem().width, self.parentItem().height)

        single_select_mode = self.scene().has_single_selection()
        self.setEnabled(single_select_mode)

        # If it's a single selection, draw the handles:
        if single_select_mode:
            pen.setWidth(self.HANDLE_SIZE)
            painter.setPen(pen)
            painter.drawPoint(
                self.parentItem().width, self.parentItem().height)

        if self.debug:
            self.draw_debug_shape(painter, self.boundingRect())
            self.draw_debug_shape(painter, self.shape())

    def hoverMoveEvent(self, event):
        # In bottomright scale area?
        if self.bottom_right_scale_bounds.contains(event.pos()):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif self.bottom_right_rotate_bounds.contains(event.pos()):
            self.setCursor(Qt.CursorShape.ForbiddenCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButtons.LeftButton:
            self.scale_active = True
            self.orig_scale_factor = self.parentItem().scale()
            self.scale_start = event.scenePos()

    def get_scale_delta(self, event):
        imgsize = self.parentItem().width + self.parentItem().height
        p = event.scenePos() - self.scale_start
        return (p.x() + p.y()) / imgsize

    def mouseMoveEvent(self, event):
        if self.scale_active:
            delta = self.get_scale_delta(event)
            self.parentItem().setScale(self.orig_scale_factor + delta)

    def mouseReleaseEvent(self, event):
        self.scene().undo_stack.push(
            commands.ScaleItemsBy(self.scene().selectedItems(),
                                  self.get_scale_delta(event),
                                  ignore_first_redo=True))
        self.scale_active = False

    @classmethod
    def activate_selection(cls, item):
        """Activates/creates the selection for a given item."""
        if item.childItems():
            item.childItems()[0].setVisible(True)
        else:
            cls(item)

    @classmethod
    def clear_selection(cls, item):
        """Deactives the selection for a given item."""
        # Is it a performance issue to keep the selection items and just
        # hide them?
        # Deleting them might have been the cause of segfaults when
        # they are in the middle of receiving events...
        item.childItems()[0].setVisible(False)

    @classmethod
    def update_selection(cls, items):
        if not isinstance(items, Iterable):
            items = [items]
        for item in items:
            if item.childItems():
                item.childItems()[0].update_geometry()
