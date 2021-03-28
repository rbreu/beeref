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

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref import commands


logger = logging.getLogger('BeeRef')


class SelectionItem(QtWidgets.QGraphicsItem):

    color = QtGui.QColor(116, 234, 231, 255)
    LINE_WIDTH = 3
    HANDLE_SIZE = 10  # scaling handles
    RESIZE_SIZE = 30  # area for scaling hover events

    debug = False

    def __init__(self, item):
        super().__init__(parent=item)
        self.single_select_mode = False
        self.setAcceptHoverEvents(True)
        self.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsSelectable
            | QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsMovable)
        self.scale_active = False

    @property
    def bottom_right_scale_bounds(self):
        """The intercatable shape of the bottom right scale handle"""
        bounds = self.parentItem().boundingRect()
        pos = bounds.bottomRight()
        return QtCore.QRectF(
            pos.x() - self.resize_size/2,
            pos.y() - self.resize_size/2,
            self.resize_size,
            self.resize_size)

    def scale_with_view(self, value):
        """The handles and line thickness should always stay the same size on
        the screen so we need to adjust the values according to the scale
        factor of the view."""

        scale = self.parentItem().scene().views()[0].get_scale()
        return value / scale / self.parentItem().scale_factor

    def boundingRect(self):
        bounds = self.parentItem().boundingRect()
        return QtCore.QRectF(
            bounds.topLeft().x() - self.resize_size / 2,
            bounds.topLeft().y() - self.resize_size / 2,
            bounds.bottomRight().x() + self.resize_size,
            bounds.bottomRight().y() + self.resize_size)

    @property
    def handle_size(self):
        return self.scale_with_view(self.HANDLE_SIZE)

    @property
    def resize_size(self):
        return self.scale_with_view(self.RESIZE_SIZE)

    @property
    def line_width(self):
        return self.scale_with_view(self.LINE_WIDTH)

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.bottom_right_scale_bounds)
        return path

    def draw_debug_rect(self, painter, rect):
        pen = QtGui.QPen(QtGui.QColor('red'))
        pen.setWidth(self.line_width / 2)
        painter.setPen(pen)
        painter.drawRect(rect)

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.color)
        pen.setWidth(self.line_width)
        painter.setPen(pen)

        # Draw the main selection rectangle
        bounds = self.parentItem().boundingRect()
        painter.drawRect(bounds)

        single_select_mode = self.parentItem().scene().has_single_selection()
        self.setEnabled(single_select_mode)

        # If it's a single selection, draw the handles:
        if single_select_mode:
            pos = bounds.bottomRight()
            painter.fillRect(pos.x() - self.handle_size/2,
                             pos.y() - self.handle_size/2,
                             self.handle_size,
                             self.handle_size,
                             self.color)

        if self.debug:
            self.draw_debug_rect(painter, self.boundingRect())
            self.draw_debug_rect(painter, self.bottom_right_scale_bounds)

    def hoverMoveEvent(self, event):
        # In bottomright scale area?
        if self.bottom_right_scale_bounds.contains(event.pos()):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
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
        self.parentItem().scene().undo_stack.push(
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
