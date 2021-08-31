from unittest.mock import patch, MagicMock, PropertyMock

from PyQt6 import QtCore, QtGui, QtWidgets

from beeref.items import BeePixmapItem, item_registry


def test_in_item_registry():
    assert item_registry['pixmap'] == BeePixmapItem


@patch('beeref.selection.SelectableMixin.init_selectable')
def test_init(selectable_mock, qapp, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3), imgfilename3x3)
    assert item.save_id is None
    assert item.width == 3
    assert item.height == 3
    assert item.scale() == 1
    assert item.filename == imgfilename3x3
    selectable_mock.assert_called_once()


def test_set_pos_center(qapp, item):
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=200):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=100):
            item.set_pos_center(QtCore.QPointF(0, 0))
            assert item.pos().x() == -100
            assert item.pos().y() == -50


def test_set_pos_center_when_scaled(qapp, item):
    item.setScale(2)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=200):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=100):
            item.set_pos_center(QtCore.QPointF(0, 0))
            assert item.pos().x() == -200
            assert item.pos().y() == -100


def test_set_pos_center_when_rotated(qapp, item):
    item.setRotation(90)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=200):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=100):
            item.set_pos_center(QtCore.QPointF(0, 0))
            assert item.pos().x() == 50
            assert item.pos().y() == -100


def test_get_extra_save_data(item):
    item.filename = 'foobar.png'
    assert item.get_extra_save_data() == {'filename': 'foobar.png'}


def test_pixmap_to_bytes(qapp, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    assert item.pixmap_to_bytes().startswith(b'\x89PNG')


def test_pixmap_from_bytes(qapp, item, imgfilename3x3):
    with open(imgfilename3x3, 'rb') as f:
        imgdata = f.read()
    item.pixmap_from_bytes(imgdata)
    assert item.width == 3
    assert item.height == 3


def test_paint(qapp, item):
    item.pixmap = MagicMock(return_value='bee')
    item.paint_selectable = MagicMock()
    painter = MagicMock()
    item.paint(painter, None, None)
    item.paint_selectable.assert_called_once()
    painter.drawPixmap.assert_called_with(0, 0, 'bee')


def test_has_selection_outline_when_not_selected(view, item):
    view.scene.addItem(item)
    item.setSelected(False)
    item.has_selection_outline() is False


def test_has_selection_outline_when_selected(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    item.has_selection_outline() is True


def test_has_selection_handles_when_not_selected(view, item):
    view.scene.addItem(item)
    item.setSelected(False)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(False)
    item.has_selection_handles() is False


def test_has_selection_handles_when_selected_single(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(False)
    item.has_selection_handles() is True


def test_has_selection_handles_when_selected_multi(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item.has_selection_handles() is False


def test_selection_action_items(qapp):
    item = BeePixmapItem(QtGui.QImage())
    assert item.selection_action_items() == [item]


def test_update_from_data(item):
    item.update_from_data(
        save_id=3,
        x=11,
        y=22,
        z=1.2,
        scale=2.5,
        rotation=45,
        flip=-1)
    assert item.save_id == 3
    assert item.pos() == QtCore.QPointF(11, 22)
    assert item.zValue() == 1.2
    assert item.rotation() == 45
    assert item.flip() == -1


def test_update_from_data_keeps_flip(item):
    item.do_flip()
    item.update_from_data(flip=-1)
    assert item.flip() == -1


def test_update_from_data_keeps_unset_values(item):
    item.setScale(3)
    item.update_from_data(rotation=45)
    assert item.scale() == 3
    assert item.flip() == 1


def test_create_from_data(item):
    new_item = BeePixmapItem.create_from_data(
        item=item, data={'filename': 'foobar.png'})
    assert new_item is item
    assert item.filename == 'foobar.png'


def test_create_copy(qapp, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3), 'foo.png')
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


def test_item_to_clipboard(qapp, imgfilename3x3):
    clipboard = QtWidgets.QApplication.clipboard()
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3), 'foo.png')
    item.copy_to_clipboard(clipboard)
    assert clipboard.pixmap().size() == item.pixmap().size()
