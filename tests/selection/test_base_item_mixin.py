from unittest.mock import patch, MagicMock, PropertyMock

from PyQt6 import QtCore, QtGui

from beeref.items import BeePixmapItem


def test_set_scale(qapp, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3), imgfilename3x3)
    item.prepareGeometryChange = MagicMock()
    item.setScale(3)
    assert item.scale() == 3
    assert item.pos().x() == 0
    assert item.pos().y() == 0
    item.prepareGeometryChange.assert_called_once()


def test_set_scale_ignores_zero(qapp, item):
    item.setScale(0)
    assert item.scale() == 1


def test_set_scale_ignores_negative(qapp, item):
    item.setScale(-0.1)
    assert item.scale() == 1


def test_set_scale_with_anchor(qapp, item):
    item.setScale(2, anchor=QtCore.QPointF(100, 100))
    assert item.scale() == 2
    assert item.pos() == QtCore.QPointF(-100, -100)


def test_set_zvalue_sets_new_max(view, item):
    view.scene.addItem(item)
    item.setZValue(1.1)
    assert item.zValue() == 1.1
    assert view.scene.max_z == 1.1
    assert view.scene.min_z == 0


def test_set_zvalue_sets_new_min(view, item):
    view.scene.addItem(item)
    item.setZValue(-1.1)
    assert item.zValue() == -1.1
    assert view.scene.max_z == 0
    assert view.scene.min_z == -1.1


def test_bring_to_front(view, item):
    view.scene.addItem(item)
    item.setZValue(3.3)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.bring_to_front()
    assert item2.zValue() > item.zValue()
    assert item2.zValue() == view.scene.max_z


def test_set_rotation_no_anchor(qapp, item):
    item.setRotation(45)
    assert item.rotation() == 45
    assert item.pos().x() == 0
    assert item.pos().y() == 0


def test_set_rotation_anchor_bottomright_cw(qapp, item):
    item.setRotation(90, QtCore.QPointF(100, 100))
    assert item.rotation() == 90
    assert item.pos().x() == 200
    assert item.pos().y() == 0


def test_set_rotation_anchor_bottomright_ccw(qapp, item):
    item.setRotation(-90, QtCore.QPointF(100, 100))
    assert item.rotation() == 270
    assert item.pos().x() == 0
    assert item.pos().y() == 200


def test_set_rotation_caps_above_360(qapp, item):
    item.setRotation(400)
    assert item.rotation() == 40


def test_flip(qapp, item):
    assert item.flip() == 1


def test_flip_when_flipped(qapp, item):
    item.do_flip()
    assert item.flip() == -1


def test_do_flip_no_anchor(qapp, item):
    item.do_flip()
    assert item.flip() == -1
    item.do_flip()
    assert item.flip() == 1


def test_do_flip_vertical(qapp, item):
    item.do_flip(vertical=True)
    assert item.flip() == -1
    assert item.rotation() == 180


def test_do_flip_anchor(qapp, item):
    item.do_flip(anchor=QtCore.QPointF(100, 100))
    assert item.flip() == -1
    assert item.pos() == QtCore.QPointF(200, 0)


def test_do_flip_vertical_anchor(qapp, item):
    item.do_flip(vertical=True, anchor=QtCore.QPointF(100, 100))
    assert item.flip() == -1
    assert item.rotation() == 180
    assert item.pos() == QtCore.QPointF(0, 200)


def test_base_item_mixin_center_scene_coords(view, item):
    view.scene.addItem(item)
    item.setPos(5, 5)
    item.setScale(2)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            assert item.center_scene_coords == QtCore.QPointF(105, 85)
