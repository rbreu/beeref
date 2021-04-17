import math
from unittest.mock import patch, MagicMock, PropertyMock

from pytest import approx

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref import commands
from beeref.items import BeePixmapItem
from beeref.scene import BeeGraphicsScene
from .base import BeeTestCase


class BeeGraphicsSceneTestCase(BeeTestCase):

    def setUp(self):
        self.undo_stack = QtGui.QUndoStack()
        self.scene = BeeGraphicsScene(self.undo_stack)
        self.view = MagicMock(get_scale=MagicMock(return_value=1))
        views_patcher = patch('beeref.scene.BeeGraphicsScene.views',
                              return_value=[self.view])
        views_patcher.start()
        self.addCleanup(views_patcher.stop)

    def test_normalize_height(self):
        item1 = MagicMock(width=200, height=100, scale_factor=1)
        item2 = MagicMock(width=300, height=200, scale_factor=3)

        with patch.object(self.scene, 'selectedItems',
                          return_value=[item1, item2]):
            self.scene.normalize_height()

        item1.setScale.assert_called_once_with(1.5, QtCore.QPointF(100, 50))
        item2.setScale.assert_called_once_with(0.75, QtCore.QPointF(150, 100))

    def test_normalize_height_when_no_items(self):
        self.scene.normalize_height()

    def test_normalize_width(self):
        item1 = MagicMock(width=100, height=200, scale_factor=1)
        item2 = MagicMock(width=200, height=300, scale_factor=3)

        with patch.object(self.scene, 'selectedItems',
                          return_value=[item1, item2]):
            self.scene.normalize_width()

        item1.setScale.assert_called_once_with(1.5, QtCore.QPointF(50, 100))
        item2.setScale.assert_called_once_with(0.75, QtCore.QPointF(100, 150))

    def test_normalize_width_when_no_items(self):
        self.scene.normalize_width()

    def test_normalize_size(self):
        item1 = MagicMock(width=100, height=200, scale_factor=1)
        item2 = MagicMock(width=400, height=100, scale_factor=3)

        with patch.object(self.scene, 'selectedItems',
                          return_value=[item1, item2]):
            self.scene.normalize_size()

        item1.setScale.assert_called_once_with(
            math.sqrt(1.5), QtCore.QPointF(50, 100))
        item2.setScale.assert_called_once_with(
            math.sqrt(0.75), QtCore.QPointF(200, 50))

    def test_normalize_size_when_no_items(self):
        self.scene.normalize_size()

    def test_flip_items(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.setSelected(True)
        self.scene.undo_stack = MagicMock(push=MagicMock())
        with patch('beeref.scene.BeeGraphicsScene.itemsBoundingRect',
                   return_value=QtCore.QRectF(10, 20, 100, 60)):
            self.scene.flip_items(vertical=True)
            args = self.scene.undo_stack.push.call_args_list[0][0]
            cmd = args[0]
            assert isinstance(cmd, commands.FlipItems)
            assert cmd.items == [item]
            assert cmd.anchor == QtCore.QPointF(60, 50)
            assert cmd.vertical is True

    def test_set_selection_all_items_when_true(self):
        item1 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item1)
        item1.setSelected(True)
        item2 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item2)
        item2.setSelected(True)

        self.scene.set_selected_all_items(True)
        assert item1.isSelected() is True
        assert item2.isSelected() is True

    def test_set_selection_all_items_when_false(self):
        item1 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item1)
        item1.setSelected(True)
        item2 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item2)
        item2.setSelected(True)

        self.scene.set_selected_all_items(False)
        assert item1.isSelected() is False
        assert item2.isSelected() is False

    def test_has_selection_when_no_selection(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        assert self.scene.has_selection() is False

    def test_has_selection_when_selection(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.setSelected(True)
        assert self.scene.has_selection() is True

    def test_has_single_selection_when_no_selection(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        assert self.scene.has_single_selection() is False

    def test_has_single_selection_when_single_selection(self):
        item1 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item1)
        item1.setSelected(True)
        item2 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item2)
        assert self.scene.has_single_selection() is True

    def test_has_single_selection_when_multi_selection(self):
        item1 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item1)
        item1.setSelected(True)
        item2 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item2)
        item2.setSelected(True)
        assert self.scene.has_single_selection() is False

    def test_has_multi_selection_when_no_selection(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        assert self.scene.has_multi_selection() is False

    def test_has_multi_selection_when_single_selection(self):
        item1 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item1)
        item1.setSelected(True)
        item2 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item2)
        assert self.scene.has_multi_selection() is False

    def test_has_multi_selection_when_multi_selection(self):
        item1 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item1)
        item1.setSelected(True)
        item2 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item2)
        item2.setSelected(True)
        assert self.scene.has_multi_selection() is True

    @patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
    def test_mouse_press_event_when_right_click(self, mouse_mock):
        event = MagicMock(
            button=MagicMock(return_value=Qt.MouseButtons.RightButton))
        self.scene.mousePressEvent(event)
        event.accept.assert_not_called()
        mouse_mock.assert_not_called()

    @patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
    def test_mouse_press_event_when_left_click_over_item(self, mouse_mock):
        self.scene.itemAt = MagicMock(
            return_value=BeePixmapItem(QtGui.QImage()))
        event = MagicMock(
            button=MagicMock(return_value=Qt.MouseButtons.LeftButton),
            scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)),
        )
        self.scene.mousePressEvent(event)
        event.accept.assert_not_called()
        mouse_mock.assert_called_once_with(event)
        assert self.scene.move_active is True
        assert self.scene.rubberband_active is False
        assert self.scene.event_start == QtCore.QPointF(10, 20)

    @patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
    def test_mouse_press_event_when_left_click_not_over_item(self, mouse_mock):
        self.scene.itemAt = MagicMock(return_value=None)
        event = MagicMock(
            button=MagicMock(return_value=Qt.MouseButtons.LeftButton),
            scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)),
        )
        self.scene.mousePressEvent(event)
        event.accept.assert_not_called()
        mouse_mock.assert_called_once_with(event)
        assert self.scene.move_active is False
        assert self.scene.rubberband_active is True
        assert self.scene.event_start == QtCore.QPointF(10, 20)

    @patch('PyQt6.QtWidgets.QGraphicsScene.mouseDoubleClickEvent')
    def test_mouse_doubleclick_event_when_over_item(self, mouse_mock):
        event = MagicMock()
        self.scene.move_active = True
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.setPos(30, 40)
        item.setSelected(True)
        self.scene.itemAt = MagicMock(return_value=item)

        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=100):
                self.scene.mouseDoubleClickEvent(event)

        assert self.scene.move_active is False
        self.view.fit_rect.assert_called_once_with(
            QtCore.QRectF(30, 40, 100, 100), toggle_item=item)
        mouse_mock.assert_not_called()

    @patch('PyQt6.QtWidgets.QGraphicsScene.mouseDoubleClickEvent')
    def test_mouse_doubleclick_event_when_item_not_selected(
            self, mouse_mock):
        event = MagicMock()
        self.scene.move_active = True
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.setPos(30, 40)
        item.setSelected(False)
        self.scene.itemAt = MagicMock(return_value=item)

        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=100):
                self.scene.mouseDoubleClickEvent(event)

        assert self.scene.move_active is False
        self.view.fit_rect.assert_called_once_with(
            QtCore.QRectF(30, 40, 100, 100), toggle_item=item)
        mouse_mock.assert_not_called()
        assert item.isSelected() is True

    @patch('PyQt6.QtWidgets.QGraphicsScene.mouseDoubleClickEvent')
    def test_mouse_doubleclick_event_when_not_over_item(self, mouse_mock):
        event = MagicMock()
        self.scene.itemAt = MagicMock(return_value=None)
        self.scene.mouseDoubleClickEvent(event)
        self.view.fit_rect.assert_not_called()
        mouse_mock.assert_called_once_with(event)

    @patch('PyQt6.QtWidgets.QGraphicsScene.mouseMoveEvent')
    def test_mouse_move_event_when_rubberband_new(self, mouse_mock):
        item = BeePixmapItem(QtGui.QImage(self.imgfilename3x3))
        self.scene.addItem(item)
        self.scene.rubberband_active = True
        self.scene.addItem = MagicMock()
        self.scene.event_start = QtCore.QPointF(0, 0)
        self.scene.rubberband_item.bring_to_front = MagicMock()
        assert self.scene.rubberband_item.scene() is None
        event = MagicMock(
            scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)),
        )

        self.scene.mouseMoveEvent(event)

        self.scene.addItem.assert_called_once_with(self.scene.rubberband_item)
        self.scene.rubberband_item.bring_to_front.assert_called_once()
        self.scene.rubberband_item.rect().topLeft().x() == 0
        self.scene.rubberband_item.rect().topLeft().y() == 0
        self.scene.rubberband_item.rect().bottomRight().x() == 10
        self.scene.rubberband_item.rect().bottomRight().y() == 20
        assert item.isSelected() is True
        assert mouse_mock.called_once_with(event)

    @patch('PyQt6.QtWidgets.QGraphicsScene.mouseMoveEvent')
    def test_mouse_move_event_when_rubberband_not_new(self, mouse_mock):
        item = BeePixmapItem(QtGui.QImage(self.imgfilename3x3))
        self.scene.addItem(item)
        self.scene.rubberband_active = True
        self.scene.event_start = QtCore.QPointF(0, 0)
        self.scene.rubberband_item.bring_to_front = MagicMock()
        self.scene.addItem(self.scene.rubberband_item)
        self.scene.addItem = MagicMock()
        event = MagicMock(
            scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)),
        )

        self.scene.mouseMoveEvent(event)

        self.scene.addItem.assert_not_called()
        self.scene.rubberband_item.bring_to_front.assert_not_called()
        self.scene.rubberband_item.rect().topLeft().x() == 0
        self.scene.rubberband_item.rect().topLeft().y() == 0
        self.scene.rubberband_item.rect().bottomRight().x() == 10
        self.scene.rubberband_item.rect().bottomRight().y() == 20
        assert item.isSelected() is True
        assert mouse_mock.called_once_with(event)

    @patch('PyQt6.QtWidgets.QGraphicsScene.mouseMoveEvent')
    def test_mouse_move_event_when_no_rubberband(self, mouse_mock):
        item = BeePixmapItem(QtGui.QImage(self.imgfilename3x3))
        self.scene.addItem(item)
        self.scene.rubberband_active = False
        self.scene.event_start = QtCore.QPointF(0, 0)
        self.scene.rubberband_item.bring_to_front = MagicMock()
        self.scene.addItem = MagicMock()
        event = MagicMock(
            scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)),
        )

        self.scene.mouseMoveEvent(event)

        self.scene.addItem.assert_not_called()
        self.scene.rubberband_item.bring_to_front.assert_not_called()
        self.scene.rubberband_item.rect().topLeft().x() == 0
        self.scene.rubberband_item.rect().topLeft().y() == 0
        self.scene.rubberband_item.rect().bottomRight().x() == 0
        self.scene.rubberband_item.rect().bottomRight().y() == 0
        assert item.isSelected() is False
        assert mouse_mock.called_once_with(event)

    @patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
    def test_mouse_release_event_when_rubberband_active(self, mouse_mock):
        event = MagicMock()
        self.scene.rubberband_active = True
        self.scene.addItem(self.scene.rubberband_item)
        self.scene.removeItem = MagicMock()

        self.scene.mouseReleaseEvent(event)
        self.scene.removeItem.assert_called_once_with(
            self.scene.rubberband_item)
        self.scene.rubberband_active is False

    @patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
    def test_mouse_release_event_when_move_active(self, mouse_mock):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.setSelected(True)
        event = MagicMock(
            scenePos=MagicMock(return_value=QtCore.QPoint(10, 20)))
        self.scene.move_active = True
        self.scene.event_start = QtCore.QPoint(0, 0)
        self.scene.undo_stack = MagicMock(push=MagicMock())

        self.scene.mouseReleaseEvent(event)
        self.scene.undo_stack.push.assert_called_once()
        args = self.scene.undo_stack.push.call_args_list[0][0]
        cmd = args[0]
        assert isinstance(cmd, commands.MoveItemsBy)
        assert cmd.items == [item]
        assert cmd.ignore_first_redo is True
        assert cmd.delta.x() == 10
        assert cmd.delta.y() == 20
        mouse_mock.assert_called_once_with(event)
        assert self.scene.move_active is False

    @patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
    def test_mouse_release_event_when_move_not_active(self, mouse_mock):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.setSelected(True)
        event = MagicMock(
            scenePos=MagicMock(return_value=QtCore.QPoint(10, 20)))
        self.scene.move_active = False
        self.scene.undo_stack = MagicMock(push=MagicMock())

        self.scene.mouseReleaseEvent(event)
        self.scene.undo_stack.push.assert_not_called()
        mouse_mock.assert_called_once_with(event)
        assert self.scene.move_active is False

    @patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
    def test_mouse_release_event_when_no_selection(self, mouse_mock):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.setSelected(False)
        event = MagicMock(
            scenePos=MagicMock(return_value=QtCore.QPoint(10, 20)))
        self.scene.move_active = True
        self.scene.undo_stack = MagicMock(push=MagicMock())

        self.scene.mouseReleaseEvent(event)
        self.scene.undo_stack.push.assert_not_called()
        mouse_mock.assert_called_once_with(event)
        assert self.scene.move_active is False

    def test_items_for_save(self):
        item1 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item1)
        item2 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item2)
        item3 = QtWidgets.QGraphicsRectItem()
        self.scene.addItem(item3)

        items = list(self.scene.items_for_save())
        assert items == [item1, item2]

    def test_clear_save_ids(self):
        item1 = BeePixmapItem(QtGui.QImage())
        item1.save_id = 5
        self.scene.addItem(item1)
        item2 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item2)
        item3 = QtWidgets.QGraphicsRectItem()
        self.scene.addItem(item3)

        self.scene.clear_save_ids()
        assert item1.save_id is None
        assert item2.save_id is None
        assert hasattr(item3, 'save_id') is False

    def test_on_view_scale_change(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.setSelected(True)
        item.on_view_scale_change = MagicMock()
        self.scene.on_view_scale_change()
        item.on_view_scale_change.assert_called_once()

    def test_items_bounding_rect_two_items_selection_only(self):
        item1 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item1)
        item1.setSelected(True)
        item1.setPos(4, -6)
        item2 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item2)
        item2.setSelected(True)
        item2.setPos(-33, 22)
        item3 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item3)
        item3.setSelected(False)
        item3.setPos(1000, 1000)

        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=100):
                rect = self.scene.itemsBoundingRect(selection_only=True)

        assert rect.topLeft().x() == -33
        assert rect.topLeft().y() == -6
        assert rect.bottomRight().x() == 104
        assert rect.bottomRight().y() == 122

    def test_items_bounding_rect_rotated_item(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.setRotation(-45)

        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=100):
                rect = self.scene.itemsBoundingRect()

        assert rect.topLeft().x() == 0
        assert rect.topLeft().y() == approx(-math.sqrt(2) * 50)
        assert rect.bottomRight().x() == approx(math.sqrt(2) * 100)
        assert rect.bottomRight().y() == approx(math.sqrt(2) * 50)

    def test_items_bounding_rect_flipped_item(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.do_flip()
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=50):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=100):
                rect = self.scene.itemsBoundingRect()

        assert rect.topLeft().x() == -50
        assert rect.topLeft().y() == 0
        assert rect.bottomRight().x() == 0
        assert rect.bottomRight().y() == 100

    def test_items_bounding_rect_when_no_items(self):
        rect = self.scene.itemsBoundingRect()
        assert rect == QtCore.QRectF(0, 0, 0, 0)

    def test_get_selection_center(self):
        with patch('beeref.scene.BeeGraphicsScene.itemsBoundingRect',
                   return_value=QtCore.QRectF(10, 20, 100, 60)):
            center = self.scene.get_selection_center()
            assert center == QtCore.QPointF(60, 50)

    def test_on_selection_change_when_multi_selection_new(self):
        self.scene.has_multi_selection = MagicMock(return_value=True)
        self.scene.multi_select_item.fit_selection_area = MagicMock()
        self.scene.multi_select_item.bring_to_front = MagicMock()
        self.scene.itemsBoundingRect = MagicMock(
            return_value=QtCore.QRectF(0, 0, 100, 80))
        self.scene.addItem = MagicMock()

        self.scene.on_selection_change()

        m_item = self.scene.multi_select_item
        m_item.fit_selection_area.assert_called_once_with(
            QtCore.QRectF(0, 0, 100, 80))
        m_item.bring_to_front.assert_called_once()
        self.scene.addItem.assert_called_once_with(m_item)

    def test_on_selection_change_when_multi_selection_existing(self):
        self.scene.addItem(self.scene.multi_select_item)
        self.scene.has_multi_selection = MagicMock(return_value=True)
        self.scene.multi_select_item.fit_selection_area = MagicMock()
        self.scene.multi_select_item.bring_to_front = MagicMock()
        self.scene.itemsBoundingRect = MagicMock(
            return_value=QtCore.QRectF(0, 0, 100, 80))
        self.scene.addItem = MagicMock()

        self.scene.on_selection_change()

        m_item = self.scene.multi_select_item
        m_item.fit_selection_area.assert_called_once_with(
            QtCore.QRectF(0, 0, 100, 80))
        m_item.bring_to_front.assert_not_called()
        self.scene.addItem.assert_not_called()

    def test_on_selection_change_when_multi_selection_ended(self):
        self.scene.addItem(self.scene.multi_select_item)
        self.scene.has_multi_selection = MagicMock(return_value=False)
        self.scene.multi_select_item.fit_selection_area = MagicMock()
        self.scene.multi_select_item.bring_to_front = MagicMock()
        self.scene.itemsBoundingRect = MagicMock(
            return_value=QtCore.QRectF(0, 0, 100, 80))
        self.scene.removeItem = MagicMock()

        self.scene.on_selection_change()

        m_item = self.scene.multi_select_item
        m_item.fit_selection_area.assert_not_called()
        self.scene.removeItem.assert_called_once_with(m_item)

    def test_on_change_when_multi_select_when_no_scale_no_rotate(self):
        self.scene.addItem(self.scene.multi_select_item)
        self.scene.multi_select_item.fit_selection_area = MagicMock()
        self.scene.multi_select_item.scale_active = False
        self.scene.multi_select_item.rotate_active = False
        self.scene.on_change(None)
        self.scene.multi_select_item.fit_selection_area.assert_called_once()

    def test_on_change_when_multi_select_when_scale_active(self):
        self.scene.addItem(self.scene.multi_select_item)
        self.scene.multi_select_item.fit_selection_area = MagicMock()
        self.scene.multi_select_item.scale_active = True
        self.scene.multi_select_item.rotate_active = False
        self.scene.on_change(None)
        self.scene.multi_select_item.fit_selection_area.assert_not_called()

    def test_on_change_when_multi_select_when_rotate_active(self):
        self.scene.addItem(self.scene.multi_select_item)
        self.scene.multi_select_item.fit_selection_area = MagicMock()
        self.scene.multi_select_item.scale_active = False
        self.scene.multi_select_item.rotate_active = True
        self.scene.on_change(None)
        self.scene.multi_select_item.fit_selection_area.assert_not_called()

    def test_on_change_when_no_multi_select(self):
        self.scene.multi_select_item.fit_selection_area = MagicMock()
        self.scene.multi_select_item.scale_active = True
        self.scene.multi_select_item.rotate_active = True
        self.scene.on_change(None)
        self.scene.multi_select_item.fit_selection_area.assert_not_called()

    def test_add_delayed_items_unselected(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setZValue(0.33)
        self.scene.add_item_later(item, selected=False)
        self.scene.add_delayed_items()
        assert self.scene.items() == [item]
        assert item.isSelected() is False
        assert self.scene.max_z == 0.33

    def test_add_delayed_items_selected(self):
        self.scene.max_z = 0.6
        item = BeePixmapItem(QtGui.QImage())
        item.setZValue(0.33)
        self.scene.add_item_later(item, selected=True)
        self.scene.add_delayed_items()
        assert self.scene.items() == [item]
        assert item.isSelected() is True
        assert item.zValue() > 0.6

    def test_add_delayed_items_when_no_items(self):
        self.scene.add_delayed_items()
        assert self.scene.items() == []
