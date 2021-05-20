import os.path
import tempfile
from unittest.mock import MagicMock, patch, mock_open

from pytest import mark

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref.config import logfile_name
from beeref.items import BeePixmapItem
from beeref import fileio
from beeref.view import BeeGraphicsView
from .base import BeeTestCase


class ViewBaseTestCase(BeeTestCase):

    def setUp(self):
        config_patcher = patch('beeref.view.commandline_args')
        self.config_mock = config_patcher.start()
        self.config_mock.filename = None
        self.addCleanup(config_patcher.stop)
        self.parent = QtWidgets.QMainWindow()
        self.view = BeeGraphicsView(self.app, self.parent)


class BeeGraphicsViewTestCase(ViewBaseTestCase):

    def setUp(self):
        config_patcher = patch('beeref.view.commandline_args')
        self.config_mock = config_patcher.start()
        self.config_mock.filename = None
        self.addCleanup(config_patcher.stop)
        self.parent = QtWidgets.QMainWindow()
        self.view = BeeGraphicsView(self.app, self.parent)

    def test_inits_menu(self):
        parent = QtWidgets.QMainWindow()
        view = BeeGraphicsView(self.app, parent)
        assert isinstance(view.context_menu, QtWidgets.QMenu)
        assert len(view.actions()) > 0
        assert view.bee_actions
        assert view.bee_actiongroups

    @patch('beeref.view.BeeGraphicsView.open_from_file')
    def test_init_without_filename(self, open_file_mock):
        self.config_mock.filename = None
        parent = QtWidgets.QMainWindow()
        view = BeeGraphicsView(self.app, parent)
        open_file_mock.assert_not_called()
        assert parent.windowTitle() == 'BeeRef'
        del view

    @patch('beeref.view.BeeGraphicsView.open_from_file')
    def test_init_with_filename(self, open_file_mock):
        self.config_mock.filename = 'test.bee'
        parent = QtWidgets.QMainWindow()
        view = BeeGraphicsView(self.app, parent)
        open_file_mock.assert_called_once_with('test.bee')
        del view

    @patch('beeref.gui.WelcomeOverlay.hide')
    def test_on_scene_changed_when_items(self, hide_mock):
        item = BeePixmapItem(QtGui.QImage())
        self.view.scene.addItem(item)
        self.view.scale(2, 2)
        with patch('beeref.view.BeeGraphicsView.recalc_scene_rect') as r:
            self.view.on_scene_changed(None)
            r.assert_called_once_with()
            hide_mock.assert_called_once_with()
            assert self.view.get_scale() == 2

    @patch('beeref.gui.WelcomeOverlay.show')
    def test_on_scene_changed_when_no_items(self, show_mock):
        self.view.scale(2, 2)
        with patch('beeref.view.BeeGraphicsView.recalc_scene_rect') as r:
            self.view.on_scene_changed(None)
            r.assert_called()
            show_mock.assert_called_once_with()
            assert self.view.get_scale() == 1

    def test_get_supported_image_formats_for_reading(self):
        formats = self.view.get_supported_image_formats(QtGui.QImageReader)
        assert '*.png' in formats
        assert '*.jpg' in formats

    def test_clear_scene(self):
        item = BeePixmapItem(QtGui.QImage())
        self.view.scene.addItem(item)
        self.view.scale(2, 2)
        self.view.translate(123, 456)
        self.view.filename = 'test.bee'
        self.view.undo_stack = MagicMock()

        self.view.clear_scene()
        assert not self.view.scene.items()
        assert self.view.transform().isIdentity()
        assert self.view.filename is None
        self.view.undo_stack.clear.assert_called_once_with()
        assert self.parent.windowTitle() == 'BeeRef'

    def test_reset_previous_transform_when_other_item(self):
        item1 = MagicMock()
        item2 = MagicMock()
        self.view.previous_transform = {
            'transform': 'foo',
            'toggle_item': item1,
        }
        self.view.reset_previous_transform(toggle_item=item2)
        assert self.view.previous_transform is None

    def test_reset_previous_transform_when_same_item(self):
        item = MagicMock()
        self.view.previous_transform = {
            'transform': 'foo',
            'toggle_item': item,
        }
        self.view.reset_previous_transform(toggle_item=item)
        assert self.view.previous_transform == {
            'transform': 'foo',
            'toggle_item': item,
        }

    @patch('beeref.view.BeeGraphicsView.fitInView')
    def test_fit_rect_no_toggle(self, fit_mock):
        rect = QtCore.QRectF(30, 40, 100, 80)
        self.view.previous_transform = {'toggle_item': MagicMock()}
        self.view.fit_rect(rect)
        fit_mock.assert_called_with(rect, Qt.AspectRatioMode.KeepAspectRatio)
        assert self.view.previous_transform is None

    @patch('beeref.view.BeeGraphicsView.fitInView')
    def test_fit_rect_toggle_when_no_previous(self, fit_mock):
        item = MagicMock()
        self.view.previous_transform = None
        self.view.setSceneRect(QtCore.QRectF(-2000, -2000, 4000, 4000))
        rect = QtCore.QRectF(30, 40, 100, 80)
        self.view.scale(2, 2)
        self.view.horizontalScrollBar().setValue(-40)
        self.view.verticalScrollBar().setValue(-50)
        self.view.fit_rect(rect, toggle_item=item)
        fit_mock.assert_called_with(rect, Qt.AspectRatioMode.KeepAspectRatio)
        assert self.view.previous_transform['toggle_item'] == item
        assert self.view.previous_transform['transform'].m11() == 2
        assert isinstance(self.view.previous_transform['center'],
                          QtCore.QPointF)

    @patch('beeref.view.BeeGraphicsView.fitInView')
    @patch('beeref.view.BeeGraphicsView.centerOn')
    def test_fit_rect_toggle_when_previous(self, center_mock, fit_mock):
        item = MagicMock()
        self.view.previous_transform = {
            'toggle_item': item,
            'transform': QtGui.QTransform.fromScale(2, 2),
            'center': QtCore.QPointF(30, 40)
        }
        self.view.setSceneRect(QtCore.QRectF(-2000, -2000, 4000, 4000))
        rect = QtCore.QRectF(30, 40, 100, 80)
        self.view.fit_rect(rect, toggle_item=item)
        fit_mock.assert_not_called()
        center_mock.assert_called_once_with(QtCore.QPointF(30, 40))
        assert self.view.get_scale() == 2

    @patch('beeref.view.BeeGraphicsView.clear_scene')
    def test_open_from_file(self, clear_mock):
        root = os.path.dirname(__file__)
        filename = os.path.join(root, 'assets', 'test1item.bee')
        self.view.open_from_file(filename)
        self.view.worker.wait()
        items = self.queue2list(self.view.scene.items_to_add)
        assert len(items) == 1
        item, selected = items[0]
        assert items[0][0].pixmap()
        assert items[0][1] is False
        clear_mock.assert_called_once_with()
        # FIXME: #1
        # Can't check signal handling currently
        # assert self.parent.windowTitle() == 'test1item.bee - BeeRef'

    @patch('PyQt6.QtWidgets.QMessageBox.warning')
    def test_open_from_file_when_error(self, warn_mock):
        # FIXME: #1
        # Can't check signal handling currently
        self.view.open_from_file('uieauiae')
        self.view.worker.wait()
        assert self.view.scene.items_to_add.empty() is True
        assert len(self.view.scene.items()) == 0

    @patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName')
    def test_on_action_open(self, dialog_mock):
        # FIXME: #1
        # Can't check signal handling currently
        root = os.path.dirname(__file__)
        dialog_mock.return_value = (
            os.path.join(root, 'assets', 'test1item.bee'),
            None)
        self.view.on_action_open()
        self.view.worker.wait()
        items = self.queue2list(self.view.scene.items_to_add)
        assert len(items) == 1
        assert items[0][0].pixmap()
        assert items[0][1] is False
        # FIXME: #1
        # Can't check signal handling currently
        # assert self.parent.windowTitle() == 'test1item.bee - BeeRef'

    @patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName')
    @patch('beeref.view.BeeGraphicsView.on_action_open')
    def test_on_action_open_when_no_filename(self, dialog_mock, open_mock):
        dialog_mock.return_value = (None, None)
        self.view.on_action_open()
        open_mock.assert_not_called()

    @patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
    def test_on_action_save_as(self, dialog_mock):
        item = BeePixmapItem(QtGui.QImage(self.imgfilename3x3))
        self.view.scene.addItem(item)
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'test.bee')
            assert os.path.exists(filename) is False
            dialog_mock.return_value = (filename, None)
            self.view.on_action_save_as()
            self.view.worker.wait()
            assert os.path.exists(filename) is True

    @patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
    @patch('beeref.view.BeeGraphicsView.do_save')
    def test_on_action_save_as_when_no_filename(self, save_mock, dialog_mock):
        item = BeePixmapItem(QtGui.QImage(self.imgfilename3x3))
        self.view.scene.addItem(item)
        dialog_mock.return_value = (None, None)
        self.view.on_action_save_as()
        save_mock.assert_not_called()

    @patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
    def test_on_action_save_as_filename_doesnt_end_with_bee(self, dialog_mock):
        item = BeePixmapItem(QtGui.QImage(self.imgfilename3x3))
        self.view.scene.addItem(item)
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'test')
            assert os.path.exists(filename) is False
            dialog_mock.return_value = (filename, None)
            self.view.on_action_save_as()
            self.view.worker.wait()
            assert os.path.exists(f'{filename}.bee') is True

    @mark.skip('needs pytest-qt')
    @patch('PyQt6.QtWidgets.QMessageBox.warning')
    @patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
    @patch('beeref.fileio.save')
    def test_on_action_save_as_when_error(
            self, save_mock, dialog_mock, warn_mock):
        item = BeePixmapItem(QtGui.QImage(self.imgfilename3x3))
        self.view.scene.addItem(item)
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'test.bee')
            assert os.path.exists(filename) is False
            dialog_mock.return_value = (filename, None)
            save_mock.side_effect = fileio.BeeFileIOError('foo', 'test.bee')
            self.view.on_action_save_as()
            warn_mock.assert_called_once()
            assert os.path.exists(filename) is False

    def test_on_action_save(self):
        item = BeePixmapItem(QtGui.QImage(self.imgfilename3x3))
        self.view.scene.addItem(item)
        with tempfile.TemporaryDirectory() as tmpdir:
            self.view.filename = os.path.join(tmpdir, 'test.bee')
            assert os.path.exists(self.view.filename) is False
            self.view.on_action_save()
            self.view.worker.wait()
            assert os.path.exists(self.view.filename) is True

    @patch('beeref.view.BeeGraphicsView.on_action_save_as')
    def test_on_action_save_when_no_filename(self, save_as_mock):
        item = BeePixmapItem(QtGui.QImage(self.imgfilename3x3))
        self.view.scene.addItem(item)
        self.view.filename = None
        self.view.on_action_save()
        save_as_mock.assert_called_once_with()

    @patch('beeref.gui.HelpDialog.show')
    def test_on_action_help(self, show_mock):
        self.view.on_action_help()
        show_mock.assert_called_once()

    @patch('beeref.gui.DebugLogDialog.show')
    def test_on_action_debuglog(self, show_mock):
        with patch('builtins.open', mock_open(read_data='log')) as open_mock:
            self.view.on_action_debuglog()
            show_mock.assert_called_once()
            open_mock.assert_called_once_with(logfile_name)

    @patch('beeref.scene.BeeGraphicsScene.clearSelection')
    @patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames')
    def test_on_action_insert_images(self, dialog_mock, clear_mock):
        # FIXME: #1
        # Can't check signal handling currently
        dialog_mock.return_value = ([self.imgfilename3x3], None)
        self.view.on_action_insert_images()
        self.view.worker.wait()
        items = self.queue2list(self.view.scene.items_to_add)
        assert len(items) == 1
        assert items[0][0].pixmap()
        assert items[0][1] is True
        clear_mock.assert_called_once_with()

    @patch('beeref.scene.BeeGraphicsScene.clearSelection')
    @patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames')
    def test_on_action_insert_images_when_error(self, dialog_mock, clear_mock):
        # FIXME: #1
        # Can't check signal handling currently
        dialog_mock.return_value = (
            [self.imgfilename3x3, 'iaeiae', 'trntrn'], None)
        self.view.on_action_insert_images()
        self.view.worker.wait()
        items = self.queue2list(self.view.scene.items_to_add)
        assert len(items) == 1
        assert items[0][0].pixmap()
        assert items[0][1] is True
        clear_mock.assert_called_once_with()

    @patch('PyQt6.QtWidgets.QApplication.clipboard')
    def test_on_action_copy(self, clipboard_mock):
        item = BeePixmapItem(QtGui.QImage(self.imgfilename3x3))
        self.view.scene.addItem(item)
        item.setSelected(True)
        mimedata = QtCore.QMimeData()
        clipboard_mock.return_value.mimeData.return_value = mimedata
        self.view.on_action_copy()

        clipboard_mock.return_value.setPixmap.assert_called_once()
        self.view.scene.internal_clipboard == [item]
        assert mimedata.data('beeref/items') == b'1'

    @patch('beeref.scene.BeeGraphicsScene.clearSelection')
    @patch('PyQt6.QtGui.QClipboard.image')
    def test_on_action_paste_external(self, clipboard_mock, clear_mock):
        clipboard_mock.return_value = QtGui.QImage(self.imgfilename3x3)
        self.view.on_action_paste()
        assert len(self.view.scene.items()) == 1
        assert self.view.scene.items()[0].isSelected() is True

    @patch('beeref.scene.BeeGraphicsScene.clearSelection')
    @patch('PyQt6.QtGui.QClipboard.mimeData')
    def test_on_action_paste_internal(self, mimedata_mock, clear_mock):
        mimedata = QtCore.QMimeData()
        mimedata.setData('beeref/items', QtCore.QByteArray.number(1))
        mimedata_mock.return_value = mimedata
        item = BeePixmapItem(QtGui.QImage())
        self.view.scene.internal_clipboard = [item]
        self.view.on_action_paste()
        assert len(self.view.scene.items()) == 1
        assert self.view.scene.items()[0].isSelected() is True
        clear_mock.assert_called_once_with()

    @patch('beeref.scene.BeeGraphicsScene.clearSelection')
    @patch('PyQt6.QtGui.QClipboard.image')
    def test_on_action_paste_when_empty(self, clipboard_mock, clear_mock):
        clipboard_mock.return_value = QtGui.QImage()
        self.view.on_action_paste()
        assert len(self.view.scene.items()) == 0
        clear_mock.assert_not_called()

    @patch('beeref.view.BeeGraphicsView.on_action_copy')
    def test_on_action_cut(self, copy_mock):
        item = BeePixmapItem(QtGui.QImage())
        self.view.scene.addItem(item)
        item.setSelected(True)
        self.view.on_action_cut()
        copy_mock.assert_called_once_with()
        assert self.view.scene.items() == []
        assert self.view.undo_stack.isClean() is False

    def test_on_action_show_menubar(self):
        self.view.toplevel_menus = [QtWidgets.QMenu('Foo')]
        self.view.on_action_show_menubar(True)
        assert len(self.view.parent().menuBar().actions()) == 1
        self.view.on_action_show_menubar(False)
        assert self.view.parent().menuBar().actions() == []

    def test_on_action_delete_items(self):
        item = BeePixmapItem(QtGui.QImage())
        self.view.scene.addItem(item)
        item.setSelected(True)
        self.view.on_action_delete_items()
        assert self.view.scene.items() == []
        assert self.view.undo_stack.isClean() is False


