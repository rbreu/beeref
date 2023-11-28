from unittest.mock import MagicMock, patch

from PyQt6 import QtCore, QtGui

from beeref import commands
from beeref.items import BeePixmapItem, BeeTextItem


def test_insert_items(view):
    view.scene.update_selection = MagicMock()
    view.scene.max_z = 5
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage())
    item2.setPos(50, 40)
    command = commands.InsertItems(view.scene, [item2])
    command.redo()
    assert list(view.scene.items_for_save()) == [item1, item2]
    assert item1.isSelected() is False
    assert item2.isSelected() is True
    assert item2.pos() == QtCore.QPointF(50, 40)
    item2.zValue() > 5
    command.undo()
    assert list(view.scene.items_for_save()) == [item1]
    assert item1.isSelected() is False
    assert item2.pos() == QtCore.QPointF(50, 40)


def test_insert_items_with_position(view):
    view.scene.update_selection = MagicMock()

    item1 = BeePixmapItem(QtGui.QImage())
    item1.setPos(10, 20)
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage())
    item2.setPos(50, 40)
    view.scene.addItem(item2)

    with patch.object(item1, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 80)):
        with patch.object(item2, 'bounding_rect_unselected',
                          return_value=QtCore.QRectF(0, 0, 100, 80)):
            command = commands.InsertItems(
                view.scene, [item1, item2], QtCore.QPointF(100, 200))
            command.redo()
            assert set(view.scene.items_for_save()) == {item1, item2}
            assert item1.pos() == QtCore.QPointF(30, 150)
            assert item2.pos() == QtCore.QPointF(70, 170)
            command.undo()
            assert list(view.scene.items_for_save()) == []
            assert item1.pos() == QtCore.QPointF(10, 20)
            assert item2.pos() == QtCore.QPointF(50, 40)


def test_insert_items_ignore_first_redo(view):
    view.scene.update_selection = MagicMock()
    view.scene.max_z = 5
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage())
    command = commands.InsertItems(view.scene, [item2], ignore_first_redo=True)
    command.redo()
    assert list(view.scene.items_for_save()) == [item1]
    assert item1.isSelected() is False
    command.redo()
    assert list(view.scene.items_for_save()) == [item1, item2]
    assert item1.isSelected() is False
    assert item2.isSelected() is True
    item2.zValue() > 5


def test_delete_items(view):
    view.scene.update_selection = MagicMock()
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    command = commands.DeleteItems(view.scene, [item2])
    command.redo()
    assert list(view.scene.items_for_save()) == [item1]
    command.undo()
    assert list(view.scene.items_for_save()) == [item1, item2]
    assert item1.isSelected() is False
    assert item2.isSelected() is True


def test_move_items_by(qapp):
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


def test_move_items_by_ignore_first_redo(qapp):
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


def test_scale_items_by(view):
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


def test_scale_items_by_ignore_first_redo(qapp):
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


def test_rotate_items_by(qapp):
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


def test_rotate_items_by_ignore_first_redo(qapp):
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


def test_normalize_items(qapp):
    item1 = BeePixmapItem(QtGui.QImage())
    item1.setScale(1)
    item2 = BeePixmapItem(QtGui.QImage())
    item2.setScale(3)
    with patch.object(item1, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 80)):
        with patch.object(item2, 'bounding_rect_unselected',
                          return_value=QtCore.QRectF(0, 0, 100, 80)):
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


def test_flip_items_horizontal(qapp):
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


def test_flip_items_vertical(qapp):
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


def test_reset_scale(view, item):
    item.setScale(2)
    with patch.object(item, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 80)):
        command = commands.ResetScale([item])
        command.redo()
        assert item.scale() == 1
        assert item.pos().x() == 50
        assert item.pos().y() == 40
        command.undo()
        assert item.scale() == 2
        assert item.pos().x() == 0
        assert item.pos().y() == 0


def test_reset_rotate(view, item):
    item.setRotation(180)
    with patch.object(item, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 80)):
        command = commands.ResetRotation([item])
        command.redo()
        assert item.rotation() == 0
        assert item.pos().x() == -100
        assert item.pos().y() == -80
        command.undo()
        assert item.rotation() == 180
        assert item.pos().x() == 0
        assert item.pos().y() == 0


def test_reset_flip(qapp):
    item1 = BeePixmapItem(QtGui.QImage())
    item1.do_flip()
    item2 = BeePixmapItem(QtGui.QImage())
    with patch.object(item1, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 80)):
        with patch.object(item2, 'bounding_rect_unselected',
                          return_value=QtCore.QRectF(0, 0, 100, 80)):
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


