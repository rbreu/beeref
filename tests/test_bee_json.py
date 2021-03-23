import os.path

from PyQt6 import QtGui

from beeref import bee_json
from beeref.items import BeePixmapItem
from beeref.scene import BeeGraphicsScene
from .base import BeeTestCase


class BeeJsonTestCase(BeeTestCase):

    def test_dumps_loads(self):
        root = os.path.dirname(__file__)
        filename = os.path.join(root, 'assets', 'test3x3.png')
        item = BeePixmapItem(QtGui.QImage(filename), filename)
        item.setScale(2)
        item.setPos(100, 200)
        item.setZValue(3)
        dump = bee_json.dumps({'items': [item]})

        obj = bee_json.loads(dump)
        assert len(obj['items']) == 1
        obj_item = obj['items'][0]
        assert obj_item.scale_factor == 2
        assert obj_item.zValue() == 3
        assert obj_item.pos().x() == 100
        assert obj_item.pos().y() == 200
        assert obj_item.width == item.width
        assert obj_item.height == item.height
        assert obj_item.filename == filename
