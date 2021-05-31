import math
from unittest.mock import patch, MagicMock, PropertyMock

from pytest import approx

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref import commands
from beeref.items import BeePixmapItem


def test_add_remove_item(view, item):
    view.scene.addItem(item)
    assert view.scene.items() == [item]
    view.scene.removeItem(item)
    assert view.scene.items() == []


def test_normalize_height(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setScale(3)

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            view.scene.normalize_height()

    assert item1.scale() == 2
    assert item1.pos() == QtCore.QPointF(-50, -40)
    assert item2.scale() == 2
    assert item2.pos() == QtCore.QPointF(50, 40)


def test_normalize_height_with_rotation(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setRotation(90)

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=200):
            view.scene.normalize_height()

    assert item1.scale() == 0.75
    assert item2.scale() == 1.5


def test_normalize_height_when_no_items(view):
    view.scene.normalize_height()


def test_normalize_width(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setScale(3)

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=80):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=100):
            view.scene.normalize_width()

    assert item1.scale() == 2
    assert item1.pos() == QtCore.QPointF(-40, -50)
    assert item2.scale() == 2
    assert item2.pos() == QtCore.QPointF(40, 50)


def test_normalize_width_with_rotation(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setRotation(90)

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=200):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=100):
            view.scene.normalize_height()

    assert item1.scale() == 1.5
    assert item2.scale() == 0.75


def test_normalize_width_when_no_items(view):
    view.scene.normalize_width()


def test_normalize_size(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setScale(2)

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=100):
            view.scene.normalize_size()

    assert item1.scale() == approx(math.sqrt(2.5))
    assert item2.scale() == approx(math.sqrt(2.5))


def test_normalize_size_with_rotation(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setRotation(90)

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=200):
            view.scene.normalize_size()

    assert item1.scale() == 1
    assert item2.scale() == 1


def test_normalize_size_when_no_items(view):
    view.scene.normalize_size()