class UpdateWindowTitleTestCase(ViewBaseTestCase):

    @patch('PyQt6.QtGui.QUndoStack.isClean', return_value=True)
    def test_update_window_title_no_changes_no_filename(self, clear_mock):
        self.view.filename = None
        self.view.update_window_title()
        assert self.parent.windowTitle() == 'BeeRef'

    @patch('PyQt6.QtGui.QUndoStack.isClean', return_value=False)
    def test_update_window_title_changes_no_filename(self, clear_mock):
        self.view.filename = None
        self.view.update_window_title()
        assert self.parent.windowTitle() == '[Untitled]* - BeeRef'

    @patch('PyQt6.QtGui.QUndoStack.isClean', return_value=True)
    def test_update_window_title_no_changes_filename(self, clear_mock):
        self.view.filename = 'test.bee'
        self.view.update_window_title()
        assert self.parent.windowTitle() == 'test.bee - BeeRef'

    @patch('PyQt6.QtGui.QUndoStack.isClean', return_value=False)
    def test_update_window_title_changes_filename(self, clear_mock):
        self.view.filename = 'test.bee'
        self.view.update_window_title()
        assert self.parent.windowTitle() == 'test.bee* - BeeRef'

    @patch('beeref.view.BeeGraphicsView.recalc_scene_rect')
    @patch('beeref.scene.BeeGraphicsScene.on_view_scale_change')
    def test_scale(self, view_scale_mock, recalc_mock):
        self.view.scale(3.3, 3.3)
        view_scale_mock.assert_called_once_with()
        recalc_mock.assert_called_once_with()
        assert self.view.get_scale() == 3.3

    @patch('PyQt6.QtWidgets.QScrollBar.setValue')
    def test_pan(self, scroll_value_mock):
        item = BeePixmapItem(QtGui.QImage())
        self.view.scene.addItem(item)
        self.view.pan(QtCore.QPointF(5, 10))
        assert scroll_value_mock.call_count == 2

    @patch('PyQt6.QtWidgets.QScrollBar.setValue')
    def test_pan_when_no_items(self, scroll_value_mock):
        self.view.pan(QtCore.QPointF(5, 10))
        scroll_value_mock.assert_not_called()


