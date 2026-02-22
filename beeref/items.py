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

import copy
from collections import defaultdict
from functools import cached_property
import logging
import math
import os.path

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref import commands
from beeref.config import BeeSettings
from beeref.constants import COLORS
from beeref.selection import SelectableMixin


logger = logging.getLogger(__name__)

item_registry = {}


def register_item(cls):
    item_registry[cls.TYPE] = cls
    return cls


def sort_by_filename(items):
    """Order items by filename.

    Items with a filename (ordered by filename) first, then items
    without a filename but with a save_id follow (ordered by
    save_id), then remaining items in the order that they have
    been inserted into the scene.
    """

    items_by_filename = []
    items_by_save_id = []
    items_remaining = []

    for item in items:
        if getattr(item, 'filename', None):
            items_by_filename.append(item)
        elif getattr(item, 'save_id', None):
            items_by_save_id.append(item)
        else:
            items_remaining.append(item)

    items_by_filename.sort(key=lambda x: x.filename)
    items_by_save_id.sort(key=lambda x: x.save_id)
    return items_by_filename + items_by_save_id + items_remaining


class BeeItemMixin(SelectableMixin):
    """Base for all items added by the user."""

    def set_pos_center(self, pos):
        """Sets the position using the item's center as the origin point."""

        self.setPos(pos - self.center_scene_coords)

    def has_selection_outline(self):
        return self.isSelected()

    def has_selection_handles(self):
        return (self.isSelected()
                and self.scene()
                and self.scene().has_single_selection())

    def selection_action_items(self):
        """The items affected by selection actions like scaling and rotating.
        """
        return [self]

    def on_selected_change(self, value):
        if (value and self.scene()
                and not self.scene().has_selection()
                and not self.scene().active_mode is None):
            self.bring_to_front()

    def update_from_data(self, **kwargs):
        self.save_id = kwargs.get('save_id', self.save_id)
        self.setPos(kwargs.get('x', self.pos().x()),
                    kwargs.get('y', self.pos().y()))
        self.setZValue(kwargs.get('z', self.zValue()))
        self.setScale(kwargs.get('scale', self.scale()))
        self.setRotation(kwargs.get('rotation', self.rotation()))
        if kwargs.get('flip', 1) != self.flip():
            self.do_flip()


