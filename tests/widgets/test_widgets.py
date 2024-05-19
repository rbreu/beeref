from unittest.mock import patch, MagicMock

from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtCore import Qt

from beeref.config import logfile_name
from beeref.widgets import (
    BeeNotification,
    ChangeOpacityDialog,
    DebugLogDialog,
    ExportImagesFileExistsDialog,
    SampleColorWidget,
    SceneToPixmapExporterDialog,
)


def test_debug_log_dialog(qtbot, settings, view):
    with open(logfile_name(), 'w') as f:
        f.write('my log output')

    dialog = DebugLogDialog(view)
    dialog.show()
    qtbot.addWidget(dialog)
    assert dialog.log.toPlainText() == 'my log output'
    qtbot.mouseClick(dialog.copy_button, Qt.MouseButton.LeftButton)
    clipboard = QtWidgets.QApplication.clipboard()
    assert clipboard.text() == 'my log output'


def test_scene_to_pixmap_exporter_dialog_sets_defaults(view):
    dlg = SceneToPixmapExporterDialog(view, QtCore.QSize(1200, 1600))
    assert dlg.width_input.value() == 1200
    assert dlg.height_input.value() == 1600
    assert dlg.value() == QtCore.QSize(1200, 1600)


def test_scene_to_pixmap_exporter_dialog_sets_defaults_when_too_large(view):
    dlg = SceneToPixmapExporterDialog(view, QtCore.QSize(120000, 160000))
    assert dlg.width_input.value() == 75000
    assert dlg.height_input.value() == 100000
    assert dlg.value() == QtCore.QSize(75000, 100000)


def test_scene_to_pixmap_exporter_dialog_updates_height(view):
    dlg = SceneToPixmapExporterDialog(view, QtCore.QSize(1200, 1600))
    dlg.width_input.setValue(600)
    assert dlg.height_input.value() == 800
    assert dlg.value() == QtCore.QSize(600, 800)


def test_scene_to_pixmap_exporter_dialog_updates_width(view):
    dlg = SceneToPixmapExporterDialog(view, QtCore.QSize(1200, 1600))
    dlg.height_input.setValue(160)
    assert dlg.width_input.value() == 120
    assert dlg.value() == QtCore.QSize(120, 160)


def test_change_opacity_dialog_init(view, item):
    item.setOpacity(0.6)
    stack = QtGui.QUndoStack()
    dlg = ChangeOpacityDialog(view, [item], stack)
    assert dlg.input.value() == 60
    assert dlg.label.text() == 'Opacity: 60%'


def test_change_opacity_dialog_live_update(view, item):
    item.setOpacity(0.6)
    stack = QtGui.QUndoStack()
    dlg = ChangeOpacityDialog(view, [item], stack)
    dlg.input.setValue(30)
    assert dlg.label.text() == 'Opacity: 30%'
    assert item.opacity() == 0.3


def test_change_opacity_dialog_accept(view, item):
    item.setOpacity(0.6)
    stack = QtGui.QUndoStack()
    dlg = ChangeOpacityDialog(view, [item], stack)
    dlg.input.setValue(30)
    dlg.accept()
    assert item.opacity() == 0.3
    assert len(stack) == 1


def test_change_opacity_dialog_accept_when_no_items(view):
    stack = QtGui.QUndoStack()
    dlg = ChangeOpacityDialog(view, [], stack)
    assert dlg.input.value() == 100
    dlg.input.setValue(30)
    dlg.accept()
    assert len(stack) == 0


def test_change_opacity_dialog_reject(view, item):
    item.setOpacity(0.6)
    stack = QtGui.QUndoStack()
    dlg = ChangeOpacityDialog(view, [item], stack)
    dlg.input.setValue(30)
    dlg.reject()
    assert item.opacity() == 0.6
    assert len(stack) == 0


@patch('PyQt6.QtCore.QTimer.singleShot')
def test_bee_notification(single_shot_mock, view):
    widget = BeeNotification(view, 'Hello World')
    assert widget.label.text() == 'Hello World'
    single_shot_mock.assert_called_once_with(1000 * 3, widget.deleteLater)


def test_sample_color_widget(view):
    widget = SampleColorWidget(
        view, QtCore.QPoint(2, 5), QtGui.QColor(255, 0, 0))
    assert widget.color == QtGui.QColor(255, 0, 0)
    assert widget.geometry() == QtCore.QRect(12, 15, 50, 50)

    widget.update(QtCore.QPoint(13, 15), QtGui.QColor(0, 255, 0))
    assert widget.color == QtGui.QColor(0, 255, 0)
    assert widget.geometry() == QtCore.QRect(23, 25, 50, 50)


def test_sample_color_widget_paint_event_when_color(view):
    widget = SampleColorWidget(
        view, QtCore.QPoint(2, 5), QtGui.QColor(255, 0, 0))
    with patch('PyQt6.QtGui.QPainter') as painter_cls_mock:
        painter_mock = MagicMock()
        painter_cls_mock.return_value = painter_mock
        widget.paintEvent(MagicMock())
        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
        painter_mock.setBrush.assert_called_once_with(brush)
        painter_mock.drawRect.assert_called_once_with(0, 0, 50, 50)


def test_sample_color_widget_paint_event_when_no_color(view):
    widget = SampleColorWidget(view, QtCore.QPoint(2, 5), None)
    with patch('PyQt6.QtGui.QPainter') as painter_cls_mock:
        painter_mock = MagicMock()
        painter_cls_mock.return_value = painter_mock
        widget.paintEvent(MagicMock())
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
        painter_mock.setBrush.assert_called_once_with(brush)
        painter_mock.drawRect.assert_called_once_with(0, 0, 50, 50)


def test_export_images_file_exists_dialog(view):
    dlg = ExportImagesFileExistsDialog(view, '/tmp/foo.png')
    assert len(dlg.radio_buttons) == 4
    assert dlg.get_answer() == 'skip'


def test_export_images_file_exists_dialog_get_answer(view):
    dlg = ExportImagesFileExistsDialog(view, '/tmp/foo.png')
    dlg.radio_buttons['overwrite'].setChecked(True)
    assert dlg.get_answer() == 'overwrite'
