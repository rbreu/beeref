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

from queue import Queue
import logging
import math

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt

import rpack

from beeref import commands
from beeref.items import item_registry
from beeref.selection import MultiSelectItem, RubberbandItem


logger = logging.getLogger(__name__)


class BeeGraphicsScene(QtWidgets.QGraphicsScene):

    def __init__(self, undo_stack):
        super().__init__()
        self.move_active = False
        self.rubberband_active = False
        self.undo_stack = undo_stack
        self.max_z = 0
        self.min_z = 0
        self.Z_STEP = 0.001
        self.multi_select_item = MultiSelectItem()
        self.rubberband_item = RubberbandItem()
        self.selectionChanged.connect(self.on_selection_change)
        self.changed.connect(self.on_change)
        self.items_to_add = Queue()
        self.internal_clipboard = []
        self.edit_item = None

    def addItem(self, item):
        logger.debug(f'Adding item {item}')
        super().addItem(item)

    def removeItem(self, item):
        logger.debug(f'Removing item {item}')
        super().removeItem(item)

    def copy_selection_to_internal_clipboard(self):
        self.internal_clipboard = []
        for item in self.selectedItems(user_only=True):
            self.internal_clipboard.append(item)

    def paste_from_internal_clipboard(self, position):
        self.set_selected_all_items(False)
        copies = []
        for item in self.internal_clipboard:
            copy = item.create_copy()
            copies.append(copy)
        self.undo_stack.push(commands.InsertItems(self, copies, position))

    def raise_to_top(self):
        items = self.selectedItems(user_only=True)
        z_values = map(lambda i: i.zValue(), items)
        delta = self.max_z + self.Z_STEP - min(z_values)
        logger.debug(f'Raise to top, delta: {delta}')
        for item in items:
            item.setZValue(item.zValue() + delta)

    def lower_to_bottom(self):
        items = self.selectedItems(user_only=True)
        z_values = map(lambda i: i.zValue(), items)
        delta = self.min_z - self.Z_STEP - max(z_values)
        logger.debug(f'Lower to bottom, delta: {delta}')

        for item in items:
            item.setZValue(item.zValue() + delta)

    def normalize_width_or_height(self, mode):
        """Scale the selected images to have the same width or height, as
        specified by ``mode``.

        :param mode: "width" or "height".
        """

        values = []
        items = self.selectedItems(user_only=True)
        for item in items:
            rect = self.itemsBoundingRect(items=[item])
            values.append(getattr(rect, mode)())
        if len(values) < 2:
            return
        avg = sum(values) / len(values)
        logger.debug(f'Calculated average {mode} {avg}')

        scale_factors = []
        for item in items:
            rect = self.itemsBoundingRect(items=[item])
            scale_factors.append(avg / getattr(rect, mode)())
        self.undo_stack.push(
            commands.NormalizeItems(items, scale_factors))

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

        sizes = []
        items = self.selectedItems(user_only=True)
        for item in items:
            rect = self.itemsBoundingRect(items=[item])
            sizes.append(rect.width() * rect.height())

        if len(sizes) < 2:
            return

        avg = sum(sizes) / len(sizes)
        logger.debug(f'Calculated average size {avg}')

        scale_factors = []
        for item in items:
            rect = self.itemsBoundingRect(items=[item])
            scale_factors.append(math.sqrt(avg / rect.width() / rect.height()))
        self.undo_stack.push(
            commands.NormalizeItems(items, scale_factors))

    def arrange(self, vertical=False):
        """Arrange items in a line (horizontally or vertically)."""

        items = self.selectedItems(user_only=True)
        if len(items) < 2:
            return

        center = self.get_selection_center()
        positions = []
        rects = []
        for item in items:
            rects.append({
                'rect': self.itemsBoundingRect(items=[item]),
                'item': item})

        if vertical:
            rects.sort(key=lambda r: r['rect'].topLeft().y())
            sum_height = sum(map(lambda r: r['rect'].height(), rects))
            y = round(center.y() - sum_height/2)
            for rect in rects:
                positions.append(
                    QtCore.QPointF(
                        round(center.x() - rect['rect'].width()/2), y))
                y += rect['rect'].height()

        else:
            rects.sort(key=lambda r: r['rect'].topLeft().x())
            sum_width = sum(map(lambda r: r['rect'].width(), rects))
            x = round(center.x() - sum_width/2)
            for rect in rects:
                positions.append(
                    QtCore.QPointF(
                        x, round(center.y() - rect['rect'].height()/2)))
                x += rect['rect'].width()

        self.undo_stack.push(
            commands.ArrangeItems(self,
                                  [r['item'] for r in rects],
                                  positions))

    def arrange_optimal(self):
        items = self.selectedItems(user_only=True)
        if len(items) < 2:
            return

        sizes = []
        for item in items:
            rect = self.itemsBoundingRect(items=[item])
            sizes.append((round(rect.width()), round(rect.height())))

        center = self.get_selection_center()

        # The minimal area the items need if they could be packed optimally;
        # we use this as a starting shape for the packing algorithm
        min_area = sum(map(lambda s: s[0] * s[1], sizes))
        width = math.ceil(math.sqrt(min_area))

        positions = None
        while not positions:
            try:
                positions = rpack.pack(
                    sizes, max_width=width, max_height=width)
            except rpack.PackingImpossibleError:
                width = math.ceil(width * 1.2)

        # We want the items to center around the selection's center,
        # not (0, 0)
        bounds = rpack.bbox_size(sizes, positions)
        diff = center - QtCore.QPointF(bounds[0]/2, bounds[1]/2)
        positions = [QtCore.QPointF(*pos) + diff for pos in positions]

        self.undo_stack.push(commands.ArrangeItems(self, items, positions))

    def flip_items(self, vertical=False):
        """Flip selected items."""
        self.undo_stack.push(
            commands.FlipItems(self.selectedItems(user_only=True),
                               self.get_selection_center(),
                               vertical=vertical))

    def set_selected_all_items(self, value):
        """Sets the selection mode of all items to ``value``."""
        for item in self.items():
            item.setSelected(value)

    def has_selection(self):
        """Checks whether there are currently items selected."""

        return bool(self.selectedItems(user_only=True))

    def has_single_selection(self):
        """Checks whether there's currently exactly one item selected."""

        return len(self.selectedItems(user_only=True)) == 1

    def has_multi_selection(self):
        """Checks whether there are currently more than one items selected."""

        return len(self.selectedItems(user_only=True)) > 1

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            # Right-click invokes the context menu on the
            # GraphicsView. We don't need it here.
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.event_start = event.scenePos()
            item_at_pos = self.itemAt(
                event.scenePos(), self.views()[0].transform())

            if self.edit_item:
                if item_at_pos != self.edit_item:
                    self.edit_item.exit_edit_mode()
                    self.edit_item = None
                else:
                    super().mousePressEvent(event)
                    return
            if item_at_pos:
                self.move_active = True
            elif self.items():
                self.rubberband_active = True

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        if item:
            self.move_active = False
            if not item.isSelected():
                item.setSelected(True)
            if item.is_editable:
                self.edit_item = item
                item.enter_edit_mode()
                self.mousePressEvent(event)
            else:
                self.views()[0].fit_rect(
                    self.itemsBoundingRect(items=[item]),
                    toggle_item=item)
            return
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if self.rubberband_active:
            if not self.rubberband_item.scene():
                logger.debug('Activating rubberband selection')
                self.addItem(self.rubberband_item)
                self.rubberband_item.bring_to_front()
            self.rubberband_item.fit(self.event_start, event.scenePos())
            self.setSelectionArea(self.rubberband_item.shape())
            self.views()[0].reset_previous_transform()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.rubberband_active:
            if self.rubberband_item.scene():
                logger.debug('Ending rubberband selection')
                self.removeItem(self.rubberband_item)
            self.rubberband_active = False
        if (self.move_active
                and self.has_selection()
                and not self.multi_select_item.is_action_active()
                and not self.selectedItems()[0].is_action_active()):
            delta = event.scenePos() - self.event_start
            if not delta.isNull():
                self.undo_stack.push(
                    commands.MoveItemsBy(self.selectedItems(),
                                         delta,
                                         ignore_first_redo=True))
        self.move_active = False
        super().mouseReleaseEvent(event)

    def selectedItems(self, user_only=False):
        """If ``user_only`` is set to ``True``, only return items added
        by the user (i.e. no multi select outlines and other UI items).

        User items are items that have a ``save_id`` attribute.
        """

        items = super().selectedItems()
        if user_only:
            return list(filter(lambda i: hasattr(i, 'save_id'), items))
        return items

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

    def itemsBoundingRect(self, selection_only=False, items=None):
        """Returns the bounding rect of the scene's items; either all of them
        or only selected ones, or the items givin in ``items``.

        Re-implemented to not include the items's selection handles.
        """

        def filter_user_items(ilist):
            return list(filter(lambda i: hasattr(i, 'save_id'), ilist))

        if selection_only:
            base = filter_user_items(self.selectedItems())
        elif items:
            base = items
        else:
            base = filter_user_items(self.items())

        if not base:
            return QtCore.QRectF(0, 0, 0, 0)

        x = []
        y = []

        for item in base:
            for corner in item.corners_scene_coords:
                x.append(corner.x())
                y.append(corner.y())

        return QtCore.QRectF(
            QtCore.QPointF(min(x), min(y)),
            QtCore.QPointF(max(x), max(y)))

    def get_selection_center(self):
        rect = self.itemsBoundingRect(selection_only=True)
        return (rect.topLeft() + rect.bottomRight()) / 2

    def on_selection_change(self):
        if self.has_multi_selection():
            self.multi_select_item.fit_selection_area(
                self.itemsBoundingRect(selection_only=True))
        if self.has_multi_selection() and not self.multi_select_item.scene():
            self.addItem(self.multi_select_item)
            self.multi_select_item.bring_to_front()
        if not self.has_multi_selection() and self.multi_select_item.scene():
            self.removeItem(self.multi_select_item)

    def on_change(self, region):
        if (self.multi_select_item.scene()
                and not self.multi_select_item.scale_active
                and not self.multi_select_item.rotate_active):
            self.multi_select_item.fit_selection_area(
                self.itemsBoundingRect(selection_only=True))

    def add_item_later(self, itemdata, selected=False):
        """Keep an item for adding later via ``add_queued_items``

        :param dict itemdata: Defines the item's data
        :param bool selected: Whether the item is initialised as selected
        """

        self.items_to_add.put((itemdata, selected))

    def add_queued_items(self):
        """Adds items added via ``add_items_later``"""

        while not self.items_to_add.empty():
            data, selected = self.items_to_add.get()
            cls = item_registry[data.pop('type')]
            item = cls.create_from_data(**data)
            item.update_from_data(**data)
            self.addItem(item)
            # Force recalculation of min/max z values:
            item.setZValue(item.zValue())
            if selected:
                item.setSelected(True)
                item.bring_to_front()
