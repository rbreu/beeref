from unittest.mock import patch, MagicMock, PropertyMock

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref.items import BeePixmapItem
from beeref.scene import BeeGraphicsScene
from .base import BeeTestCase


class BeePixmapItemTestCase(BeeTestCase):

    def setUp(self):
        self.scene = BeeGraphicsScene(None)

    def test_init(self):
        item = BeePixmapItem(
            QtGui.QImage(self.imgfilename3x3), self.imgfilename3x3)
        assert item.save_id is None
        assert item.width == 3
        assert item.height == 3
        assert item.scale() == 1
        assert item.flags() == (
            QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsMovable
            | QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsSelectable)
        assert item.filename == self.imgfilename3x3

    def test_set_scale(self):
        item = BeePixmapItem(
            QtGui.QImage(self.imgfilename3x3), self.imgfilename3x3)
        item.prepareGeometryChange = MagicMock()
        item.setScale(3)
        assert item.scale() == 3
        assert item.pos().x() == 0
        assert item.pos().y() == 0
        item.prepareGeometryChange.assert_called_once()

    def test_set_scale_ignores_zero(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setScale(0)
        assert item.scale() == 1

    def test_set_scale_ignores_negative(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setScale(-0.1)
        assert item.scale() == 1

    def test_set_pos_center(self):
        item = BeePixmapItem(QtGui.QImage())
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=200):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=100):
                item.set_pos_center(0, 0)
                assert item.pos().x() == -100
                assert item.pos().y() == -50

    def test_set_zvalue_sets_new_max(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.setZValue(1.1)
        assert item.zValue() == 1.1
        assert self.scene.max_z == 1.1

    def test_set_zvalue_keeps_old_max(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        self.scene.max_z = 3.3
        item.setZValue(1.1)
        assert item.zValue() == 1.1
        assert self.scene.max_z == 3.3

    def test_bring_to_front(self):
        item1 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item1)
        item1.setZValue(3.3)
        item2 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item2)
        item2.bring_to_front()
        assert item2.zValue() > item1.zValue()
        assert item2.zValue() == self.scene.max_z

    def test_on_view_scale_change(self):
        item = BeePixmapItem(QtGui.QImage())
        with patch('beeref.items.BeePixmapItem.prepareGeometryChange') as m:
            item.on_view_scale_change()
            m.assert_called_once()


class BeePixmapItemWithViewBaseTestCase(BeeTestCase):

    def setUp(self):
        self.scene = BeeGraphicsScene(None)
        self.item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(self.item)
        self.view = MagicMock(get_scale=MagicMock(return_value=1))
        views_patcher = patch('beeref.scene.BeeGraphicsScene.views',
                              return_value=[self.view])
        views_patcher.start()
        self.addCleanup(views_patcher.stop)
        width_patcher = patch('beeref.items.BeePixmapItem.width',
                              new_callable=PropertyMock,
                              return_value=100)
        width_patcher.start()
        self.addCleanup(width_patcher.stop)
        height_patcher = patch('beeref.items.BeePixmapItem.height',
                               new_callable=PropertyMock,
                               return_value=80)
        height_patcher.start()
        self.addCleanup(height_patcher.stop)


