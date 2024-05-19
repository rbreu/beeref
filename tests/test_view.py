import os.path
from pathlib import Path
import shutil
import sqlite3
from unittest.mock import MagicMock, patch, mock_open

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref import widgets
from beeref.actions import actions
from beeref.config import logfile_name
from beeref.items import BeePixmapItem, BeeTextItem
from beeref.view import BeeGraphicsView


def test_inits_menu(qapp):
    parent = QtWidgets.QMainWindow()
    view = BeeGraphicsView(qapp, parent)
    assert isinstance(view.context_menu, QtWidgets.QMenu)
    assert len(view.actions()) > 0
    assert view.actions()
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
def test_init_with_filename(open_file_mock, qapp, commandline_args):
    commandline_args.filename = 'test.bee'
    parent = QtWidgets.QMainWindow()
    view = BeeGraphicsView(qapp, parent)
    open_file_mock.assert_called_once_with('test.bee')
    del view


@patch('beeref.widgets.welcome_overlay.WelcomeOverlay.hide')
def test_on_scene_changed_when_items(hide_mock, view):
    item = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item)
    view.scale(2, 2)
    with patch('beeref.view.BeeGraphicsView.recalc_scene_rect') as r:
        view.on_scene_changed(None)
        r.assert_called_once_with()
        hide_mock.assert_called_once_with()
        assert view.get_scale() == 2


@patch('beeref.widgets.welcome_overlay.WelcomeOverlay.show')
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
    view.scene.internal_clipboard.append(item)
    view.scale(2, 2)
    view.translate(123, 456)
    view.filename = 'test.bee'
    view.undo_stack = MagicMock()

    view.clear_scene()
    assert not view.scene.items()
    assert view.scene.internal_clipboard == []
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
    view.cancel_active_modes = MagicMock()

    view.on_action_open()
    qtbot.waitUntil(lambda: view.on_loading_finished.called is True)
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.isSelected() is False
    assert item.pixmap()
    view.on_loading_finished.assert_called_once_with(filename, [])
    view.cancel_active_modes.assert_called_with()


@patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName')
@patch('beeref.view.BeeGraphicsView.open_from_file')
def test_on_action_open_when_no_filename(open_mock, dialog_mock, view):
    dialog_mock.return_value = (None, None)
    view.cancel_active_modes = MagicMock()
    view.on_action_open()
    open_mock.assert_not_called()
    view.cancel_active_modes.assert_called_once_with()


@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
def test_on_action_save_as(dialog_mock, view, imgfilename3x3, tmpdir):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.cancel_active_modes = MagicMock()
    filename = os.path.join(tmpdir, 'test.bee')
    assert os.path.exists(filename) is False
    dialog_mock.return_value = (filename, None)
    view.on_action_save_as()
    view.worker.wait()
    assert os.path.exists(filename) is True
    view.cancel_active_modes.assert_called_once_with()


