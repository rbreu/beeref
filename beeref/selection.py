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


logger = logging.getLogger('BeeRef')


class SelectionItem(QtWidgets.QGraphicsItem):

    color = QtGui.QColor(116, 234, 231, 255)
    handle_size = 30  # scaling handles
    resize_size = 50  # area for scaling hover events
    margin = 200  # margin for bounding box etc

    debug = False

    def __init__(self, item):
        super().__init__(parent=item)
        self.single_select_mode = False
        self.setAcceptHoverEvents(True)
        self.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsSelectable
            | QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsMovable)
        bounds = self.parentItem().boundingRect()
        pos = bounds.bottomRight()
        self.scale_active = False

        # The intercatable shape of the bottom right scale handle:
        self.bottom_right_scale_bounds = QtCore.QRectF(
            pos.x() - self.resize_size/2,
            pos.y() - self.resize_size/2,
            self.resize_size,
            self.resize_size)

    def boundingRect(self):
        bounds = self.parentItem().boundingRect()
        return QtCore.QRectF(
            bounds.topLeft().x() - self.margin,
            bounds.topLeft().y() - self.margin,
            bounds.bottomRight().x() + self.margin * 2,
            bounds.bottomRight().y() + self.margin * 2)

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.bottom_right_scale_bounds)
        return path

    def draw_debug_rect(self, painter, rect):
        pen = QtGui.QPen(QtGui.QColor('red'))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawRect(rect)

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(self.color)
        pen.setWidth(10)
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

    def mouseMoveEvent(self, event):
        if self.scale_active:
            imgsize = self.parentItem().width + self.parentItem().height
            p = event.scenePos() - self.scale_start
            mousemove = p.x() + p.y()
            scale = self.orig_scale_factor + mousemove / imgsize
            self.parentItem().setScale(scale)

    def mouseReleaseEvent(self, event):
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
