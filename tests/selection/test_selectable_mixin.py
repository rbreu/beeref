import math
from pytest import approx, mark
from unittest.mock import patch, MagicMock, PropertyMock

from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt

from beeref.assets import BeeAssets
from beeref import commands
from beeref.items import BeePixmapItem
from beeref.scene import BeeGraphicsScene


@mark.skip
class SelectableMixinBaseTestCase():

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


def test_init_selectable(view):
    item = BeePixmapItem(QtGui.QImage())
    assert item.viewport_scale == 1
    assert item.scale_active is False
    assert item.rotate_active is False
    assert item.flip_active is False
    assert item.just_selected is False


def test_is_action_active_when_no_action(view, item):
    assert item.is_action_active() is False


def test_is_action_active_when_action(view, item):
    item.scale_active = True
    assert item.is_action_active() is True


def test_on_view_scale_change(view, item):
    with patch('beeref.items.BeePixmapItem.prepareGeometryChange') as m:
        item.on_view_scale_change()
        m.assert_called_once()


def test_fixed_length_for_viewport_when_default_scale(view, item):
    view.scene.addItem(item)
    assert item.fixed_length_for_viewport(100) == 100
    assert item._view_scale == 1


def test_fixed_length_for_viewport_when_viewport_scaled(view, item):
    view.scene.addItem(item)
    view.scale(2, 2)
    assert item.fixed_length_for_viewport(100) == 50
    assert item._view_scale == 2


def test_fixed_length_for_viewport_when_item_scaled(view, item):
    view.scene.addItem(item)
    item.setScale(5)
    assert item.fixed_length_for_viewport(100) == 20
    assert item._view_scale == 1


def test_fixed_length_for_viewport_when_no_scene(view, item):
    item._view_scale = 0.5
    assert item.fixed_length_for_viewport(100) == 200


def test_resize_size_when_scaled(view, item):
    view.scene.addItem(item)
    view.scale(2, 2)
    item.setScale(2)
    item.SELECT_RESIZE_SIZE = 100
    assert item.select_resize_size == 25


def test_rotate_size_when_scaled(view, item):
    view.scene.addItem(item)
    view.scale(2, 2)
    item.setScale(2)
    item.SELECT_ROTATE_SIZE = 100
    assert item.select_rotate_size == 25


def test_draw_debug_shape_rect(view, item):
    view.scene.addItem(item)
    painter = MagicMock()
    item.draw_debug_shape(
        painter,
        QtCore.QRectF(5, 6, 20, 30),
        255, 0, 0)
    painter.fillRect.assert_called_once()
    painter.fillPath.assert_not_called()


def test_draw_debug_shape_path(view, item):
    view.scene.addItem(item)
    painter = MagicMock()
    path = QtGui.QPainterPath()
    path.addRect(QtCore.QRectF(5, 6, 20, 30))
    item.draw_debug_shape(
        painter,
        path,
        0, 255, 0)
    painter.fillPath.assert_called_once()
    painter.fillRect.assert_not_called()


@patch('beeref.items.BeePixmapItem.draw_debug_shape')
def test_paint_when_not_selected(debug_mock, view, item):
    view.scene.addItem(item)
    painter = MagicMock()
    item.setSelected(False)
    item.paint(painter, None, None)
    painter.drawPixmap.assert_called_once()
    painter.drawRect.assert_not_called()
    painter.drawPoint.assert_not_called()
    debug_mock.assert_not_called()


def test_paint_when_selected_single_selection(view, item):
    view.scene.addItem(item)
    painter = MagicMock()
    item.setSelected(True)
    item.paint(painter, None, None)
    painter.drawPixmap.assert_called_once()
    painter.drawRect.assert_called_once()
    assert painter.drawPoint.call_count == 4


def test_paint_when_selected_multi_selection(view, item):
    view.scene.addItem(item)
    item2 = BeePixmapItem(QtGui.QImage())
    item2.setSelected(True)
    view.scene.addItem(item2)
    painter = MagicMock()
    item.setSelected(True)
    item.paint(painter, None, None)
    painter.drawPixmap.assert_called_once()
    painter.drawRect.assert_called_once()
    painter.drawPoint.assert_not_called()


