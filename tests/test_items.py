from unittest.mock import patch, MagicMock, PropertyMock

from PyQt6 import QtCore, QtGui, QtWidgets

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
        item = BeePixmapItem(QtGui.QImage())
        item.prepareGeometryChange = MagicMock()
        item.setScale(3)
        assert item.scale() == 3
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


class BeePixmapItemPaintstuffTestCase(BeeTestCase):

    def setUp(self):
        self.scene = BeeGraphicsScene(None)
        self.item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(self.item)
        self.view = MagicMock(get_scale=MagicMock(return_value=1))
        views_patcher = patch('beeref.scene.BeeGraphicsScene.views')
        views_mock = views_patcher.start()
        views_mock.return_value = [self.view]
        self.addCleanup(views_patcher.stop)

    def test_fixed_length_for_viewport_when_default_scales(self):
        self.view.get_scale = MagicMock(return_value=1)
        assert self.item.fixed_length_for_viewport(100) == 100

    def test_fixed_length_for_viewport_when_viewport_scaled(self):
        self.view.get_scale = MagicMock(return_value=2)
        assert self.item.fixed_length_for_viewport(100) == 50

    def test_fixed_length_for_viewport_when_item_scaled(self):
        self.view.get_scale = MagicMock(return_value=1)
        self.item.setScale(5)
        assert self.item.fixed_length_for_viewport(100) == 20

    def test_fixed_length_for_viewport_when_no_scene(self):
        item = BeePixmapItem(QtGui.QImage())
        item.viewport_scale = 0.5
        assert item.fixed_length_for_viewport(100) == 50

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

    def test_paint_when_not_selected(self):
        painter = MagicMock()
        self.item.setSelected(False)
        self.item.pixmap = MagicMock(return_value='pixmap')
        self.item.paint(painter, None, None)
        painter.drawPixmap.assert_called_once_with(0, 0, 'pixmap')
        painter.drawRect.assert_not_called()
        painter.drawPoint.assert_not_called()

    def test_paint_when_selected_single_selection(self):
        painter = MagicMock()
        self.item.setSelected(True)
        self.item.paint(painter, None, None)
        painter.drawPixmap.assert_called_once()
        painter.drawRect.assert_called_once()
        painter.drawPoint.assert_called()

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

    def test_bottom_right_scale_bounds(self):
        self.view.get_scale = MagicMock(return_value=1)
        self.item.SELECT_RESIZE_SIZE = 10
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=80):
                rect = self.item.bottom_right_scale_bounds
                assert rect.topLeft().x() == 95
                assert rect.topLeft().y() == 75
                assert rect.bottomRight().x() == 105
                assert rect.bottomRight().y() == 85

    def test_bottom_right_rotate_bounds(self):
        self.view.get_scale = MagicMock(return_value=1)
        self.item.SELECT_RESIZE_SIZE = 10
        self.item.SELECT_ROTATE_SIZE = 10
        with patch('beeref.items.BeePixmapItem.width',
                   new_callable=PropertyMock, return_value=100):
            with patch('beeref.items.BeePixmapItem.height',
                       new_callable=PropertyMock, return_value=80):
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
            with patch('beeref.items.BeePixmapItem.width',
                       new_callable=PropertyMock, return_value=100):
                with patch('beeref.items.BeePixmapItem.height',
                           new_callable=PropertyMock, return_value=80):
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
            with patch('beeref.items.BeePixmapItem.width',
                       new_callable=PropertyMock, return_value=100):
                with patch('beeref.items.BeePixmapItem.height',
                           new_callable=PropertyMock, return_value=80):
                    shape = self.item.shape().boundingRect()
                    assert shape.topLeft().x() == 0
                    assert shape.topLeft().y() == 0
                    assert shape.bottomRight().x() == 115
                    assert shape.bottomRight().y() == 95