@register_item
class BeePixmapItem(BeeItemMixin, QtWidgets.QGraphicsPixmapItem):
    """Class for images added by the user."""

    TYPE = 'pixmap'
    CROP_HANDLE_SIZE = 15

    def __init__(self, image, filename=None, **kwargs):
        super().__init__(QtGui.QPixmap.fromImage(image))
        self.save_id = None
        self.filename = filename
        self.reset_crop()
        logger.debug(f'Initialized {self}')
        self.is_image = True
        self.crop_mode = False
        self.init_selectable()
        self.settings = BeeSettings()
        self.grayscale = False

    @classmethod
    def create_from_data(self, **kwargs):
        item = kwargs.pop('item')
        data = kwargs.pop('data', {})
        item.filename = item.filename or data.get('filename')
        if 'crop' in data:
            item.crop = QtCore.QRectF(*data['crop'])
        item.setOpacity(data.get('opacity', 1))
        item.grayscale = data.get('grayscale', False)
        return item

    def __str__(self):
        size = self.pixmap().size()
        return (f'Image "{self.filename}" {size.width()} x {size.height()}')

    @property
    def crop(self):
        return self._crop

    @crop.setter
    def crop(self, value):
        logger.debug(f'Setting crop for {self} to {value}')
        self.prepareGeometryChange()
        self._crop = value
        self.update()

    @property
    def grayscale(self):
        return self._grayscale

    @grayscale.setter
    def grayscale(self, value):
        logger.debug('Setting grayscale for {self} to {value}')
        self._grayscale = value
        if value is True:
            # Using the grayscale image format to convert to grayscale
            # loses an image's tranparency. So the straightworward
            # following method gives us an ugly black replacement:
            # img = img.convertToFormat(QtGui.QImage.Format.Format_Grayscale8)

            # Instead, we will fill the background with the current
            # canvas colour, so the issue is only visible if the image
            # overlaps other images. The way we do it here only works
            # as long as the canvas colour is itself grayscale,
            # though.
            img = QtGui.QImage(
                self.pixmap().size(), QtGui.QImage.Format.Format_Grayscale8)
            img.fill(QtGui.QColor(*COLORS['Scene:Canvas']))
            painter = QtGui.QPainter(img)
            painter.drawPixmap(0, 0, self.pixmap())
            painter.end()
            self._grayscale_pixmap = QtGui.QPixmap.fromImage(img)

            # Alternative methods that have their own issues:
            #
            # 1. Use setAlphaChannel of the resulting grayscale
            # image. How do we get the original alpha channel? Using
            # the whole original image also takes color values into
            # account, not just their alpha values.
            #
            # 2. QtWidgets.QGraphicsColorizeEffect() with black colour
            # on the GraphicsItem. This applys to everything the paint
            # method does, so the selection outline/handles will also
            # be gray. setGraphicsEffect is only available on some
            # widgets, so we can't apply it selectively.
            #
            # 3. Going through every pixel and doing it manually — bad
            # performance.
        else:
            self._grayscale_pixmap = None

        self.update()

    def sample_color_at(self, pos):
        ipos = self.mapFromScene(pos)
        if self.grayscale:
            pm = self._grayscale_pixmap
        else:
            pm = self.pixmap()
        img = pm.toImage()

        color = img.pixelColor(int(ipos.x()), int(ipos.y()))
        if color.alpha():
            return color

    def bounding_rect_unselected(self):
        if self.crop_mode:
            return QtWidgets.QGraphicsPixmapItem.boundingRect(self)
        else:
            return self.crop

    def get_extra_save_data(self):
        return {'filename': self.filename,
                'opacity': self.opacity(),
                'grayscale': self.grayscale,
                'crop': [self.crop.topLeft().x(),
                         self.crop.topLeft().y(),
                         self.crop.width(),
                         self.crop.height()]}

    def get_filename_for_export(self, imgformat, save_id_default=None):
        save_id = self.save_id or save_id_default
        assert save_id is not None

        if self.filename:
            basename = os.path.splitext(os.path.basename(self.filename))[0]
            return f'{save_id:04}-{basename}.{imgformat}'
        else:
            return f'{save_id:04}.{imgformat}'

    def get_imgformat(self, img):
        """Determines the format for storing this image."""

        formt = self.settings.valueOrDefault('Items/image_storage_format')

        if formt == 'best':
            # Images with alpha channel and small images are stored as png
            if (img.hasAlphaChannel()
                    or (img.height() < 500 and img.width() < 500)):
                formt = 'png'
            else:
                formt = 'jpg'

        logger.debug(f'Found format {formt} for {self}')
        return formt

    def pixmap_to_bytes(self, apply_grayscale=False, apply_crop=False):
        """Convert the pixmap data to PNG bytestring."""
        barray = QtCore.QByteArray()
        buffer = QtCore.QBuffer(barray)
        buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
        if apply_grayscale and self.grayscale:
            pm = self._grayscale_pixmap
        else:
            pm = self.pixmap()

        if apply_crop:
            pm = pm.copy(self.crop.toRect())

        img = pm.toImage()
        imgformat = self.get_imgformat(img)
        img.save(buffer, imgformat.upper(), quality=90)
        return (barray.data(), imgformat)

    def setPixmap(self, pixmap):
        super().setPixmap(pixmap)
        self.reset_crop()

    def pixmap_from_bytes(self, data):
        """Set image pimap from a bytestring."""
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(data)
        self.setPixmap(pixmap)

    def create_copy(self):
        item = BeePixmapItem(QtGui.QImage(), self.filename)
        item.setPixmap(self.pixmap())
        item.setPos(self.pos())
        item.setZValue(self.zValue())
        item.setScale(self.scale())
        item.setRotation(self.rotation())
        item.setOpacity(self.opacity())
        item.grayscale = self.grayscale
        if self.flip() == -1:
            item.do_flip()
        item.crop = self.crop
        return item

    @cached_property
    def color_gamut(self):
        logger.debug(f'Calculating color gamut for {self}')
        gamut = defaultdict(int)
        img = self.pixmap().toImage()
        # Don't evaluate every pixel for larger images:
        step = max(1, int(max(img.width(), img.height()) / 1000))
        logger.debug(f'Considering every {step}. row/column')

        # Not actually faster than solution below :(
        # ptr = img.bits()
        # size = img.sizeInBytes()
        # pixelsize = int(img.sizeInBytes() / img.width() / img.height())
        # ptr.setsize(size)
        # for pixel in batched(ptr, n=pixelsize):
        #     r, g, b, alpha = tuple(map(ord, pixel))
        #     if 5 < alpha and 5 < r < 250 and 5 < g < 250 and 5 < b < 250:
        #         # Only consider pixels that aren't close to
        #         # transparent, white or black
        #         rgb = QtGui.QColor(r, g, b)
        #         gamut[rgb.hue(), rgb.saturation()] += 1

        for i in range(0, img.width(), step):
            for j in range(0, img.height(), step):
                rgb = img.pixelColor(i, j)
                rgbtuple = (rgb.red(), rgb.blue(), rgb.green())
                if (5 < rgb.alpha()
                        and min(rgbtuple) < 250 and max(rgbtuple) > 5):
                    # Only consider pixels that aren't close to
                    # transparent, white or black
                    gamut[rgb.hue(), rgb.saturation()] += 1

        logger.debug(f'Got {len(gamut)} color gamut values')
        return gamut

    def copy_to_clipboard(self, clipboard):
        clipboard.setPixmap(self.pixmap())

    def reset_crop(self):
        self.crop = QtCore.QRectF(
            0, 0, self.pixmap().size().width(), self.pixmap().size().height())

    @property
    def crop_handle_size(self):
        return self.fixed_length_for_viewport(self.CROP_HANDLE_SIZE)

    def crop_handle_topleft(self):
        topleft = self.crop_temp.topLeft()
        return QtCore.QRectF(
            topleft.x(),
            topleft.y(),
            self.crop_handle_size,
            self.crop_handle_size)

    def crop_handle_bottomleft(self):
        bottomleft = self.crop_temp.bottomLeft()
        return QtCore.QRectF(
            bottomleft.x(),
            bottomleft.y() - self.crop_handle_size,
            self.crop_handle_size,
            self.crop_handle_size)

    def crop_handle_bottomright(self):
        bottomright = self.crop_temp.bottomRight()
        return QtCore.QRectF(
            bottomright.x() - self.crop_handle_size,
            bottomright.y() - self.crop_handle_size,
            self.crop_handle_size,
            self.crop_handle_size)

    def crop_handle_topright(self):
        topright = self.crop_temp.topRight()
        return QtCore.QRectF(
            topright.x() - self.crop_handle_size,
            topright.y(),
            self.crop_handle_size,
            self.crop_handle_size)

    def crop_handles(self):
        return (self.crop_handle_topleft,
                self.crop_handle_bottomleft,
                self.crop_handle_bottomright,
                self.crop_handle_topright)

    def crop_edge_top(self):
        topleft = self.crop_temp.topLeft()
        return QtCore.QRectF(
            topleft.x() + self.crop_handle_size,
            topleft.y(),
            self.crop_temp.width() - 2 * self.crop_handle_size,
            self.crop_handle_size)

    def crop_edge_left(self):
        topleft = self.crop_temp.topLeft()
        return QtCore.QRectF(
            topleft.x(),
            topleft.y() + self.crop_handle_size,
            self.crop_handle_size,
            self.crop_temp.height() - 2 * self.crop_handle_size)

    def crop_edge_bottom(self):
        bottomleft = self.crop_temp.bottomLeft()
        return QtCore.QRectF(
            bottomleft.x() + self.crop_handle_size,
            bottomleft.y() - self.crop_handle_size,
            self.crop_temp.width() - 2 * self.crop_handle_size,
            self.crop_handle_size)

    def crop_edge_right(self):
        topright = self.crop_temp.topRight()
        return QtCore.QRectF(
            topright.x() - self.crop_handle_size,
            topright.y() + self.crop_handle_size,
            self.crop_handle_size,
            self.crop_temp.height() - 2 * self.crop_handle_size)

    def crop_edges(self):
        return (self.crop_edge_top,
                self.crop_edge_left,
                self.crop_edge_bottom,
                self.crop_edge_right)

    def get_crop_handle_cursor(self, handle):
        """Gets the crop cursor for the given handle."""

        is_topleft_or_bottomright = handle in (
            self.crop_handle_topleft, self.crop_handle_bottomright)
        return self.get_diag_cursor(is_topleft_or_bottomright)

    def get_crop_edge_cursor(self, edge):
        """Gets the crop edge cursor for the given edge."""

        top_or_bottom = edge in (
            self.crop_edge_top, self.crop_edge_bottom)
        sideways = (45 < self.rotation() < 135
                    or 225 < self.rotation() < 315)

        if top_or_bottom is sideways:
            return Qt.CursorShape.SizeHorCursor
        else:
            return Qt.CursorShape.SizeVerCursor

    def draw_crop_rect(self, painter, rect):
        """Paint a dotted rectangle for the cropping UI."""
        pen = QtGui.QPen(QtGui.QColor(255, 255, 255))
        pen.setWidth(2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawRect(rect)
        pen.setColor(QtGui.QColor(0, 0, 0))
        pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(pen)
        painter.drawRect(rect)

    def paint(self, painter, option, widget):
        if abs(painter.combinedTransform().m11()) < 2:
            # We want image smoothing, but only for images where we
            # are not zoomed in a lot. This is to ensure that for
            # example icons and pixel sprites can be viewed correctly.
            painter.setRenderHint(painter.RenderHint.SmoothPixmapTransform)

        if self.crop_mode:
            self.paint_debug(painter, option, widget)

            # Darken image outside of cropped area
            painter.drawPixmap(0, 0, self.pixmap())
            path = QtWidgets.QGraphicsPixmapItem.shape(self)
            path.addRect(self.crop_temp)
            color = QtGui.QColor(0, 0, 0)
            color.setAlpha(100)
            painter.setBrush(QtGui.QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(path)
            painter.setBrush(QtGui.QBrush())

            for handle in self.crop_handles():
                self.draw_crop_rect(painter, handle())
            self.draw_crop_rect(painter, self.crop_temp)
        else:
            pm = self._grayscale_pixmap if self.grayscale else self.pixmap()
            painter.drawPixmap(self.crop, pm, self.crop)
            self.paint_selectable(painter, option, widget)

    def enter_crop_mode(self):
        logger.debug(f'Entering crop mode on {self}')
        self.prepareGeometryChange()
        self.crop_mode = True
        self.crop_temp = QtCore.QRectF(self.crop)
        self.crop_mode_move = None
        self.crop_mode_event_start = None
        self.grabKeyboard()
        self.update()
        self.scene().crop_item = self

    def exit_crop_mode(self, confirm):
        logger.debug(f'Exiting crop mode with {confirm} on {self}')
        if confirm and self.crop != self.crop_temp:
            self.scene().undo_stack.push(
                commands.CropItem(self, self.crop_temp))
        self.prepareGeometryChange()
        self.crop_mode = False
        self.crop_temp = None
        self.crop_mode_move = None
        self.crop_mode_event_start = None
        self.ungrabKeyboard()
        self.update()
        self.scene().crop_item = None

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.exit_crop_mode(confirm=True)
        elif event.key() == Qt.Key.Key_Escape:
            self.exit_crop_mode(confirm=False)
        else:
            super().keyPressEvent(event)

    def hoverMoveEvent(self, event):
        if not self.crop_mode:
            return super().hoverMoveEvent(event)

        for handle in self.crop_handles():
            if handle().contains(event.pos()):
                self.set_cursor(self.get_crop_handle_cursor(handle))
                return
        for edge in self.crop_edges():
            if edge().contains(event.pos()):
                self.set_cursor(self.get_crop_edge_cursor(edge))
                return
        self.unset_cursor()

    def mousePressEvent(self, event):
        if not self.crop_mode:
            return super().mousePressEvent(event)

        event.accept()
        for handle in self.crop_handles():
            # Click into a handle?
            if handle().contains(event.pos()):
                self.crop_mode_event_start = event.pos()
                self.crop_mode_move = handle
                return
        for edge in self.crop_edges():
            # Click into an edge handle?
            if edge().contains(event.pos()):
                self.crop_mode_event_start = event.pos()
                self.crop_mode_move = edge
                return
        # Click not in handle, end cropping mode:
        self.exit_crop_mode(
            confirm=self.crop_temp.contains(event.pos()))

    def ensure_point_within_crop_bounds(self, point, handle):
        """Returns the point, or the nearest point within the pixmap."""

        if handle == self.crop_handle_topleft:
            topleft = QtCore.QPointF(0, 0)
            bottomright = self.crop_temp.bottomRight()
        if handle == self.crop_handle_bottomleft:
            topleft = QtCore.QPointF(0, self.crop_temp.top())
            bottomright = QtCore.QPointF(
                self.crop_temp.right(), self.pixmap().size().height())
        if handle == self.crop_handle_bottomright:
            topleft = self.crop_temp.topLeft()
            bottomright = QtCore.QPointF(
                self.pixmap().size().width(), self.pixmap().size().height())
        if handle == self.crop_handle_topright:
            topleft = QtCore.QPointF(self.crop_temp.left(), 0)
            bottomright = QtCore.QPointF(
                self.pixmap().size().width(), self.crop_temp.bottom())
        if handle == self.crop_edge_top:
            topleft = QtCore.QPointF(0, 0)
            bottomright = QtCore.QPointF(
                self.pixmap().size().width(), self.crop_temp.bottom())
        if handle == self.crop_edge_bottom:
            topleft = QtCore.QPointF(0, self.crop_temp.top())
            bottomright = QtCore.QPointF(
                self.pixmap().size().width(), self.pixmap().size().height())
        if handle == self.crop_edge_left:
            topleft = QtCore.QPointF(0, 0)
            bottomright = QtCore.QPointF(
                self.crop_temp.right(), self.pixmap().size().height())
        if handle == self.crop_edge_right:
            topleft = QtCore.QPointF(self.crop_temp.left(), 0)
            bottomright = QtCore.QPointF(
                self.pixmap().size().width(), self.pixmap().size().height())

        point.setX(min(bottomright.x(), max(topleft.x(), point.x())))
        point.setY(min(bottomright.y(), max(topleft.y(), point.y())))

        return point

    def mouseMoveEvent(self, event):
        if self.crop_mode and self.crop_mode_event_start:
            diff = event.pos() - self.crop_mode_event_start
            if self.crop_mode_move == self.crop_handle_topleft:
                new = self.ensure_point_within_crop_bounds(
                    self.crop_temp.topLeft() + diff, self.crop_mode_move)
                self.crop_temp.setTopLeft(new)
            if self.crop_mode_move == self.crop_handle_bottomleft:
                new = self.ensure_point_within_crop_bounds(
                    self.crop_temp.bottomLeft() + diff, self.crop_mode_move)
                self.crop_temp.setBottomLeft(new)
            if self.crop_mode_move == self.crop_handle_bottomright:
                new = self.ensure_point_within_crop_bounds(
                    self.crop_temp.bottomRight() + diff, self.crop_mode_move)
                self.crop_temp.setBottomRight(new)
            if self.crop_mode_move == self.crop_handle_topright:
                new = self.ensure_point_within_crop_bounds(
                    self.crop_temp.topRight() + diff, self.crop_mode_move)
                self.crop_temp.setTopRight(new)
            if self.crop_mode_move == self.crop_edge_top:
                new = self.ensure_point_within_crop_bounds(
                    self.crop_temp.topLeft() + diff, self.crop_mode_move)
                self.crop_temp.setTop(new.y())
            if self.crop_mode_move == self.crop_edge_left:
                new = self.ensure_point_within_crop_bounds(
                    self.crop_temp.topLeft() + diff, self.crop_mode_move)
                self.crop_temp.setLeft(new.x())
            if self.crop_mode_move == self.crop_edge_bottom:
                new = self.ensure_point_within_crop_bounds(
                    self.crop_temp.bottomLeft() + diff, self.crop_mode_move)
                self.crop_temp.setBottom(new.y())
            if self.crop_mode_move == self.crop_edge_right:
                new = self.ensure_point_within_crop_bounds(
                    self.crop_temp.topRight() + diff, self.crop_mode_move)
                self.crop_temp.setRight(new.x())
            self.update()
            self.crop_mode_event_start = event.pos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.crop_mode:
            self.crop_mode_move = None
            self.crop_mode_event_start = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)


@register_item
class BeeTextItem(BeeItemMixin, QtWidgets.QGraphicsTextItem):
    """Class for text added by the user."""

    TYPE = 'text'

    def __init__(self, text=None, **kwargs):
        super().__init__(text or "Text")
        self.save_id = None
        logger.debug(f'Initialized {self}')
        self.is_image = False
        self.init_selectable()
        self.is_editable = True
        self.edit_mode = False
        self.setDefaultTextColor(QtGui.QColor(*COLORS['Scene:Text']))

    @classmethod
    def create_from_data(cls, **kwargs):
        data = kwargs.get('data', {})
        item = cls(**data)
        return item

    def __str__(self):
        txt = self.toPlainText()[:40]
        return (f'Text "{txt}"')

    def get_extra_save_data(self):
        return {'text': self.toPlainText()}

    def contains(self, point):
        return self.boundingRect().contains(point)

    def paint(self, painter, option, widget):
        painter.setPen(Qt.PenStyle.NoPen)
        color = QtGui.QColor(0, 0, 0)
        color.setAlpha(40)
        brush = QtGui.QBrush(color)
        painter.setBrush(brush)
        painter.drawRect(QtWidgets.QGraphicsTextItem.boundingRect(self))
        option.state = QtWidgets.QStyle.StateFlag.State_Enabled
        super().paint(painter, option, widget)
        self.paint_selectable(painter, option, widget)

    def create_copy(self):
        item = BeeTextItem(self.toPlainText())
        item.setPos(self.pos())
        item.setZValue(self.zValue())
        item.setScale(self.scale())
        item.setRotation(self.rotation())
        if self.flip() == -1:
            item.do_flip()
        return item

    def enter_edit_mode(self):
        logger.debug(f'Entering edit mode on {self}')
        self.edit_mode = True
        self.old_text = self.toPlainText()
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextEditorInteraction)
        self.scene().edit_item = self

    def exit_edit_mode(self, commit=True):
        logger.debug(f'Exiting edit mode on {self}')
        self.edit_mode = False
        # reset selection:
        self.setTextCursor(QtGui.QTextCursor(self.document()))
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.scene().edit_item = None
        if commit:
            self.scene().undo_stack.push(
                commands.ChangeText(self, self.toPlainText(), self.old_text))
            if not self.toPlainText().strip():
                logger.debug('Removing empty text item')
                self.scene().undo_stack.push(
                    commands.DeleteItems(self.scene(), [self]))
        else:
            self.setPlainText(self.old_text)

    def has_selection_handles(self):
        return super().has_selection_handles() and not self.edit_mode

    def keyPressEvent(self, event):
        if (event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return)
                and event.modifiers() == Qt.KeyboardModifier.NoModifier):
            self.exit_edit_mode()
            event.accept()
            return
        if (event.key() == Qt.Key.Key_Escape
                and event.modifiers() == Qt.KeyboardModifier.NoModifier):
            self.exit_edit_mode(commit=False)
            event.accept()
            return
        super().keyPressEvent(event)

    def copy_to_clipboard(self, clipboard):
        clipboard.setText(self.toPlainText())