def test_arrange_horizontal(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.setPos(10, -100)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setPos(-10, 40)

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            view.scene.arrange()

    assert item2.pos() == QtCore.QPointF(-50, -30)
    assert item1.pos() == QtCore.QPointF(50, -30)


def test_arrange_vertical(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.setPos(10, -100)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setPos(-10, 40)

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            view.scene.arrange(vertical=True)

    assert item1.pos() == QtCore.QPointF(0, -70)
    assert item2.pos() == QtCore.QPointF(0, 10)


def test_arrange_when_rotated(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.setPos(10, -100)
    item1.setRotation(90)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setPos(-10, 40)
    item2.setRotation(90)

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            view.scene.arrange()

    assert item2.pos() == QtCore.QPointF(-40, -30)
    assert item1.pos() == QtCore.QPointF(40, -30)


def test_arrange_when_no_items(view):
    view.scene.arrange()


def test_arrange_optimal(view):
    for i in range(4):
        item = BeePixmapItem(QtGui.QImage())
        view.scene.addItem(item)
        item.setSelected(True)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            view.scene.arrange_optimal()

    expected_positions = {(-50, -40), (50, -40), (-50, 40), (50, 40)}
    actual_positions = {
        (i.pos().x(), i.pos().y())
        for i in view.scene.selectedItems(user_only=True)}
    assert expected_positions == actual_positions


def test_arrange_optimal_when_rotated(view):
    for i in range(4):
        item = BeePixmapItem(QtGui.QImage())
        view.scene.addItem(item)
        item.setRotation(90)
        item.setSelected(True)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            view.scene.arrange_optimal()

    expected_positions = {(-40, -50), (40, -50), (-40, 50), (40, 50)}
    actual_positions = {
        (i.pos().x(), i.pos().y())
        for i in view.scene.selectedItems(user_only=True)}
    assert expected_positions == actual_positions


def test_arrange_optimal_when_no_items(view):
    view.scene.arrange_optimal()


def test_flip_items(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    view.scene.undo_stack = MagicMock(push=MagicMock())
    with patch('beeref.scene.BeeGraphicsScene.itemsBoundingRect',
               return_value=QtCore.QRectF(10, 20, 100, 60)):
        view.scene.flip_items(vertical=True)
        args = view.scene.undo_stack.push.call_args_list[0][0]
        cmd = args[0]
        assert isinstance(cmd, commands.FlipItems)
        assert cmd.items == [item]
        assert cmd.anchor == QtCore.QPointF(60, 50)
        assert cmd.vertical is True


def test_set_selection_all_items_when_true(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)

    view.scene.set_selected_all_items(True)
    assert item1.isSelected() is True
    assert item2.isSelected() is True


def test_set_selection_all_items_when_false(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)

    view.scene.set_selected_all_items(False)
    assert item1.isSelected() is False
    assert item2.isSelected() is False


def test_has_selection_when_no_selection(view, item):
    view.scene.addItem(item)
    assert view.scene.has_selection() is False


def test_has_selection_when_selection(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    assert view.scene.has_selection() is True


def test_has_single_selection_when_no_selection(view, item):
    view.scene.addItem(item)
    assert view.scene.has_single_selection() is False


def test_has_single_selection_when_single_selection(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    assert view.scene.has_single_selection() is True


def test_has_single_selection_when_multi_selection(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    assert view.scene.has_single_selection() is False


def test_has_multi_selection_when_no_selection(view, item):
    view.scene.addItem(item)
    assert view.scene.has_multi_selection() is False


def test_has_multi_selection_when_single_selection(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    assert view.scene.has_multi_selection() is False


def test_has_multi_selection_when_multi_selection(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    assert view.scene.has_multi_selection() is True


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
def test_mouse_press_event_when_right_click(mouse_mock, view):
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.RightButton))
    view.scene.mousePressEvent(event)
    event.accept.assert_not_called()
    mouse_mock.assert_not_called()


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
def test_mouse_press_event_when_left_click_over_item(mouse_mock, view, item):
    view.scene.itemAt = MagicMock(return_value=item)
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
        scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)),
    )
    view.scene.mousePressEvent(event)
    event.accept.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    assert view.scene.move_active is True
    assert view.scene.rubberband_active is False
    assert view.scene.event_start == QtCore.QPointF(10, 20)


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
def test_mouse_press_event_when_left_click_not_over_item(
        mouse_mock, view, item):
    view.scene.addItem(item)
    view.scene.itemAt = MagicMock(return_value=None)
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
        scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)),
    )
    view.scene.mousePressEvent(event)
    event.accept.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    assert view.scene.move_active is False
    assert view.scene.rubberband_active is True
    assert view.scene.event_start == QtCore.QPointF(10, 20)


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
def test_mouse_press_event_when_no_items(mouse_mock, view):
    view.scene.itemAt = MagicMock(return_value=None)
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
        scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)),
    )
    view.scene.mousePressEvent(event)
    event.accept.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    assert view.scene.move_active is False
    assert view.scene.rubberband_active is False
    mouse_mock.assert_called_once_with(event)


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseDoubleClickEvent')
def test_mouse_doubleclick_event_when_over_item(mouse_mock, view, item):
    event = MagicMock()
    view.scene.move_active = True
    view.scene.addItem(item)
    item.setPos(30, 40)
    item.setSelected(True)
    view.scene.itemAt = MagicMock(return_value=item)
    view.fit_rect = MagicMock()

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=100):
            view.scene.mouseDoubleClickEvent(event)

    assert view.scene.move_active is False
    view.fit_rect.assert_called_once_with(
        QtCore.QRectF(30, 40, 100, 100), toggle_item=item)
    mouse_mock.assert_not_called()


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseDoubleClickEvent')
def test_mouse_doubleclick_event_when_item_not_selected(
        mouse_mock, view, item):
    event = MagicMock()
    view.scene.move_active = True
    view.scene.addItem(item)
    item.setPos(30, 40)
    item.setSelected(False)
    view.scene.itemAt = MagicMock(return_value=item)
    view.fit_rect = MagicMock()

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=100):
            view.scene.mouseDoubleClickEvent(event)

    assert view.scene.move_active is False
    view.fit_rect.assert_called_once_with(
        QtCore.QRectF(30, 40, 100, 100), toggle_item=item)
    mouse_mock.assert_not_called()
    assert item.isSelected() is True


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseDoubleClickEvent')
def test_mouse_doubleclick_event_when_not_over_item(mouse_mock, view):
    event = MagicMock()
    view.fit_rect = MagicMock()
    view.scene.itemAt = MagicMock(return_value=None)
    view.scene.mouseDoubleClickEvent(event)
    view.fit_rect.assert_not_called()
    mouse_mock.assert_called_once_with(event)


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseMoveEvent')
def test_mouse_move_event_when_rubberband_new(
        mouse_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.scene.rubberband_active = True
    view.scene.addItem = MagicMock()
    view.scene.event_start = QtCore.QPointF(0, 0)
    view.scene.rubberband_item.bring_to_front = MagicMock()
    assert view.scene.rubberband_item.scene() is None
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)))

    view.scene.mouseMoveEvent(event)

    view.scene.addItem.assert_called_once_with(view.scene.rubberband_item)
    view.scene.rubberband_item.bring_to_front.assert_called_once()
    view.scene.rubberband_item.rect().topLeft().x() == 0
    view.scene.rubberband_item.rect().topLeft().y() == 0
    view.scene.rubberband_item.rect().bottomRight().x() == 10
    view.scene.rubberband_item.rect().bottomRight().y() == 20
    assert item.isSelected() is True
    assert mouse_mock.called_once_with(event)


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseMoveEvent')
def test_mouse_move_event_when_rubberband_not_new(
        mouse_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.scene.rubberband_active = True
    view.scene.event_start = QtCore.QPointF(0, 0)
    view.scene.rubberband_item.bring_to_front = MagicMock()
    view.scene.addItem(view.scene.rubberband_item)
    view.scene.addItem = MagicMock()
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)))

    view.scene.mouseMoveEvent(event)

    view.scene.addItem.assert_not_called()
    view.scene.rubberband_item.bring_to_front.assert_not_called()
    view.scene.rubberband_item.rect().topLeft().x() == 0
    view.scene.rubberband_item.rect().topLeft().y() == 0
    view.scene.rubberband_item.rect().bottomRight().x() == 10
    view.scene.rubberband_item.rect().bottomRight().y() == 20
    assert item.isSelected() is True
    assert mouse_mock.called_once_with(event)


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseMoveEvent')
def test_mouse_move_event_when_no_rubberband(mouse_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.scene.rubberband_active = False
    view.scene.event_start = QtCore.QPointF(0, 0)
    view.scene.rubberband_item.bring_to_front = MagicMock()
    view.scene.addItem = MagicMock()
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)))

    view.scene.mouseMoveEvent(event)

    view.scene.addItem.assert_not_called()
    view.scene.rubberband_item.bring_to_front.assert_not_called()
    view.scene.rubberband_item.rect().topLeft().x() == 0
    view.scene.rubberband_item.rect().topLeft().y() == 0
    view.scene.rubberband_item.rect().bottomRight().x() == 0
    view.scene.rubberband_item.rect().bottomRight().y() == 0
    assert item.isSelected() is False
    assert mouse_mock.called_once_with(event)


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
def test_mouse_release_event_when_rubberband_active(mouse_mock, view):
    event = MagicMock()
    view.scene.rubberband_active = True
    view.scene.addItem(view.scene.rubberband_item)
    view.scene.removeItem = MagicMock()

    view.scene.mouseReleaseEvent(event)
    view.scene.removeItem.assert_called_once_with(view.scene.rubberband_item)
    view.scene.rubberband_active is False


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
def test_mouse_release_event_when_move_active(mouse_mock, view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPoint(10, 20)))
    view.scene.move_active = True
    view.scene.event_start = QtCore.QPoint(0, 0)
    view.scene.undo_stack = MagicMock(push=MagicMock())

    view.scene.mouseReleaseEvent(event)
    view.scene.undo_stack.push.assert_called_once()
    args = view.scene.undo_stack.push.call_args_list[0][0]
    cmd = args[0]
    assert isinstance(cmd, commands.MoveItemsBy)
    assert cmd.items == [item]
    assert cmd.ignore_first_redo is True
    assert cmd.delta.x() == 10
    assert cmd.delta.y() == 20
    mouse_mock.assert_called_once_with(event)
    assert view.scene.move_active is False


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
def test_mouse_release_event_when_move_not_active(mouse_mock, view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPoint(10, 20)))
    view.scene.move_active = False
    view.scene.undo_stack = MagicMock(push=MagicMock())

    view.scene.mouseReleaseEvent(event)
    view.scene.undo_stack.push.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    assert view.scene.move_active is False


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
def test_mouse_release_event_when_no_selection(mouse_mock, view, item):
    view.scene.addItem(item)
    item.setSelected(False)
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPoint(10, 20)))
    view.scene.move_active = True
    view.scene.undo_stack = MagicMock(push=MagicMock())

    view.scene.mouseReleaseEvent(event)
    view.scene.undo_stack.push.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    assert view.scene.move_active is False


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
def test_mouse_release_event_when_item_action_active(mouse_mock, view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPoint(10, 20)))
    view.scene.move_active = True
    item.scale_active = True
    view.scene.undo_stack = MagicMock(push=MagicMock())

    view.scene.mouseReleaseEvent(event)
    view.scene.undo_stack.push.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    assert view.scene.move_active is False


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
def test_mouse_release_event_when_multiselect_action_active(mouse_mock, view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPoint(10, 20)))
    view.scene.move_active = True
    view.scene.multi_select_item.scale_active = True
    view.scene.undo_stack = MagicMock(push=MagicMock())

    view.scene.mouseReleaseEvent(event)
    view.scene.undo_stack.push.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    assert view.scene.move_active is False


