import math
from pytest import approx
from unittest.mock import patch, MagicMock, PropertyMock

from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt

from beeref.assets import BeeAssets
from beeref import commands
from beeref.items import BeePixmapItem
from beeref.scene import BeeGraphicsScene
from beeref.selection import MultiSelectItem, RubberbandItem
from .base import BeeTestCase


class BaseItemMixinTestCase(BeeTestCase):

    def setUp(self):
        self.scene = BeeGraphicsScene(None)

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

    def test_set_scale_with_anchor(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setScale(2, anchor=QtCore.QPointF(100, 100))
        assert item.scale() == 2
        assert item.pos() == QtCore.QPointF(-100, -100)

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

    def test_set_rotation_no_anchor(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setRotation(45)
        assert item.rotation() == 45
        assert item.pos().x() == 0
        assert item.pos().y() == 0

    def test_set_rotation_anchor_bottomright_cw(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setRotation(90, QtCore.QPointF(100, 100))
        assert item.rotation() == 90
        assert item.pos().x() == 200
        assert item.pos().y() == 0

    def test_set_rotation_anchor_bottomright_ccw(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setRotation(-90, QtCore.QPointF(100, 100))
        assert item.rotation() == 270
        assert item.pos().x() == 0
        assert item.pos().y() == 200

    def test_set_rotation_caps_above_360(self):
        item = BeePixmapItem(QtGui.QImage())
        item.setRotation(400)
        assert item.rotation() == 40

    def test_flip(self):
        item = BeePixmapItem(QtGui.QImage())
        assert item.flip() == 1

    def test_flip_when_flipped(self):
        item = BeePixmapItem(QtGui.QImage())
        item.do_flip()
        assert item.flip() == -1

    def test_do_flip_no_anchor(self):
        item = BeePixmapItem(QtGui.QImage())
        item.do_flip()
        assert item.flip() == -1
        item.do_flip()
        assert item.flip() == 1

    def test_do_flip_vertical(self):
        item = BeePixmapItem(QtGui.QImage())
        item.do_flip(vertical=True)
        assert item.flip() == -1
        assert item.rotation() == 180

    def test_do_flip_anchor(self):
        item = BeePixmapItem(QtGui.QImage())
        item.do_flip(anchor=QtCore.QPointF(100, 100))
        assert item.flip() == -1
        assert item.pos() == QtCore.QPointF(200, 0)

    def test_do_flip_vertical_anchor(self):
        item = BeePixmapItem(QtGui.QImage())
        item.do_flip(vertical=True, anchor=QtCore.QPointF(100, 100))
        assert item.flip() == -1
        assert item.rotation() == 180
        assert item.pos() == QtCore.QPointF(0, 200)

    def test_center_scene_coords(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        item.setPos(5, 5)
        item.setScale(2)
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=80):
                assert item.center_scene_coords == QtCore.QPointF(105, 85)


class SelectableMixinBaseTestCase(BeeTestCase):

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


class SelectableMixinTestCase(SelectableMixinBaseTestCase):

    def test_on_view_scale_change(self):
        item = BeePixmapItem(QtGui.QImage())
        with patch('beeref.items.BeePixmapItem.prepareGeometryChange') as m:
            item.on_view_scale_change()
            m.assert_called_once()

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

    def test_draw_debug_shape_rect(self):
        painter = MagicMock()
        self.item.draw_debug_shape(
            painter,
            QtCore.QRectF(5, 6, 20, 30),
            255, 0, 0)
        painter.fillRect.assert_called_once()
        painter.fillPath.assert_not_called()

    def test_draw_debug_shape_path(self):
        painter = MagicMock()
        path = QtGui.QPainterPath()
        path.addRect(QtCore.QRectF(5, 6, 20, 30))
        self.item.draw_debug_shape(
            painter,
            path,
            0, 255, 0)
        painter.fillPath.assert_called_once()
        painter.fillRect.assert_not_called()

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

    def test_paint_when_debug_shapes(self):
        with patch('beeref.selection.commandline_args') as args_mock:
            with patch('beeref.items.BeePixmapItem.draw_debug_shape') as m:
                args_mock.debug_shapes = True
                args_mock.debug_boundingrects = False
                args_mock.debug_handles = False
                item = BeePixmapItem(QtGui.QImage())
                item.paint(MagicMock(), None, None)
                m.assert_called_once()

    def test_paint_when_debug_boundingrects(self):
        with patch('beeref.selection.commandline_args') as args_mock:
            with patch('beeref.items.BeePixmapItem.draw_debug_shape') as m:
                args_mock.debug_shapes = False
                args_mock.debug_boundingrects = True
                args_mock.debug_handles = False
                item = BeePixmapItem(QtGui.QImage())
                item.paint(MagicMock(), None, None)
                m.assert_called_once()

    def test_paint_when_debug_handles(self):
        with patch('beeref.selection.commandline_args') as args_mock:
            with patch('beeref.items.BeePixmapItem.draw_debug_shape') as m:
                args_mock.debug_shapes = False
                args_mock.debug_boundingrects = False
                args_mock.debug_handles = True
                item = BeePixmapItem(QtGui.QImage())
                self.scene.addItem(item)
                item.setSelected(True)
                item.paint(MagicMock(), None, None)
                m.assert_called()

    def test_corners(self):
        assert len(self.item.corners) == 4
        assert QtCore.QPointF(0, 0) in self.item.corners
        assert QtCore.QPointF(100, 0) in self.item.corners
        assert QtCore.QPointF(0, 80) in self.item.corners
        assert QtCore.QPointF(100, 80) in self.item.corners

    def test_corners_scene_coords_translated(self):
        self.item.setPos(5, 5)
        corners = self.item.corners_scene_coords
        assert len(self.item.corners) == 4
        assert QtCore.QPointF(5, 5) in corners
        assert QtCore.QPointF(105, 5) in corners
        assert QtCore.QPointF(5, 85) in corners
        assert QtCore.QPointF(105, 85) in corners

    def test_corners_scene_coords_scaled(self):
        self.item.setScale(2)
        corners = self.item.corners_scene_coords
        assert len(self.item.corners) == 4
        assert QtCore.QPointF(0, 0) in corners
        assert QtCore.QPointF(200, 0) in corners
        assert QtCore.QPointF(0, 160) in corners
        assert QtCore.QPointF(200, 160) in corners

    def test_get_scale_bounds(self):
        self.view.get_scale = MagicMock(return_value=1)
        self.item.SELECT_RESIZE_SIZE = 10
        rect = self.item.get_scale_bounds(
            QtCore.QPointF(100, 80)).boundingRect()
        assert rect.topLeft().x() == 95
        assert rect.topLeft().y() == 75
        assert rect.bottomRight().x() == 105
        assert rect.bottomRight().y() == 85

    def test_get_scale_bounds_with_margin(self):
        self.view.get_scale = MagicMock(return_value=1)
        self.item.SELECT_RESIZE_SIZE = 10
        rect = self.item.get_scale_bounds(
            QtCore.QPointF(100, 80), margin=1).boundingRect()
        assert rect.topLeft().x() == 94
        assert rect.topLeft().y() == 74
        assert rect.bottomRight().x() == 106
        assert rect.bottomRight().y() == 86

    def test_rotate_bounds_bottomright(self):
        self.view.get_scale = MagicMock(return_value=1)
        self.item.SELECT_RESIZE_SIZE = 10
        self.item.SELECT_ROTATE_SIZE = 10
        path = self.item.get_rotate_bounds(QtCore.QPointF(100, 80))
        assert path.boundingRect().topLeft().x() == 95
        assert path.boundingRect().topLeft().y() == 75
        assert path.boundingRect().bottomRight().x() == 115
        assert path.boundingRect().bottomRight().y() == 95
        assert path.contains(QtCore.QPointF(104, 84)) is False

    def test_rotate_bounds_topleft(self):
        self.view.get_scale = MagicMock(return_value=1)
        self.item.SELECT_RESIZE_SIZE = 10
        self.item.SELECT_ROTATE_SIZE = 10
        path = self.item.get_rotate_bounds(QtCore.QPointF(0, 0))
        assert path.boundingRect().topLeft().x() == -15
        assert path.boundingRect().topLeft().y() == -15
        assert path.boundingRect().bottomRight().x() == 5
        assert path.boundingRect().bottomRight().y() == 5
        assert path.contains(QtCore.QPointF(-4, -4)) is False

    def test_get_flip_bounds(self):
        self.view.get_scale = MagicMock(return_value=1)
        self.item.SELECT_RESIZE_SIZE = 10
        self.item.SELECT_ROTATE_SIZE = 10
        edges = self.item.get_flip_bounds()
        assert edges[0]['rect'].topLeft() == QtCore.QPointF(5, -15)
        assert edges[0]['rect'].bottomRight() == QtCore.QPointF(95, 5)
        assert edges[0]['flip_v'] is True
        assert edges[1]['rect'].topLeft() == QtCore.QPointF(5, 75)
        assert edges[1]['rect'].bottomRight() == QtCore.QPointF(95, 95)
        assert edges[1]['flip_v'] is True
        assert edges[2]['rect'].topLeft() == QtCore.QPointF(-15, 5)
        assert edges[2]['rect'].bottomRight() == QtCore.QPointF(5, 75)
        assert edges[2]['flip_v'] is False
        assert edges[3]['rect'].topLeft() == QtCore.QPointF(95, 5)
        assert edges[3]['rect'].bottomRight() == QtCore.QPointF(115, 75)
        assert edges[3]['flip_v'] is False

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
        rect = self.item.boundingRect()
        assert rect.topLeft().x() == -15
        assert rect.topLeft().y() == -15
        assert rect.bottomRight().x() == 115
        assert rect.bottomRight().y() == 95

    def test_shape_when_not_selected(self):
        self.view.get_scale = MagicMock(return_value=1)
        self.item.setSelected(False)
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.boundingRect',
                   return_value=QtCore.QRectF(0, 0, 100, 80)):
            shape = self.item.shape().boundingRect()
            assert shape.topLeft().x() == 0
            assert shape.topLeft().y() == 0
            assert shape.bottomRight().x() == 100
            assert shape.bottomRight().y() == 80

    def test_shape_when_selected_single(self):
        self.item.SELECT_RESIZE_SIZE = 10
        self.item.SELECT_ROTATE_SIZE = 10
        self.view.get_scale = MagicMock(return_value=1)
        self.item.setSelected(True)
        path = QtGui.QPainterPath()
        path.addRect(QtCore.QRectF(0, 0, 100, 80))

        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.shape',
                   return_value=path):
            shape = self.item.shape().boundingRect()
            assert shape.topLeft().x() == -15
            assert shape.topLeft().y() == -15
            assert shape.bottomRight().x() == 115
            assert shape.bottomRight().y() == 95

    def test_shape_when_selected_multi(self):
        item2 = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item2)
        item2.setSelected(True)
        self.item.SELECT_RESIZE_SIZE = 10
        self.item.SELECT_ROTATE_SIZE = 10
        self.view.get_scale = MagicMock(return_value=1)
        self.item.setSelected(True)

        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.boundingRect',
                   return_value=QtCore.QRectF(0, 0, 100, 80)):
            shape = self.item.shape().boundingRect()
            assert shape.topLeft().x() == 0
            assert shape.topLeft().y() == 0
            assert shape.bottomRight().x() == 100
            assert shape.bottomRight().y() == 80


