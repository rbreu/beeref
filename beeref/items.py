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

from beeref.selection import SelectableMixin


logger = logging.getLogger(__name__)


class BeePixmapItem(SelectableMixin, QtWidgets.QGraphicsPixmapItem):
    """Class for images added by the user."""

    def __init__(self, image, filename=None):
        super().__init__(QtGui.QPixmap.fromImage(image))
        self.save_id = None
        self.filename = filename
        logger.debug(f'Initialized {self}')
        self.init_selectable()

    def __str__(self):
        return (f'Image "{self.filename}" {self.width} x {self.height}')

    def set_pos_center(self, pos):
        """Sets the position using the item's center as the origin point."""

        self.setPos(pos - self.center_scene_coords)

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
        buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
        img = self.pixmap().toImage()
        img.save(buffer, 'PNG')
        return barray.data()

    def pixmap_from_bytes(self, data):
        """Set image pimap from a bytestring."""
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(data)
        self.setPixmap(pixmap)

    def paint(self, painter, option, widget):
        painter.drawPixmap(0, 0, self.pixmap())
        self.paint_selectable(painter, option, widget)

    def has_selection_outline(self):
        return self.isSelected()

    def has_selection_handles(self):
        return self.isSelected() and self.scene().has_single_selection()

    def selection_action_items(self):
        """The items affected by selection actions like scaling and rotating.
        """
        return [self]

    def on_selected_change(self, value):
        if (value and self.scene()
                and not self.scene().has_selection()
                and not self.scene().rubberband_active):
            self.bring_to_front()

    def create_copy(self):
        item = BeePixmapItem(QtGui.QImage(), self.filename)
        item.setPixmap(self.pixmap())
        item.setPos(self.pos())
        item.setZValue(self.zValue())
        item.setScale(self.scale())
        item.setRotation(self.rotation())
        if self.flip() == -1:
            item.do_flip()
        return item