class BeePixmapItemPaintstuffTestCase(BeePixmapItemWithViewBaseTestCase):

    def test_fixed_length_for_viewport_when_default_scales(self):
        self.view.get_scale = MagicMock(return_value=1)
        assert self.item.fixed_length_for_viewport(100) == 100
        assert self.item._view_scale == 1

    def test_fixed_length_for_viewport_when_viewport_scaled(self):
        self.view.get_scale = MagicMock(return_value=2)
        assert self.item.fixed_length_for_viewport(100) == 50
        assert self.item._view_scale == 2

    def test_fixed_length_for_viewport_when_item_scaled(self):
        self.view.get_scale = MagicMock(return_value=1)
        self.item.setScale(5)
        assert self.item.fixed_length_for_viewport(100) == 20
        assert self.item._view_scale == 1

    def test_fixed_length_for_viewport_when_no_scene(self):
        item = BeePixmapItem(QtGui.QImage())
        item._view_scale = 0.5
        assert item.fixed_length_for_viewport(100) == 200

    def test_resize_size_when_scaled(self):
        self.view.get_scale = MagicMock(return_value=2)
        self.item.setScale(2)
        self.item.SELECT_RESIZE_SIZE = 100
        assert self.item.select_resize_size == 25

    def test_rotate_size_when_scaled(self):
        self.view.get_scale = MagicMock(return_value=2)
        self.item.setScale(2)
        self.item.SELECT_ROTATE_SIZE = 100
        assert self.item.select_rotate_size == 25

    @patch('beeref.items.BeePixmapItem.draw_debug_shape')
    def test_paint_when_not_selected(self, debug_mock):
        painter = MagicMock()
        self.item.setSelected(False)
        self.item.pixmap = MagicMock(return_value='pixmap')
        self.item.paint(painter, None, None)
        painter.drawPixmap.assert_called_once_with(0, 0, 'pixmap')
        painter.drawRect.assert_not_called()
        painter.drawPoint.assert_not_called()
        debug_mock.assert_not_called()

    def test_paint_when_selected_single_selection(self):
        painter = MagicMock()
        self.item.setSelected(True)
        self.item.paint(painter, None, None)
        painter.drawPixmap.assert_called_once()
        painter.drawRect.assert_called_once()
        assert painter.drawPoint.call_count == 4

    def test_paint_when_selected_multi_selection(self):
        item2 = BeePixmapItem(QtGui.QImage())
        item2.setSelected(True)
        self.scene.addItem(item2)
        painter = MagicMock()
        self.item.setSelected(True)
        self.item.paint(painter, None, None)
        painter.drawPixmap.assert_called_once()
        painter.drawRect.assert_called_once()
        painter.drawPoint.assert_not_called()

    def test_paint_when_draw_debug_shapes(self):
        with patch('beeref.items.commandline_args') as args_mock:
            with patch('beeref.items.BeePixmapItem.draw_debug_shape') as m:
                args_mock.draw_debug_shapes = True
                item = BeePixmapItem(QtGui.QImage())
                item.paint(MagicMock(), None, None)
                m.assert_called()

    def test_corners(self):
        assert set(self.item.corners) == set((
            (0, 0),
            (100, 0),
            (0, 80),
            (100, 80)))

    def test_get_scale_bounds(self):
        self.view.get_scale = MagicMock(return_value=1)
        self.item.SELECT_RESIZE_SIZE = 10
        rect = self.item.get_scale_bounds((100, 100))
        assert rect.topLeft().x() == 95
        assert rect.topLeft().y() == 95
        assert rect.bottomRight().x() == 105
        assert rect.bottomRight().y() == 105

    def test_bottom_right_rotate_bounds(self):
        self.view.get_scale = MagicMock(return_value=1)
        self.item.SELECT_RESIZE_SIZE = 10
        self.item.SELECT_ROTATE_SIZE = 10
        rect = self.item.bottom_right_rotate_bounds
        assert rect.topLeft().x() == 105
        assert rect.topLeft().y() == 85
        assert rect.bottomRight().x() == 115
        assert rect.bottomRight().y() == 95

    def test_bounding_rect_when_not_selected(self):
        self.view.get_scale = MagicMock(return_value=1)
        self.item.setSelected(False)
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.boundingRect',
                   return_value=QtCore.QRectF(0, 0, 100, 80)):
            rect = self.item.boundingRect()
            assert rect.topLeft().x() == 0
            assert rect.topLeft().y() == 0
            assert rect.bottomRight().x() == 100
            assert rect.bottomRight().y() == 80

    def test_bounding_rect_when_selected(self):
        self.item.SELECT_RESIZE_SIZE = 10
        self.item.SELECT_ROTATE_SIZE = 10
        self.view.get_scale = MagicMock(return_value=1)
        self.item.setSelected(True)
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.boundingRect',
                   return_value=QtCore.QRectF(0, 0, 100, 80)):
            rect = self.item.boundingRect()
            assert rect.topLeft().x() == -15
            assert rect.topLeft().y() == -15
            assert rect.bottomRight().x() == 115
            assert rect.bottomRight().y() == 95

    def test_shape_when_not_selected(self):
        self.view.get_scale = MagicMock(return_value=1)
        self.item.setSelected(False)
        path = QtGui.QPainterPath()
        path.addRect(QtCore.QRectF(0, 0, 100, 80))

        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.shape',
                   return_value=path):
            shape = self.item.shape().boundingRect()
            assert shape.topLeft().x() == 0
            assert shape.topLeft().y() == 0
            assert shape.bottomRight().x() == 100
            assert shape.bottomRight().y() == 80

    def test_shape_when_selected(self):
        self.item.SELECT_RESIZE_SIZE = 10
        self.item.SELECT_ROTATE_SIZE = 10
        self.view.get_scale = MagicMock(return_value=1)
        self.item.setSelected(True)
        path = QtGui.QPainterPath()
        path.addRect(QtCore.QRectF(0, 0, 100, 80))

        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.shape',
                   return_value=path):
            shape = self.item.shape().boundingRect()
            assert shape.topLeft().x() == -5
            assert shape.topLeft().y() == -5
            assert shape.bottomRight().x() == 115
            assert shape.bottomRight().y() == 95