class ZoomTestCase(ViewBaseTestCase):

    def setUp(self):
        super().setUp()
        pan_patcher = patch('beeref.view.BeeGraphicsView.pan')
        self.pan_mock = pan_patcher.start()
        self.addCleanup(pan_patcher.stop)
        reset_patcher = patch(
            'beeref.view.BeeGraphicsView.reset_previous_transform')
        self.reset_mock = reset_patcher.start()
        self.addCleanup(reset_patcher.stop)
        self.item = BeePixmapItem(QtGui.QImage(self.imgfilename3x3))

    def test_zoom_in(self):
        self.view.scene.addItem(self.item)
        self.view.zoom(40, QtCore.QPointF(10, 10))
        assert self.view.get_scale() == 1.04
        self.reset_mock.assert_called_once_with()
        self.pan_mock.assert_called_once_with(QtCore.QPoint(-52, -15))

    def test_zoom_in_max_zoom_size(self):
        self.view.scale(10000000, 10000000)
        self.view.scene.addItem(self.item)
        self.view.zoom(40, QtCore.QPointF(10, 10))
        assert self.view.get_scale() == 10000000
        self.reset_mock.assert_not_called()
        self.pan_mock.assert_not_called()

    def test_zoom_out(self):
        self.view.scale(100, 100)
        self.view.scene.addItem(self.item)
        self.view.zoom(-40, QtCore.QPointF(10, 10))
        assert self.view.get_scale() == 100 / 1.04
        self.reset_mock.assert_called_once_with()
        self.pan_mock.assert_called_once_with(QtCore.QPoint(49, 14))

    def test_zoom_out_min_zoom_size(self):
        self.view.scene.addItem(self.item)
        self.view.zoom(-40, QtCore.QPointF(10, 10))
        assert self.view.get_scale() == 1
        self.reset_mock.assert_not_called()
        self.pan_mock.assert_not_called()

    def test_no_items(self):
        self.view.zoom(40, QtCore.QPointF(10, 10))
        assert self.view.get_scale() == 1
        self.reset_mock.assert_not_called()
        self.pan_mock.assert_not_called()

    def test_delta_zero(self):
        self.view.scene.addItem(self.item)
        self.view.zoom(0, QtCore.QPointF(10, 10))
        assert self.view.get_scale() == 1
        self.reset_mock.assert_not_called()
        self.pan_mock.assert_not_called()