def test_reset_crop(qapp):
    item1 = BeePixmapItem(QtGui.QImage())
    item1.crop = QtCore.QRectF(10, 20, 30, 50)
    item2 = BeePixmapItem(QtGui.QImage())
    item2.crop = QtCore.QRectF(5, 6, 55, 66)
    with patch.object(BeePixmapItem, 'reset_crop'):
        command = commands.ResetCrop([item1, item2])
        command.redo()
        assert BeePixmapItem.reset_crop.call_count == 2
        assert item1.pos() == QtCore.QPointF(0, 0)
        assert item2.pos() == QtCore.QPointF(0, 0)

        item1.crop = QtCore.QRectF(0, 0, 0, 0)
        item2.crop = QtCore.QRectF(0, 0, 0, 0)
        command.undo()
        assert item1.crop == QtCore.QRectF(10, 20, 30, 50)
        assert item1.pos() == QtCore.QPointF(0, 0)
        assert item2.crop == QtCore.QRectF(5, 6, 55, 66)
        assert item2.pos() == QtCore.QPointF(0, 0)


def test_reset_crop_ignores_uncroppable(qapp):
    item = BeeTextItem('foo')
    brect = item.boundingRect()
    command = commands.ResetCrop([item])
    command.redo()
    assert item.pos() == QtCore.QPointF(0, 0)
    assert item.boundingRect() == brect
    command.undo()
    assert item.pos() == QtCore.QPointF(0, 0)
    assert item.boundingRect() == brect


def test_reset_transforms(qapp):
    item1 = BeePixmapItem(QtGui.QImage())
    item1.setScale(2)
    item1.do_flip()
    item2 = BeeTextItem('foo')
    item2.setRotation(180)
    item3 = BeePixmapItem(QtGui.QImage())
    item3.crop = QtCore.QRectF(10, 20, 30, 40)
    item3.reset_crop = MagicMock()
    with patch.object(item1, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 80)):
        with patch.object(item2, 'bounding_rect_unselected',
                          return_value=QtCore.QRectF(0, 0, 100, 80)):
            command = commands.ResetTransforms([item1, item2, item3])
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
            item3.reset_crop.assert_called_once_with()

            item3.crop = QtCore.QRectF(0, 0, 0, 0)
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
            assert item3.crop == QtCore.QRectF(10, 20, 30, 40)


def test_arrange_items(view):
    item1 = BeePixmapItem(QtGui.QImage())
    item1.do_flip()
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage())
    item2.setRotation(90)
    view.scene.addItem(item2)
    item3 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item3)
    with patch.object(item1, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 80)):
        with patch.object(item2, 'bounding_rect_unselected',
                          return_value=QtCore.QRectF(0, 0, 100, 80)):
            with patch.object(item3, 'bounding_rect_unselected',
                              return_value=QtCore.QRectF(5, 5, 20, 30)):

                command = commands.ArrangeItems(
                    view.scene,
                    [item1, item2, item3],
                    [QtCore.QPointF(1, 2),
                     QtCore.QPointF(203, 204),
                     QtCore.QPointF(307, 308)])

                command.redo()
                assert item1.pos() == QtCore.QPointF(101, 2)
                assert item2.pos() == QtCore.QPointF(283, 204)
                assert item3.pos() == QtCore.QPointF(302, 303)
                command.undo()
                assert item1.pos() == QtCore.QPointF(0, 0)
                assert item2.pos() == QtCore.QPointF(0, 0)
                assert item3.pos() == QtCore.QPointF(0, 0)


def test_crop_item(item):
    item.crop = QtCore.QRectF(0, 0, 100, 80)
    command = commands.CropItem(item, QtCore.QRectF(10, 20, 30, 40))
    command.redo()
    assert item.crop == QtCore.QRectF(10, 20, 30, 40)
    assert item.pos() == QtCore.QPointF(0, 0)
    command.undo()
    assert item.crop == QtCore.QRectF(0, 0, 100, 80)
    assert item.pos() == QtCore.QPointF(0, 0)


def test_change_text():
    item = BeeTextItem('foo')
    command = commands.ChangeText(item, 'bar', 'foo')
    command.redo()
    assert item.toPlainText() == 'bar'
    command.undo()
    assert item.toPlainText() == 'foo'