@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
@patch('beeref.view.BeeGraphicsView.do_save')
def test_on_action_save_as_when_no_filename(
        save_mock, dialog_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.cancel_active_modes = MagicMock()
    dialog_mock.return_value = (None, None)
    view.on_action_save_as()
    save_mock.assert_not_called()
    view.cancel_active_modes.assert_called_once_with()


@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
def test_on_action_save_as_filename_doesnt_end_with_bee(
        dialog_mock, view, qtbot, imgfilename3x3, tmpdir):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.cancel_active_modes = MagicMock()
    view.on_saving_finished = MagicMock()
    filename = os.path.join(tmpdir, 'test')
    assert os.path.exists(filename) is False
    dialog_mock.return_value = (filename, None)
    view.on_action_save_as()
    qtbot.waitUntil(lambda: view.on_saving_finished.called is True)
    assert os.path.exists(f'{filename}.bee') is True
    view.on_saving_finished.assert_called_once_with(f'{filename}.bee', [])
    view.cancel_active_modes.assert_called_once_with()


@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
@patch('beeref.fileio.sql.SQLiteIO.write_data')
def test_on_action_save_as_when_error(
        save_mock, dialog_mock, view, qtbot, imgfilename3x3, tmpdir):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.on_saving_finished = MagicMock()
    view.cancel_active_modes = MagicMock()
    filename = os.path.join(tmpdir, 'test.bee')
    dialog_mock.return_value = (filename, None)
    save_mock.side_effect = sqlite3.Error('foo')
    view.on_action_save_as()
    qtbot.waitUntil(lambda: view.on_saving_finished.called is True)
    view.on_saving_finished.assert_called_once_with(filename, ['foo'])
    view.cancel_active_modes.assert_called_once_with()


def test_on_action_save(view, qtbot, imgfilename3x3, tmpdir):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.cancel_active_modes = MagicMock()
    view.filename = os.path.join(tmpdir, 'test.bee')
    root = os.path.dirname(__file__)
    shutil.copyfile(os.path.join(root, 'assets', 'test1item.bee'),
                    view.filename)
    view.on_saving_finished = MagicMock()
    view.on_action_save()
    qtbot.waitUntil(lambda: view.on_saving_finished.called is True)
    assert os.path.exists(view.filename) is True
    view.on_saving_finished.assert_called_once_with(view.filename, [])
    view.cancel_active_modes.assert_called_once_with()


@patch('beeref.view.BeeGraphicsView.on_action_save_as')
def test_on_action_save_when_no_filename(save_as_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.cancel_active_modes = MagicMock()
    view.filename = None
    view.on_action_save()
    save_as_mock.assert_called_once_with()
    view.cancel_active_modes.assert_called_once_with()


@patch('beeref.widgets.SceneToPixmapExporterDialog.exec')
@patch('beeref.widgets.SceneToPixmapExporterDialog.value')
@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
def test_on_action_export_scene(
        file_mock, value_mock, exec_mock, view, tmpdir, qtbot):
    item = BeeTextItem('foo')
    view.scene.addItem(item)
    filename = os.path.join(tmpdir, 'test.png')
    assert os.path.exists(filename) is False
    file_mock.return_value = (filename, None)
    exec_mock.return_value = 1
    value_mock.return_value = QtCore.QSize(100, 100)
    view.on_export_finished = MagicMock()

    view.on_action_export_scene()
    qtbot.waitUntil(lambda: view.on_export_finished.called is True)
    view.on_export_finished.assert_called_once_with(filename, [])
    img = QtGui.QImage(filename)
    assert img.size() == QtCore.QSize(100, 100)


@patch('beeref.widgets.SceneToPixmapExporterDialog.exec')
@patch('beeref.widgets.SceneToPixmapExporterDialog.value')
@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
def test_on_action_export_scene_no_file_extension(
        file_mock, value_mock, exec_mock, view, tmpdir, qtbot):
    item = BeeTextItem('foo')
    view.scene.addItem(item)
    filename = os.path.join(tmpdir, 'test')
    assert os.path.exists(filename) is False
    file_mock.return_value = (filename, 'PNG (*.png)')
    exec_mock.return_value = 1
    value_mock.return_value = QtCore.QSize(100, 100)
    view.on_export_finished = MagicMock()

    view.on_action_export_scene()
    qtbot.waitUntil(lambda: view.on_export_finished.called is True)
    view.on_export_finished.assert_called_once_with(f'{filename}.png', [])
    img = QtGui.QImage(f'{filename}.png')
    assert img.size() == QtCore.QSize(100, 100)


@patch('beeref.widgets.SceneToPixmapExporterDialog.exec')
@patch('beeref.widgets.SceneToPixmapExporterDialog.value')
@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
def test_on_action_export_scene_no_filename(
        file_mock, value_mock, exec_mock, view):
    item = BeeTextItem('foo')
    view.scene.addItem(item)
    file_mock.return_value = (None, None)
    view.on_export_finished = MagicMock()

    view.on_action_export_scene()
    exec_mock.assert_not_called()
    value_mock.assert_not_called()
    view.on_export_finished.assert_not_called()


@patch('beeref.widgets.SceneToPixmapExporterDialog.exec')
@patch('beeref.widgets.SceneToPixmapExporterDialog.value')
@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
def test_on_action_export_scene_settings_input_canceled(
        file_mock, value_mock, exec_mock, view, tmpdir):
    item = BeeTextItem('foo')
    view.scene.addItem(item)
    filename = os.path.join(tmpdir, 'test.png')
    assert os.path.exists(filename) is False
    file_mock.return_value = (filename, None)
    exec_mock.return_value = 0
    view.on_action_export_scene()
    value_mock.assert_not_called()
    assert os.path.exists(filename) is False


@patch('PyQt6.QtWidgets.QFileDialog.getExistingDirectory')
def test_on_action_export_images(
        dir_mock, view, tmpdir, qtbot, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    dir_mock.return_value = tmpdir
    view.on_export_finished = MagicMock()

    view.on_action_export_images()
    qtbot.waitUntil(lambda: view.on_export_finished.called is True)
    view.on_export_finished.assert_called_once_with(tmpdir, [])
    assert os.path.exists(os.path.join(tmpdir, '0001.png'))


@patch('PyQt6.QtWidgets.QFileDialog.getExistingDirectory')
def test_on_action_export_images_no_dirname(
        dir_mock, view, tmpdir, qtbot, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    dir_mock.return_value = None
    view.on_export_finished = MagicMock()

    view.on_action_export_images()
    view.on_export_finished.assert_not_called()
    assert os.path.exists(os.path.join(tmpdir, '0001.png')) is False


@patch('beeref.widgets.ExportImagesFileExistsDialog.exec',
       return_value=QtWidgets.QDialog.DialogCode.Accepted)
@patch('beeref.widgets.ExportImagesFileExistsDialog.get_answer',
       return_value='overwrite')
@patch('PyQt6.QtWidgets.QFileDialog.getExistingDirectory')
def test_on_action_export_images_file_exists_overwrite(
        dir_mock, answer_mock, exec_mock, view, tmpdir, qtbot, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    dir_mock.return_value = tmpdir
    view.on_export_finished = MagicMock()

    imgfilename = Path(tmpdir) / '0001.png'
    imgfilename.write_text('foo')

    view.on_action_export_images()
    qtbot.waitUntil(lambda: view.on_export_finished.called is True)
    view.on_export_finished.assert_called_once_with(tmpdir, [])
    answer_mock.assert_called_once_with()
    exec_mock.assert_called_once_with()
    imgfilename.read_bytes().startswith(b'\x89PNG')


@patch('beeref.widgets.ExportImagesFileExistsDialog.exec',
       return_value=QtWidgets.QDialog.DialogCode.Accepted)
@patch('beeref.widgets.ExportImagesFileExistsDialog.get_answer',
       return_value='skip')
@patch('PyQt6.QtWidgets.QFileDialog.getExistingDirectory')
def test_on_action_export_images_file_exists_skip(
        dir_mock, answer_mock, exec_mock, view, tmpdir, qtbot, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    dir_mock.return_value = tmpdir
    view.on_export_finished = MagicMock()
    imgfilename = Path(tmpdir) / '0001.png'
    imgfilename.write_text('foo')

    view.on_action_export_images()
    qtbot.waitUntil(lambda: view.on_export_finished.called is True)
    view.on_export_finished.assert_called_once_with(tmpdir, [])
    answer_mock.assert_called_once_with()
    exec_mock.assert_called_once_with()
    imgfilename.read_text() == 'foo'


@patch('beeref.widgets.ExportImagesFileExistsDialog.exec',
       return_value=QtWidgets.QDialog.DialogCode.Rejected)
@patch('beeref.widgets.ExportImagesFileExistsDialog.get_answer',
       return_value='skip')
@patch('PyQt6.QtWidgets.QFileDialog.getExistingDirectory')
def test_on_action_export_images_file_exists_canceled(
        dir_mock, answer_mock, exec_mock, view, tmpdir, qtbot, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    dir_mock.return_value = tmpdir
    view.on_export_finished = MagicMock()
    imgfilename = Path(tmpdir) / '0001.png'
    imgfilename.write_text('foo')

    view.on_action_export_images()
    qtbot.waitUntil(lambda: exec_mock.called is True)
    view.on_export_finished.assert_not_called()
    answer_mock.assert_not_called()
    imgfilename.read_text() == 'foo'


@patch('beeref.widgets.settings.SettingsDialog.show')
def test_on_action_settings(show_mock, view):
    view.on_action_settings()
    show_mock.assert_called_once()


@patch('beeref.widgets.controls.ControlsDialog.show')
def test_on_action_keyboard_settings(show_mock, view):
    view.on_action_keyboard_settings()
    show_mock.assert_called_once()


@patch('beeref.widgets.HelpDialog.show')
def test_on_action_help(show_mock, view):
    view.on_action_help()
    show_mock.assert_called_once()


@patch('beeref.widgets.DebugLogDialog.show')
def test_on_action_debuglog(show_mock, view):
    with patch('builtins.open', mock_open(read_data='log')) as open_mock:
        view.on_action_debuglog()
        show_mock.assert_called_once()
        open_mock.assert_called_once_with(logfile_name())


@patch('beeref.scene.BeeGraphicsScene.clearSelection')
@patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames')
def test_on_action_insert_images_new_scene(
        dialog_mock, clear_mock, view, imgfilename3x3, qtbot):
    dialog_mock.return_value = ([imgfilename3x3], None)
    view.on_insert_images_finished = MagicMock()
    view.cancel_active_modes = MagicMock()
    view.on_action_insert_images()
    qtbot.waitUntil(lambda: view.on_insert_images_finished.called is True)
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.isSelected() is True
    assert item.pixmap()
    clear_mock.assert_called_once_with()
    view.on_insert_images_finished.assert_called_once_with(True, '', [])
    view.cancel_active_modes.assert_called_once_with()


@patch('beeref.scene.BeeGraphicsScene.clearSelection')
@patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames')
def test_on_action_insert_images_existing_scene(
        dialog_mock, clear_mock, view, imgfilename3x3, qtbot, item):
    view.scene.addItem(item)
    dialog_mock.return_value = ([imgfilename3x3], None)
    view.on_insert_images_finished = MagicMock()
    view.cancel_active_modes = MagicMock()
    view.on_action_insert_images()
    qtbot.waitUntil(lambda: view.on_insert_images_finished.called is True)
    assert len(view.scene.items()) == 2
    item = view.scene.items()[0]
    assert item.isSelected() is True
    assert item.pixmap()
    clear_mock.assert_called_once_with()
    view.on_insert_images_finished.assert_called_once_with(False, '', [])
    view.cancel_active_modes.assert_called_once_with()


@patch('beeref.scene.BeeGraphicsScene.clearSelection')
@patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames')
def test_on_action_insert_images_when_error(
        dialog_mock, clear_mock, view, imgfilename3x3, qtbot):
    dialog_mock.return_value = ([imgfilename3x3, 'iaeiae', 'trntrn'], None)
    view.on_insert_images_finished = MagicMock()
    view.cancel_active_modes = MagicMock()
    view.on_action_insert_images()
    qtbot.waitUntil(lambda: view.on_insert_images_finished.called is True)
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.isSelected() is True
    assert item.pixmap()
    clear_mock.assert_called_once_with()
    view.on_insert_images_finished.assert_called_once_with(
        True, '', ['iaeiae', 'trntrn'])
    view.cancel_active_modes.assert_called_once_with()


@patch('beeref.scene.BeeGraphicsScene.clearSelection')
def test_on_action_insert_text(clear_mock, view):
    view.cancel_active_modes = MagicMock()
    view.on_action_insert_text()
    clear_mock.assert_called_once_with()
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.toPlainText() == 'Text'
    assert item.isSelected() is True
    view.cancel_active_modes.assert_called_once_with()


@patch('PyQt6.QtWidgets.QApplication.clipboard')
def test_on_action_copy_image(clipboard_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.cancel_active_modes = MagicMock()
    item.setSelected(True)
    mimedata = QtCore.QMimeData()
    clipboard_mock.return_value.mimeData.return_value = mimedata
    view.on_action_copy()

    clipboard_mock.return_value.setPixmap.assert_called_once()
    view.scene.internal_clipboard == [item]
    assert mimedata.data('beeref/items') == b'1'
    view.cancel_active_modes.assert_called_once_with()


@patch('PyQt6.QtWidgets.QApplication.clipboard')
def test_on_action_copy_text(clipboard_mock, view, imgfilename3x3):
    item = BeeTextItem('foo bar')
    view.scene.addItem(item)
    view.cancel_active_modes = MagicMock()
    item.setSelected(True)
    mimedata = QtCore.QMimeData()
    clipboard_mock.return_value.mimeData.return_value = mimedata
    view.on_action_copy()

    clipboard_mock.return_value.setText.assert_called_once_with('foo bar')
    view.scene.internal_clipboard == [item]
    assert mimedata.data('beeref/items') == b'1'
    view.cancel_active_modes.assert_called_once_with()


@patch('beeref.view.BeeGraphicsView.on_action_fit_scene')
@patch('beeref.scene.BeeGraphicsScene.clearSelection')
@patch('PyQt6.QtGui.QClipboard.image')
def test_on_action_paste_external_new_scene(
        clipboard_mock, clear_mock, fit_mock, view, imgfilename3x3):
    clipboard_mock.return_value = QtGui.QImage(imgfilename3x3)
    view.cancel_active_modes = MagicMock()
    view.on_action_paste()
    assert len(view.scene.items()) == 1
    assert view.scene.items()[0].isSelected() is True
    fit_mock.assert_called_once_with()
    view.cancel_active_modes.assert_called_once_with()


@patch('beeref.view.BeeGraphicsView.on_action_fit_scene')
@patch('beeref.scene.BeeGraphicsScene.clearSelection')
@patch('PyQt6.QtGui.QClipboard.image')
def test_on_action_paste_external_existing_scene(
        clipboard_mock, clear_mock, fit_mock, view, item, imgfilename3x3):
    view.scene.addItem(item)
    view.cancel_active_modes = MagicMock()
    clipboard_mock.return_value = QtGui.QImage(imgfilename3x3)
    view.on_action_paste()
    assert len(view.scene.items()) == 2
    assert view.scene.items()[0].isSelected() is True
    assert view.scene.items()[1].isSelected() is False
    fit_mock.assert_not_called()
    view.cancel_active_modes.assert_called_once_with()


@patch('beeref.scene.BeeGraphicsScene.clearSelection')
@patch('PyQt6.QtGui.QClipboard.mimeData')
def test_on_action_paste_internal(mimedata_mock, clear_mock, view):
    mimedata = QtCore.QMimeData()
    mimedata.setData('beeref/items', QtCore.QByteArray.number(1))
    mimedata_mock.return_value = mimedata
    item = BeePixmapItem(QtGui.QImage())
    view.scene.internal_clipboard = [item]
    view.cancel_active_modes = MagicMock()
    view.on_action_paste()
    assert len(view.scene.items()) == 1
    assert view.scene.items()[0].isSelected() is True
    clear_mock.assert_called_once_with()
    view.cancel_active_modes.assert_called()


@patch('beeref.scene.BeeGraphicsScene.clearSelection')
@patch('PyQt6.QtGui.QClipboard.text')
@patch('PyQt6.QtGui.QClipboard.image')
def test_on_action_paste_when_text(img_mock, text_mock, clear_mock, view):
    img_mock.return_value = QtGui.QImage()
    text_mock.return_value = 'foo bar'
    view.cancel_active_modes = MagicMock()
    view.on_action_paste()
    assert len(view.scene.items()) == 1
    assert view.scene.items()[0].isSelected() is True
    assert view.scene.items()[0].toPlainText() == 'foo bar'
    clear_mock.assert_called_once_with()
    view.cancel_active_modes.assert_called_once_with()


@patch('beeref.scene.BeeGraphicsScene.clearSelection')
@patch('PyQt6.QtGui.QClipboard.text')
@patch('PyQt6.QtGui.QClipboard.image')
@patch('beeref.widgets.BeeNotification')
def test_on_action_paste_when_empty(
        notification_mock, img_mock, text_mock, clear_mock, view):
    view.cancel_active_modes = MagicMock()
    img_mock.return_value = QtGui.QImage()
    text_mock.return_value = ''
    view.on_action_paste()
    assert len(view.scene.items()) == 0
    notification_mock.assert_called()
    assert notification_mock.call_args[0][0] == view
    assert notification_mock.call_args[0][1].startswith('No image data')
    clear_mock.assert_not_called()
    view.cancel_active_modes.assert_called_once_with()


@patch('beeref.view.BeeGraphicsView.on_action_copy')
def test_on_action_cut(copy_mock, view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    view.on_action_cut()
    copy_mock.assert_called_once_with()
    assert view.scene.items() == []
    assert view.undo_stack.isClean() is False


def test_on_selection_changed_updates_grayscale_action(view):
    item = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item)
    item.grayscale = True
    actions.actions['grayscale'].qaction.setChecked(False)
    item.setSelected(True)
    assert actions.actions['grayscale'].qaction.isChecked() is True


def test_on_selection_changed_grayscale_action_ignores_textitem(view):
    item = BeeTextItem('foo')
    view.scene.addItem(item)
    actions.actions['grayscale'].qaction.setChecked(True)
    item.setSelected(True)
    assert actions.actions['grayscale'].qaction.isChecked() is False


def test_on_action_reset_scale(view, item):
    view.scene.addItem(item)
    item.setScale(2)
    item.setSelected(True)
    view.on_action_reset_scale()
    assert item.scale() == 1


def test_on_action_reset_rotation(view, item):
    view.scene.addItem(item)
    item.setRotation(90)
    item.setSelected(True)
    view.on_action_reset_rotation()
    assert item.rotation() == 0


def test_on_action_reset_flip(view, item):
    view.scene.addItem(item)
    item.do_flip()
    item.setSelected(True)
    view.on_action_reset_flip()
    assert item.flip() == 1


def test_on_action_reset_crop(view, item):
    view.scene.addItem(item)
    item.crop = QtCore.QRectF(2, 2, 10, 10)
    assert item.crop == QtCore.QRectF(2, 2, 10, 10)
    item.setSelected(True)
    view.on_action_reset_crop()
    assert item.crop == QtCore.QRectF(0, 0, 10, 10)


def test_on_action_reset_transforms(view, item):
    view.scene.addItem(item)
    item.crop = QtCore.QRectF(2, 2, 10, 10)
    item.do_flip()
    item.setRotation(90)
    item.setScale(2)
    assert item.crop == QtCore.QRectF(2, 2, 10, 10)
    item.setSelected(True)
    view.on_action_reset_transforms()
    assert item.crop == QtCore.QRectF(0, 0, 10, 10)
    assert item.flip() == 1
    assert item.rotation() == 0
    assert item.scale() == 1


def test_on_action_sample_color(view):
    view.cancel_active_modes = MagicMock()
    view.on_action_sample_color()
    assert view.active_mode == view.SAMPLE_COLOR_MODE
    assert isinstance(view.sample_color_widget, widgets.SampleColorWidget)
    assert view.viewport().cursor() == Qt.CursorShape.CrossCursor
    view.cancel_active_modes.assert_called_once_with()


def test_on_action_sample_color_when_multi_selection(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    item2 = BeeTextItem('foo')
    view.scene.addItem(item2)
    item2.setSelected(True)

    view.cancel_active_modes = MagicMock()
    view.scene.multi_select_item.lower_behind_selection = MagicMock()
    view.on_action_sample_color()
    assert view.active_mode == view.SAMPLE_COLOR_MODE
    assert isinstance(view.sample_color_widget, widgets.SampleColorWidget)
    assert view.viewport().cursor() == Qt.CursorShape.CrossCursor
    view.cancel_active_modes.assert_called_once_with()
    view.scene.multi_select_item.lower_behind_selection\
                                .assert_called_once_with()


@patch('PyQt6.QtWidgets.QWidget.create')
@patch('PyQt6.QtWidgets.QWidget.destroy')
@patch('PyQt6.QtWidgets.QWidget.show')
def test_on_action_always_on_top_checked(
        show_mock, destroy_mock, create_mock, view):
    view.on_action_always_on_top(True)
    assert view.parent.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    show_mock.assert_called_once()
    destroy_mock.assert_called_once()
    create_mock.assert_called_once()


@patch('PyQt6.QtWidgets.QWidget.create')
@patch('PyQt6.QtWidgets.QWidget.destroy')
@patch('PyQt6.QtWidgets.QWidget.show')
def test_on_action_always_on_top_unchecked(
        show_mock, destroy_mock, create_mock, view):
    view.on_action_always_on_top(False)
    assert not (view.parent.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)
    show_mock.assert_called_once()
    destroy_mock.assert_called_once()
    create_mock.assert_called_once()


def test_on_action_show_menubar(view):
    view.toplevel_menus = [QtWidgets.QMenu('Foo')]
    view.on_action_show_menubar(True)
    assert len(view.parent.menuBar().actions()) == 1
    view.on_action_show_menubar(False)
    assert view.parent.menuBar().actions() == []


@patch('PyQt6.QtWidgets.QWidget.create')
@patch('PyQt6.QtWidgets.QWidget.destroy')
@patch('PyQt6.QtWidgets.QWidget.show')
def test_on_action_show_titlebar_checked(
        show_mock, destroy_mock, create_mock, view):
    view.on_action_show_titlebar(True)
    assert not (view.parent.windowFlags() & Qt.WindowType.FramelessWindowHint)
    show_mock.assert_called_once()
    destroy_mock.assert_called_once()
    create_mock.assert_called_once()


@patch('PyQt6.QtWidgets.QWidget.create')
@patch('PyQt6.QtWidgets.QWidget.destroy')
@patch('PyQt6.QtWidgets.QWidget.show')
def test_on_action_show_titlebar_unchecked(
        show_mock, destroy_mock, create_mock, view):
    view.on_action_show_titlebar(False)
    assert view.parent.windowFlags() & Qt.WindowType.FramelessWindowHint
    show_mock.assert_called_once()
    destroy_mock.assert_called_once()
    create_mock.assert_called_once()


@patch('beeref.widgets.welcome_overlay.WelcomeOverlay.cursor')
def test_on_action_move_window_when_welcome_overlay(cursor_mock, view):
    cursor_mock.return_value = MagicMock(
        pos=MagicMock(return_value=QtCore.QPointF(10.0, 20.0)))
    view.on_action_move_window()
    assert view.welcome_overlay.movewin_active is True
    assert view.welcome_overlay.event_start == QtCore.QPointF(10.0, 20.0)


def test_on_action_move_window_when_already_active(view):
    view.welcome_overlay.event_start = QtCore.QPointF(10.0, 20.0)
    view.welcome_overlay.movewin_active = True
    view.on_action_move_window()
    assert view.welcome_overlay.movewin_active is False
    assert view.welcome_overlay.event_start == QtCore.QPointF(10.0, 20.0)


@patch('beeref.view.BeeGraphicsView.cursor')
def test_on_action_move_window_when_scene(cursor_mock, view):
    cursor_mock.return_value = MagicMock(
        pos=MagicMock(return_value=QtCore.QPointF(10.0, 20.0)))
    view.welcome_overlay.hide()
    view.on_action_move_window()
    assert view.movewin_active is True
    assert view.event_start == QtCore.QPointF(10.0, 20.0)


def test_on_action_select_all(view, item):
    view.scene.addItem(item)
    item.setSelected(False)
    view.on_action_select_all()
    assert item.isSelected() is True


def test_on_action_deselect_all(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    view.on_action_deselect_all()
    assert item.isSelected() is False


def test_on_action_delete_items(view, item):
    view.cancel_active_modes = MagicMock()
    view.scene.addItem(item)
    item.setSelected(True)
    view.on_action_delete_items()
    assert view.scene.items() == []
    assert view.undo_stack.isClean() is False
    view.cancel_active_modes.assert_called_once()


@patch('beeref.widgets.ChangeOpacityDialog.__init__',
       return_value=None)
def test_on_action_change_opacity(dialog_mock, view):
    pixmapitem1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(pixmapitem1)
    pixmapitem1.setSelected(True)

    pixmapitem2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(pixmapitem2)
    pixmapitem2.setSelected(False)

    textitem = BeeTextItem('foo')
    view.scene.addItem(textitem)
    textitem.setSelected(True)

    view.on_action_change_opacity()
    dialog_mock.assert_called_once_with(view, [pixmapitem1], view.undo_stack)


def test_on_action_grayscale(view):
    pixmapitem1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(pixmapitem1)
    pixmapitem1.setSelected(True)

    pixmapitem2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(pixmapitem2)
    pixmapitem2.setSelected(False)

    textitem = BeeTextItem('foo')
    view.scene.addItem(textitem)
    textitem.setSelected(True)

    view.on_action_grayscale(True)
    assert len(view.undo_stack) == 1
    assert pixmapitem1.grayscale is True
    assert pixmapitem2.grayscale is False


def test_cancel_active_modes_when_sample_color_mode(view):
    view.active_mode = view.SAMPLE_COLOR_MODE
    view.sample_color_widget = widgets.SampleColorWidget(
        view, MagicMock(), MagicMock())
    view.viewport().setCursor(Qt.CursorShape.CrossCursor)
    view.cancel_active_modes()

    assert view.active_mode is None
    assert hasattr(view, 'sample_color_widget') is False
    assert view.viewport().cursor() == Qt.CursorShape.ArrowCursor


def test_cancel_sample_color_mode_when_multi_selection(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    item2 = BeeTextItem('foo')
    view.scene.addItem(item2)
    item2.setSelected(True)

    view.scene.multi_select_item.bring_to_front = MagicMock()
    view.active_mode = view.SAMPLE_COLOR_MODE
    view.sample_color_widget = widgets.SampleColorWidget(
        view, MagicMock(), MagicMock())
    view.viewport().setCursor(Qt.CursorShape.CrossCursor)
    view.cancel_active_modes()

    assert view.active_mode is None
    assert hasattr(view, 'sample_color_widget') is False
    assert view.viewport().cursor() == Qt.CursorShape.ArrowCursor
    view.scene.multi_select_item.bring_to_front.assert_called_once()


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
    view.pan(QtCore.QPointF(5.0, 10.0))
    assert scroll_value_mock.call_count == 2


@patch('PyQt6.QtWidgets.QScrollBar.setValue')
def test_pan_when_no_items(scroll_value_mock, view):
    view.pan(QtCore.QPointF(5.0, 10.0))
    scroll_value_mock.assert_not_called()


@patch('beeref.view.BeeGraphicsView.reset_previous_transform')
@patch('beeref.view.BeeGraphicsView.pan')
def test_zoom_in(pan_mock, reset_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.zoom(40, QtCore.QPointF(10.0, 10.0))
    assert view.get_scale() == 1.04
    reset_mock.assert_called_once_with()
    pan_mock.assert_called_once()


@patch('beeref.view.BeeGraphicsView.reset_previous_transform')
@patch('beeref.view.BeeGraphicsView.pan')
def test_zoom_in_max_zoom_size(pan_mock, reset_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scale(10000000, 10000000)
    view.scene.addItem(item)
    view.zoom(40, QtCore.QPointF(10.0, 10.0))
    assert view.get_scale() == 10000000
    reset_mock.assert_not_called()
    pan_mock.assert_not_called()


@patch('beeref.view.BeeGraphicsView.reset_previous_transform')
@patch('beeref.view.BeeGraphicsView.pan')
def test_zoom_out(pan_mock, reset_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scale(100, 100)
    view.scene.addItem(item)
    view.zoom(-40, QtCore.QPointF(10.0, 10.0))
    assert view.get_scale() == 100 / 1.04
    reset_mock.assert_called_once_with()
    pan_mock.assert_called_once()


@patch('beeref.view.BeeGraphicsView.reset_previous_transform')
@patch('beeref.view.BeeGraphicsView.pan')
def test_zoom_out_min_zoom_size(pan_mock, reset_mock, view, item):
    view.scene.addItem(item)
    view.zoom(-40, QtCore.QPointF(10.0, 10.0))
    assert view.get_scale() == 1
    reset_mock.assert_not_called()
    pan_mock.assert_not_called()


@patch('beeref.view.BeeGraphicsView.reset_previous_transform')
@patch('beeref.view.BeeGraphicsView.pan')
def test_no_items(pan_mock, reset_mock, view, item):
    view.zoom(40, QtCore.QPointF(10.0, 10.0))
    assert view.get_scale() == 1
    reset_mock.assert_not_called()
    pan_mock.assert_not_called()


@patch('beeref.view.BeeGraphicsView.reset_previous_transform')
@patch('beeref.view.BeeGraphicsView.pan')
def test_delta_zero(pan_mock, reset_mock, view, item):
    view.scene.addItem(item)
    view.zoom(0, QtCore.QPointF(10.0, 10.0))
    assert view.get_scale() == 1
    reset_mock.assert_not_called()
    pan_mock.assert_not_called()


@patch('beeref.view.BeeGraphicsView.zoom')
def test_wheel_event_zoom(zoom_mock, view):
    event = MagicMock()
    event.angleDelta.return_value = QtCore.QPointF(0.0, 40.0)
    event.position.return_value = QtCore.QPointF(10.0, 20.0)
    event.modifiers.return_value = Qt.KeyboardModifier.NoModifier
    view.wheelEvent(event)
    zoom_mock.assert_called_once_with(40, QtCore.QPointF(10.0, 20.0))
    event.accept.assert_called_once_with()


@patch('beeref.view.BeeGraphicsView.zoom')
def test_wheel_event_zoom_custom_inverted(zoom_mock, view, kbsettings):
    kbsettings.MOUSEWHEEL_ACTIONS['zoom2'].set_modifiers(['Alt'])
    kbsettings.MOUSEWHEEL_ACTIONS['zoom2'].set_inverted(True)
    event = MagicMock()
    event.angleDelta.return_value = QtCore.QPointF(0.0, 40.0)
    event.position.return_value = QtCore.QPointF(10.0, 20.0)
    event.modifiers.return_value = Qt.KeyboardModifier.AltModifier
    view.wheelEvent(event)
    zoom_mock.assert_called_once_with(-40, QtCore.QPointF(10.0, 20.0))
    event.accept.assert_called_once_with()


@patch('beeref.view.BeeGraphicsView.pan')
def test_wheel_event_pan_vertically(pan_mock, view):
    event = MagicMock()
    event.angleDelta.return_value = QtCore.QPointF(0.0, 40.0)
    event.position.return_value = QtCore.QPointF(10.0, 20.0)
    event.modifiers.return_value = (Qt.KeyboardModifier.ShiftModifier
                                    | Qt.KeyboardModifier.ControlModifier)
    view.wheelEvent(event)
    pan_mock.assert_called_once_with(QtCore.QPointF(20, 0))
    event.accept.assert_called_once_with()


@patch('beeref.view.BeeGraphicsView.pan')
def test_wheel_event_pan_vertically_custom_inverted(
        pan_mock, view, kbsettings):
    kbsettings.MOUSEWHEEL_ACTIONS['pan_vertical2'].set_modifiers(['Alt'])
    kbsettings.MOUSEWHEEL_ACTIONS['pan_vertical2'].set_inverted(True)
    event = MagicMock()
    event.angleDelta.return_value = QtCore.QPointF(0.0, 40.0)
    event.position.return_value = QtCore.QPointF(10.0, 20.0)
    event.modifiers.return_value = Qt.KeyboardModifier.AltModifier
    view.wheelEvent(event)
    pan_mock.assert_called_once_with(QtCore.QPointF(-20, 0))
    event.accept.assert_called_once_with()


@patch('beeref.view.BeeGraphicsView.pan')
def test_wheel_event_pan_horizontally(pan_mock, view):
    event = MagicMock()
    event.angleDelta.return_value = QtCore.QPointF(0.0, 40.0)
    event.position.return_value = QtCore.QPointF(10.0, 20.0)
    event.modifiers.return_value = Qt.KeyboardModifier.ShiftModifier
    view.wheelEvent(event)
    pan_mock.assert_called_once_with(QtCore.QPointF(0, 20))
    event.accept.assert_called_once_with()


@patch('beeref.view.BeeGraphicsView.pan')
def test_wheel_event_pan_horizontally_custom_inverted(
        pan_mock, view, kbsettings):
    kbsettings.MOUSEWHEEL_ACTIONS['pan_horizontal2'].set_modifiers(['Alt'])
    kbsettings.MOUSEWHEEL_ACTIONS['pan_horizontal2'].set_inverted(True)
    event = MagicMock()
    event.angleDelta.return_value = QtCore.QPointF(0.0, 40.0)
    event.position.return_value = QtCore.QPointF(10.0, 20.0)
    event.modifiers.return_value = Qt.KeyboardModifier.AltModifier
    view.wheelEvent(event)
    pan_mock.assert_called_once_with(QtCore.QPointF(0, -20))
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_zoom(mouse_event_mock, view):
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10.0, 20.0)
    event.button.return_value = Qt.MouseButton.MiddleButton
    event.modifiers.return_value = Qt.KeyboardModifier.ControlModifier
    view.mousePressEvent(event)
    assert view.active_mode == view.ZOOM_MODE
    assert view.event_start == QtCore.QPointF(10.0, 20.0)
    assert view.event_anchor == QtCore.QPointF(10.0, 20.0)
    assert view.event_inverted is False
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_zoom_custom_inverted(mouse_event_mock, view, kbsettings):
    kbsettings.MOUSE_ACTIONS['zoom1'].set_button('Left')
    kbsettings.MOUSE_ACTIONS['zoom1'].set_modifiers(['Alt', 'Shift'])
    kbsettings.MOUSE_ACTIONS['zoom1'].set_inverted(True)
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10.0, 20.0)
    event.button.return_value = Qt.MouseButton.LeftButton
    event.modifiers.return_value = (
        Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier)
    view.mousePressEvent(event)
    assert view.active_mode == view.ZOOM_MODE
    assert view.event_start == QtCore.QPointF(10.0, 20.0)
    assert view.event_anchor == QtCore.QPointF(10.0, 20.0)
    assert view.event_inverted is True
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_pan_middle_drag(mouse_event_mock, view):
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10.0, 20.0)
    event.button.return_value = Qt.MouseButton.MiddleButton
    event.modifiers.return_value = Qt.KeyboardModifier.NoModifier
    view.mousePressEvent(event)
    assert view.active_mode == view.PAN_MODE
    assert view.event_start == QtCore.QPointF(10.0, 20.0)
    mouse_event_mock.assert_not_called()
    view.cursor() == Qt.CursorShape.ClosedHandCursor
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_pan_alt_left_drag(mouse_event_mock, view):
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10.0, 20.0)
    event.button.return_value = Qt.MouseButton.LeftButton
    event.modifiers.return_value = Qt.KeyboardModifier.AltModifier
    view.mousePressEvent(event)
    assert view.active_mode == view.PAN_MODE
    assert view.event_start == QtCore.QPointF(10.0, 20.0)
    mouse_event_mock.assert_not_called()
    view.cursor() == Qt.CursorShape.ClosedHandCursor
    event.accept.assert_called_once_with()


@patch('beeref.widgets.BeeNotification')
@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_sample_color_when_color(
        mouse_event_mock, notification_mock, view):
    view.scene.sample_color_at = MagicMock(
        return_value=QtGui.QColor(255, 0, 0, 255))
    view.active_mode = view.SAMPLE_COLOR_MODE
    event = MagicMock()
    event.pos.return_value = QtCore.QPoint(2, 2)
    event.button.return_value = Qt.MouseButton.LeftButton

    view.mousePressEvent(event)
    assert QtWidgets.QApplication.clipboard().text() == '#ff0000'
    notification_mock.assert_called_once_with(
        view, 'Copied color to clipboard: #ff0000')
    assert view.active_mode is None
    view.scene.sample_color_at.assert_called_once()
    mouse_event_mock.assert_not_called()


@patch('beeref.widgets.BeeNotification')
@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_sample_color_when_color_with_alpha(
        mouse_event_mock, notification_mock, view):
    view.scene.sample_color_at = MagicMock(
        return_value=QtGui.QColor(255, 0, 0, 100))
    view.active_mode = view.SAMPLE_COLOR_MODE
    event = MagicMock()
    event.pos.return_value = QtCore.QPoint(2, 2)
    event.button.return_value = Qt.MouseButton.LeftButton

    view.mousePressEvent(event)
    assert QtWidgets.QApplication.clipboard().text() == '#ff000064'
    notification_mock.assert_called_once_with(
        view, 'Copied color to clipboard: #ff000064')
    assert view.active_mode is None
    view.scene.sample_color_at.assert_called_once()
    mouse_event_mock.assert_not_called()


@patch('beeref.widgets.BeeNotification')
@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_sample_color_when_no_color(
        mouse_event_mock, notification_mock, view):
    view.scene.sample_color_at = MagicMock(return_value=None)
    view.active_mode = view.SAMPLE_COLOR_MODE
    event = MagicMock()
    event.pos.return_value = QtCore.QPoint(2, 2)
    event.button.return_value = Qt.MouseButton.LeftButton

    view.mousePressEvent(event)
    notification_mock.assert_not_called()
    assert view.active_mode is None
    view.scene.sample_color_at.assert_called_once()
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
@patch('beeref.view.BeeGraphicsView.cursor')
def test_mouse_press_move_window(cursor_mock, mouse_event_mock, view):
    event = MagicMock()
    cursor_mock.return_value = MagicMock(
        pos=MagicMock(return_value=QtCore.QPointF(10.0, 20.0)))
    event.button.return_value = Qt.MouseButton.LeftButton
    event.modifiers.return_value = (
        Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ControlModifier)
    view.mousePressEvent(event)
    assert view.active_mode is None
    assert view.movewin_active is True
    assert view.event_start == view.mapToGlobal(QtCore.QPointF(10.0, 20.0))
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_when_move_window_active(mouse_event_mock, view):
    view.movewin_active = True
    view.mousePressEvent(MagicMock())
    assert view.movewin_active is False
    mouse_event_mock.assert_not_called()


@patch('PyQt6.QtWidgets.QGraphicsView.keyPressEvent')
def test_key_press_when_sample_color_mode(key_event_mock, view):
    view.active_mode = view.SAMPLE_COLOR_MODE
    event = MagicMock()
    view.keyPressEvent(event)
    assert view.active_mode is None
    event.accept.assert_called_once_with()
    key_event_mock.assert_not_called()


@patch('PyQt6.QtWidgets.QGraphicsView.keyPressEvent')
def test_key_press_when_move_window_active(key_event_mock, view):
    view.movewin_active = True
    view.keyPressEvent(MagicMock())
    assert view.movewin_active is False
    key_event_mock.assert_not_called()


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_unhandled(mouse_event_mock, view):
    event = MagicMock()
    event.button.return_value = Qt.MouseButton.LeftButton
    event.modifiers.return_value = None
    view.mousePressEvent(event)
    assert view.active_mode is None
    mouse_event_mock.assert_called_once_with(event)
    event.accept.assert_not_called()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
@patch('beeref.view.BeeGraphicsView.pan')
def test_mouse_move_pan(pan_mock, mouse_event_mock, view):
    view.active_mode = view.PAN_MODE
    view.event_start = QtCore.QPointF(55.0, 66.0)
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10.0, 20.0)
    view.mouseMoveEvent(event)
    pan_mock.assert_called_once_with(QtCore.QPointF(45.0, 46.0))
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
@patch('beeref.view.BeeGraphicsView.zoom')
def test_mouse_move_zoom(zoom_mock, mouse_event_mock, view):
    view.active_mode = view.ZOOM_MODE
    view.event_anchor = QtCore.QPointF(55.0, 66.0)
    view.event_start = QtCore.QPointF(10.0, 20.0)
    view.event_inverted = False
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10.0, 18.0)
    view.mouseMoveEvent(event)
    zoom_mock.assert_called_once_with(40, QtCore.QPointF(55.0, 66.0))
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
@patch('beeref.view.BeeGraphicsView.zoom')
def test_mouse_move_zoom_inverted(zoom_mock, mouse_event_mock, view):
    view.active_mode = view.ZOOM_MODE
    view.event_anchor = QtCore.QPointF(55.0, 66.0)
    view.event_start = QtCore.QPointF(10.0, 20.0)
    view.event_inverted = True
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10.0, 18.0)
    view.mouseMoveEvent(event)
    zoom_mock.assert_called_once_with(-40, QtCore.QPointF(55.0, 66.0))
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
def test_mouse_move_sample_color(mouse_event_mock, view):
    view.active_mode = view.SAMPLE_COLOR_MODE
    view.scene.sample_color_at = MagicMock(
        return_value=QtGui.QColor(255, 0, 0, 255))
    view.sample_color_widget = MagicMock()
    event = MagicMock()
    event.pos.return_value = QtCore.QPoint(2, 2)
    event.position.return_value = QtCore.QPointF(10.0, 18.0)
    view.mouseMoveEvent(event)
    view.scene.sample_color_at.assert_called_once()
    view.sample_color_widget.update.assert_called_once_with(
        QtCore.QPointF(10.0, 18.0),
        QtGui.QColor(255, 0, 0, 255))
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
@patch('PyQt6.QtWidgets.QWidget.move')
def test_mouse_move_movewin(move_mock, mouse_event_mock, view):
    view.movewin_active = True
    view.event_start = QtCore.QPointF(10.0, 20.0)
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(15.0, 18.0)
    view.mouseMoveEvent(event)
    move_mock.assert_called_once_with(5, -2)
    mouse_event_mock.assert_not_called()
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseMoveEvent')
def test_mouse_move_unhandled(mouse_event_mock, view):
    event = MagicMock()
    event.position.return_value = QtCore.QPointF(10.0, 20.0)
    view.mouseMoveEvent(event)
    mouse_event_mock.assert_called_once_with(event)
    event.accept.assert_not_called()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseReleaseEvent')
def test_mouse_release_pan(mouse_event_mock, view):
    event = MagicMock()
    view.active_mode = view.PAN_MODE
    view.setCursor(Qt.CursorShape.ClosedHandCursor)
    view.mouseReleaseEvent(event)
    mouse_event_mock.assert_not_called()
    assert view.active_mode is None
    event.accept.assert_called_once_with()
    view.cursor() == Qt.CursorShape.ArrowCursor


@patch('PyQt6.QtWidgets.QGraphicsView.mouseReleaseEvent')
def test_mouse_release_zoom(mouse_event_mock, view):
    event = MagicMock()
    view.active_mode = view.ZOOM_MODE
    view.mouseReleaseEvent(event)
    mouse_event_mock.assert_not_called()
    assert view.active_mode is None
    event.accept.assert_called_once_with()


@patch('PyQt6.QtWidgets.QGraphicsView.mouseReleaseEvent')
def test_mouse_release_movewin(mouse_event_mock, view):
    event = MagicMock()
    view.movewin_active = True
    view.mouseReleaseEvent(event)
    mouse_event_mock.assert_not_called()
    assert view.movewin_active is False
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
    url = QtCore.QUrl.fromLocalFile(imgfilename3x3)
    mimedata = QtCore.QMimeData()
    mimedata.setUrls([url])
    event = MagicMock()
    event.mimeData.return_value = mimedata
    event.position.return_value = QtCore.QPointF(10.0, 20.0)

    view.dropEvent(event)
    insert_mock.assert_called_once_with([url], QtCore.QPoint(10, 20))


@patch('beeref.view.BeeGraphicsView.open_from_file')
def test_drop_when_url_beefile_and_scene_empty(open_mock, view):
    root = os.path.dirname(__file__)
    filename = os.path.join(root, 'assets', 'test1item.bee')
    url = QtCore.QUrl.fromLocalFile(filename)
    mimedata = QtCore.QMimeData()
    mimedata.setUrls([url])
    event = MagicMock()
    event.mimeData.return_value = mimedata
    event.position.return_value = QtCore.QPointF(10.0, 20.0)

    view.dropEvent(event)
    open_mock.assert_called_once_with(filename)


@patch('beeref.view.BeeGraphicsView.do_insert_images')
@patch('beeref.view.BeeGraphicsView.open_from_file')
def test_drop_when_url_beefile_and_scene_not_empty(
        open_mock, insert_mock, view, item):
    view.scene.addItem(item)
    root = os.path.dirname(__file__)
    filename = os.path.join(root, 'assets', 'test1item.bee')
    url = QtCore.QUrl.fromLocalFile(filename)
    mimedata = QtCore.QMimeData()
    mimedata.setUrls([url])
    event = MagicMock()
    event.mimeData.return_value = mimedata
    event.position.return_value = QtCore.QPointF(10.0, 20.0)

    view.dropEvent(event)
    open_mock.assert_not_called()


def test_drop_when_img(view, imgfilename3x3):
    mimedata = QtCore.QMimeData()
    mimedata.setImageData(QtGui.QImage(imgfilename3x3))
    event = MagicMock()
    event.mimeData.return_value = mimedata
    event.position.return_value = QtCore.QPointF(10.0, 20.0)

    view.dropEvent(event)
    assert len(view.scene.items()) == 1
    assert view.scene.items()[0].isSelected() is True
