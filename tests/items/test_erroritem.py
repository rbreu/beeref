from unittest.mock import patch, MagicMock

from PyQt6 import QtCore, QtWidgets

from beeref.items import BeeErrorItem, item_registry


def test_in_items_registry():
    assert item_registry['error'] == BeeErrorItem


@patch('beeref.selection.SelectableMixin.init_selectable')
def test_init(selectable_mock, qapp):
    item = BeeErrorItem('foo bar')
    assert hasattr(item, 'save_id') is False
    assert item.original_save_id is None
    assert item.width
    assert item.height
    assert item.scale() == 1
    assert item.toPlainText() == 'foo bar'
    assert item.is_editable is False
    assert item.is_image is False
    selectable_mock.assert_called_once()


@patch('PyQt6.QtWidgets.QGraphicsTextItem.paint')
def test_paint(paint_mock, qapp):
    item = BeeErrorItem('foo bar')
    item.paint_selectable = MagicMock()
    painter = MagicMock()
    option = MagicMock()
    item.paint(painter, option, 'widget')
    item.paint_selectable.assert_called_once()
    painter.drawRect.assert_called_once()
    assert option.state == QtWidgets.QStyle.StateFlag.State_Enabled
    paint_mock.assert_called_once_with(painter, option, 'widget')


def test_update_from_data(qapp):
    item = BeeErrorItem('foo bar')
    item.update_from_data(
        save_id=3,
        x=11,
        y=22,
        z=1.2,
        scale=2.5,
        rotation=45,
        flip=-1,
        data={'opactiy': 0.5})
    assert item.original_save_id == 3
    assert item.pos() == QtCore.QPointF(11, 22)
    assert item.zValue() == 1.2
    assert item.rotation() == 45
    assert item.flip() == 1
    assert hasattr(item, 'save_id') is False


def test_update_from_data_keeps_unset_values(qapp):
    item = BeeErrorItem('foo bar')
    item.setScale(3)
    item.update_from_data(rotation=45)
    assert item.scale() == 3
    assert item.flip() == 1


def test_create_from_data(qapp):
    item = BeeErrorItem.create_from_data(data={'text': 'hello world'})
    item.toPlainText() == 'hello world'
    assert hasattr(item, 'save_id') is False


def test_create_copy(qapp):
    item = BeeErrorItem('foo bar')
    item.setPos(20, 30)
    item.setRotation(33)
    item.setZValue(0.5)
    item.setScale(2.2)

    copy = item.create_copy()
    assert copy.toPlainText() == 'foo bar'
    assert copy.pos() == QtCore.QPointF(20, 30)
    assert copy.rotation() == 33
    assert copy.zValue() == 0.5
    assert copy.scale() == 2.2
    assert copy.flip() == 1


def test_item_to_clipboard(qapp):
    clipboard = QtWidgets.QApplication.clipboard()
    item = BeeErrorItem('foo bar')
    item.copy_to_clipboard(clipboard)
    assert clipboard.text() == 'foo bar'


def test_flip(qapp):
    item = BeeErrorItem('foo bar')
    item.do_flip()
    assert item.flip() == 1


@patch('beeref.items.BeeErrorItem.boundingRect')
def test_contains_when_inside_bounds(brect_mock, qapp):
    brect_mock.return_value = QtCore.QRectF(20, 30, 50, 50)
    item = BeeErrorItem('foo bar')
    item.contains(QtCore.QPointF(33, 45)) is True
    brect_mock.assert_called_once_with()


@patch('beeref.items.BeeErrorItem.boundingRect')
def test_contains_when_outside_bounds(brect_mock, qapp):
    brect_mock.return_value = QtCore.QRectF(20, 30, 50, 50)
    item = BeeErrorItem('foo bar')
    item.contains(QtCore.QPointF(19, 29)) is False
    brect_mock.assert_called_once_with()