class SelectableMixinCalculationsTestCase(SelectableMixinBaseTestCase):

    def test_get_scale_factor_bottomright(self):
        self.item.event_start = QtCore.QPointF(10, 10)
        self.item.event_direction = QtCore.QPointF(1, 1) / math.sqrt(2)
        self.item.scale_orig_factor = 1
        event = MagicMock()
        event.scenePos = MagicMock(return_value=QtCore.QPointF(20, 90))
        assert self.item.get_scale_factor(event) == approx(1.5, 0.01)

    def test_get_scale_factor_topleft(self):
        self.item.event_start = QtCore.QPointF(10, 10)
        self.item.event_direction = QtCore.QPointF(-1, -1) / math.sqrt(2)
        self.item.scale_orig_factor = 0.5
        event = MagicMock()
        event.scenePos = MagicMock(return_value=QtCore.QPointF(-10, -60))
        assert self.item.get_scale_factor(event) == approx(2, 0.01)

    def test_get_scale_anchor_topleft(self):
        anchor = self.item.get_scale_anchor(QtCore.QPointF(0, 0))
        assert anchor.x() == 100
        assert anchor.y() == 80

    def test_get_scale_anchor_bottomright(self):
        anchor = self.item.get_scale_anchor(QtCore.QPointF(100, 80))
        assert anchor.x() == 0
        assert anchor.y() == 0

    def test_get_scale_anchor_topright(self):
        anchor = self.item.get_scale_anchor(QtCore.QPointF(100, 0))
        assert anchor.x() == 0
        assert anchor.y() == 80

    def test_get_scale_anchor_bottomleft(self):
        anchor = self.item.get_scale_anchor(QtCore.QPointF(0, 80))
        assert anchor.x() == 100
        assert anchor.y() == 0

    def test_get_corner_direction_topleft(self):
        assert self.item.get_corner_direction(
            QtCore.QPointF(0, 0)) == QtCore.QPointF(-1, -1)

    def test_get_corner_direction_bottomright(self):
        assert self.item.get_corner_direction(
            QtCore.QPointF(100, 80)) == QtCore.QPointF(1, 1)

    def test_get_corner_direction_topright(self):
        assert self.item.get_corner_direction(
            QtCore.QPointF(100, 0)) == QtCore.QPointF(1, -1)

    def test_get_corner_direction_bottomleft(self):
        assert self.item.get_corner_direction(
            QtCore.QPointF(0, 80)) == QtCore.QPointF(-1, 1)

    def test_get_direction_from_center_bottomright(self):
        direction = self.item.get_direction_from_center(
            QtCore.QPointF(100, 90))
        assert direction == approx(QtCore.QPointF(1, 1) / math.sqrt(2))

    def test_get_direction_from_center_topleft(self):
        direction = self.item.get_direction_from_center(
            QtCore.QPointF(0, -10))
        assert direction == approx(QtCore.QPointF(-1, -1) / math.sqrt(2))

    def test_get_direction_from_center_bottomright_when_rotated_180(self):
        self.item.setRotation(180, QtCore.QPointF(50, 40))
        direction = self.item.get_direction_from_center(
            QtCore.QPointF(100, 90))
        assert direction == approx(QtCore.QPointF(1, 1) / math.sqrt(2))

    def test_get_rotate_angle(self):
        self.item.event_anchor = QtCore.QPointF(10, 20)
        assert self.item.get_rotate_angle(QtCore.QPointF(15, 25)) == -45

    def test_get_rotate_delta(self):
        self.item.event_anchor = QtCore.QPointF(10, 20)
        self.item.rotate_start_angle = -3
        assert self.item.get_rotate_delta(QtCore.QPointF(15, 25)) == -42

    def test_get_rotate_delta_snaps(self):
        self.item.event_anchor = QtCore.QPointF(10, 20)
        self.item.rotate_start_angle = -3
        self.item.rotate_orig_degrees = 5
        assert self.item.get_rotate_delta(
            QtCore.QPointF(15, 25), snap=True) == -35

    def test_edge_flips_v_when_item_horizontal(self):
        self.item.setRotation(20)
        assert self.item.get_edge_flips_v({'flip_v': True}) is True

    def test_edge_flips_v_when_item_horizontal_upside_down(self):
        self.item.setRotation(200)
        assert self.item.get_edge_flips_v({'flip_v': True}) is True

    def test_edge_flips_v_when_item_vertical_cw(self):
        self.item.setRotation(80)
        assert self.item.get_edge_flips_v({'flip_v': True}) is False

    def test_edge_flips_v_when_item_vertical_ccw(self):
        self.item.setRotation(120)
        assert self.item.get_edge_flips_v({'flip_v': True}) is False


