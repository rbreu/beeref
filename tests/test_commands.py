from unittest.mock import MagicMock, patch, PropertyMock

from PyQt6 import QtCore, QtGui

from beeref import commands
from beeref.items import BeePixmapItem
from beeref.scene import BeeGraphicsScene
from .base import BeeTestCase


class InsertItemsTestCase(BeeTestCase):

    @patch('beeref.scene.BeeGraphicsScene.views')
    def test_redo_undo(self, views_mock):
        scene = BeeGraphicsScene(None)
        view = MagicMock(get_scale=MagicMock(return_value=1))
        views_mock.return_value = [view]
        scene.update_selection = MagicMock()
        scene.max_z = 5
        item1 = BeePixmapItem(QtGui.QImage())
        scene.addItem(item1)
        item2 = BeePixmapItem(QtGui.QImage())
        command = commands.InsertItems(scene, [item2])
        command.redo()
        assert list(scene.items_for_save()) == [item1, item2]
        assert item1.isSelected() is False
        assert item2.isSelected() is True
        item2.zValue() > 5
        command.undo()
        assert list(scene.items_for_save()) == [item1]
        assert item1.isSelected() is False


class DeleteItemsTestCase(BeeTestCase):

    def test_redo_undo(self):
        scene = BeeGraphicsScene(None)
        scene.update_selection = MagicMock()
        item1 = BeePixmapItem(QtGui.QImage())
        scene.addItem(item1)
        item2 = BeePixmapItem(QtGui.QImage())
        scene.addItem(item2)
        item2.setSelected(True)
        command = commands.DeleteItems(scene, [item2])
        command.redo()
        assert list(scene.items_for_save()) == [item1]
        command.undo()
        assert list(scene.items_for_save()) == [item1, item2]
        assert item1.isSelected() is False
        assert item2.isSelected() is True


class MoveItemsByTestCase(BeeTestCase):

    def test_redo_undo(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.setPos(0, 0)
        item2 = BeePixmapItem(QtGui.QImage())
        item2.setPos(30, 40)
        command = commands.MoveItemsBy([item1, item2], QtCore.QPointF(50, 100))
        command.redo()
        assert item1.pos().x() == 50
        assert item1.pos().y() == 100
        assert item2.pos().x() == 80
        assert item2.pos().y() == 140

        command.undo()
        assert item1.pos().x() == 0
        assert item1.pos().y() == 0
        assert item2.pos().x() == 30
        assert item2.pos().y() == 40

    def test_ignore_first_redo(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.setPos(0, 0)
        item2 = BeePixmapItem(QtGui.QImage())
        item2.setPos(30, 40)
        command = commands.MoveItemsBy([item1, item2],
                                       QtCore.QPointF(50, 100),
                                       ignore_first_redo=True)
        command.redo()
        assert item1.pos().x() == 0
        assert item1.pos().y() == 0
        assert item2.pos().x() == 30
        assert item2.pos().y() == 40
        command.redo()
        assert item1.pos().x() == 50
        assert item1.pos().y() == 100
        assert item2.pos().x() == 80
        assert item2.pos().y() == 140


class ScaleItemsByTestCase(BeeTestCase):

    def test_redo_undo(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.setScale(1)
        item2 = BeePixmapItem(QtGui.QImage())
        item2.setScale(3)
        item2.setPos(100, 100)
        command = commands.ScaleItemsBy([item1, item2], 2,
                                        QtCore.QPointF(100, 100))
        command.redo()
        assert item1.scale() == 2
        assert item1.pos().x() == -100
        assert item1.pos().y() == -100
        assert item2.scale() == 6
        assert item2.pos().x() == 100
        assert item2.pos().y() == 100
        command.undo()
        assert item1.scale() == 1
        assert item1.pos().x() == 0
        assert item1.pos().y() == 0
        assert item2.scale() == 3
        assert item2.pos().x() == 100
        assert item2.pos().y() == 100

    def test_ignore_first_redo(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.setScale(1)
        item2 = BeePixmapItem(QtGui.QImage())
        item2.setScale(3)
        item2.setPos(100, 100)
        command = commands.ScaleItemsBy([item1, item2], 2,
                                        QtCore.QPointF(100, 100),
                                        ignore_first_redo=True)
        command.redo()
        assert item1.scale() == 1
        assert item1.pos().x() == 0
        assert item1.pos().y() == 0
        assert item2.scale() == 3
        assert item2.pos().x() == 100
        assert item2.pos().y() == 100
        command.redo()
        assert item1.scale() == 2
        assert item1.pos().x() == -100
        assert item1.pos().y() == -100
        assert item2.scale() == 6
        assert item2.pos().x() == 100
        assert item2.pos().y() == 100


class RotateItemsByTestCase(BeeTestCase):

    def test_redo_undo(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.setRotation(0)

        item2 = BeePixmapItem(QtGui.QImage())
        item2.setRotation(30)
        item2.setPos(100, 100)
        command = commands.RotateItemsBy([item1, item2], -90,
                                         QtCore.QPointF(100, 100))
        command.redo()
        assert item1.rotation() == -90
        assert item1.pos().x() == 0
        assert item1.pos().y() == 200
        assert item2.rotation() == -60
        assert item2.pos().x() == 100
        assert item2.pos().y() == 100
        command.undo()
        assert item1.rotation() == 0
        assert item1.pos().x() == 0
        assert item1.pos().y() == 0
        assert item2.rotation() == 30
        assert item2.pos().x() == 100
        assert item2.pos().y() == 100

    def test_ignore_first_redo(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.setRotation(0)

        item2 = BeePixmapItem(QtGui.QImage())
        item2.setRotation(30)
        item2.setPos(100, 100)
        command = commands.RotateItemsBy([item1, item2], -90,
                                         QtCore.QPointF(100, 100),
                                         ignore_first_redo=True)
        command.redo()
        assert item1.rotation() == 0
        assert item1.pos().x() == 0
        assert item1.pos().y() == 0
        assert item2.rotation() == 30
        assert item2.pos().x() == 100
        assert item2.pos().y() == 100
        command.redo()
        assert item1.rotation() == -90
        assert item1.pos().x() == 0
        assert item1.pos().y() == 200
        assert item2.rotation() == -60
        assert item2.pos().x() == 100
        assert item2.pos().y() == 100


class NormalizeItemsTestCase(BeeTestCase):

    def test_redo_undo(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.setScale(1)
        item2 = BeePixmapItem(QtGui.QImage())
        item2.setScale(3)
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=80):
                command = commands.NormalizeItems([item1, item2], [2, 0.5])
                command.redo()
                assert item1.scale() == 2
                assert item1.pos() == QtCore.QPointF(-50, -40)
                assert item2.scale() == 0.5
                assert item2.pos() == QtCore.QPointF(125, 100)
                command.undo()
                assert item1.scale() == 1
                assert item1.pos() == QtCore.QPointF(0, 0)
                assert item2.scale() == 3
                assert item2.pos() == QtCore.QPointF(0, 0)