class BeePixmapItemScalingTestCase(BeePixmapItemWithViewBaseTestCase):

    def test_get_scale_delta_bottomright(self):
        self.item.scale_start = QtCore.QPoint(10, 10)
        event = MagicMock()
        event.scenePos = MagicMock(return_value=QtCore.QPoint(20, 90))
        assert self.item.get_scale_delta(event, (100, 80)) == 0.5

    def test_get_scale_delta_topleft(self):
        self.item.scale_start = QtCore.QPoint(10, 10)
        event = MagicMock()
        event.scenePos = MagicMock(return_value=QtCore.QPoint(-10, -60))
        assert self.item.get_scale_delta(event, (0, 0)) == 0.5

    def test_get_scale_anchor_topleft(self):
        assert self.item.get_scale_anchor((0, 0)) == (100, 80)

    def test_get_scale_anchor_bottomright(self):
        assert self.item.get_scale_anchor((100, 80)) == (0, 0)

    def test_get_scale_anchor_topright(self):
        assert self.item.get_scale_anchor((100, 0)) == (0, 80)

    def test_get_scale_anchor_bottomleft(self):
        assert self.item.get_scale_anchor((0, 80)) == (100, 0)

    def test_get_scale_direction_topleft(self):
        assert self.item.get_scale_direction((0, 0)) == (-1, -1)

    def test_get_scale_direction_bottomright(self):
        assert self.item.get_scale_direction((100, 80)) == (1, 1)

    def test_get_scale_direction_topright(self):
        assert self.item.get_scale_direction((100, 0)) == (1, -1)

    def test_get_scale_direction_bottomleft(self):
        assert self.item.get_scale_direction((0, 80)) == (-1, 1)

    def test_translate_for_scale_anchor(self):
        pos = QtCore.QPoint(50, 70)
        self.item.translate_for_scale_anchor(pos, 2, (100, 80))
        assert self.item.pos().x() == -150
        assert self.item.pos().y() == -90


