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

"""Classes for items that draw and handle selection stuff."""

import logging
import math

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsItem

from beeref.assets import BeeAssets
from beeref import commands
from beeref.config import CommandlineArgs
from beeref import utils


commandline_args = CommandlineArgs()
logger = logging.getLogger('BeeRef')
SELECT_COLOR = QtGui.QColor(116, 234, 231, 255)


class BaseItemMixin:

    def setScale(self, factor):
        if factor <= 0:
            return

        logger.debug(f'Setting scale for {self} to {factor}')
        self.prepareGeometryChange()
        super().setScale(factor)

    def setZValue(self, value):
        logger.debug(f'Setting z-value for {self} to {value}')
        super().setZValue(value)
        self.scene().max_z = max(self.scene().max_z, value)

    def bring_to_front(self):
        self.setZValue(self.scene().max_z + 0.001)

    def setRotation(self, rotation, anchor=None):
        anchor = anchor or QtCore.QPointF(0, 0)
        prev = self.mapToScene(anchor)
        super().setRotation(rotation)

        # Calculate where the anchor moved to so that we can shift the
        # item back to keep the anchor fixed
        diff = self.mapToScene(anchor) - prev
        self.setPos(self.pos() - diff)


class SelectableMixin(BaseItemMixin):
    """Common code for selectable items: Selection outline, handles etc."""

    SELECT_LINE_WIDTH = 4  # line width for the selection box
    SELECT_HANDLE_SIZE = 15  # size of selection handles for scaling
    SELECT_RESIZE_SIZE = 20  # size of hover area for scaling
    SELECT_ROTATE_SIZE = 15  # size of hover area for rotating

    def init_selectable(self):
        self.setAcceptHoverEvents(True)
        self.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsMovable
            | QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsSelectable)

        self.scale_active = False
        self.rotate_active = False
        self.viewport_scale = 1
        self.conf_debug_shapes = commandline_args.draw_debug_shapes

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

    def paint_selectable(self, painter, option, widget):
        if self.conf_debug_shapes:
            self.draw_debug_shape(painter, self.boundingRect(), 0, 255, 0)
            self.draw_debug_shape(painter, self.shape(), 255, 0, 0)

        if not self.has_selection_outline():
            return

        pen = QtGui.QPen(SELECT_COLOR)
        pen.setWidth(self.SELECT_LINE_WIDTH)
        pen.setCosmetic(True)
        painter.setPen(pen)

        # Draw the main selection rectangle
        painter.drawRect(0, 0, self.width, self.height)

        # If it's a single selection, draw the handles:
        if self.has_selection_handles():
            pen.setWidth(self.SELECT_HANDLE_SIZE)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            for corner in self.corners:
                painter.drawPoint(corner)

    @property
    def corners(self):
        """The corners of the item. Used for scale and rotate handles."""
        return (QtCore.QPointF(0, 0),
                QtCore.QPointF(0, self.height),
                QtCore.QPointF(self.width, 0),
                QtCore.QPointF(self.width, self.height))

    @property
    def corners_scene_coords(self):
        """The corners of the item mapped to scene coordinates."""

        return [self.mapToScene(corner) for corner in self.corners]

    def get_scale_bounds(self, corner, margin=0):
        """The interactable shape of the scale handles."""
        path = QtGui.QPainterPath()
        path.addRect(QtCore.QRectF(
            corner.x() - self.select_resize_size/2 - margin,
            corner.y() - self.select_resize_size/2 - margin,
            self.select_resize_size + 2 * margin,
            self.select_resize_size + 2 * margin))
        return path

    def get_rotate_bounds(self, corner):
        """The interactable shape of the rotation area. It sits around the
        scale area like an L shape, e.g. for the bottom right corner:
          │
         ┌┴┬─┐
        ─┤S│R│
         ├─┘ │
         │R R│
         └───┘
        """

        path = QtGui.QPainterPath()

        # The whole square containing the rotate area:
        d = self.get_corner_direction(corner)
        p1 = corner - d * self.select_resize_size / 2
        p2 = p1 + d * (self.select_resize_size + self.select_rotate_size)
        path.addRect(utils.get_rect_from_points(p1, p2))

        # Substract the scale area:
        # We need to make the substracted shape slighty bigger due to this bug:
        # https://bugreports.qt.io/browse/QTBUG-57567
        return path - self.get_scale_bounds(corner, margin=0.001)

    def boundingRect(self):
        bounds = super().boundingRect()
        if not self.has_selection_outline():
            return bounds

        # Add extra space for scale and rotate interactive areas
        margin = self.select_resize_size / 2 + self.select_rotate_size
        return QtCore.QRectF(
            bounds.topLeft().x() - margin,
            bounds.topLeft().y() - margin,
            bounds.bottomRight().x() + 2 * margin,
            bounds.bottomRight().y() + 2 * margin)

    def shape(self):
        path = super().shape()
        if self.has_selection_handles():
            # Add extra space for scale and rotate interactive areas
            for corner in self.corners:
                path += self.get_scale_bounds(corner)
                path += self.get_rotate_bounds(corner)
        return path

    def hoverMoveEvent(self, event):
        if not self.has_selection_handles():
            return

        for corner in self.corners:
            # See if we need to change the cursor for scale areas
            if self.get_scale_bounds(corner).contains(event.pos()):
                direction = self.get_corner_direction(corner)
                if direction.x() == direction.y():
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                else:
                    self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                return
            if self.get_rotate_bounds(corner).contains(event.pos()):
                self.setCursor(BeeAssets().cursor_rotate)
                return

        self.setCursor(Qt.CursorShape.ArrowCursor)

    def hoverEnterEvent(self, event):
        # Always return regular cursor when there aren't any selection handles
        if not self.has_selection_handles():
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if (event.button() == Qt.MouseButtons.LeftButton
                and self.has_selection_handles()):
            for corner in self.corners:
                # Check if we are in one of the corner's scale areas
                if self.get_scale_bounds(corner).contains(event.pos()):
                    # Start scale action for this corner
                    self.scale_active = True
                    self.event_start = event.scenePos()
                    self.scale_direction = self.get_corner_direction(corner)
                    for item in self.selection_action_items():
                        item.scale_anchor = self.get_scale_anchor(item, corner)
                        item.scale_orig_factor = item.scale()
                        item.scale_orig_pos = item.pos()
                    event.accept()
                    return
                # Check if we are in one of the corner's rotate areas
                if self.get_rotate_bounds(corner).contains(event.pos()):
                    # Start rotate action
                    self.rotate_active = True
                    self.rotate_anchor = self.mapToScene(
                        QtCore.QPointF(self.width/2, self.height/2))
                    self.rotate_start_angle = self.get_rotate_angle(event)
                    for item in self.selection_action_items():
                        item.rotate_anchor = self.rotate_anchor
                        item.rotate_orig_degrees = item.rotation()
                    event.accept()
                    return

        super().mousePressEvent(event)

    def get_scale_factor(self, event):
        """Get the scale factor for the current mouse movement."""
        imgsize = self.width + self.height
        p = event.scenePos() - self.event_start
        direction = self.scale_direction
        delta = QtCore.QPointF.dotProduct(direction, p) / imgsize
        return (self.scale_orig_factor + delta) / self.scale_orig_factor

    def get_scale_anchor(self, item, corner):
        """Get the anchor around which the scale for this corner operates."""
        return item.mapFromScene(
            self.mapToScene(self.width - corner.x(), self.height - corner.y()))

    def get_corner_direction(self, corner):
        """Get the direction facing away from the center, e.g. the direction
        in which the scale for this corner increases."""
        return QtCore.QPointF(1 if corner.x() > 0 else -1,
                              1 if corner.y() > 0 else -1)

    def translate_for_scale_anchor(self, scale_factor):
        """Adjust the item's position so that a scale with the given scale
        factor appears to operate around the scale anchor. ``setScale``
        needs to be called separately with ``scale_factor`` multiplied by
        the item's current scale factor.
        """

        factor = self.scale_orig_factor * (scale_factor - 1)
        self.setPos(
            self.scale_orig_pos.x() - self.scale_anchor.x() * factor,
            self.scale_orig_pos.y() - self.scale_anchor.y() * factor,
        )

    def get_rotate_angle(self, event):
        """Get the angle of the current mouse position towards the
        scale center."""

        diff = event.scenePos() - self.rotate_anchor
        return -math.degrees(math.atan2(diff.x(), diff.y()))

    def get_rotate_delta(self, event):
        """Get the rotate delta for the current mouse movement"""
        return self.get_rotate_angle(event) - self.rotate_start_angle

    def mouseMoveEvent(self, event):
        if self.scale_active:
            factor = self.get_scale_factor(event)
            for item in self.selection_action_items():
                item.setScale(item.scale_orig_factor * factor)
                item.translate_for_scale_anchor(factor)
            event.accept()
        elif self.rotate_active:
            delta = self.get_rotate_delta(event)
            for item in self.selection_action_items():
                item.setRotation(item.rotate_orig_degrees + delta,
                                 item.mapFromScene(self.rotate_anchor))
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.scale_active:
            self.scene().undo_stack.push(
                commands.ScaleItemsBy(
                    self.selection_action_items(),
                    self.get_scale_factor(event),
                    ignore_first_redo=True))
            self.scale_active = False
            event.accept()
        elif self.rotate_active:
            self.scene().on_selection_change()
            self.scene().undo_stack.push(
                commands.RotateItemsBy(
                    self.selection_action_items(),
                    self.get_rotate_delta(event),
                    self.rotate_anchor,
                    ignore_first_redo=True))
            self.rotate_active = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def on_view_scale_change(self):
        self.prepareGeometryChange()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self.prepareGeometryChange()
            if hasattr(self, 'on_selected_change'):
                self.on_selected_change(value)
        return super().itemChange(change, value)