def test_paint_when_debug_shapes(view):
    with patch('beeref.selection.commandline_args') as args_mock:
        with patch('beeref.items.BeePixmapItem.draw_debug_shape') as m:
            args_mock.debug_shapes = True
            args_mock.debug_boundingrects = False
            args_mock.debug_handles = False
            item = BeePixmapItem(QtGui.QImage())
            item.paint(MagicMock(), None, None)
            m.assert_called_once()


def test_paint_when_debug_boundingrects(view):
    with patch('beeref.selection.commandline_args') as args_mock:
        with patch('beeref.items.BeePixmapItem.draw_debug_shape') as m:
            args_mock.debug_shapes = False
            args_mock.debug_boundingrects = True
            args_mock.debug_handles = False
            item = BeePixmapItem(QtGui.QImage())
            item.paint(MagicMock(), None, None)
            m.assert_called_once()


def test_paint_when_debug_handles(view):
    with patch('beeref.selection.commandline_args') as args_mock:
        with patch('beeref.items.BeePixmapItem.draw_debug_shape') as m:
            args_mock.debug_shapes = False
            args_mock.debug_boundingrects = False
            args_mock.debug_handles = True
            item = BeePixmapItem(QtGui.QImage())
            view.scene.addItem(item)
            item.setSelected(True)
            item.paint(MagicMock(), None, None)
            m.assert_called()


def test_corners(view, item):
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            assert len(item.corners) == 4
            assert QtCore.QPointF(0, 0) in item.corners
            assert QtCore.QPointF(100, 0) in item.corners
            assert QtCore.QPointF(0, 80) in item.corners
            assert QtCore.QPointF(100, 80) in item.corners


def test_corners_scene_coords_translated(view, item):
    item.setPos(5, 5)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            corners = item.corners_scene_coords
            assert len(item.corners) == 4
            assert QtCore.QPointF(5, 5) in corners
            assert QtCore.QPointF(105, 5) in corners
            assert QtCore.QPointF(5, 85) in corners
            assert QtCore.QPointF(105, 85) in corners


def test_corners_scene_coords_scaled(view, item):
    item.setScale(2)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            corners = item.corners_scene_coords
            assert len(item.corners) == 4
            assert QtCore.QPointF(0, 0) in corners
            assert QtCore.QPointF(200, 0) in corners
            assert QtCore.QPointF(0, 160) in corners
            assert QtCore.QPointF(200, 160) in corners


def test_get_scale_bounds(view, item):
    item.SELECT_RESIZE_SIZE = 10
    rect = item.get_scale_bounds(
        QtCore.QPointF(100, 80)).boundingRect()
    assert rect.topLeft().x() == 95
    assert rect.topLeft().y() == 75
    assert rect.bottomRight().x() == 105
    assert rect.bottomRight().y() == 85


def test_get_scale_bounds_with_margin(view, item):
    item.SELECT_RESIZE_SIZE = 10
    rect = item.get_scale_bounds(
        QtCore.QPointF(100, 80), margin=1).boundingRect()
    assert rect.topLeft().x() == 94
    assert rect.topLeft().y() == 74
    assert rect.bottomRight().x() == 106
    assert rect.bottomRight().y() == 86


def test_rotate_bounds_bottomright(view, item):
    item.SELECT_RESIZE_SIZE = 10
    item.SELECT_ROTATE_SIZE = 10
    path = item.get_rotate_bounds(QtCore.QPointF(100, 80))
    assert path.boundingRect().topLeft().x() == 95
    assert path.boundingRect().topLeft().y() == 75
    assert path.boundingRect().bottomRight().x() == 115
    assert path.boundingRect().bottomRight().y() == 95
    assert path.contains(QtCore.QPointF(104, 84)) is False


def test_rotate_bounds_topleft(view, item):
    item.SELECT_RESIZE_SIZE = 10
    item.SELECT_ROTATE_SIZE = 10
    path = item.get_rotate_bounds(QtCore.QPointF(0, 0))
    assert path.boundingRect().topLeft().x() == -15
    assert path.boundingRect().topLeft().y() == -15
    assert path.boundingRect().bottomRight().x() == 5
    assert path.boundingRect().bottomRight().y() == 5
    assert path.contains(QtCore.QPointF(-4, -4)) is False