class SelectableMixinMouseEventsTestCase(SelectableMixinBaseTestCase):

    def setUp(self):
        super().setUp()
        self.event = MagicMock()
        self.item.setCursor = MagicMock()
        self.item.SELECT_RESIZE_SIZE = 10
        self.item.SELECT_ROTATE_SIZE = 10

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

    def test_hover_move_event_topright_scale_rotated_90(self):
        self.item.setRotation(90)
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(0, 0))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_called_once_with(
            Qt.CursorShape.SizeBDiagCursor)

    def test_hover_move_event_top_scale_rotated_45(self):
        self.item.setRotation(45)
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(0, 0))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_called_once_with(
            Qt.CursorShape.SizeVerCursor)

    def test_hover_move_event_left_scale_rotated_45(self):
        self.item.setRotation(45)
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(0, 80))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_called_once_with(
            Qt.CursorShape.SizeHorCursor)

    def test_hover_move_event_rotate(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(110, 90))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_called_once_with(BeeAssets().cursor_rotate)

    def test_hover_flip_event_top_edge(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(50, 0))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_called_once_with(
            BeeAssets().cursor_flip_v)

    def test_hover_flip_event_bottom_edge(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(50, 80))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_called_once_with(
            BeeAssets().cursor_flip_v)

    def test_hover_flip_event_left_edge(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(0, 50))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_called_once_with(
            BeeAssets().cursor_flip_h)

    def test_hover_flip_event_right_edge(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(100, 50))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_called_once_with(
            BeeAssets().cursor_flip_h)

    def test_hover_flip_event_top_edge_rotated_90(self):
        self.item.setSelected(True)
        self.item.setRotation(90)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(50, 0))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_called_once_with(
            BeeAssets().cursor_flip_h)

    def test_hover_flip_event_left_edge_when_rotated_90(self):
        self.item.setSelected(True)
        self.item.setRotation(90)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(0, 50))
        self.item.hoverMoveEvent(self.event)
        self.item.setCursor.assert_called_once_with(
            BeeAssets().cursor_flip_v)

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

    def test_mouse_press_event_just_selected(self):
        self.event.pos = MagicMock(return_value=QtCore.QPointF(-100, -100))
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mousePressEvent'):
            self.item.mousePressEvent(self.event)
        assert self.item.just_selected is True

    def test_mouse_press_event_previously_selected(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(-100, -100))
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mousePressEvent'):
            self.item.mousePressEvent(self.event)
        assert self.item.just_selected is False

    def test_mouse_press_event_topleft_scale(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(2, 2))
        self.event.scenePos = MagicMock(return_value=QtCore.QPointF(-1, -1))
        self.event.button = MagicMock(return_value=Qt.MouseButtons.LeftButton)
        self.item.mousePressEvent(self.event)
        assert self.item.scale_active is True
        assert self.item.event_start == QtCore.QPointF(-1, -1)
        assert self.item.event_direction.x() < 0
        assert self.item.event_direction.y() < 0
        assert self.item.scale_orig_factor == 1

    def test_mouse_press_event_bottomright_scale(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(99, 79))
        self.event.scenePos = MagicMock(return_value=QtCore.QPointF(101, 81))
        self.event.button = MagicMock(return_value=Qt.MouseButtons.LeftButton)
        self.item.mousePressEvent(self.event)
        assert self.item.scale_active is True
        assert self.item.event_start == QtCore.QPointF(101, 81)
        assert self.item.event_direction.x() > 0
        assert self.item.event_direction.y() > 0
        assert self.item.scale_orig_factor == 1

    def test_mouse_press_event_rotate(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(111, 91))
        self.event.scenePos = MagicMock(return_value=QtCore.QPointF(66, 99))
        self.event.button = MagicMock(return_value=Qt.MouseButtons.LeftButton)
        self.item.mousePressEvent(self.event)
        assert self.item.rotate_active is True
        assert self.item.event_anchor == QtCore.QPointF(50, 40)
        assert self.item.rotate_orig_degrees == 0

    def test_mouse_press_event_flip(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(0, 40))
        self.event.button = MagicMock(return_value=Qt.MouseButtons.LeftButton)
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mousePressEvent'):
            self.item.mousePressEvent(self.event)
        assert self.item.flip_active is True

    def test_mouse_press_event_not_selected(self):
        self.item.setSelected(False)
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mousePressEvent') as m:
            self.item.mousePressEvent(self.event)
            m.assert_called_once_with(self.event)
            assert self.item.scale_active is False
            assert self.item.rotate_active is False
            assert self.item.flip_active is False

    def test_mouse_press_event_not_in_handles(self):
        self.item.setSelected(True)
        self.event.pos = MagicMock(return_value=QtCore.QPointF(50, 40))
        self.event.button = MagicMock(return_value=Qt.MouseButtons.LeftButton)
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mousePressEvent') as m:
            self.item.mousePressEvent(self.event)
            m.assert_called_once_with(self.event)
            assert self.item.scale_active is False
            assert self.item.rotate_active is False
            assert self.item.flip_active is False

    def test_mouse_move_event_when_no_action(self):
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mouseMoveEvent') as m:
            self.item.mouseMoveEvent(self.event)
            m.assert_called_once_with(self.event)

    def test_mouse_move_event_when_scale_action(self):
        self.event.scenePos = MagicMock(return_value=QtCore.QPointF(20, 90))
        self.item.scale_active = True
        self.item.event_direction = QtCore.QPointF(1, 1) / math.sqrt(2)
        self.item.event_anchor = QtCore.QPointF(100, 80)
        self.item.event_start = QtCore.QPointF(10, 10)
        self.item.scale_orig_factor = 1

        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mouseMoveEvent') as m:
            self.item.mouseMoveEvent(self.event)
            m.assert_not_called()
        assert self.item.scale() == approx(1.5, 0.01)

    def test_mouse_move_event_when_rotate_action(self):
        self.event.scenePos = MagicMock(return_value=QtCore.QPointF(15, 25))
        self.item.rotate_active = True
        self.item.rotate_orig_degrees = 0
        self.item.rotate_start_angle = -3
        self.item.event_anchor = QtCore.QPointF(10, 20)
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mouseMoveEvent') as m:
            self.item.mouseMoveEvent(self.event)
            m.assert_not_called()
        assert self.item.rotation() == 318

    def test_mouse_move_event_when_flip_action(self):
        self.event.scenePos = MagicMock(return_value=QtCore.QPointF(15, 25))
        self.item.flip_active = True
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mouseMoveEvent') as m:
            self.item.mouseMoveEvent(self.event)
            m.assert_not_called()

    def test_mouse_release_event_when_no_action(self):
        self.event.pos = MagicMock(return_value=QtCore.QPointF(-100, -100))
        with patch('PyQt6.QtWidgets.QGraphicsPixmapItem'
                   '.mouseReleaseEvent') as m:
            self.item.mouseReleaseEvent(self.event)
            m.assert_called_once_with(self.event)

    def test_mouse_release_event_when_scale_action(self):
        self.event.scenePos = MagicMock(return_value=QtCore.QPointF(20, 90))
        self.item.scale_active = True
        self.item.event_direction = QtCore.QPointF(1, 1) / math.sqrt(2)
        self.item.event_anchor = QtCore.QPointF(100, 80)
        self.item.event_start = QtCore.QPointF(10, 10)
        self.item.scale_orig_factor = 1
        self.scene.undo_stack = MagicMock(push=MagicMock())

        self.item.mouseReleaseEvent(self.event)
        self.scene.undo_stack.push.assert_called_once()
        args = self.scene.undo_stack.push.call_args_list[0][0]
        cmd = args[0]
        isinstance(cmd, commands.ScaleItemsBy)
        assert cmd.items == [self.item]
        assert cmd.factor == approx(1.5, 0.01)
        assert cmd.anchor == QtCore.QPointF(100, 80)
        assert cmd.ignore_first_redo is True
        assert self.item.scale_active is False

    def test_mouse_release_event_when_rotate_action(self):
        self.event.scenePos = MagicMock(return_value=QtCore.QPointF(15, 25))
        self.item.rotate_active = True
        self.item.rotate_orig_degrees = 0
        self.item.rotate_start_angle = -3
        self.item.event_anchor = QtCore.QPointF(10, 20)
        self.scene.undo_stack = MagicMock(push=MagicMock())

        self.item.mouseReleaseEvent(self.event)
        args = self.scene.undo_stack.push.call_args_list[0][0]
        cmd = args[0]
        isinstance(cmd, commands.RotateItemsBy)
        assert cmd.items == [self.item]
        assert cmd.delta == -42
        assert cmd.anchor == QtCore.QPointF(10, 20)
        assert cmd.ignore_first_redo is True
        assert self.item.rotate_active is False

    def test_mouse_release_event_when_flip_action(self):
        self.event.pos = MagicMock(return_value=QtCore.QPointF(0, 40))
        self.item.flip_active = True
        self.scene.undo_stack = MagicMock(push=MagicMock())

        self.item.mouseReleaseEvent(self.event)
        args = self.scene.undo_stack.push.call_args_list[0][0]
        cmd = args[0]
        isinstance(cmd, commands.FlipItems)
        assert cmd.items == [self.item]
        assert cmd.anchor == QtCore.QPointF(50, 40)
        assert cmd.vertical is False


