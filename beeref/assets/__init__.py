#!/usr/bin/env python3

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

from importlib.resources import files as rsc_files
import logging

from PyQt6 import QtGui, QtWidgets, QtSvg


logger = logging.getLogger(__name__)


class BeeAssets:
    _instance = None
    PATH = rsc_files('beeref.assets')

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.on_new()
        return cls._instance

    def on_new(self):
        logger.debug(f'Assets path: {self.PATH}')

        self.logo = QtGui.QIcon(str(self.PATH.joinpath('logo.png')))
        assert self.logo.isNull() is False
        self.cursor_rotate = self.cursor_from_image(
            'cursor_rotate.png', (20, 20))
        self.cursor_flip_h = self.cursor_from_image(
            'cursor_flip_h.png', (20, 20))
        self.cursor_flip_v = self.cursor_from_image(
            'cursor_flip_v.png', (20, 20))
        self.cursor_draw_line = self.cursor_from_svg(
            'icons/draw-line.svg', (12, 12))

    def cursor_from_image(self, filename, hotspot):
        app = QtWidgets.QApplication.instance()
        scaling = app.primaryScreen().devicePixelRatio()
        img = QtGui.QImage(str(self.PATH.joinpath(filename)))
        assert img.isNull() is False
        pixmap = QtGui.QPixmap.fromImage(img)
        pixmap.setDevicePixelRatio(scaling)
        return QtGui.QCursor(
            pixmap, int(hotspot[0]/scaling), int(hotspot[1]/scaling))

    def cursor_from_svg(self, filename, hotspot, size=24):
        """Creates cursor from SVG file."""
        app = QtWidgets.QApplication.instance()
        scaling = app.primaryScreen().devicePixelRatio()
        
        # Load SVG
        svg_path = str(self.PATH.joinpath(filename))
        renderer = QtSvg.QSvgRenderer(svg_path)
        
        # Create pixmap of required size
        pixmap_size = int(size * scaling)
        pixmap = QtGui.QPixmap(pixmap_size, pixmap_size)
        pixmap.fill(QtGui.QColor(0, 0, 0, 0))  # Transparent background
        
        # Render SVG to pixmap
        painter = QtGui.QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        pixmap.setDevicePixelRatio(scaling)
        return QtGui.QCursor(
            pixmap, int(hotspot[0]/scaling), int(hotspot[1]/scaling))