def test_selected_items(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    selected = view.scene.selectedItems()
    assert len(selected) == 3  # Multi select item!
    assert item1 in selected
    assert item2 in selected


def test_selected_items_user_only(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    selected = view.scene.selectedItems(user_only=True)
    assert len(selected) == 2  # No multi select item!
    assert item1 in selected
    assert item2 in selected


def test_items_for_save(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item3 = QtWidgets.QGraphicsRectItem()
    view.scene.addItem(item3)

    items = list(view.scene.items_for_save())
    assert items == [item1, item2]


def test_clear_save_ids(view):
    item1 = BeePixmapItem(QtGui.QImage())
    item1.save_id = 5
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item3 = QtWidgets.QGraphicsRectItem()
    view.scene.addItem(item3)

    view.scene.clear_save_ids()
    assert item1.save_id is None
    assert item2.save_id is None
    assert hasattr(item3, 'save_id') is False


def test_on_view_scale_change(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    item.on_view_scale_change = MagicMock()
    view.scene.on_view_scale_change()
    item.on_view_scale_change.assert_called_once()


def test_items_bounding_rect_given_items(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.setPos(4, -6)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setPos(-33, 22)
    item3 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item3)
    item3.setSelected(True)
    item3.setPos(1000, 1000)

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=100):
            rect = view.scene.itemsBoundingRect(items=[item1, item2])

    assert rect.topLeft().x() == -33
    assert rect.topLeft().y() == -6
    assert rect.bottomRight().x() == 104
    assert rect.bottomRight().y() == 122


def test_items_bounding_rect_two_items_selection_only(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.setPos(4, -6)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setPos(-33, 22)
    item3 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item3)
    item3.setSelected(False)
    item3.setPos(1000, 1000)

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=100):
            rect = view.scene.itemsBoundingRect(selection_only=True)

    assert rect.topLeft().x() == -33
    assert rect.topLeft().y() == -6
    assert rect.bottomRight().x() == 104
    assert rect.bottomRight().y() == 122


def test_items_bounding_rect_rotated_item(view, item):
    view.scene.addItem(item)
    item.setRotation(-45)

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=100):
            rect = view.scene.itemsBoundingRect()

    assert rect.topLeft().x() == 0
    assert rect.topLeft().y() == approx(-math.sqrt(2) * 50)
    assert rect.bottomRight().x() == approx(math.sqrt(2) * 100)
    assert rect.bottomRight().y() == approx(math.sqrt(2) * 50)


def test_items_bounding_rect_flipped_item(view):
    item = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item)
    item.do_flip()
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=50):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=100):
            rect = view.scene.itemsBoundingRect()

    assert rect.topLeft().x() == -50
    assert rect.topLeft().y() == 0
    assert rect.bottomRight().x() == 0
    assert rect.bottomRight().y() == 100


