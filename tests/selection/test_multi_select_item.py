from unittest.mock import patch, MagicMock

from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt

from beeref.items import BeePixmapItem
from beeref.selection import MultiSelectItem


@patch('beeref.selection.SelectableMixin.init_selectable')
def test_init(selectable_mock):
    item = MultiSelectItem()
    assert hasattr(item, 'save_id') is False
    selectable_mock.assert_called_once()


def test_paint():
    item = MultiSelectItem()
    item.paint_selectable = MagicMock()
    painter = MagicMock()
    item.paint(painter, None, None)
    item.paint_selectable.assert_called_once()
    painter.drawRect.assert_not_called()


def test_has_selection_outline():
    item = MultiSelectItem()
    item.has_selection_outline() is True


def test_has_selection_handles():
    item = MultiSelectItem()
    item.has_selection_handles() is True


def test_selection_action_items(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item3 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item3)
    item3.setSelected(False)
    action_items = set(view.scene.multi_select_item.selection_action_items())
    assert action_items == {item1, item2, view.scene.multi_select_item}


def test_lower_behind_selection_when_selection(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item3 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item3)
    item3.setSelected(False)

    item1.setZValue(3)
    item2.setZValue(4)
    item3.setZValue(1)

    view.scene.multi_select_item.setZValue(5)
    view.scene.multi_select_item.lower_behind_selection()
    assert view.scene.multi_select_item.zValue() == 2.999


def test_lower_behind_selection_when_no_selection(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(False)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(False)
    item3 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item3)
    item3.setSelected(False)

    item1.setZValue(3)
    item2.setZValue(4)
    item3.setZValue(1)

    view.scene.multi_select_item.setZValue(5)
    view.scene.multi_select_item.lower_behind_selection()
    assert view.scene.multi_select_item.zValue() == 5


def test_fit_selection_area():
    item = MultiSelectItem()
    item.setScale(5)
    item.setRotation(-20)
    item.do_flip()
    item.fit_selection_area(QtCore.QRectF(-10, -20, 100, 80))
    assert item.pos().x() == -10
    assert item.pos().y() == -20
    assert item.width == 101
    assert item.height == 81
    assert item.scale() == 1
    assert item.rotation() == 0
    assert item.flip() == 1
    assert item.isSelected() is True


@patch('PyQt6.QtWidgets.QGraphicsRectItem.mousePressEvent')
def test_mouse_press_event_when_ctrl_leftclick(mouse_mock):
    item = MultiSelectItem()
    item.fit_selection_area(QtCore.QRectF(0, 0, 100, 80))
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
        modifiers=MagicMock(
            return_value=Qt.KeyboardModifier.ControlModifier))
    item.mousePressEvent(event)
    event.ignore.assert_called_once()
    mouse_mock.assert_not_called()


@patch('beeref.selection.SelectableMixin.mousePressEvent')
def test_mouse_press_event_when_leftclick(mouse_mock):
    item = MultiSelectItem()
    item.fit_selection_area(QtCore.QRectF(0, 0, 100, 80))
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton))
    item.mousePressEvent(event)
    event.ignore.assert_not_called()
    mouse_mock.assert_called_once_with(event)
