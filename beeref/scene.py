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


logger = logging.getLogger('BeeRef')


class BeeGraphicsScene(QtWidgets.QGraphicsScene):

    def delete_selected_items(self):
        for item in self.selectedItems():
            logger.debug('Deleting item...')
            self.removeItem(item)

    def normalize_width_or_height(self, mode):
        values = [getattr(i, mode) for i in self.selectedItems()]
        if not values:
            return
        avg = sum(values) / len(values)

        logger.debug(f'Calculated average {mode} {avg}')

        for item in self.selectedItems():
            factor = avg / getattr(item, mode)
            item.setScale(factor)

    def normalize_height(self):
        return self.normalize_width_or_height('height')

    def normalize_width(self):
        return self.normalize_width_or_height('width')

    def normalize_size(self):
        sizes = [i.width * i.height for i in self.selectedItems()]

        if not sizes:
            return

        avg = sum(sizes) / len(sizes)
        logger.debug(f'Calculated average size {avg}')

        for item in self.selectedItems():
            factor = math.sqrt(avg / item.width / item.height)
            item.setScale(factor)

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
        super().mousePressEvent(event)

    def items_for_export(self):
        """Returns the items that are to be exported."""

        # self.items() holds items in reverse order of addition
        return list(filter(lambda i: hasattr(i, 'to_bee_json'),
                           reversed(self.items())))
