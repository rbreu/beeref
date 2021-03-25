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

from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt

from beeref import commands

logger = logging.getLogger('BeeRef')


class BeeGraphicsScene(QtWidgets.QGraphicsScene):

    def __init__(self, undo_stack):
        super().__init__()
        self.move_active = False
        self.undo_stack = undo_stack

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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButtons.RightButton:
            # Right-click invokes the context menu on the
            # GraphicsView. We don't need it here.
            return

        if event.button() == Qt.MouseButtons.LeftButton:
            self.move_active = True
            self.move_start = event.scenePos()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):

        if self.move_active and self.has_selection():
            delta = event.scenePos() - self.move_start
            if not delta.isNull():
                self.undo_stack.push(
                    commands.MoveItemsBy(self.selectedItems(),
                                         delta.x(), delta.y(),
                                         ignore_first_redo=True))
            self.move_active = False
        super().mouseReleaseEvent(event)

    def items_for_export(self):
        """Returns the items that are to be exported.

        Items to be exported are items that implement ``to_bee_json``.
        """

        # self.items() holds items in reverse order of addition, so we
        # need to reverse it for export
        return list(filter(lambda i: hasattr(i, 'to_bee_json'),
                           reversed(self.items())))