def test_get_flip_bounds(view, item):
    item.SELECT_RESIZE_SIZE = 10
    item.SELECT_ROTATE_SIZE = 10
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            edges = item.get_flip_bounds()
            assert edges[0]['rect'].topLeft() == QtCore.QPointF(5, -5)
            assert edges[0]['rect'].bottomRight() == QtCore.QPointF(95, 5)
            assert edges[0]['flip_v'] is True
            assert edges[1]['rect'].topLeft() == QtCore.QPointF(5, 75)
            assert edges[1]['rect'].bottomRight() == QtCore.QPointF(95, 85)
            assert edges[1]['flip_v'] is True
            assert edges[2]['rect'].topLeft() == QtCore.QPointF(-5, 5)
            assert edges[2]['rect'].bottomRight() == QtCore.QPointF(5, 75)
            assert edges[2]['flip_v'] is False
            assert edges[3]['rect'].topLeft() == QtCore.QPointF(95, 5)
            assert edges[3]['rect'].bottomRight() == QtCore.QPointF(105, 75)
            assert edges[3]['flip_v'] is False


def test_bounding_rect_when_not_selected(view, item):
    item.setSelected(False)
    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.boundingRect',
               return_value=QtCore.QRectF(0, 0, 100, 80)):
        rect = item.boundingRect()
        assert rect.topLeft().x() == 0
        assert rect.topLeft().y() == 0
        assert rect.bottomRight().x() == 100
        assert rect.bottomRight().y() == 80


def test_bounding_rect_when_selected(view, item):
    item.SELECT_RESIZE_SIZE = 10
    item.SELECT_ROTATE_SIZE = 10
    item.setSelected(True)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            rect = item.boundingRect()
            assert rect.topLeft().x() == -15
            assert rect.topLeft().y() == -15
            assert rect.bottomRight().x() == 115
            assert rect.bottomRight().y() == 95


def test_shape_when_not_selected(view, item):
    view.scene.addItem(item)
    item.setSelected(False)
    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.boundingRect',
               return_value=QtCore.QRectF(0, 0, 100, 80)):
        shape = item.shape().boundingRect()
        assert shape.topLeft().x() == 0
        assert shape.topLeft().y() == 0
        assert shape.bottomRight().x() == 100
        assert shape.bottomRight().y() == 80


def test_shape_when_selected_single(view, item):
    view.scene.addItem(item)
    item.SELECT_RESIZE_SIZE = 10
    item.SELECT_ROTATE_SIZE = 10
    item.setSelected(True)
    path = QtGui.QPainterPath()
    path.addRect(QtCore.QRectF(0, 0, 100, 80))

    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.shape',
               return_value=path):
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=80):
                shape = item.shape().boundingRect()
                assert shape.topLeft().x() == -15
                assert shape.topLeft().y() == -15
                assert shape.bottomRight().x() == 115
                assert shape.bottomRight().y() == 95


def test_shape_when_selected_multi(view, item):
    view.scene.addItem(item)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item.SELECT_RESIZE_SIZE = 10
    item.SELECT_ROTATE_SIZE = 10
    item.setSelected(True)

    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.boundingRect',
               return_value=QtCore.QRectF(0, 0, 100, 80)):
        shape = item.shape().boundingRect()
        assert shape.topLeft().x() == 0
        assert shape.topLeft().y() == 0
        assert shape.bottomRight().x() == 100
        assert shape.bottomRight().y() == 80


def test_get_scale_factor_bottomright(view, item):
    item.event_start = QtCore.QPointF(10, 10)
    item.event_direction = QtCore.QPointF(1, 1) / math.sqrt(2)
    item.scale_orig_factor = 1
    event = MagicMock()
    event.scenePos.return_value = QtCore.QPointF(20, 90)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            assert item.get_scale_factor(event) == approx(1.5, 0.01)