@register_item
class BeePathItem(BeeItemMixin, QtWidgets.QGraphicsItem):
    """Class for freehand drawing/sketch strokes added by the user."""

    TYPE = 'path'

    def __init__(self, strokes=None, **kwargs):
        super().__init__()
        self.save_id = None
        self.is_image = False
        self.strokes = strokes or []
        self.temp_stroke = None
        self._cached_rect = QtCore.QRectF(0, 0, 1, 1)
        self._cache_pixmap = None
        self.init_selectable()
        logger.debug(f'Initialized {self}')

    @classmethod
    def create_from_data(cls, **kwargs):
        data = kwargs.get('data', {})
        item = cls(strokes=data.get('strokes', []))
        item._update_bounding_rect()
        item._invalidate_cache()
        return item

    def __str__(self):
        n = len(self.strokes)
        return f'Path ({n} stroke{"s" if n != 1 else ""})'

    def get_extra_save_data(self):
        return {'strokes': self.strokes}

    def create_copy(self):
        item = BeePathItem(strokes=copy.deepcopy(self.strokes))
        item.setPos(self.pos())
        item.setZValue(self.zValue())
        item.setScale(self.scale())
        item.setRotation(self.rotation())
        if self.flip() == -1:
            item.do_flip()
        item._update_bounding_rect()
        item._invalidate_cache()
        return item

    def contains(self, point):
        return self.boundingRect().contains(point)

    def bounding_rect_unselected(self):
        rect = QtCore.QRectF(self._cached_rect)
        if self.temp_stroke:
            base_size = self.temp_stroke.get('base_size', 10)
            for pt in self.temp_stroke.get('points', []):
                r = base_size * pt.get('pressure', 1.0) / 2 + 1
                rect = rect.united(QtCore.QRectF(
                    pt['x'] - r, pt['y'] - r, 2 * r, 2 * r))
        return rect

    def add_stroke(self, stroke):
        self.prepareGeometryChange()
        self.strokes.append(stroke)
        self._update_bounding_rect()
        self._invalidate_cache()
        self.update()

    def _invalidate_cache(self):
        self._cache_pixmap = None

    def _update_bounding_rect(self):
        if not self.strokes:
            self._cached_rect = QtCore.QRectF(0, 0, 1, 1)
            return
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        max_r = 0
        for stroke in self.strokes:
            base_size = stroke.get('base_size', 10)
            for pt in stroke.get('points', []):
                r = base_size * pt.get('pressure', 1.0) / 2
                if r > max_r:
                    max_r = r
                x = pt['x']
                y = pt['y']
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y
        pad = max_r + 1
        self._cached_rect = QtCore.QRectF(
            min_x - pad, min_y - pad,
            (max_x - min_x) + 2 * pad,
            (max_y - min_y) + 2 * pad)

    def _paint_stroke(self, painter, stroke):
        color_data = stroke.get('color', [0, 0, 0, 255])
        color = QtGui.QColor(*color_data)
        base_size = stroke.get('base_size', 10)
        points = stroke.get('points', [])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QBrush(color))

        for i, pt in enumerate(points):
            pressure = pt.get('pressure', 1.0)
            radius = base_size * pressure / 2
            painter.drawEllipse(
                QtCore.QPointF(pt['x'], pt['y']),
                radius, radius)
            if i > 0:
                prev = points[i - 1]
                dx = pt['x'] - prev['x']
                dy = pt['y'] - prev['y']
                dist = math.hypot(dx, dy)
                if dist > 1:
                    steps = int(dist)
                    for s in range(1, steps):
                        t = s / dist
                        ix = prev['x'] + dx * t
                        iy = prev['y'] + dy * t
                        prev_p = prev.get('pressure', 1.0)
                        ip = prev_p + (pressure - prev_p) * t
                        ir = base_size * ip / 2
                        painter.drawEllipse(
                            QtCore.QPointF(ix, iy), ir, ir)

    def _ensure_cache(self):
        if self._cache_pixmap is not None:
            return
        if not self.strokes:
            return
        rect = self._cached_rect
        w = max(1, int(math.ceil(rect.width())))
        h = max(1, int(math.ceil(rect.height())))
        pixmap = QtGui.QPixmap(w, h)
        pixmap.fill(QtGui.QColor(0, 0, 0, 0))
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.translate(-rect.x(), -rect.y())
        for stroke in self.strokes:
            self._paint_stroke(painter, stroke)
        painter.end()
        self._cache_pixmap = pixmap

    def paint(self, painter, option, widget):
        if self.strokes:
            self._ensure_cache()
            if self._cache_pixmap is not None:
                painter.drawPixmap(
                    QtCore.QPointF(
                        self._cached_rect.x(),
                        self._cached_rect.y()),
                    self._cache_pixmap)

        if self.temp_stroke:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            self._paint_stroke(painter, self.temp_stroke)

        self.paint_selectable(painter, option, widget)

    def copy_to_clipboard(self, clipboard):
        pass


