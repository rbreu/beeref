import math
from unittest.mock import patch, MagicMock, PropertyMock

from pytest import approx

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref.items import BeePixmapItem
from beeref.scene import BeeGraphicsScene
from .base import BeeTestCase


class BeeGraphicsSceneNormalizeTestCase(BeeTestCase):

    def setUp(self):
        self.undo_stack = QtGui.QUndoStack()
        self.scene = BeeGraphicsScene(self.undo_stack)
        self.view = MagicMock(get_scale=MagicMock(return_value=1))
        views_patcher = patch('beeref.scene.BeeGraphicsScene.views',
                              return_value=[self.view])
        views_patcher.start()

    def test_normalize_height(self):
        item1 = MagicMock(height=100, scale_factor=1)
        item2 = MagicMock(height=200, scale_factor=3)

        with patch.object(self.scene, 'selectedItems',
                          return_value=[item1, item2]):
            self.scene.normalize_height()

        item1.setScale.assert_called_once_with(1.5)
        item2.setScale.assert_called_once_with(0.75)

    def test_normalize_height_when_no_items(self):
        self.scene.normalize_height()

    def test_normalize_width(self):
        item1 = MagicMock(width=100, scale_factor=1)
        item2 = MagicMock(width=200, scale_factor=3)

        with patch.object(self.scene, 'selectedItems',
                          return_value=[item1, item2]):
            self.scene.normalize_width()

        item1.setScale.assert_called_once_with(1.5)
        item2.setScale.assert_called_once_with(0.75)

    def test_normalize_width_when_no_items(self):
        self.scene.normalize_width()

    def test_normalize_size(self):
        item1 = MagicMock(width=100, height=200, scale_factor=1)
        item2 = MagicMock(width=400, height=100, scale_factor=3)

        with patch.object(self.scene, 'selectedItems',
                          return_value=[item1, item2]):
            self.scene.normalize_size()

        item1.setScale.assert_called_once_with(math.sqrt(1.5))
        item2.setScale.assert_called_once_with(math.sqrt(0.75))

    def test_normalize_size_when_no_items(self):
        self.scene.normalize_size()

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

    @patch('PyQt6.QtWidgets.QGraphicsScene.mouseMoveEvent')
    def test_mouse_move_event_when_rubberband_new(self, mouse_mock):
        item = BeePixmapItem(QtGui.QImage(self.imgfilename3x3))
        self.scene.addItem(item)
        self.scene.rubberband_active = True
        self.scene.addItem = MagicMock()
        self.scene.event_start = QtCore.QPointF(0, 0)
        self.scene.rubberband_item.bring_to_front = MagicMock()
        self.scene.removeItem(self.scene.rubberband_item)
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

    def test_get_selection_rect_two_items(self):
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
                rect = self.scene.get_selection_rect()

        assert rect.topLeft().x() == -33
        assert rect.topLeft().y() == -6
        assert rect.bottomRight().x() == 104
        assert rect.bottomRight().y() == 122

    def test_get_selection_rect_rotated_item(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.setSelected(True)
        item.setRotation(-45)

        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=100):
                rect = self.scene.get_selection_rect()

        assert rect.topLeft().x() == 0
        assert rect.topLeft().y() == approx(-math.sqrt(2) * 50)
        assert rect.bottomRight().x() == approx(math.sqrt(2) * 100)
        assert rect.bottomRight().y() == approx(math.sqrt(2) * 50)

    def test_on_selection_change_when_multi_selection_new(self):
        self.scene.has_multi_selection = MagicMock(return_value=True)
        self.scene.multi_select_item.fit_selection_area = MagicMock()
        self.scene.multi_select_item.bring_to_front = MagicMock()
        self.scene.get_selection_rect = MagicMock(
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
        self.scene.get_selection_rect = MagicMock(
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
        self.scene.get_selection_rect = MagicMock(
            return_value=QtCore.QRectF(0, 0, 100, 80))
        self.scene.removeItem = MagicMock()

        self.scene.on_selection_change()

        m_item = self.scene.multi_select_item
        m_item.fit_selection_area.assert_not_called()
        self.scene.removeItem.assert_called_once_with(m_item)
