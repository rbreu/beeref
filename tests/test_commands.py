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

    @patch('beeref.scene.BeeGraphicsScene.views')
    def test_ignore_first_redo(self, views_mock):
        scene = BeeGraphicsScene(None)
        view = MagicMock(get_scale=MagicMock(return_value=1))
        views_mock.return_value = [view]
        scene.update_selection = MagicMock()
        scene.max_z = 5
        item1 = BeePixmapItem(QtGui.QImage())
        scene.addItem(item1)
        item2 = BeePixmapItem(QtGui.QImage())
        command = commands.InsertItems(scene, [item2], ignore_first_redo=True)
        command.redo()
        assert list(scene.items_for_save()) == [item1]
        assert item1.isSelected() is False
        command.redo()
        assert list(scene.items_for_save()) == [item1, item2]
        assert item1.isSelected() is False
        assert item2.isSelected() is True
        item2.zValue() > 5


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
        item2.do_flip()
        command = commands.RotateItemsBy([item1, item2], -90,
                                         QtCore.QPointF(100, 100))
        command.redo()
        assert item1.rotation() == 270
        assert item1.pos().x() == 0
        assert item1.pos().y() == 200
        assert item2.rotation() == 120
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
        item2.do_flip()
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
        assert item1.rotation() == 270
        assert item1.pos().x() == 0
        assert item1.pos().y() == 200
        assert item2.rotation() == 120
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
                assert item2.scale() == 1.5
                assert item2.pos() == QtCore.QPointF(75, 60)
                command.undo()
                assert item1.scale() == 1
                assert item1.pos() == QtCore.QPointF(0, 0)
                assert item2.scale() == 3
                assert item2.pos() == QtCore.QPointF(0, 0)


class FlipItemsTestCase(BeeTestCase):

    def test_redo_undo_horizontal(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.setRotation(0)

        item2 = BeePixmapItem(QtGui.QImage())
        item2.setRotation(30)
        item2.setPos(100, 100)
        item2.do_flip()
        command = commands.FlipItems([item1, item2],
                                     QtCore.QPointF(100, 100),
                                     vertical=False)
        command.redo()
        assert item1.flip() == -1
        assert item1.rotation() == 0
        assert item1.pos() == QtCore.QPointF(200, 0)
        assert item2.flip() == 1
        assert item2.rotation() == 30
        assert item2.pos() == QtCore.QPointF(100, 100)
        command.undo()
        assert item1.flip() == 1
        assert item1.rotation() == 0
        assert item1.pos() == QtCore.QPointF(0, 0)
        assert item2.flip() == -1
        assert item2.rotation() == 30
        assert item2.pos() == QtCore.QPointF(100, 100)

    def test_redo_undo_vertical(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.setRotation(0)

        item2 = BeePixmapItem(QtGui.QImage())
        item2.setRotation(30)
        item2.setPos(100, 100)
        item2.do_flip()
        command = commands.FlipItems([item1, item2],
                                     QtCore.QPointF(100, 100),
                                     vertical=True)
        command.redo()
        assert item1.flip() == -1
        assert item1.rotation() == 180
        assert item1.pos() == QtCore.QPointF(0, 200)
        assert item2.flip() == 1
        assert item2.rotation() == 210
        assert item2.pos() == QtCore.QPointF(100, 100)
        command.undo()
        assert item1.flip() == 1
        assert item1.rotation() == 0
        assert item1.pos() == QtCore.QPointF(0, 0)
        assert item2.flip() == -1
        assert item2.rotation() == 30
        assert item2.pos() == QtCore.QPointF(100, 100)


class ResetScaleTestCase(BeeTestCase):

    def test_redo_undo(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setScale(2)
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=80):
                command = commands.ResetScale([item])
                command.redo()
                assert item.scale() == 1
                assert item.pos().x() == 50
                assert item.pos().y() == 40
                command.undo()
                assert item.scale() == 2
                assert item.pos().x() == 0
                assert item.pos().y() == 0


class ResetRotateTestCase(BeeTestCase):

    def test_redo_undo(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setRotation(180)
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=80):
                command = commands.ResetRotation([item])
                command.redo()
                assert item.rotation() == 0
                assert item.pos().x() == -100
                assert item.pos().y() == -80
                command.undo()
                assert item.rotation() == 180
                assert item.pos().x() == 0
                assert item.pos().y() == 0


class ResetFlipTestCase(BeeTestCase):

    def test_redo_undo(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.do_flip()
        item2 = BeePixmapItem(QtGui.QImage())
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=80):
                command = commands.ResetFlip([item1, item2])
                command.redo()
                assert item1.flip() == 1
                assert item1.pos().x() == -100
                assert item1.pos().y() == 0
                assert item2.flip() == 1
                assert item2.pos().x() == 0
                assert item2.pos().y() == 0
                command.undo()
                assert item1.flip() == -1
                assert item1.pos().x() == 0
                assert item1.pos().y() == 0
                assert item2.flip() == 1
                assert item2.pos().x() == 0
                assert item2.pos().y() == 0


class ResetTransformsTestCase(BeeTestCase):

    def test_redo_undo(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.setScale(2)
        item1.do_flip()
        item2 = BeePixmapItem(QtGui.QImage())
        item2.setRotation(180)
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=80):
                command = commands.ResetTransforms([item1, item2])
                command.redo()
                assert item1.scale() == 1
                assert item1.rotation() == 0
                assert item1.flip() == 1
                assert item1.pos().x() == -150
                assert item1.pos().y() == 40
                assert item2.scale() == 1
                assert item2.rotation() == 0
                assert item2.flip() == 1
                assert item2.pos().x() == -100
                assert item2.pos().y() == -80
                command.undo()
                assert item1.scale() == 2
                assert item1.rotation() == 0
                assert item1.flip() == -1
                assert item1.pos().x() == 0
                assert item1.pos().y() == 0
                assert item2.scale() == 1
                assert item2.rotation() == 180
                assert item2.flip() == 1
                assert item2.pos().x() == 0
                assert item2.pos().y() == 0


class ArrangeItemsTestCase(BeeTestCase):

    def test_redo_undo(self):
        scene = BeeGraphicsScene(None)
        item1 = BeePixmapItem(QtGui.QImage())
        item1.do_flip()
        scene.addItem(item1)
        item2 = BeePixmapItem(QtGui.QImage())
        item2.setRotation(90)
        scene.addItem(item2)
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=80):
                command = commands.ArrangeItems(
                    scene,
                    [item1, item2],
                    [QtCore.QPointF(1, 2), QtCore.QPointF(203, 204)])

                command.redo()
                assert item1.pos() == QtCore.QPointF(101, 2)
                assert item2.pos() == QtCore.QPointF(283, 204)
                command.undo()
                assert item1.pos() == QtCore.QPointF(0, 0)
                assert item2.pos() == QtCore.QPointF(0, 0)