@register_item
class BeeErrorItem(BeeItemMixin, QtWidgets.QGraphicsTextItem):
    """Class for displaying error messages when an item can't be loaded
    from a bee file.

    This item will be displayed instead of the original item. It won't
    save to bee files. The original item will be preserved in the bee
    file, unless this item gets deleted by the user, or a new bee file
    is saved.
    """

    TYPE = 'error'

    def __init__(self, text=None, **kwargs):
        super().__init__(text or "Text")
        self.original_save_id = None
        logger.debug(f'Initialized {self}')
        self.is_image = False
        self.init_selectable()
        self.is_editable = False
        self.setDefaultTextColor(QtGui.QColor(*COLORS['Scene:Text']))

    @classmethod
    def create_from_data(cls, **kwargs):
        data = kwargs.get('data', {})
        item = cls(**data)
        return item

    def __str__(self):
        txt = self.toPlainText()[:40]
        return (f'Error "{txt}"')

    def contains(self, point):
        return self.boundingRect().contains(point)

    def paint(self, painter, option, widget):
        painter.setPen(Qt.PenStyle.NoPen)
        color = QtGui.QColor(200, 0, 0)
        brush = QtGui.QBrush(color)
        painter.setBrush(brush)
        painter.drawRect(QtWidgets.QGraphicsTextItem.boundingRect(self))
        option.state = QtWidgets.QStyle.StateFlag.State_Enabled
        super().paint(painter, option, widget)
        self.paint_selectable(painter, option, widget)

    def update_from_data(self, **kwargs):
        self.original_save_id = kwargs.get('save_id', self.original_save_id)
        self.setPos(kwargs.get('x', self.pos().x()),
                    kwargs.get('y', self.pos().y()))
        self.setZValue(kwargs.get('z', self.zValue()))
        self.setScale(kwargs.get('scale', self.scale()))
        self.setRotation(kwargs.get('rotation', self.rotation()))

    def create_copy(self):
        item = BeeErrorItem(self.toPlainText())
        item.setPos(self.pos())
        item.setZValue(self.zValue())
        item.setScale(self.scale())
        item.setRotation(self.rotation())
        return item

    def flip(self, *args, **kwargs):
        """Returns the flip value (1 or -1)"""
        # Never display error messages flipped
        return 1

    def do_flip(self, *args, **kwargs):
        """Flips the item."""
        # Never flip error messages
        pass

    def copy_to_clipboard(self, clipboard):
        clipboard.setText(self.toPlainText())