def test_get_scale_factor_topleft(view, item):
    item.event_start = QtCore.QPointF(10, 10)
    item.event_direction = QtCore.QPointF(-1, -1) / math.sqrt(2)
    item.scale_orig_factor = 0.5
    event = MagicMock()
    event.scenePos.return_value = QtCore.QPointF(-10, -60)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            assert item.get_scale_factor(event) == approx(2, 0.01)


def test_get_scale_anchor_topleft(view, item):
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            anchor = item.get_scale_anchor(QtCore.QPointF(0, 0))
            assert anchor.x() == 100
            assert anchor.y() == 80


def test_get_scale_anchor_bottomright(view, item):
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            anchor = item.get_scale_anchor(QtCore.QPointF(100, 80))
            assert anchor.x() == 0
            assert anchor.y() == 0


def test_get_scale_anchor_topright(view, item):
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            anchor = item.get_scale_anchor(QtCore.QPointF(100, 0))
            assert anchor.x() == 0
            assert anchor.y() == 80


def test_get_scale_anchor_bottomleft(view, item):
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            anchor = item.get_scale_anchor(QtCore.QPointF(0, 80))
            assert anchor.x() == 100
            assert anchor.y() == 0


def test_get_corner_direction_topleft(view, item):
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            assert item.get_corner_direction(
                QtCore.QPointF(0, 0)) == QtCore.QPointF(-1, -1)


def test_get_corner_direction_bottomright(view, item):
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            assert item.get_corner_direction(
                QtCore.QPointF(100, 80)) == QtCore.QPointF(1, 1)


def test_get_corner_direction_topright(view, item):
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            assert item.get_corner_direction(
                QtCore.QPointF(100, 0)) == QtCore.QPointF(1, -1)


def test_get_corner_direction_bottomleft(view, item):
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            assert item.get_corner_direction(
                QtCore.QPointF(0, 80)) == QtCore.QPointF(-1, 1)


def test_get_direction_from_center_bottomright(view, item):
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            direction = item.get_direction_from_center(QtCore.QPointF(100, 90))
            assert direction == approx(QtCore.QPointF(1, 1) / math.sqrt(2))


def test_get_direction_from_center_topleft(view, item):
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            direction = item.get_direction_from_center(QtCore.QPointF(0, -10))
            assert direction == approx(QtCore.QPointF(-1, -1) / math.sqrt(2))


def test_get_direction_from_center_bottomright_when_rotated_180(view, item):
    item.setRotation(180, QtCore.QPointF(50, 40))
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            direction = item.get_direction_from_center(QtCore.QPointF(100, 90))
            assert direction == approx(QtCore.QPointF(1, 1) / math.sqrt(2))


def test_get_rotate_angle(view, item):
    item.event_anchor = QtCore.QPointF(10, 20)
    assert item.get_rotate_angle(QtCore.QPointF(15, 25)) == -45


def test_get_rotate_delta(view, item):
    item.event_anchor = QtCore.QPointF(10, 20)
    item.rotate_start_angle = -3
    assert item.get_rotate_delta(QtCore.QPointF(15, 25)) == -42


def test_get_rotate_delta_snaps(view, item):
    item.event_anchor = QtCore.QPointF(10, 20)
    item.rotate_start_angle = -3
    item.rotate_orig_degrees = 5
    assert item.get_rotate_delta(QtCore.QPointF(15, 25), snap=True) == -35


def test_edge_flips_v_when_item_horizontal(view, item):
    item.setRotation(20)
    assert item.get_edge_flips_v({'flip_v': True}) is True


def test_edge_flips_v_when_item_horizontal_upside_down(view, item):
    item.setRotation(200)
    assert item.get_edge_flips_v({'flip_v': True}) is True


def test_edge_flips_v_when_item_vertical_cw(view, item):
    item.setRotation(80)
    assert item.get_edge_flips_v({'flip_v': True}) is False


def test_edge_flips_v_when_item_vertical_ccw(view, item):
    item.setRotation(120)
    assert item.get_edge_flips_v({'flip_v': True}) is False


def test_hover_move_event_no_selection(view, item):
    view.scene.addItem(item)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(0, 0)
    item.setCursor = MagicMock()
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            item.setCursor.assert_not_called()


