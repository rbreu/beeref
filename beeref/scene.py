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

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt

from beeref import commands
from beeref.selection import MultiSelectItem, RubberbandItem


logger = logging.getLogger('BeeRef')


class BeeGraphicsScene(QtWidgets.QGraphicsScene):

    def __init__(self, undo_stack):
        super().__init__()
        self.move_active = False
        self.rubberband_active = False
        self.undo_stack = undo_stack
        self.max_z = 0
        self.multi_select_item = MultiSelectItem()
        self.rubberband_item = RubberbandItem()
        self.selectionChanged.connect(self.on_selection_change)

    def normalize_width_or_height(self, mode):
        """Scale the selected images to have the same width or height, as
        specified by ``mode``.

        :param mode: "width" or "height".
        """

        values = [getattr(i, mode) for i in self.selectedItems()]
        if not values:
            return
        avg = sum(values) / len(values)

        logger.debug(f'Calculated average {mode} {avg}')

        scale_factors = []
        for item in self.selectedItems():
            scale_factors.append(avg / getattr(item, mode))
        self.undo_stack.push(
            commands.NormalizeItems(self.selectedItems(), scale_factors))

    def normalize_height(self):
        """Scale selected images to the same height."""
        return self.normalize_width_or_height('height')

    def normalize_width(self):
        """Scale selected images to the same width."""
        return self.normalize_width_or_height('width')

    def normalize_size(self):
        """Scale selected images to the same size.

        Size meaning the area = widh * height.
        """
        sizes = [i.width * i.height for i in self.selectedItems()]

        if not sizes:
            return

        avg = sum(sizes) / len(sizes)
        logger.debug(f'Calculated average size {avg}')

        scale_factors = []
        for item in self.selectedItems():
            scale_factors.append(math.sqrt(avg / item.width / item.height))
        self.undo_stack.push(
            commands.NormalizeItems(self.selectedItems(), scale_factors))

    def has_selection(self):
        """Checks whether there are currently items selected."""

        return bool(self.selectedItems())

    def has_single_selection(self):
        """Checks whether there's currently exactly one item selected."""

        return len(self.selectedItems()) == 1

    def has_multi_selection(self):
        """Checks whether there are currently more than one items selected."""

        return len(self.selectedItems()) > 1

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButtons.RightButton:
            # Right-click invokes the context menu on the
            # GraphicsView. We don't need it here.
            return

        if event.button() == Qt.MouseButtons.LeftButton:
            self.event_start = event.scenePos()
            if self.itemAt(event.scenePos(), self.views()[0].transform()):
                self.move_active = True
            else:
                self.rubberband_active = True

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.rubberband_active:
            if not self.rubberband_item.scene():
                logger.debug('Activating rubberband selection')
                self.addItem(self.rubberband_item)
                self.rubberband_item.bring_to_front()
            self.rubberband_item.fit(self.event_start, event.scenePos())
            self.setSelectionArea(self.rubberband_item.shape())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.rubberband_active:
            if self.rubberband_item.scene():
                logger.debug('Ending rubberband selection')
                self.removeItem(self.rubberband_item)
            self.rubberband_active = False
        if self.move_active and self.has_selection():
            delta = event.scenePos() - self.event_start
            if not delta.isNull():
                self.undo_stack.push(
                    commands.MoveItemsBy(self.selectedItems(),
                                         delta,
                                         ignore_first_redo=True))
        self.move_active = False
        super().mouseReleaseEvent(event)

    def items_for_save(self):
        """Returns the items that are to be saved.

        Items to be saved are items that have a save_id attribute.
        """

        return filter(lambda i: hasattr(i, 'save_id'),
                      self.items(order=Qt.SortOrder.AscendingOrder))

    def clear_save_ids(self):
        for item in self.items_for_save():
            item.save_id = None

    def on_view_scale_change(self):
        for item in self.selectedItems():
            item.on_view_scale_change()

    def get_selection_rect(self):
        """Returns the bounding rect of the currently selected items."""

        items = list(filter(lambda i: hasattr(i, 'save_id'),
                            self.selectedItems()))
        x = []
        y = []

        for item in items:
            for corner in item.corners_scene_coords:
                x.append(corner.x())
                y.append(corner.y())

        return QtCore.QRectF(
            QtCore.QPointF(min(x), min(y)),
            QtCore.QPointF(max(x), max(y)))

    def on_selection_change(self):
        if self.has_multi_selection():
            self.multi_select_item.fit_selection_area(
                self.get_selection_rect())
        if self.has_multi_selection() and not self.multi_select_item.scene():
            logger.debug('Adding multi select outline')
            self.addItem(self.multi_select_item)
            self.multi_select_item.bring_to_front()
        if not self.has_multi_selection() and self.multi_select_item.scene():
            logger.debug('Removing multi select outline')
            self.removeItem(self.multi_select_item)