class MouseEventsTestCase(ViewBaseTestCase):

    def setUp(self):
        super().setUp()
        self.event = MagicMock()

    @patch('beeref.view.BeeGraphicsView.zoom')
    def test_wheel_event(self, zoom_mock):
        self.event.angleDelta.return_value = QtCore.QPointF(0, 40)
        self.event.position.return_value = QtCore.QPointF(10, 20)
        self.view.wheelEvent(self.event)
        zoom_mock.assert_called_once_with(40, QtCore.QPointF(10, 20))
        self.event.accept.assert_called_once_with()

    @patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
    def test_mouse_press_zoom(self, mouse_event_mock):
        self.event.position.return_value = QtCore.QPointF(10, 20)
        self.event.button.return_value = Qt.MouseButton.MiddleButton
        self.event.modifiers.return_value = Qt.KeyboardModifier.ControlModifier
        self.view.mousePressEvent(self.event)
        assert self.view.zoom_active is True
        assert self.view.pan_active is False
        assert self.view.event_start == QtCore.QPointF(10, 20)
        assert self.view.event_anchor == QtCore.QPointF(10, 20)
        mouse_event_mock.assert_not_called()
        self.event.accept.assert_called_once_with()

    @patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
    def test_mouse_press_pan_middle_drag(self, mouse_event_mock):
        self.event.position.return_value = QtCore.QPointF(10, 20)
        self.event.button.return_value = Qt.MouseButton.MiddleButton
        self.event.modifiers.return_value = None
        self.view.mousePressEvent(self.event)
        assert self.view.pan_active is True
        assert self.view.zoom_active is False
        assert self.view.event_start == QtCore.QPointF(10, 20)
        mouse_event_mock.assert_not_called()
        self.view.cursor() == Qt.CursorShape.ClosedHandCursor
        self.event.accept.assert_called_once_with()

    @patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
    def test_mouse_press_pan_alt_left_drag(self, mouse_event_mock):
        self.event.position.return_value = QtCore.QPointF(10, 20)
        self.event.button.return_value = Qt.MouseButton.LeftButton
        self.event.modifiers.return_value = Qt.KeyboardModifier.AltModifier
        self.view.mousePressEvent(self.event)
        assert self.view.pan_active is True
        assert self.view.zoom_active is False
        assert self.view.event_start == QtCore.QPointF(10, 20)
        mouse_event_mock.assert_not_called()
        self.view.cursor() == Qt.CursorShape.ClosedHandCursor
        self.event.accept.assert_called_once_with()

    @patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
    def test_mouse_press_unhandled(self, mouse_event_mock):
        self.event.button.return_value = Qt.MouseButton.LeftButton
        self.event.modifiers.return_value = None
        self.view.mousePressEvent(self.event)
        assert self.view.pan_active is False
        assert self.view.zoom_active is False
        mouse_event_mock.assert_called_once_with(self.event)
        self.event.accept.assert_not_called()

    @patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
    @patch('beeref.view.BeeGraphicsView.pan')
    def test_mouse_move_pan(self, pan_mock, mouse_event_mock):
        self.view.pan_active = True
        self.view.event_start = QtCore.QPointF(55, 66)
        self.event.position.return_value = QtCore.QPointF(10, 20)
        self.view.mouseMoveEvent(self.event)
        pan_mock.assert_called_once_with(QtCore.QPointF(45, 46))
        mouse_event_mock.assert_not_called()
        self.event.accept.assert_called_once_with()

    @patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
    @patch('beeref.view.BeeGraphicsView.zoom')
    def test_mouse_move_zoom(self, zoom_mock, mouse_event_mock):
        self.view.zoom_active = True
        self.view.event_anchor = QtCore.QPointF(55, 66)
        self.view.event_start = QtCore.QPointF(10, 20)
        self.event.position.return_value = QtCore.QPointF(10, 18)
        self.view.mouseMoveEvent(self.event)
        zoom_mock.assert_called_once_with(40, QtCore.QPointF(55, 66))
        mouse_event_mock.assert_not_called()
        self.event.accept.assert_called_once_with()

    @patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
    def test_mouse_move_unhandled(self, mouse_event_mock):
        self.event.position.return_value = QtCore.QPointF(10, 20)
        self.view.mouseMoveEvent(self.event)
        mouse_event_mock.assert_called_once_with(self.event)
        self.event.accept.assert_not_called()

    @patch('PyQt6.QtWidgets.QGraphicsView.mouseReleaseEvent')
    def test_mouse_release_pan(self, mouse_event_mock):
        self.view.pan_active = True
        self.view.setCursor(Qt.CursorShape.ClosedHandCursor)
        self.view.mouseReleaseEvent(self.event)
        mouse_event_mock.assert_not_called()
        assert self.view.pan_active is False
        self.event.accept.assert_called_once_with()
        self.view.cursor() == Qt.CursorShape.ArrowCursor

    @patch('PyQt6.QtWidgets.QGraphicsView.mouseReleaseEvent')
    def test_mouse_release_zoom(self, mouse_event_mock):
        self.view.zoom_active = True
        self.view.mouseReleaseEvent(self.event)
        mouse_event_mock.assert_not_called()
        assert self.view.zoom_active is False
        self.event.accept.assert_called_once_with()

    @patch('PyQt6.QtWidgets.QGraphicsView.mouseReleaseEvent')
    def test_mouse_release_unhandled(self, mouse_event_mock):
        self.view.mouseReleaseEvent(self.event)
        mouse_event_mock.assert_called_once_with(self.event)
        self.event.accept.assert_not_called()