class MultiSelectItemTestCase(BeeTestCase):

    def setUp(self):
        self.scene = BeeGraphicsScene(None)

    @patch('beeref.selection.SelectableMixin.init_selectable')
    def test_init(self, selectable_mock):
        item = MultiSelectItem()
        assert hasattr(item, 'save_id') is False
        selectable_mock.assert_called_once()

    def test_width(self):
        item = MultiSelectItem()
        item.setRect(0, 0, 50, 100)
        assert item.width == 50

    def test_height(self):
        item = MultiSelectItem()
        item.setRect(0, 0, 50, 100)
        assert item.height == 100

    def test_paint(self):
        item = MultiSelectItem()
        item.paint_selectable = MagicMock()
        painter = MagicMock()
        item.paint(painter, None, None)
        item.paint_selectable.assert_called_once()
        painter.drawRect.assert_not_called()

    def test_has_selection_outline(self):
        item = MultiSelectItem()
        item.has_selection_outline() is True

    def test_has_selection_handles(self):
        item = MultiSelectItem()
        item.has_selection_handles() is True

    def test_selection_action_items(self):
        view = MagicMock(get_scale=MagicMock(return_value=1))
        with patch('beeref.scene.BeeGraphicsScene.views',
                   return_value=[view]):
            img1 = BeePixmapItem(QtGui.QImage())
            self.scene.addItem(img1)
            img1.setSelected(True)
            img2 = BeePixmapItem(QtGui.QImage())
            self.scene.addItem(img2)
            img2.setSelected(False)
            item = MultiSelectItem()
            self.scene.addItem(item)
            item.setSelected(True)
            action_items = item.selection_action_items()
            assert img1 in action_items
            assert item in action_items
            assert img2 not in action_items

    def test_fit_selection_area(self):
        item = MultiSelectItem()
        item.setScale(5)
        item.setRotation(-20)
        item.do_flip()
        item.fit_selection_area(QtCore.QRectF(-10, -20, 100, 80))
        assert item.pos().x() == -10
        assert item.pos().y() == -20
        assert item.width == 100
        assert item.height == 80
        assert item.scale() == 1
        assert item.rotation() == 0
        assert item.flip() == 1
        assert item.isSelected() is True

    @patch('PyQt6.QtWidgets.QGraphicsRectItem.mousePressEvent')
    def test_mouse_press_event_when_ctrl_leftclick(self, mouse_mock):
        item = MultiSelectItem()
        item.fit_selection_area(QtCore.QRectF(0, 0, 100, 80))
        event = MagicMock(
            button=MagicMock(return_value=Qt.MouseButtons.LeftButton),
            modifiers=MagicMock(
                return_value=Qt.KeyboardModifiers.ControlModifier))
        item.mousePressEvent(event)
        event.ignore.assert_called_once()
        mouse_mock.assert_not_called()

    @patch('beeref.selection.SelectableMixin.mousePressEvent')
    def test_mouse_press_event_when_leftclick(self, mouse_mock):
        item = MultiSelectItem()
        item.fit_selection_area(QtCore.QRectF(0, 0, 100, 80))
        event = MagicMock(
            button=MagicMock(return_value=Qt.MouseButtons.LeftButton))
        item.mousePressEvent(event)
        event.ignore.assert_not_called()
        mouse_mock.assert_called_once_with(event)


class RubberbandItemTestCase(BeeTestCase):

    def setUp(self):
        self.scene = BeeGraphicsScene(None)

    def test_width(self):
        item = RubberbandItem()
        item.setRect(5, 5, 100, 80)
        assert item.width == 100

    def test_height(self):
        item = RubberbandItem()
        item.setRect(5, 5, 100, 80)
        assert item.height == 80

    def test_fit_topleft_to_bottomright(self):
        item = RubberbandItem()
        item.fit(QtCore.QPointF(-10, -20), QtCore.QPointF(30, 40))
        assert item.rect().topLeft().x() == -10
        assert item.rect().topLeft().y() == -20
        assert item.rect().bottomRight().x() == 30
        assert item.rect().bottomRight().y() == 40

    def test_fit_topright_to_bottomleft(self):
        item = RubberbandItem()
        item.fit(QtCore.QPointF(50, -20), QtCore.QPointF(-30, 40))
        assert item.rect().topLeft().x() == -30
        assert item.rect().topLeft().y() == -20
        assert item.rect().bottomRight().x() == 50
        assert item.rect().bottomRight().y() == 40
