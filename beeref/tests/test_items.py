import os.path

from PyQt6 import QtGui, QtWidgets

from beeref.items import BeePixmapItem
from beeref.tests.base import BeeTestCase


class BeePixmapItemTestCase(BeeTestCase):

    def test_init(self):
        filename = os.path.join('beeref', 'tests', 'assets', 'test3x3.png')
        item = BeePixmapItem(QtGui.QImage(filename), filename)
        assert item.width == 3
        assert item.height == 3
        assert item.scale_factor == 1
        assert item.flags() == (
            QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsMovable
            | QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsSelectable)
        assert item.filename == filename


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
        filename = os.path.join('beeref', 'tests', 'assets', 'test3x3.png')
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