class DragDropTestCase(ViewBaseTestCase):

    def setUp(self):
        super().setUp()
        self.event = MagicMock()

    def test_drag_enter_when_url(self):
        url = QtCore.QUrl()
        url.fromLocalFile(self.imgfilename3x3)
        mimedata = QtCore.QMimeData()
        mimedata.setUrls([url])
        self.event.mimeData.return_value = mimedata

        self.view.dragEnterEvent(self.event)
        self.event.acceptProposedAction.assert_called_once()

    def test_drag_enter_when_img(self):
        mimedata = QtCore.QMimeData()
        mimedata.setImageData(QtGui.QImage(self.imgfilename3x3))
        self.event.mimeData.return_value = mimedata

        self.view.dragEnterEvent(self.event)
        self.event.acceptProposedAction.assert_called_once()

    def test_drag_enter_when_unsupported(self):
        mimedata = QtCore.QMimeData()
        self.event.mimeData.return_value = mimedata

        self.view.dragEnterEvent(self.event)
        self.event.acceptProposedAction.assert_not_called()

    def test_drag_move(self):
        self.view.dragMoveEvent(self.event)
        self.event.acceptProposedAction.assert_called_once()

    @patch('beeref.view.BeeGraphicsView.do_insert_images')
    def test_drop_when_url(self, insert_mock):
        url = QtCore.QUrl()
        url.fromLocalFile(self.imgfilename3x3)
        mimedata = QtCore.QMimeData()
        mimedata.setUrls([url])
        self.event.mimeData.return_value = mimedata
        self.event.position.return_value = QtCore.QPointF(10, 20)

        self.view.dropEvent(self.event)
        insert_mock.assert_called_once_with([url], QtCore.QPoint(10, 20))

    def test_drop_when_img(self):
        mimedata = QtCore.QMimeData()
        mimedata.setImageData(QtGui.QImage(self.imgfilename3x3))
        self.event.mimeData.return_value = mimedata
        self.event.position.return_value = QtCore.QPointF(10, 20)

        self.view.dropEvent(self.event)
        assert len(self.view.scene.items()) == 1
        assert self.view.scene.items()[0].isSelected() is True