def test_hover_move_event_topleft_scale(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(0, 0)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            assert item.cursor() == Qt.CursorShape.SizeFDiagCursor


def test_hover_move_event_bottomright_scale(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(100, 80)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            assert item.cursor() == Qt.CursorShape.SizeFDiagCursor


def test_hover_move_event_topright_scale(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(100, 0)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            assert item.cursor() == Qt.CursorShape.SizeBDiagCursor


def test_hover_move_event_topright_scale_rotated_90(view, item):
    view.scene.addItem(item)
    item.setRotation(90)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(0, 0)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            assert item.cursor() == Qt.CursorShape.SizeBDiagCursor


def test_hover_move_event_top_scale_rotated_45(view, item):
    view.scene.addItem(item)
    item.setRotation(45)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(0, 0)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            assert item.cursor() == Qt.CursorShape.SizeVerCursor


def test_hover_move_event_left_scale_rotated_45(view, item):
    view.scene.addItem(item)
    item.setRotation(45)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(0, 80)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            assert item.cursor() == Qt.CursorShape.SizeHorCursor


def test_hover_move_event_rotate(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(115, 95)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            assert item.cursor() == BeeAssets().cursor_rotate


def test_hover_flip_event_top_edge(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(50, 0)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            assert item.cursor() == BeeAssets().cursor_flip_v


def test_hover_flip_event_bottom_edge(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(50, 80)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            assert item.cursor() == BeeAssets().cursor_flip_v


def test_hover_flip_event_left_edge(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(0, 50)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            assert item.cursor() == BeeAssets().cursor_flip_h


def test_hover_flip_event_right_edge(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(100, 50)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            assert item.cursor() == BeeAssets().cursor_flip_h


def test_hover_flip_event_top_edge_rotated_90(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    item.setRotation(90)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(50, 0)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            assert item.cursor() == BeeAssets().cursor_flip_h


def test_hover_flip_event_left_edge_when_rotated_90(view, item):
    view.scene.addItem(item)
    event = MagicMock()
    item.setSelected(True)
    item.setRotation(90)
    event.pos.return_value = QtCore.QPointF(0, 50)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            assert item.cursor() == BeeAssets().cursor_flip_v


def test_hover_move_event_not_in_handles(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(50, 50)
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.hoverMoveEvent(event)
            assert item.cursor() == Qt.CursorShape.ArrowCursor


def test_hover_enter_event_when_selected(view, item):
    view.scene.addItem(item)
    event = MagicMock()
    item.setSelected(True)
    item.setCursor = MagicMock()
    item.hoverEnterEvent(event)
    item.setCursor.assert_not_called()


def test_hover_enter_event_when_not_selected(view, item):
    view.scene.addItem(item)
    event = MagicMock()
    item.setSelected(False)
    item.hoverEnterEvent(event)
    assert item.cursor() == Qt.CursorShape.ArrowCursor


def test_mouse_press_event_just_selected(view, item):
    view.scene.addItem(item)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(-100, -100)
    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mousePressEvent'):
        item.mousePressEvent(event)
    assert item.just_selected is True


def test_mouse_press_event_previously_selected(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(-100, -100)
    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mousePressEvent'):
        item.mousePressEvent(event)
    assert item.just_selected is False


def test_mouse_press_event_topleft_scale(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(2, 2)
    event.scenePos.return_value = QtCore.QPointF(-1, -1)
    event.button.return_value = Qt.MouseButton.LeftButton
    item.mousePressEvent(event)
    assert item.scale_active is True
    assert item.event_start == QtCore.QPointF(-1, -1)
    assert item.event_direction.x() < 0
    assert item.event_direction.y() < 0
    assert item.scale_orig_factor == 1


def test_mouse_press_event_bottomright_scale(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(99, 79)
    event.scenePos.return_value = QtCore.QPointF(101, 81)
    event.button.return_value = Qt.MouseButton.LeftButton
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.mousePressEvent(event)
            assert item.scale_active is True
            assert item.event_start == QtCore.QPointF(101, 81)
            assert item.event_direction.x() > 0
            assert item.event_direction.y() > 0
            assert item.scale_orig_factor == 1


def test_mouse_press_event_rotate(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(111, 91)
    event.scenePos.return_value = QtCore.QPointF(66, 99)
    event.button.return_value = Qt.MouseButton.LeftButton
    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.mousePressEvent(event)
            assert item.rotate_active is True
            assert item.event_anchor == QtCore.QPointF(50, 40)
            assert item.rotate_orig_degrees == 0


def test_mouse_press_event_flip(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(0, 40)
    event.button.return_value = Qt.MouseButton.LeftButton
    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mousePressEvent'):
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=80):
                item.mousePressEvent(event)
    assert item.flip_active is True


def test_mouse_press_event_not_selected(view, item):
    view.scene.addItem(item)
    view.reset_previous_transform = MagicMock()
    item.setSelected(False)
    event = MagicMock()
    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mousePressEvent') as m:
        item.mousePressEvent(event)
        m.assert_called_once_with(event)
        assert item.scale_active is False
        assert item.rotate_active is False
        assert item.flip_active is False


def test_mouse_press_event_not_in_handles(view, item):
    view.scene.addItem(item)
    view.reset_previous_transform = MagicMock()
    item.setSelected(True)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(50, 40)
    event.button.return_value = Qt.MouseButton.LeftButton
    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mousePressEvent') as m:
        item.mousePressEvent(event)
        m.assert_called_once_with(event)
        assert item.scale_active is False
        assert item.rotate_active is False
        assert item.flip_active is False


def test_mouse_move_event_when_no_action_reset_prev_transform(view, item):
    view.scene.addItem(item)
    view.reset_previous_transform = MagicMock()
    event = MagicMock()
    item.event_start = QtCore.QPointF(10, 10)
    event.scenePos.return_value = QtCore.QPointF(50, 40)
    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mouseMoveEvent') as m:
        item.mouseMoveEvent(event)
        m.assert_called_once_with(event)
        view.reset_previous_transform.assert_called_once()


def test_mouse_move_event_when_no_action_doesnt_reset_prev_transf(view, item):
    view.scene.addItem(item)
    view.reset_previous_transform = MagicMock()
    event = MagicMock()
    item.event_start = QtCore.QPointF(10, 10)
    event.scenePos.return_value = QtCore.QPointF(11, 11)
    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mouseMoveEvent') as m:
        item.mouseMoveEvent(event)
        m.assert_called_once_with(event)
        view.reset_previous_transform.assert_not_called()


def test_mouse_move_event_when_scale_action(view, item):
    view.scene.addItem(item)
    event = MagicMock()
    event.scenePos.return_value = QtCore.QPointF(20, 90)
    item.scale_active = True
    item.event_direction = QtCore.QPointF(1, 1) / math.sqrt(2)
    item.event_anchor = QtCore.QPointF(100, 80)
    item.event_start = QtCore.QPointF(10, 10)
    item.scale_orig_factor = 1

    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mouseMoveEvent') as m:
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=80):
                item.mouseMoveEvent(event)
                m.assert_not_called()
                assert item.scale() == approx(1.5, 0.01)


def test_mouse_move_event_when_rotate_action(view, item):
    view.scene.addItem(item)
    event = MagicMock()
    event.scenePos.return_value = QtCore.QPointF(15, 25)
    item.event_start = QtCore.QPointF(10, 10)
    item.rotate_active = True
    item.rotate_orig_degrees = 0
    item.rotate_start_angle = -3
    item.event_anchor = QtCore.QPointF(10, 20)
    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mouseMoveEvent') as m:
        item.mouseMoveEvent(event)
        m.assert_not_called()
    assert item.rotation() == 318


def test_mouse_move_event_when_flip_action(view, item):
    view.scene.addItem(item)
    event = MagicMock()
    event.scenePos.return_value = QtCore.QPointF(15, 25)
    item.event_start = QtCore.QPointF(10, 10)
    item.flip_active = True
    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem.mouseMoveEvent') as m:
        item.mouseMoveEvent(event)
        m.assert_not_called()


def test_mouse_release_event_when_no_action(view, item):
    view.scene.addItem(item)
    event = MagicMock()
    item.flip_active = True
    event.pos.return_value = QtCore.QPointF(-100, -100)
    with patch('PyQt6.QtWidgets.QGraphicsPixmapItem'
               '.mouseReleaseEvent') as m:
        item.mouseReleaseEvent(event)
        m.assert_called_once_with(event)
        item.flip_active is False


def test_mouse_release_event_when_scale_action(view, item):
    view.scene.addItem(item)
    event = MagicMock()
    event.scenePos.return_value = QtCore.QPointF(20, 90)
    item.scale_active = True
    item.event_direction = QtCore.QPointF(1, 1) / math.sqrt(2)
    item.event_anchor = QtCore.QPointF(100, 80)
    item.event_start = QtCore.QPointF(10, 10)
    item.scale_orig_factor = 1
    view.scene.undo_stack = MagicMock(push=MagicMock())

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.mouseReleaseEvent(event)
            view.scene.undo_stack.push.assert_called_once()
            args = view.scene.undo_stack.push.call_args_list[0][0]
            cmd = args[0]
            isinstance(cmd, commands.ScaleItemsBy)
            assert cmd.items == [item]
            assert cmd.factor == approx(1.5, 0.01)
            assert cmd.anchor == QtCore.QPointF(100, 80)
            assert cmd.ignore_first_redo is True
            assert item.scale_active is False


def test_mouse_release_event_when_scale_action_zero(view, item):
    view.scene.addItem(item)
    event = MagicMock()
    event.scenePos.return_value = QtCore.QPointF(20, 90)
    item.scale_active = True
    item.event_direction = QtCore.QPointF(1, 1) / math.sqrt(2)
    item.event_anchor = QtCore.QPointF(100, 80)
    item.event_start = QtCore.QPointF(20, 90)
    item.scale_orig_factor = 1
    view.scene.undo_stack = MagicMock(push=MagicMock())

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.mouseReleaseEvent(event)
            view.scene.undo_stack.push.assert_not_called()
            assert item.scale_active is False


def test_mouse_release_event_when_rotate_action(view, item):
    view.scene.addItem(item)
    event = MagicMock()
    event.scenePos.return_value = QtCore.QPointF(15, 25)
    item.rotate_active = True
    item.rotate_orig_degrees = 0
    item.rotate_start_angle = -3
    item.event_anchor = QtCore.QPointF(10, 20)
    view.scene.undo_stack = MagicMock(push=MagicMock())

    item.mouseReleaseEvent(event)
    view.scene.undo_stack.push.assert_called_once()
    args = view.scene.undo_stack.push.call_args_list[0][0]
    cmd = args[0]
    isinstance(cmd, commands.RotateItemsBy)
    assert cmd.items == [item]
    assert cmd.delta == -42
    assert cmd.anchor == QtCore.QPointF(10, 20)
    assert cmd.ignore_first_redo is True
    assert item.rotate_active is False


def test_mouse_release_event_when_rotate_action_zero(view, item):
    view.scene.addItem(item)
    event = MagicMock()
    event.scenePos.return_value = QtCore.QPointF(15, 25)
    item.rotate_active = True
    item.rotate_orig_degrees = 0
    item.rotate_start_angle = -45
    item.event_anchor = QtCore.QPointF(10, 20)
    view.scene.undo_stack = MagicMock(push=MagicMock())

    item.mouseReleaseEvent(event)
    view.scene.undo_stack.push.assert_not_called()
    assert item.rotate_active is False


def test_mouse_release_event_when_flip_action(view, item):
    view.scene.addItem(item)
    event = MagicMock()
    event.pos.return_value = QtCore.QPointF(0, 40)
    item.flip_active = True
    view.scene.undo_stack = MagicMock(push=MagicMock())

    with patch('beeref.items.BeePixmapItem.width',
               new_callable=PropertyMock, return_value=100):
        with patch('beeref.items.BeePixmapItem.height',
                   new_callable=PropertyMock, return_value=80):
            item.mouseReleaseEvent(event)
            args = view.scene.undo_stack.push.call_args_list[0][0]
            cmd = args[0]
            isinstance(cmd, commands.FlipItems)
            assert cmd.items == [item]
            assert cmd.anchor == QtCore.QPointF(50, 40)
            assert cmd.vertical is False
            assert item.flip_active is False
