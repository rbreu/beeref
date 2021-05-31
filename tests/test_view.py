import os.path
import sqlite3
from unittest.mock import MagicMock, patch, mock_open

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref.config import logfile_name
from beeref.items import BeePixmapItem
from beeref.view import BeeGraphicsView


def test_inits_menu(view, qapp):
    parent = QtWidgets.QMainWindow()
    view = BeeGraphicsView(qapp, parent)
    assert isinstance(view.context_menu, QtWidgets.QMenu)
    assert len(view.actions()) > 0
    assert view.bee_actions
    assert view.bee_actiongroups


@patch('beeref.view.BeeGraphicsView.open_from_file')
def test_init_without_filename(open_file_mock, qapp, commandline_args):
    commandline_args.filename = None
    parent = QtWidgets.QMainWindow()
    view = BeeGraphicsView(qapp, parent)
    open_file_mock.assert_not_called()
    assert view.parent.windowTitle() == 'BeeRef'
    del view


@patch('beeref.view.BeeGraphicsView.open_from_file')
def test_init_with_filename(open_file_mock, view, qapp, commandline_args):
    commandline_args.filename = 'test.bee'
    parent = QtWidgets.QMainWindow()
    view = BeeGraphicsView(qapp, parent)
    open_file_mock.assert_called_once_with('test.bee')
    del view


@patch('beeref.gui.WelcomeOverlay.hide')
def test_on_scene_changed_when_items(hide_mock, view):
    item = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item)
    view.scale(2, 2)
    with patch('beeref.view.BeeGraphicsView.recalc_scene_rect') as r:
        view.on_scene_changed(None)
        r.assert_called_once_with()
        hide_mock.assert_called_once_with()
        assert view.get_scale() == 2


@patch('beeref.gui.WelcomeOverlay.show')
def test_on_scene_changed_when_no_items(show_mock, view):
    view.scale(2, 2)
    with patch('beeref.view.BeeGraphicsView.recalc_scene_rect') as r:
        view.on_scene_changed(None)
        r.assert_called()
        show_mock.assert_called_once_with()
        assert view.get_scale() == 1


def test_get_supported_image_formats_for_reading(view):
    formats = view.get_supported_image_formats(QtGui.QImageReader)
    assert '*.png' in formats
    assert '*.jpg' in formats


def test_clear_scene(view, item):
    view.scene.addItem(item)
    view.scale(2, 2)
    view.translate(123, 456)
    view.filename = 'test.bee'
    view.undo_stack = MagicMock()

    view.clear_scene()
    assert not view.scene.items()
    assert view.transform().isIdentity()
    assert view.filename is None
    view.undo_stack.clear.assert_called_once_with()
    assert view.parent.windowTitle() == 'BeeRef'


def test_reset_previous_transform_when_other_item(view):
    item1 = MagicMock()
    item2 = MagicMock()
    view.previous_transform = {
        'transform': 'foo',
        'toggle_item': item1,
    }
    view.reset_previous_transform(toggle_item=item2)
    assert view.previous_transform is None


def test_reset_previous_transform_when_same_item(view):
    item = MagicMock()
    view.previous_transform = {
        'transform': 'foo',
        'toggle_item': item,
    }
    view.reset_previous_transform(toggle_item=item)
    assert view.previous_transform == {
        'transform': 'foo',
        'toggle_item': item,
    }


@patch('beeref.view.BeeGraphicsView.fitInView')
def test_fit_rect_no_toggle(fit_mock, view):
    rect = QtCore.QRectF(30, 40, 100, 80)
    view.previous_transform = {'toggle_item': MagicMock()}
    view.fit_rect(rect)
    fit_mock.assert_called_with(rect, Qt.AspectRatioMode.KeepAspectRatio)
    assert view.previous_transform is None


