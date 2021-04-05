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

import logging
import os.path

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt


logger = logging.getLogger('BeeRef')


class BeeAssets:
    _instance = None
    PATH = os.path.join( os.path.dirname(__file__), 'assets')

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.on_new()
        return cls._instance

    def on_new(self):
        PATH = os.path.join(os.path.dirname(__file__), 'assets')
        logger.debug(f'Assets path: {self.PATH}')

        self.logo = QtGui.QIcon(os.path.join(self.PATH, 'logo.png'))
        self.cursor_rotate = self.cursor_from_image('cursor_rotate', (6, 10))

    def cursor_from_image(self, filename, hotspot):
        img = QtGui.QImage(os.path.join(self.PATH, filename))
        return QtGui.QCursor(
            QtGui.QPixmap.fromImage(img), hotspot[0], hotspot[1])
