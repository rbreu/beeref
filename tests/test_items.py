from unittest.mock import patch, MagicMock, PropertyMock

from PyQt6 import QtCore, QtGui

from beeref.items import BeePixmapItem
from beeref.scene import BeeGraphicsScene
from .base import BeeTestCase


class BeePixmapItemTestCase(BeeTestCase):

    def setUp(self):
        self.scene = BeeGraphicsScene(None)

    @patch('beeref.selection.SelectableMixin.init_selectable')
    def test_init(self, selectable_mock):
        item = BeePixmapItem(
            QtGui.QImage(self.imgfilename3x3), self.imgfilename3x3)
        assert item.save_id is None
        assert item.width == 3
        assert item.height == 3
        assert item.scale() == 1
        assert item.filename == self.imgfilename3x3
        selectable_mock.assert_called_once()

    def test_set_pos_center(self):
        item = BeePixmapItem(QtGui.QImage())
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=200):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=100):
                item.set_pos_center(QtCore.QPointF(0, 0))
                assert item.pos().x() == -100
                assert item.pos().y() == -50

    def test_set_pos_center_when_scaled(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setScale(2)
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=200):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=100):
                item.set_pos_center(QtCore.QPointF(0, 0))
                assert item.pos().x() == -200
                assert item.pos().y() == -100

    def test_set_pos_center_when_rotated(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setRotation(90)
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=200):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=100):
                item.set_pos_center(QtCore.QPointF(0, 0))
                assert item.pos().x() == 50
                assert item.pos().y() == -100

    def test_pixmap_to_bytes(self):
        item = BeePixmapItem(QtGui.QImage(self.imgfilename3x3))
        assert item.pixmap_to_bytes().startswith(b'\x89PNG')

    def test_pixmap_from_bytes(self):
        item = BeePixmapItem(QtGui.QImage())
        with open(self.imgfilename3x3, 'rb') as f:
            imgdata = f.read()
        item.pixmap_from_bytes(imgdata)
        assert item.width == 3
        assert item.height == 3

    def test_paint(self):
        item = BeePixmapItem(QtGui.QImage())
        item.pixmap = MagicMock(return_value='bee')
        item.paint_selectable = MagicMock()
        painter = MagicMock()
        item.paint(painter, None, None)
        item.paint_selectable.assert_called_once()
        painter.drawPixmap.assert_called_with(0, 0, 'bee')

    def test_has_selection_outline_when_not_selected(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.setSelected(False)
        item.has_selection_outline() is False

    def test_has_selection_outline_when_selected(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.setSelected(True)
        item.has_selection_outline() is True

    def test_has_selection_handles_when_not_selected(self):
        item1 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item1)
        item1.setSelected(False)
        item2 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item2)
        item2.setSelected(False)
        item1.has_selection_handles() is False

    def test_has_selection_handles_when_selected_single(self):
        item1 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item1)
        item1.setSelected(True)
        item2 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item2)
        item2.setSelected(False)
        item1.has_selection_handles() is True

    def test_has_selection_handles_when_selected_multi(self):
        view = MagicMock(get_scale=MagicMock(return_value=1))
        with patch('beeref.scene.BeeGraphicsScene.views',
                   return_value=[view]):
            item1 = BeePixmapItem(QtGui.QImage())
            self.scene.addItem(item1)
            item1.setSelected(True)
            item2 = BeePixmapItem(QtGui.QImage())
            self.scene.addItem(item2)
            item2.setSelected(True)
            item1.has_selection_handles() is False

    def test_selection_action_items(self):
        item = BeePixmapItem(QtGui.QImage())
        assert item.selection_action_items() == [item]

    def test_create_copy(self):
        item = BeePixmapItem(QtGui.QImage(self.imgfilename3x3), 'foo.png')
        item.setPos(20, 30)
        item.setRotation(33)
        item.do_flip()
        item.setZValue(0.5)
        item.setScale(2.2)

        copy = item.create_copy()
        assert copy.pixmap_to_bytes() == item.pixmap_to_bytes()
        assert copy.filename == 'foo.png'
        assert copy.pos() == QtCore.QPointF(20, 30)
        assert copy.rotation() == 33
        assert item.flip() == -1
        assert item.zValue() == 0.5
        assert item.scale() == 2.2