class MultiSelectItem(SelectableMixin,
                      QtWidgets.QGraphicsRectItem):
    """The multi selection outline around all selected items."""

    def __init__(self):
        super().__init__()
        self.init_selectable()

    def __str__(self):
        return (f'MultiSelectItem {self.width} x {self.height}')

    @property
    def width(self):
        return self.rect().width()

    @property
    def height(self):
        return self.rect().height()

    def paint(self, painter, option, widget):
        self.paint_selectable(painter, option, widget)

    def has_selection_outline(self):
        return True

    def has_selection_handles(self):
        return True

    def selection_action_items(self):
        """The items affected by selection actions like scaling and rotating.
        """
        return list(self.scene().selectedItems())

    def fit_selection_area(self, rect):
        """Updates itself to fit the given selection area."""

        logging.debug(f'Fit selection area to {rect}')
        self.setRect(0, 0, rect.width(), rect.height())
        self.setPos(rect.topLeft())
        self.setScale(1)
        self.setRotation(0)
        self.setSelected(True)

    def mousePressEvent(self, event):
        if (event.button() == Qt.MouseButtons.LeftButton
                and event.modifiers() == Qt.KeyboardModifiers.ControlModifier):
            # We still need to be able to select additional images
            # within/"under" the multi select rectangle, so let ctrl+click
            # events pass through
            event.ignore()
            return

        super().mousePressEvent(event)


class RubberbandItem(BaseItemMixin, QtWidgets.QGraphicsRectItem):
    """The outline for the rubber band selection."""

    def __init__(self):
        super().__init__()
        color = QtGui.QColor(SELECT_COLOR)
        color.setAlpha(40)
        self.setBrush(QtGui.QBrush(color))

    def __str__(self):
        return (f'RubberbandItem {self.width} x {self.height}')

    @property
    def width(self):
        return self.rect().width()

    @property
    def height(self):
        return self.rect().height()

    def fit(self, point1, point2):
        """Updates itself to fit the two given points."""

        self.setRect(utils.get_rect_from_points(point1, point2))
        logger.debug(f'Updated rubberband {self}')
