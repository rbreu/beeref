from PyQt6 import QtGui

from beeref import commands
from beeref.items import BeePixmapItem
from beeref.scene import BeeGraphicsScene
from .base import BeeTestCase


class InsertItemsTestCase(BeeTestCase):

    def test_redo_undo(self):
        def get_images():
            return list(filter(lambda i: isinstance(i, BeePixmapItem),
                               scene.items()))

        scene = BeeGraphicsScene(None)
        item1 = BeePixmapItem(QtGui.QImage())
        scene.addItem(item1)
        item2 = BeePixmapItem(QtGui.QImage())
        command = commands.InsertItems(scene, [item2])
        command.redo()
        assert len(get_images()) == 2
        assert item1 in scene.items()
        assert item1.isSelected() is False
        assert item2 in scene.items()
        assert item2.isSelected() is True
        command.undo()
        assert get_images() == [item1]
        assert item1.isSelected() is False


class DeleteItemsTestCase(BeeTestCase):

    def test_redo_undo(self):
        def get_images():
            return list(filter(lambda i: isinstance(i, BeePixmapItem),
                               scene.items()))

        scene = BeeGraphicsScene(None)
        item1 = BeePixmapItem(QtGui.QImage())
        scene.addItem(item1)
        item2 = BeePixmapItem(QtGui.QImage())
        scene.addItem(item2)
        item2.setSelected(True)
        command = commands.DeleteItems(scene, [item2])
        command.redo()
        assert get_images() == [item1]
        command.undo()
        assert len(get_images()) == 2
        assert item1 in scene.items()
        assert item1.isSelected() is False
        assert item2 in scene.items()
        assert item2.isSelected() is True


class MoveItemsByTestCase(BeeTestCase):

    def test_redo_undo(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.setPos(0, 0)
        item2 = BeePixmapItem(QtGui.QImage())
        item2.setPos(30, 40)
        command = commands.MoveItemsBy([item1, item2], 50, 100)
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
        command = commands.MoveItemsBy([item1, item2], 50, 100, True)
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
        item1.scale_factor = 1
        item2 = BeePixmapItem(QtGui.QImage())
        item2.scale_factor = 3
        command = commands.ScaleItemsBy([item1, item2], 2)
        command.redo()
        assert item1.scale_factor == 3
        assert item2.scale_factor == 5
        command.undo()
        assert item1.scale_factor == 1
        assert item2.scale_factor == 3

    def test_ignore_first_redo(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.scale_factor = 1
        item2 = BeePixmapItem(QtGui.QImage())
        item2.scale_factor = 3
        command = commands.ScaleItemsBy([item1, item2], 2, True)
        command.redo()
        assert item1.scale_factor == 1
        assert item2.scale_factor == 3
        command.redo()
        assert item1.scale_factor == 3
        assert item2.scale_factor == 5


class NormalizeItemsTestCase(BeeTestCase):

    def test_redo_undo(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.scale_factor = 1
        item2 = BeePixmapItem(QtGui.QImage())
        item2.scale_factor = 3
        command = commands.NormalizeItems([item1, item2], [2, 0.5])
        command.redo()
        assert item1.scale_factor == 2
        assert item2.scale_factor == 0.5
        command.undo()
        assert item1.scale_factor == 1
        assert item2.scale_factor == 3
