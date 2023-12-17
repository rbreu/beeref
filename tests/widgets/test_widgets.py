from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtCore import Qt

from beeref.config import logfile_name
from beeref.widgets import (
    ChangeOpacityDialog,
    DebugLogDialog,
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
