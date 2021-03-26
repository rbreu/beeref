from unittest.mock import patch, PropertyMock

import os.path

from PyQt6 import QtGui, QtWidgets

from beeref.items import BeePixmapItem
from .base import BeeTestCase


class BeePixmapItemTestCase(BeeTestCase):

    def test_init(self):
        root = os.path.dirname(__file__)
        filename = os.path.join(root, 'assets', 'test3x3.png')
        item = BeePixmapItem(QtGui.QImage(filename), filename)
        assert item.width == 3
        assert item.height == 3
        assert item.scale_factor == 1
        assert item.flags() == (
            QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsMovable
            | QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsSelectable)
        assert item.filename == filename

    def test_set_scale(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setScale(3)
        assert item.scale_factor == 3

    def test_set_scale_ignores_zero(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setScale(0)
        assert item.scale_factor == 1

    def test_set_scale_ignores_negative(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setScale(-0.1)
        assert item.scale_factor == 1

    def test_set_pos_center(self):
        item = BeePixmapItem(QtGui.QImage())
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=200):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=100):
                item.set_pos_center(0, 0)
                assert item.pos().x() == -100
                assert item.pos().y() == -50
