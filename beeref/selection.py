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

        bounds = self.parentItem().boundingRect()
        pos = bounds.bottomRight()
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
        path.addRect(self.boundingRect())
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

        self.single_select_mode = self.parentItem()\
            .scene().has_single_selection()

        self.setAcceptHoverEvents(self.single_select_mode)
        self.setAcceptDrops(self.single_select_mode)


        # If it's a single selection, draw the handles:
        if self.single_select_mode:
            self.setFlags(
                QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsSelectable)
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
        if not self.single_select_mode:
            return

        # In bottomright scale area?
        if self.bottom_right_scale_bounds.contains(event.pos()):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def dragEnterEvent(self, event):
        print('OOOOOOOOOOOOOOOdrag enter')
