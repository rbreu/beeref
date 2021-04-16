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


def with_anchor(func):
    """Decorator that adds an anchor parameter to transform operations.

    The anchor is given in item coordinates.
    """

    def wrapper(self, *args, **kwargs):
        # We caculate where the anchor is before and after the transformation
        # and then move the item accordingly to keep the anchor fixed

        anchor = kwargs.pop('anchor', None)
        if not anchor:
            if args and isinstance(args[-1], QtCore.QPointF):
                anchor = args[-1]
                args = args[:-1]

        anchor = anchor or QtCore.QPointF(0, 0)
        prev = self.mapToScene(anchor)
        func(self, *args, **kwargs)
        diff = self.mapToScene(anchor) - prev
        self.setPos(self.pos() - diff)

    return wrapper


class BaseItemMixin:

    @with_anchor
    def setScale(self, value):
        if value <= 0:
            return

        logger.debug(f'Setting scale for {self} to {value}')
        self.prepareGeometryChange()
        super().setScale(value)

    def setZValue(self, value):
        logger.debug(f'Setting z-value for {self} to {value}')
        super().setZValue(value)
        if self.scene():
            self.scene().max_z = max(self.scene().max_z, value)

    def bring_to_front(self):
        self.setZValue(self.scene().max_z + 0.001)

    @with_anchor
    def setRotation(self, value):
        logger.debug(f'Setting rotation for {self} to {value}')
        super().setRotation(value % 360)

    def flip(self):
        """Returns the flip value (1 or -1)"""
        # We use the transformation matrix only for flipping, so checking
        # the x scale is enough
        return self.transform().m11()

    @with_anchor
    def do_flip(self, vertical=False):
        """Flips the item."""
        self.setTransform(QtGui.QTransform.fromScale(-self.flip(), 1))
        if vertical:
            self.setRotation(self.rotation() + 180)

    @property
    def center(self):
        return QtCore.QPointF(self.width, self.height) / 2

    @property
    def center_scene_coords(self):
        """The item's center in scene coordinates."""
        return self.mapToScene(self.center)


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
        self.flip_active = False
        self.just_selected = False
        self.viewport_scale = 1

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
        if commandline_args.debug_shapes:
            self.draw_debug_shape(painter, self.shape(), 255, 0, 0)
        if commandline_args.debug_boundingrects:
            self.draw_debug_shape(painter, self.boundingRect(), 0, 255, 0)
        if (commandline_args.debug_handles and self.has_selection_handles()):
            for corner in self.corners:
                self.draw_debug_shape(
                    painter, self.get_scale_bounds(corner), 0, 0, 255)
                self.draw_debug_shape(
                    painter, self.get_rotate_bounds(corner), 0, 255, 255)
            for edge in self.get_flip_bounds():
                self.draw_debug_shape(painter, edge['rect'], 255, 255, 0)

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
                QtCore.QPointF(self.width, 0),
                QtCore.QPointF(self.width, self.height),
                QtCore.QPointF(0, self.height))

    @property
    def corners_scene_coords(self):
        """The corners of the item mapped to scene coordinates."""

        return [self.mapToScene(corner) for corner in self.corners]

    def get_scale_bounds(self, corner, margin=0):
        """The interactable shape of the scale handles. The scale handles sit
        centered around the visible handle."""
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

    def get_flip_bounds(self):
        """The interactactable shape of the flip handles.

        These stretch around the edge of the item filling the areas
        between the scale and rotate handles, e.g. for the bottom right corner:

          │FFF│
        ──┼─┬─┤
        FF│S│R│
        FF├─┘ │
        FF│R R│
        ──┴───┘
        """

        outer_margin = self.select_resize_size / 2 + self.select_rotate_size
        inner_margin = self.select_resize_size / 2
        return [
            # top:
            {
                'rect': QtCore.QRectF(inner_margin,
                                      -outer_margin,
                                      self.width - 2 * inner_margin,
                                      outer_margin + inner_margin),
                'flip_v': True,
            },
            # bottom:
            {
                'rect': QtCore.QRectF(inner_margin,
                                      self.height - inner_margin,
                                      self.width - 2 * inner_margin,
                                      outer_margin + inner_margin),
                'flip_v': True,
            },
            # left:
            {
                'rect': QtCore.QRectF(-outer_margin,
                                      inner_margin,
                                      outer_margin + inner_margin,
                                      self.height - 2 * inner_margin),
                'flip_v': False,
            },
            # right:
            {
                'rect': QtCore.QRectF(self.width - inner_margin,
                                      inner_margin,
                                      outer_margin + inner_margin,
                                      self.height - 2 * inner_margin),
                'flip_v': False,
            }
        ]

    def boundingRect(self):
        if not self.has_selection_outline():
            return super().boundingRect()

        # Add extra space for the interactive areas
        margin = self.select_resize_size / 2 + self.select_rotate_size
        return QtCore.QRectF(
            -margin, -margin,
            self.width + 2 * margin,
            self.height + 2 * margin)

    def shape(self):
        path = QtGui.QPainterPath()
        if self.has_selection_handles():
            rect = self.boundingRect()
        else:
            rect = super().boundingRect()
        path.addRect(rect)
        return path

    def hoverMoveEvent(self, event):
        if not self.has_selection_handles():
            return

        for corner in self.corners:
            # See if we need to change the cursor for interactable areas
            if self.get_scale_bounds(corner).contains(event.pos()):
                self.event_anchor = self.center_scene_coords
                angle = self.get_rotate_angle(self.mapToScene(corner))
                if abs(angle) >= 157.5 or abs(angle) <= 22.5:
                    self.setCursor(Qt.CursorShape.SizeVerCursor)
                elif 112.5 <= angle <= 157.5 or -67.5 <= angle <= -22.5:
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                elif 67.5 <= abs(angle) <= 112.5:
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                else:
                    self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                return
            elif self.get_rotate_bounds(corner).contains(event.pos()):
                self.setCursor(BeeAssets().cursor_rotate)
                return
        for edge in self.get_flip_bounds():
            if edge['rect'].contains(event.pos()):
                if self.get_edge_flips_v(edge):
                    self.setCursor(BeeAssets().cursor_flip_v)
                else:
                    self.setCursor(BeeAssets().cursor_flip_h)
                return

        self.setCursor(Qt.CursorShape.ArrowCursor)

    def hoverEnterEvent(self, event):
        # Always return regular cursor when there aren't any selection handles
        if not self.has_selection_handles():
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        self.scene().views()[0].reset_previous_transform(toggle_item=self)
        if not self.isSelected():
            self.just_selected = True
        if (event.button() == Qt.MouseButtons.LeftButton
                and self.has_selection_handles()):
            for corner in self.corners:
                # Check if we are in one of the corner's scale areas
                if self.get_scale_bounds(corner).contains(event.pos()):
                    # Start scale action for this corner
                    self.scale_active = True
                    self.event_start = event.scenePos()
                    self.event_direction = self.get_direction_from_center(
                        event.scenePos())
                    self.event_anchor = self.mapToScene(
                        self.get_scale_anchor(corner))
                    for item in self.selection_action_items():
                        item.scale_orig_factor = item.scale()
                    event.accept()
                    return
                # Check if we are in one of the corner's rotate areas
                if self.get_rotate_bounds(corner).contains(event.pos()):
                    # Start rotate action
                    self.rotate_active = True
                    self.event_anchor = self.center_scene_coords
                    self.rotate_start_angle = self.get_rotate_angle(
                        event.scenePos())
                    for item in self.selection_action_items():
                        item.rotate_orig_degrees = item.rotation()
                    event.accept()
                    return
                # Check if we are in one of the flip edges:
                for edge in self.get_flip_bounds():
                    if edge['rect'].contains(event.pos()):
                        self.flip_active = True

        super().mousePressEvent(event)

    def get_scale_factor(self, event):
        """Get the scale factor for the current mouse movement."""
        imgsize = math.sqrt(self.width**2 + self.height**2)
        p = event.scenePos() - self.event_start
        direction = self.event_direction
        delta = QtCore.QPointF.dotProduct(direction, p) / imgsize
        return (self.scale_orig_factor + delta) / self.scale_orig_factor

    def get_scale_anchor(self, corner):
        """Get the anchor around which the scale for this corner operates."""
        return QtCore.QPointF(self.width - corner.x(),
                              self.height - corner.y())

    def get_corner_direction(self, corner):
        """Get the direction facing away from the center, e.g. the direction
        in which the scale for this corner increases."""
        return QtCore.QPointF(1 if corner.x() > 0 else -1,
                              1 if corner.y() > 0 else -1)

    def get_direction_from_center(self, pos):
        """The direction of a point in relation to the item's center."""
        diff = pos - self.center_scene_coords
        length = math.sqrt(QtCore.QPointF.dotProduct(diff, diff))
        return diff / length

    def get_rotate_angle(self, pos):
        """Get the angle of the given position towards the event anchor."""

        diff = pos - self.event_anchor
        return -math.degrees(math.atan2(diff.x(), diff.y()))

    def get_rotate_delta(self, pos, snap=False):
        """Get the rotate delta for the current mouse movement.

        If ``snap`` is True, snap to 15 degree units."""

        delta = self.get_rotate_angle(pos) - self.rotate_start_angle
        if snap:
            target = utils.round_to(self.rotate_orig_degrees + delta, 15)
            delta = target - self.rotate_orig_degrees

        return delta

    def get_edge_flips_v(self, edge):
        """Returns ``True`` if the given edge invokes a horizontal flip,
        ``False`` if it invokes a vertacal flip."""

        if 45 < self.rotation() < 135 or 225 < self.rotation() < 315:
            return not edge['flip_v']
        else:
            return edge['flip_v']

    def mouseMoveEvent(self, event):
        self.scene().views()[0].reset_previous_transform()

        if self.scale_active:
            factor = self.get_scale_factor(event)
            for item in self.selection_action_items():
                item.setScale(item.scale_orig_factor * factor,
                              item.mapFromScene(self.event_anchor))
            event.accept()
            return
        if self.rotate_active:
            snap = (event.modifiers() == Qt.KeyboardModifiers.ControlModifier
                    or event.modifiers() == Qt.KeyboardModifiers.ShiftModifier)
            delta = self.get_rotate_delta(event.scenePos(), snap)
            for item in self.selection_action_items():
                item.setRotation(
                    item.rotate_orig_degrees + delta * item.flip(),
                    item.mapFromScene(self.event_anchor))
            event.accept()
            return
        if self.flip_active:
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        just_selected = self.just_selected
        self.just_selected = False
        if self.scale_active:
            self.scene().undo_stack.push(
                commands.ScaleItemsBy(
                    self.selection_action_items(),
                    self.get_scale_factor(event),
                    self.event_anchor,
                    ignore_first_redo=True))
            self.scale_active = False
            event.accept()
            return
        elif self.rotate_active:
            self.scene().on_selection_change()
            self.scene().undo_stack.push(
                commands.RotateItemsBy(
                    self.selection_action_items(),
                    self.get_rotate_delta(event.scenePos()),
                    self.event_anchor,
                    ignore_first_redo=True))
            self.rotate_active = False
            event.accept()
            return
        elif not just_selected:
            for edge in self.get_flip_bounds():
                if edge['rect'].contains(event.pos()):
                    self.scene().undo_stack.push(
                        commands.FlipItems(
                            self.selection_action_items(),
                            self.center_scene_coords,
                            vertical=self.get_edge_flips_v(edge)))
                    event.accept()
                    self.flip_active = False
                    return
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

        logger.debug(f'Fit selection area to {rect}')

        # Only update when values have changed, otherwise we end up in an
        # infinite event loop sceneChange -> itemChange -> sceneChange ...
        if self.width != rect.width() or self.height != rect.height():
            self.setRect(0, 0, rect.width(), rect.height())
        if self.pos() != rect.topLeft():
            self.setPos(rect.topLeft())
        if self.scale() != 1:
            self.setScale(1)
        if self.rotation() != 0:
            self.setRotation(0)
        if not self.isSelected():
            self.setSelected(True)
        if self.flip() == -1:
            self.setTransform(QtGui.QTransform.fromScale(1, 1))

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