def test_items_bounding_rect_when_no_items(view):
    rect = view.scene.itemsBoundingRect()
    assert rect == QtCore.QRectF(0, 0, 0, 0)


def test_get_selection_center(view):
    with patch('beeref.scene.BeeGraphicsScene.itemsBoundingRect',
               return_value=QtCore.QRectF(10, 20, 100, 60)):
        center = view.scene.get_selection_center()
        assert center == QtCore.QPointF(60, 50)


def test_on_selection_change_when_multi_selection_new(view):
    view.scene.has_multi_selection = MagicMock(return_value=True)
    view.scene.multi_select_item.fit_selection_area = MagicMock()
    view.scene.multi_select_item.bring_to_front = MagicMock()
    view.scene.itemsBoundingRect = MagicMock(
        return_value=QtCore.QRectF(0, 0, 100, 80))
    view.scene.addItem = MagicMock()

    view.scene.on_selection_change()

    m_item = view.scene.multi_select_item
    m_item.fit_selection_area.assert_called_once_with(
        QtCore.QRectF(0, 0, 100, 80))
    m_item.bring_to_front.assert_called_once()
    view.scene.addItem.assert_called_once_with(m_item)


def test_on_selection_change_when_multi_selection_existing(view):
    view.scene.addItem(view.scene.multi_select_item)
    view.scene.has_multi_selection = MagicMock(return_value=True)
    view.scene.multi_select_item.fit_selection_area = MagicMock()
    view.scene.multi_select_item.bring_to_front = MagicMock()
    view.scene.itemsBoundingRect = MagicMock(
        return_value=QtCore.QRectF(0, 0, 100, 80))
    view.scene.addItem = MagicMock()

    view.scene.on_selection_change()

    m_item = view.scene.multi_select_item
    m_item.fit_selection_area.assert_called_once_with(
        QtCore.QRectF(0, 0, 100, 80))
    m_item.bring_to_front.assert_not_called()
    view.scene.addItem.assert_not_called()


