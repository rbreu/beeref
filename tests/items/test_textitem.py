from unittest.mock import patch, MagicMock

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt

from beeref.items import BeeTextItem, item_registry


def test_in_items_registry():
    assert item_registry['text'] == BeeTextItem


@patch('beeref.selection.SelectableMixin.init_selectable')
def test_init(selectable_mock, qapp):
    item = BeeTextItem('foo bar')
    assert item.save_id is None
    assert item.width
    assert item.height
    assert item.scale() == 1
    assert item.toPlainText() == 'foo bar'
    assert item.is_editable is True
    assert item.edit_mode is False
    selectable_mock.assert_called_once()


def test_set_pos_center(qapp):
    item = BeeTextItem('foo bar')
    with patch.object(item, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 200, 100)):
        item.set_pos_center(QtCore.QPointF(0, 0))
        assert item.pos().x() == -100
        assert item.pos().y() == -50


def test_set_pos_center_when_scaled(qapp):
    item = BeeTextItem('foo bar')
    item.setScale(2)
    with patch.object(item, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 200, 100)):
        item.set_pos_center(QtCore.QPointF(0, 0))
        assert item.pos().x() == -200
        assert item.pos().y() == -100


def test_set_pos_center_when_rotated(qapp):
    item = BeeTextItem('foo bar')
    item.setRotation(90)
    with patch.object(item, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 200, 100)):
        item.set_pos_center(QtCore.QPointF(0, 0))
        assert item.pos().x() == 50
        assert item.pos().y() == -100


def test_get_extra_save_data(qapp):
    item = BeeTextItem('foo bar')
    assert item.get_extra_save_data() == {'text': 'foo bar'}


@patch('beeref.items.BeeTextItem.boundingRect')
def test_contains_when_inside_bounds(brect_mock, qapp):
    brect_mock.return_value = QtCore.QRectF(20, 30, 50, 50)
    item = BeeTextItem('foo bar')
    item.contains(QtCore.QPointF(33, 45)) is True
    brect_mock.assert_called_once_with()


@patch('beeref.items.BeeTextItem.boundingRect')
def test_contains_when_outside_bounds(brect_mock, qapp):
    brect_mock.return_value = QtCore.QRectF(20, 30, 50, 50)
    item = BeeTextItem('foo bar')
    item.contains(QtCore.QPointF(19, 29)) is False
    brect_mock.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsTextItem.paint')
def test_paint(paint_mock, qapp):
    item = BeeTextItem('foo bar')
    item.paint_selectable = MagicMock()
    painter = MagicMock()
    option = MagicMock()
    item.paint(painter, option, 'widget')
    item.paint_selectable.assert_called_once()
    painter.drawRect.assert_called_once()
    assert option.state == QtWidgets.QStyle.StateFlag.State_Enabled
    paint_mock.assert_called_once_with(painter, option, 'widget')


def test_has_selection_outline_when_not_selected(view):
    item = BeeTextItem('foo bar')
    view.scene.addItem(item)
    item.setSelected(False)
    item.has_selection_outline() is False


def test_has_selection_outline_when_selected(view):
    item = BeeTextItem('foo bar')
    view.scene.addItem(item)
    item.setSelected(True)
    item.has_selection_outline() is True


def test_has_selection_handles_when_not_selected(view):
    item = BeeTextItem('foo bar')
    view.scene.addItem(item)
    item.setSelected(False)
    item2 = BeeTextItem('baz')
    view.scene.addItem(item2)
    item2.setSelected(False)
    item.has_selection_handles() is False


def test_has_selection_handles_when_selected_single(view):
    item = BeeTextItem('foo bar')
    view.scene.addItem(item)
    item.setSelected(True)
    item2 = BeeTextItem('baz')
    view.scene.addItem(item2)
    item2.setSelected(False)
    item.has_selection_handles() is True


def test_has_selection_handles_when_selected_multi(view):
    item = BeeTextItem('foo bar')
    view.scene.addItem(item)
    item.setSelected(True)
    item2 = BeeTextItem('baz')
    view.scene.addItem(item2)
    item2.setSelected(True)
    item.has_selection_handles() is False


def test_has_selection_handles_when_selected_single_and_edit_mode(view):
    item = BeeTextItem('foo bar')
    item.edit_mode = False
    view.scene.addItem(item)
    item.setSelected(True)
    item2 = BeeTextItem('baz')
    view.scene.addItem(item2)
    item2.setSelected(False)
    item.has_selection_handles() is False


def test_selection_action_items(qapp):
    item = BeeTextItem('foo bar')
    assert item.selection_action_items() == [item]


def test_update_from_data(qapp):
    item = BeeTextItem('foo bar')
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


def test_update_from_data_keeps_flip(qapp):
    item = BeeTextItem('foo bar')
    item.do_flip()
    item.update_from_data(flip=-1)
    assert item.flip() == -1


def test_update_from_data_keeps_unset_values(qapp):
    item = BeeTextItem('foo bar')
    item.setScale(3)
    item.update_from_data(rotation=45)
    assert item.scale() == 3
    assert item.flip() == 1


def test_create_from_data(qapp):
    item = BeeTextItem.create_from_data(data={'text': 'hello world'})
    item.toPlainText() == 'hello world'