class BeePixmapItemEventsstuffTestCase(BeePixmapItemWithViewBaseTestCase):

    def setUp(self):
        super().setUp()
        self.event = MagicMock()
        self.item.setCursor = MagicMock()

    def test_hover_move_event_no_selection(self):
        self.event.pos = MagicMock(return_value=QtCore.QPointF(0, 0))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_not_called()

    def test_hover_move_event_topleft_scale(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(0, 0))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_called_once_with(
            Qt.CursorShape.SizeFDiagCursor)

    def test_hover_move_event_bottomright_scale(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(100, 80))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_called_once_with(
            Qt.CursorShape.SizeFDiagCursor)

    def test_hover_move_event_topright_scale(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(100, 0))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_called_once_with(
            Qt.CursorShape.SizeBDiagCursor)

    def test_hover_move_event_not_in_handles(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(50, 50))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_called_once_with(
            Qt.CursorShape.ArrowCursor)

    def test_hover_enter_event_when_selected(self):
        self.item.setSelected(True)
        self.item.hoverEnterEvent(self.event)
        self.item.setCursor.assert_not_called()

    def test_hover_enter_event_when_not_selected(self):
        self.item.setSelected(False)
        self.item.hoverEnterEvent(self.event)
        self.item.setCursor.assert_called_once_with(
            Qt.CursorShape.ArrowCursor)

    def test_mouse_press_event_topleft_scale(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(2, 2))
        self.event.scenePos = MagicMock(return_value=QtCore.QPointF(66, 99))
        self.event.button = MagicMock(
            return_value=Qt.MouseButtons.LeftButton)
        self.item.mousePressEvent(self.event)
        assert self.item.scale_active_corner == (0, 0)
        assert self.item.scale_start == QtCore.QPointF(66, 99)
        assert self.item.scale_orig_factor == 1
        assert self.item.scale_orig_pos == QtCore.QPointF(0, 0)

    def test_mouse_press_event_bottomright_scale(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(99, 79))
        self.event.scenePos = MagicMock(return_value=QtCore.QPointF(66, 99))
        self.event.button = MagicMock(
            return_value=Qt.MouseButtons.LeftButton)
        self.item.mousePressEvent(self.event)
        assert self.item.scale_active_corner == (100, 80)
        assert self.item.scale_start == QtCore.QPointF(66, 99)
        assert self.item.scale_orig_factor == 1
        assert self.item.scale_orig_pos == QtCore.QPointF(0, 0)

    def test_mouse_press_event_not_selected(self):
        self.item.setSelected(False)
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mousePressEvent') as m:
            self.item.mousePressEvent(self.event)
            m.assert_called_once_with(self.event)
            assert self.item.scale_active_corner is None

    def test_mouse_press_not_in_handles(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(50, 40))
        self.event.button = MagicMock(
            return_value=Qt.MouseButtons.LeftButton)
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mousePressEvent') as m:
            self.item.mousePressEvent(self.event)
            m.assert_called_once_with(self.event)
            assert self.item.scale_active_corner is None

    def test_mouse_move_event_when_no_action(self):
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mouseMoveEvent') as m:
            self.item.mouseMoveEvent(self.event)
            m.assert_called_once_with(self.event)

    def test_move_event_when_scale_action(self):
        self.event.scenePos = MagicMock(return_value=QtCore.QPointF(20, 90))
        self.item.scale_active_corner = (100, 80)
        self.item.scale_start = QtCore.QPointF(10, 10)
        self.item.scale_orig_factor = 1
        self.item.scale_orig_pos = QtCore.QPointF(0, 0)

        self.item.mouseMoveEvent(self.event)
        assert self.item.scale() == 1.5

    def test_mouse_release_event_when_no_action(self):
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem'
                   '.mouseReleaseEvent') as m:
            self.item.mouseReleaseEvent(self.event)
            m.assert_called_once_with(self.event)

    def test_mouse_release_event_when_scale_action(self):
        self.event.scenePos = MagicMock(return_value=QtCore.QPointF(20, 90))
        self.item.scale_active_corner = (100, 80)
        self.item.scale_start = QtCore.QPointF(10, 10)
        self.item.scale_orig_factor = 1
        self.item.scale_orig_pos = QtCore.QPointF(0, 0)
        self.scene.undo_stack = MagicMock()
        self.scene.undo_stack.push = MagicMock()

        self.item.mouseReleaseEvent(self.event)
        self.scene.undo_stack.push.assert_called_once()
        args = self.scene.undo_stack.push.call_args_list[0][0]
        cmd = args[0]
        assert cmd.items == [self.item]
        assert cmd.delta == 0.5
        assert cmd.anchor == (0, 0)
        assert cmd.ignore_first_redo is True
        assert self.item.scale_active_corner is None