@patch('beeref.view.BeeGraphicsView.fitInView')
def test_fit_rect_toggle_when_no_previous(fit_mock, view):
    item = MagicMock()
    view.previous_transform = None
    view.setSceneRect(QtCore.QRectF(-2000, -2000, 4000, 4000))
    rect = QtCore.QRectF(30, 40, 100, 80)
    view.scale(2, 2)
    view.horizontalScrollBar().setValue(-40)
    view.verticalScrollBar().setValue(-50)
    view.fit_rect(rect, toggle_item=item)
    fit_mock.assert_called_with(rect, Qt.AspectRatioMode.KeepAspectRatio)
    assert view.previous_transform['toggle_item'] == item
    assert view.previous_transform['transform'].m11() == 2
    assert isinstance(view.previous_transform['center'], QtCore.QPointF)


@patch('beeref.view.BeeGraphicsView.fitInView')
@patch('beeref.view.BeeGraphicsView.centerOn')
def test_fit_rect_toggle_when_previous(center_mock, fit_mock, view):
    item = MagicMock()
    view.previous_transform = {
        'toggle_item': item,
        'transform': QtGui.QTransform.fromScale(2, 2),
        'center': QtCore.QPointF(30, 40)
    }
    view.setSceneRect(QtCore.QRectF(-2000, -2000, 4000, 4000))
    rect = QtCore.QRectF(30, 40, 100, 80)
    view.fit_rect(rect, toggle_item=item)
    fit_mock.assert_not_called()
    center_mock.assert_called_once_with(QtCore.QPointF(30, 40))
    assert view.get_scale() == 2


@patch('beeref.view.BeeGraphicsView.clear_scene')
def test_open_from_file(clear_mock, view, qtbot):
    root = os.path.dirname(__file__)
    filename = os.path.join(root, 'assets', 'test1item.bee')
    view.on_loading_finished = MagicMock()
    view.open_from_file(filename)
    view.worker.wait()
    qtbot.waitUntil(lambda: view.on_loading_finished.called is True)
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.isSelected() is False
    assert item.pixmap()
    clear_mock.assert_called_once_with()
    view.on_loading_finished.assert_called_once_with(filename, [])


def test_open_from_file_when_error(view, qtbot):
    view.on_loading_finished = MagicMock()
    view.open_from_file('uieauiae')
    view.worker.wait()
    qtbot.waitUntil(lambda: view.on_loading_finished.called is True)
    assert list(view.scene.items()) == []
    view.on_loading_finished.assert_called_once_with(
        'uieauiae', ['unable to open database file'])


@patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName')
def test_on_action_open(dialog_mock, view, qtbot):
    # FIXME: #1
    # Can't check signal handling currently
    root = os.path.dirname(__file__)
    filename = os.path.join(root, 'assets', 'test1item.bee')
    dialog_mock.return_value = (filename, None)
    view.on_loading_finished = MagicMock()
    view.on_action_open()
    qtbot.waitUntil(lambda: view.on_loading_finished.called is True)
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.isSelected() is False
    assert item.pixmap()
    view.on_loading_finished.assert_called_once_with(filename, [])


@patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName')
@patch('beeref.view.BeeGraphicsView.on_action_open')
def test_on_action_open_when_no_filename(dialog_mock, open_mock, view):
    dialog_mock.return_value = (None, None)
    view.on_action_open()
    open_mock.assert_not_called()


@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
def test_on_action_save_as(dialog_mock, view, imgfilename3x3, tmpdir):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    filename = os.path.join(tmpdir, 'test.bee')
    assert os.path.exists(filename) is False
    dialog_mock.return_value = (filename, None)
    view.on_action_save_as()
    view.worker.wait()
    assert os.path.exists(filename) is True


