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

from PyQt6 import QtCore, QtGui

from .errors import BeeFileIOError
from beeref import constants


logger = logging.getLogger(__name__)


class SceneToPixmapExporter:
    """For exporting the scene to a single image."""

    MARGIN = 100

    def __init__(self, scene):
        self.scene = scene
        self.scene.cancel_crop_mode()
        self.scene.set_selected_all_items(False)
        # Selection outlines/handles will be rendered to the exported
        # image, so deselect first. (Alternatively, pass an attribute
        # to paint functions to not paint them?)
        rect = scene.itemsBoundingRect()
        size = QtCore.QSize(int(rect.width()), int(rect.height()))
        self.margin = max(size.width(), size.height()) * 0.03
        self.default_size = size.grownBy(
            QtCore.QMargins(*([int(self.margin)] * 4)))
        logger.debug(f'Default export size: {self.default_size}')
        logger.debug(f'Default export margin: {self.margin}')

    def render_to_image(self, size):
        logger.debug(f'Final export size: {size}')
        margin = self.margin * size.width() / self.default_size.width()
        logger.debug(f'Final export margin: {margin}')

        image = QtGui.QImage(size, QtGui.QImage.Format.Format_RGB32)
        image.fill(QtGui.QColor(*constants.COLORS['Scene:Canvas']))
        painter = QtGui.QPainter(image)
        painter.setViewport(QtCore.QRect(
            int(margin),
            int(margin),
            int(size.width() - 2 * margin),
            int(size.height() - 2 * margin)))
        self.scene.render(painter)
        painter.end()
        return image

    def export(self, filename, size):
        logger.debug(f'Exporting scene to {filename}')
        image = self.render_to_image(size)
        if not image.save(filename, quality=90):
            raise BeeFileIOError(
                msg=str('Error writing image'), filename=filename)