def test_create_copy(qapp):
    item = BeeTextItem('foo bar')
    item.setPos(20, 30)
    item.setRotation(33)
    item.do_flip()
    item.setZValue(0.5)
    item.setScale(2.2)

    copy = item.create_copy()
    assert copy.toPlainText() == 'foo bar'
    assert copy.pos() == QtCore.QPointF(20, 30)
    assert copy.rotation() == 33
    assert item.flip() == -1
    assert item.zValue() == 0.5
    assert item.scale() == 2.2


def test_enter_edit_mode(view):
    item = BeeTextItem('foo bar')
    view.scene.addItem(item)
    item.enter_edit_mode()
    assert item.edit_mode is True
    assert view.scene.edit_item == item
    flags = item.textInteractionFlags()
    assert flags == Qt.TextInteractionFlag.TextEditorInteraction


@patch('PyQt6.QtGui.QTextCursor')
@patch('beeref.items.BeeTextItem.setTextCursor')
def test_exit_edit_mode(setcursor_mock, cursor_mock, view):
    item = BeeTextItem('foo bar')
    item.edit_mode = True
    item.old_text = 'old'
    view.scene.addItem(item)
    view.scene.edit_item = item
    item.exit_edit_mode()
    assert item.edit_mode is False
    assert view.scene.edit_item is None
    flags = item.textInteractionFlags()
    assert flags == Qt.TextInteractionFlag.NoTextInteraction
    cursor_mock.assert_called_once_with(item.document())
    setcursor_mock.assert_called_once_with(cursor_mock.return_value)
    assert view.scene.edit_item is None


def test_exit_edit_mode_when_text_empty(view):
    item = BeeTextItem(' \r\n\t')
    item.edit_mode = True
    item.old_text = 'old'
    view.scene.addItem(item)
    view.scene.edit_item = item
    item.exit_edit_mode()
    assert item.edit_mode is False
    assert view.scene.edit_item is None
    flags = item.textInteractionFlags()
    assert flags == Qt.TextInteractionFlag.NoTextInteraction
    assert item.scene() is None
    assert view.scene.items() == []
    assert view.scene.edit_item is None


@patch('PyQt6.QtWidgets.QGraphicsTextItem.keyPressEvent')
@patch('beeref.items.BeeTextItem.exit_edit_mode')
def test_key_press_event_any_key(exit_mock, key_press_mock, view):
    item = BeeTextItem('foo bar')
    view.scene.addItem(item)
    view.scene.edit_item = item
    event = MagicMock()
    event.key.return_value = Qt.Key.Key_T
    event.modifiers.return_value = Qt.KeyboardModifier.NoModifier
    item.keyPressEvent(event)
    key_press_mock.assert_called_once_with(event)
    exit_mock.assert_not_called()
    assert view.scene.edit_item == item


@patch('PyQt6.QtWidgets.QGraphicsTextItem.keyPressEvent')
@patch('beeref.items.BeeTextItem.exit_edit_mode')
def test_key_press_event_shift_return(exit_mock, key_press_mock, view):
    item = BeeTextItem('foo bar')
    view.scene.addItem(item)
    view.scene.edit_item = item
    event = MagicMock()
    event.key.return_value = Qt.Key.Key_Return
    event.modifiers.return_value = Qt.KeyboardModifier.ShiftModifier
    item.keyPressEvent(event)
    key_press_mock.assert_called_once_with(event)
    exit_mock.assert_not_called()
    assert view.scene.edit_item == item


@patch('PyQt6.QtWidgets.QGraphicsTextItem.keyPressEvent')
@patch('beeref.items.BeeTextItem.exit_edit_mode')
def test_key_press_event_shift_enter(exit_mock, key_press_mock, view):
    item = BeeTextItem('foo bar')
    view.scene.addItem(item)
    view.scene.edit_item = item
    event = MagicMock()
    event.key.return_value = Qt.Key.Key_Enter
    event.modifiers.return_value = Qt.KeyboardModifier.ShiftModifier
    item.keyPressEvent(event)
    key_press_mock.assert_called_once_with(event)
    exit_mock.assert_not_called()
    assert view.scene.edit_item == item


@patch('PyQt6.QtWidgets.QGraphicsTextItem.keyPressEvent')
@patch('beeref.items.BeeTextItem.exit_edit_mode')
def test_key_press_event_return(exit_mock, key_press_mock, view):
    item = BeeTextItem('foo bar')
    view.scene.addItem(item)
    view.scene.edit_item = item
    event = MagicMock()
    event.key.return_value = Qt.Key.Key_Return
    event.modifiers.return_value = Qt.KeyboardModifier.NoModifier
    item.keyPressEvent(event)
    key_press_mock.assert_not_called()
    exit_mock.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsTextItem.keyPressEvent')
@patch('beeref.items.BeeTextItem.exit_edit_mode')
def test_key_press_event_enter(exit_mock, key_press_mock, view):
    item = BeeTextItem('foo bar')
    view.scene.addItem(item)
    view.scene.edit_item = item
    event = MagicMock()
    event.key.return_value = Qt.Key.Key_Enter
    event.modifiers.return_value = Qt.KeyboardModifier.NoModifier
    item.keyPressEvent(event)
    key_press_mock.assert_not_called()
    exit_mock.assert_called_once_with()


def test_item_to_clipboard(qapp):
    clipboard = QtWidgets.QApplication.clipboard()
    item = BeeTextItem('foo bar')
    item.copy_to_clipboard(clipboard)
    assert clipboard.text() == 'foo bar'
