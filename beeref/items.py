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

import logging

from PyQt6 import QtCore, QtGui, QtWidgets

from beeref.selection import SelectionItem


logger = logging.getLogger('BeeRef')


class BeePixmapItem(QtWidgets.QGraphicsPixmapItem):
    """Class for images added by the user."""

    def __init__(self, image, filename=None):
        super().__init__(QtGui.QPixmap.fromImage(image))
        self.save_id = None
        self.filename = filename
        logger.debug(f'Initialized {self}')

        self.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsMovable
            | QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsSelectable)

    def __str__(self):
        return (f'Image "{self.filename}" '
                f'with dimensions {self.width} x {self.height}')

    def setScale(self, factor):
        if factor <= 0:
            return

        logger.debug(f'Setting scale for image "{self.filename}" to {factor}')
        super().setScale(factor)
        SelectionItem.update_selection(self)

    def set_pos_center(self, x, y):
        """Sets the position using the item's center as the origin point."""

        self.setPos(x - self.width * self.scale() / 2,
                    y - self.height * self.scale() / 2)

    @property
    def width(self):
        return self.pixmap().size().width()

    @property
    def height(self):
        return self.pixmap().size().height()

    def pixmap_to_bytes(self):
        """Convert the pixmap data to PNG bytestring."""
        barray = QtCore.QByteArray()
        buffer = QtCore.QBuffer(barray)
        buffer.open(QtCore.QIODevice.OpenMode.WriteOnly)
        img = self.pixmap().toImage()
        img.save(buffer, 'PNG')
        return barray.data()

    def pixmap_from_bytes(self, data):
        """Set image pimap from a bytestring."""
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(data)
        self.setPixmap(pixmap)

    def itemChange(self, change, value):
        if change == self.GraphicsItemChange.ItemSelectedChange:
            if value:
                logger.debug(f'Item selected {self.filename}')
                SelectionItem.activate_selection(self)
            else:
                logger.debug(f'Item deselected {self.filename}')
                SelectionItem.clear_selection(self)
        return super().itemChange(change, value)