def test_on_selection_change_when_multi_selection_ended(view):
    view.scene.addItem(view.scene.multi_select_item)
    view.scene.has_multi_selection = MagicMock(return_value=False)
    view.scene.multi_select_item.fit_selection_area = MagicMock()
    view.scene.multi_select_item.bring_to_front = MagicMock()
    view.scene.itemsBoundingRect = MagicMock(
        return_value=QtCore.QRectF(0, 0, 100, 80))
    view.scene.removeItem = MagicMock()

    view.scene.on_selection_change()

    m_item = view.scene.multi_select_item
    m_item.fit_selection_area.assert_not_called()
    view.scene.removeItem.assert_called_once_with(m_item)


def test_on_change_when_multi_select_when_no_scale_no_rotate(view):
    view.scene.addItem(view.scene.multi_select_item)
    view.scene.multi_select_item.fit_selection_area = MagicMock()
    view.scene.multi_select_item.scale_active = False
    view.scene.multi_select_item.rotate_active = False
    view.scene.on_change(None)
    view.scene.multi_select_item.fit_selection_area.assert_called_once()


def test_on_change_when_multi_select_when_scale_active(view):
    view.scene.addItem(view.scene.multi_select_item)
    view.scene.multi_select_item.fit_selection_area = MagicMock()
    view.scene.multi_select_item.scale_active = True
    view.scene.multi_select_item.rotate_active = False
    view.scene.on_change(None)
    view.scene.multi_select_item.fit_selection_area.assert_not_called()


def test_on_change_when_multi_select_when_rotate_active(view):
    view.scene.addItem(view.scene.multi_select_item)
    view.scene.multi_select_item.fit_selection_area = MagicMock()
    view.scene.multi_select_item.scale_active = False
    view.scene.multi_select_item.rotate_active = True
    view.scene.on_change(None)
    view.scene.multi_select_item.fit_selection_area.assert_not_called()


def test_on_change_when_no_multi_select(view):
    view.scene.multi_select_item.fit_selection_area = MagicMock()
    view.scene.multi_select_item.scale_active = True
    view.scene.multi_select_item.rotate_active = True
    view.scene.on_change(None)
    view.scene.multi_select_item.fit_selection_area.assert_not_called()


def test_add_queued_items_unselected(view, item):
    item.setZValue(0.33)
    view.scene.add_item_later(item, selected=False)
    view.scene.add_queued_items()
    assert view.scene.items() == [item]
    assert item.isSelected() is False
    assert view.scene.max_z == 0.33


def test_add_queued_items_selected(view, item):
    view.scene.max_z = 0.6
    item.setZValue(0.33)
    view.scene.add_item_later(item, selected=True)
    view.scene.add_queued_items()
    assert view.scene.items() == [item]
    assert item.isSelected() is True
    assert item.zValue() > 0.6


def test_add_queued_items_when_no_items(view):
    view.scene.add_queued_items()
    assert view.scene.items() == []


def test_copy_selection_to_internal_clipboard(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item3 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item3)

    view.scene.copy_selection_to_internal_clipboard()
    assert set(view.scene.internal_clipboard) == {item1, item2}
    assert set(view.scene.items_for_save()) == {item1, item2, item3}


def test_paste_from_internal_clipboard(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    item2.setScale(3.3)
    view.scene.internal_clipboard = [item2]

    view.scene.paste_from_internal_clipboard(None)
    assert len(list(view.scene.items_for_save())) == 2
    assert item1.isSelected() is False
    new_item = view.scene.selectedItems(user_only=True)[0]
    assert new_item.scale() == 3.3
    assert new_item is not item2
