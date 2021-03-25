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


class BeePixmapItemToBeeJsonTestCase(BeeTestCase):

    def test_basic(self):
        item = BeePixmapItem(QtGui.QImage(), 'bee.png')
        assert item.to_bee_json() == {
            'cls': 'BeePixmapItem',
            'scale': 1,
            'pos': [0.0, 0.0],
            'z': 0.0,
            'pixmap': '',
            'filename': 'bee.png',
        }

    def test_scale(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setScale(2)
        beejson = item.to_bee_json()
        assert beejson['scale'] == 2

    def test_position(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setPos(100, 200)
        beejson = item.to_bee_json()
        assert beejson['pos'] == [100, 200]

    def test_z_value(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setZValue(3)
        beejson = item.to_bee_json()
        assert beejson['z'] == 3.0

    def test_pixmap(self):
        root = os.path.dirname(__file__)
        filename = os.path.join(root, 'assets', 'test3x3.png')
        item = BeePixmapItem(QtGui.QImage(filename))
        beejson = item.to_bee_json()
        assert len(beejson['pixmap']) > 0


class BeePixmapItemFromBeeJsonTestCase(BeeTestCase):

    def test_basic(self):
        bee_json = {
            'cls': 'BeePixmapItem',
            'scale': 2,
            'pos': [100.0, 200.0],
            'z': 3.0,
            'pixmap': '',
            'filename': 'bee.png',
        }

        item = BeePixmapItem.from_bee_json(bee_json)

        assert isinstance(item, BeePixmapItem)
        assert item.scale_factor == 2
        assert item.pos().x() == 100.0
        assert item.pos().y() == 200.0
        assert item.zValue() == 3.0
        assert item.filename == 'bee.png'