@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
@patch('beeref.view.BeeGraphicsView.do_save')
def test_on_action_save_as_when_no_filename(
        save_mock, dialog_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    dialog_mock.return_value = (None, None)
    view.on_action_save_as()
    save_mock.assert_not_called()


@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
def test_on_action_save_as_filename_doesnt_end_with_bee(
        dialog_mock, view, qtbot, imgfilename3x3, tmpdir):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.on_saving_finished = MagicMock()
    filename = os.path.join(tmpdir, 'test')
    assert os.path.exists(filename) is False
    dialog_mock.return_value = (filename, None)
    view.on_action_save_as()
    qtbot.waitUntil(lambda: view.on_saving_finished.called is True)
    assert os.path.exists(f'{filename}.bee') is True
    view.on_saving_finished.assert_called_once_with(f'{filename}.bee', [])


@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
@patch('beeref.fileio.sql.SQLiteIO.write_data')
def test_on_action_save_as_when_error(
        save_mock, dialog_mock, view, qtbot, imgfilename3x3, tmpdir):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.on_saving_finished = MagicMock()
    filename = os.path.join(tmpdir, 'test.bee')
    assert os.path.exists(filename) is False
    dialog_mock.return_value = (filename, None)
    save_mock.side_effect = sqlite3.Error('foo')
    view.on_action_save_as()
    qtbot.waitUntil(lambda: view.on_saving_finished.called is True)
    view.on_saving_finished.assert_called_once_with(filename, ['foo'])


def test_on_action_save(view, qtbot, imgfilename3x3, tmpdir):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.filename = os.path.join(tmpdir, 'test.bee')
    view.on_saving_finished = MagicMock()
    assert os.path.exists(view.filename) is False
    view.on_action_save()
    qtbot.waitUntil(lambda: view.on_saving_finished.called is True)
    assert os.path.exists(view.filename) is True
    view.on_saving_finished.assert_called_once_with(view.filename, [])


@patch('beeref.view.BeeGraphicsView.on_action_save_as')
def test_on_action_save_when_no_filename(save_as_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.filename = None
    view.on_action_save()
    save_as_mock.assert_called_once_with()


@patch('beeref.gui.HelpDialog.show')
def test_on_action_help(show_mock, view):
    view.on_action_help()
    show_mock.assert_called_once()


@patch('beeref.gui.DebugLogDialog.show')
def test_on_action_debuglog(show_mock, view):
    with patch('builtins.open', mock_open(read_data='log')) as open_mock:
        view.on_action_debuglog()
        show_mock.assert_called_once()
        open_mock.assert_called_once_with(logfile_name())


@patch('beeref.scene.BeeGraphicsScene.clearSelection')
@patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames')
def test_on_action_insert_images(
        dialog_mock, clear_mock, view, imgfilename3x3, qtbot):
    dialog_mock.return_value = ([imgfilename3x3], None)
    view.on_insert_images_finished = MagicMock()
    view.on_action_insert_images()
    qtbot.waitUntil(lambda: view.on_insert_images_finished.called is True)
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.isSelected() is True
    assert item.pixmap()
    clear_mock.assert_called_once_with()
    view.on_insert_images_finished.assert_called_once_with('', [])


@patch('beeref.scene.BeeGraphicsScene.clearSelection')
@patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames')
def test_on_action_insert_images_when_error(
        dialog_mock, clear_mock, view, imgfilename3x3, qtbot):
    dialog_mock.return_value = ([imgfilename3x3, 'iaeiae', 'trntrn'], None)
    view.on_insert_images_finished = MagicMock()
    view.on_action_insert_images()
    qtbot.waitUntil(lambda: view.on_insert_images_finished.called is True)
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.isSelected() is True
    assert item.pixmap()
    clear_mock.assert_called_once_with()
    view.on_insert_images_finished.assert_called_once_with(
        '', ['iaeiae', 'trntrn'])


@patch('PyQt6.QtWidgets.QApplication.clipboard')
def test_on_action_copy(clipboard_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    item.setSelected(True)
    mimedata = QtCore.QMimeData()
    clipboard_mock.return_value.mimeData.return_value = mimedata
    view.on_action_copy()

    clipboard_mock.return_value.setPixmap.assert_called_once()
    view.scene.internal_clipboard == [item]
    assert mimedata.data('beeref/items') == b'1'


@patch('beeref.scene.BeeGraphicsScene.clearSelection')
@patch('PyQt6.QtGui.QClipboard.image')
def test_on_action_paste_external(
        clipboard_mock, clear_mock, view, imgfilename3x3):
    clipboard_mock.return_value = QtGui.QImage(imgfilename3x3)
    view.on_action_paste()
    assert len(view.scene.items()) == 1
    assert view.scene.items()[0].isSelected() is True


@patch('beeref.scene.BeeGraphicsScene.clearSelection')
@patch('PyQt6.QtGui.QClipboard.mimeData')
def test_on_action_paste_internal(mimedata_mock, clear_mock, view):
    mimedata = QtCore.QMimeData()
    mimedata.setData('beeref/items', QtCore.QByteArray.number(1))
    mimedata_mock.return_value = mimedata
    item = BeePixmapItem(QtGui.QImage())
    view.scene.internal_clipboard = [item]
    view.on_action_paste()
    assert len(view.scene.items()) == 1
    assert view.scene.items()[0].isSelected() is True
    clear_mock.assert_called_once_with()


@patch('beeref.scene.BeeGraphicsScene.clearSelection')
@patch('PyQt6.QtGui.QClipboard.image')
def test_on_action_paste_when_empty(clipboard_mock, clear_mock, view):
    clipboard_mock.return_value = QtGui.QImage()
    view.on_action_paste()
    assert len(view.scene.items()) == 0
    clear_mock.assert_not_called()


@patch('beeref.view.BeeGraphicsView.on_action_copy')
def test_on_action_cut(copy_mock, view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    view.on_action_cut()
    copy_mock.assert_called_once_with()
    assert view.scene.items() == []
    assert view.undo_stack.isClean() is False


def test_on_action_show_menubar(view):
    view.toplevel_menus = [QtWidgets.QMenu('Foo')]
    view.on_action_show_menubar(True)
    assert len(view.parent.menuBar().actions()) == 1
    view.on_action_show_menubar(False)
    assert view.parent.menuBar().actions() == []


def test_on_action_delete_items(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    view.on_action_delete_items()
    assert view.scene.items() == []
    assert view.undo_stack.isClean() is False


@patch('PyQt6.QtGui.QUndoStack.isClean', return_value=True)
def test_update_window_title_no_changes_no_filename(clear_mock, view):
    view.filename = None
    view.update_window_title()
    assert view.parent.windowTitle() == 'BeeRef'


@patch('PyQt6.QtGui.QUndoStack.isClean', return_value=False)
def test_update_window_title_changes_no_filename(clear_mock, view):
    view.filename = None
    view.update_window_title()
    assert view.parent.windowTitle() == '[Untitled]* - BeeRef'


@patch('PyQt6.QtGui.QUndoStack.isClean', return_value=True)
def test_update_window_title_no_changes_filename(clear_mock, view):
    view.filename = 'test.bee'
    view.update_window_title()
    assert view.parent.windowTitle() == 'test.bee - BeeRef'


@patch('PyQt6.QtGui.QUndoStack.isClean', return_value=False)
def test_update_window_title_changes_filename(clear_mock, view):
    view.filename = 'test.bee'
    view.update_window_title()
    assert view.parent.windowTitle() == 'test.bee* - BeeRef'


@patch('beeref.view.BeeGraphicsView.recalc_scene_rect')
@patch('beeref.scene.BeeGraphicsScene.on_view_scale_change')
def test_scale(view_scale_mock, recalc_mock, view):
    view.scale(3.3, 3.3)
    view_scale_mock.assert_called_once_with()
    recalc_mock.assert_called_once_with()
    assert view.get_scale() == 3.3


@patch('PyQt6.QtWidgets.QScrollBar.setValue')
def test_pan(scroll_value_mock, view, item):
    view.scene.addItem(item)
    view.pan(QtCore.QPointF(5, 10))
    assert scroll_value_mock.call_count == 2


@patch('PyQt6.QtWidgets.QScrollBar.setValue')
def test_pan_when_no_items(scroll_value_mock, view):
    view.pan(QtCore.QPointF(5, 10))
    scroll_value_mock.assert_not_called()


@patch('beeref.view.BeeGraphicsView.reset_previous_transform')
@patch('beeref.view.BeeGraphicsView.pan')
def test_zoom_in(pan_mock, reset_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.zoom(40, QtCore.QPointF(10, 10))
    assert view.get_scale() == 1.04
    reset_mock.assert_called_once_with()
    pan_mock.assert_called_once_with(QtCore.QPoint(-10, -6))


@patch('beeref.view.BeeGraphicsView.reset_previous_transform')
@patch('beeref.view.BeeGraphicsView.pan')
def test_zoom_in_max_zoom_size(pan_mock, reset_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scale(10000000, 10000000)
    view.scene.addItem(item)
    view.zoom(40, QtCore.QPointF(10, 10))
    assert view.get_scale() == 10000000
    reset_mock.assert_not_called()
    pan_mock.assert_not_called()


@patch('beeref.view.BeeGraphicsView.reset_previous_transform')
@patch('beeref.view.BeeGraphicsView.pan')
def test_zoom_out(pan_mock, reset_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scale(100, 100)
    view.scene.addItem(item)
    view.zoom(-40, QtCore.QPointF(10, 10))
    assert view.get_scale() == 100 / 1.04
    reset_mock.assert_called_once_with()
    pan_mock.assert_called_once_with(QtCore.QPoint(9, 5))


@patch('beeref.view.BeeGraphicsView.reset_previous_transform')
@patch('beeref.view.BeeGraphicsView.pan')
def test_zoom_out_min_zoom_size(pan_mock, reset_mock, view, item):
    view.scene.addItem(item)
    view.zoom(-40, QtCore.QPointF(10, 10))
    assert view.get_scale() == 1
    reset_mock.assert_not_called()
    pan_mock.assert_not_called()


@patch('beeref.view.BeeGraphicsView.reset_previous_transform')
@patch('beeref.view.BeeGraphicsView.pan')
def test_no_items(pan_mock, reset_mock, view, item):
    view.zoom(40, QtCore.QPointF(10, 10))
    assert view.get_scale() == 1
    reset_mock.assert_not_called()
    pan_mock.assert_not_called()


@patch('beeref.view.BeeGraphicsView.reset_previous_transform')
@patch('beeref.view.BeeGraphicsView.pan')
def test_delta_zero(pan_mock, reset_mock, view, item):
    view.scene.addItem(item)
    view.zoom(0, QtCore.QPointF(10, 10))
    assert view.get_scale() == 1
    reset_mock.assert_not_called()
    pan_mock.assert_not_called()


@patch('beeref.view.BeeGraphicsView.zoom')
def test_wheel_event(zoom_mock, view):
    event = MagicMock()
    event.angleDelta.return_value = QtCore.QPointF(0, 40)
    event.position.return_value = QtCore.QPointF(10, 20)
    view.wheelEvent(event)
    zoom_mock.assert_called_once_with(40, QtCore.QPointF(10, 20))
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_zoom(mouse_event_mock, view):
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10, 20)
    event.button.return_value = Qt.MouseButton.MiddleButton
    event.modifiers.return_value = Qt.KeyboardModifier.ControlModifier
    view.mousePressEvent(event)
    assert view.zoom_active is True
    assert view.pan_active is False
    assert view.event_start == QtCore.QPointF(10, 20)
    assert view.event_anchor == QtCore.QPointF(10, 20)
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_pan_middle_drag(mouse_event_mock, view):
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10, 20)
    event.button.return_value = Qt.MouseButton.MiddleButton
    event.modifiers.return_value = None
    view.mousePressEvent(event)
    assert view.pan_active is True
    assert view.zoom_active is False
    assert view.event_start == QtCore.QPointF(10, 20)
    mouse_event_mock.assert_not_called()
    view.cursor() == Qt.CursorShape.ClosedHandCursor
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_pan_alt_left_drag(mouse_event_mock, view):
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10, 20)
    event.button.return_value = Qt.MouseButton.LeftButton
    event.modifiers.return_value = Qt.KeyboardModifier.AltModifier
    view.mousePressEvent(event)
    assert view.pan_active is True
    assert view.zoom_active is False
    assert view.event_start == QtCore.QPointF(10, 20)
    mouse_event_mock.assert_not_called()
    view.cursor() == Qt.CursorShape.ClosedHandCursor
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_unhandled(mouse_event_mock, view):
    event = MagicMock()
    event.button.return_value = Qt.MouseButton.LeftButton
    event.modifiers.return_value = None
    view.mousePressEvent(event)
    assert view.pan_active is False
    assert view.zoom_active is False
    mouse_event_mock.assert_called_once_with(event)
    event.accept.assert_not_called()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
@patch('beeref.view.BeeGraphicsView.pan')
def test_mouse_move_pan(pan_mock, mouse_event_mock, view):
    view.pan_active = True
    view.event_start = QtCore.QPointF(55, 66)
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10, 20)
    view.mouseMoveEvent(event)
    pan_mock.assert_called_once_with(QtCore.QPointF(45, 46))
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
@patch('beeref.view.BeeGraphicsView.zoom')
def test_mouse_move_zoom(zoom_mock, mouse_event_mock, view):
    view.zoom_active = True
    view.event_anchor = QtCore.QPointF(55, 66)
    view.event_start = QtCore.QPointF(10, 20)
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10, 18)
    view.mouseMoveEvent(event)
    zoom_mock.assert_called_once_with(40, QtCore.QPointF(55, 66))
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
def test_mouse_move_unhandled(mouse_event_mock, view):
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10, 20)
    view.mouseMoveEvent(event)
    mouse_event_mock.assert_called_once_with(event)
    event.accept.assert_not_called()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseReleaseEvent')
def test_mouse_release_pan(mouse_event_mock, view):
    event = MagicMock()
    view.pan_active = True
    view.setCursor(Qt.CursorShape.ClosedHandCursor)
    view.mouseReleaseEvent(event)
    mouse_event_mock.assert_not_called()
    assert view.pan_active is False
    event.accept.assert_called_once_with()
    view.cursor() == Qt.CursorShape.ArrowCursor


@patch('PyQt6.QtWidgets.QGraphicsView.mouseReleaseEvent')
def test_mouse_release_zoom(mouse_event_mock, view):
    event = MagicMock()
    view.zoom_active = True
    view.mouseReleaseEvent(event)
    mouse_event_mock.assert_not_called()
    assert view.zoom_active is False
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseReleaseEvent')
def test_mouse_release_unhandled(mouse_event_mock, view):
    event = MagicMock()
    view.mouseReleaseEvent(event)
    mouse_event_mock.assert_called_once_with(event)
    event.accept.assert_not_called()


def test_drag_enter_when_url(view, imgfilename3x3):
    url = QtCore.QUrl()
    url.fromLocalFile(imgfilename3x3)
    mimedata = QtCore.QMimeData()
    mimedata.setUrls([url])
    event = MagicMock()
    event.mimeData.return_value = mimedata

    view.dragEnterEvent(event)
    event.acceptProposedAction.assert_called_once()


def test_drag_enter_when_img(view, imgfilename3x3):
    mimedata = QtCore.QMimeData()
    mimedata.setImageData(QtGui.QImage(imgfilename3x3))
    event = MagicMock()
    event.mimeData.return_value = mimedata

    view.dragEnterEvent(event)
    event.acceptProposedAction.assert_called_once()


def test_drag_enter_when_unsupported(view):
    mimedata = QtCore.QMimeData()
    event = MagicMock()
    event.mimeData.return_value = mimedata

    view.dragEnterEvent(event)
    event.acceptProposedAction.assert_not_called()


def test_drag_move(view):
    event = MagicMock()
    view.dragMoveEvent(event)
    event.acceptProposedAction.assert_called_once()


@patch('beeref.view.BeeGraphicsView.do_insert_images')
def test_drop_when_url(insert_mock, view, imgfilename3x3):
    url = QtCore.QUrl()
    url.fromLocalFile(imgfilename3x3)
    mimedata = QtCore.QMimeData()
    mimedata.setUrls([url])
    event = MagicMock()
    event.mimeData.return_value = mimedata
    event.position.return_value = QtCore.QPointF(10, 20)

    view.dropEvent(event)
    insert_mock.assert_called_once_with([url], QtCore.QPoint(10, 20))


def test_drop_when_img(view, imgfilename3x3):
    mimedata = QtCore.QMimeData()
    mimedata.setImageData(QtGui.QImage(imgfilename3x3))
    event = MagicMock()
    event.mimeData.return_value = mimedata
    event.position.return_value = QtCore.QPointF(10, 20)

    view.dropEvent(event)
    assert len(view.scene.items()) == 1
    assert view.scene.items()[0].isSelected() is True
