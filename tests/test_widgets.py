from unittest.mock import MagicMock

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt

from beeref.config import logfile_name
from beeref.widgets import (
    DebugLogDialog,
    RecentFilesModel,
    SceneToPixmapExporterDialog)


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


def test_recent_files_model_rowcount(view):
    model = RecentFilesModel(['foo.png', 'bar.png'])
    assert model.rowCount(None) == 2


def test_recent_files_model_data_diplayrole(view):
    model = RecentFilesModel(['foo.png', 'bar.png'])
    index = MagicMock()
    index.row.return_value = 1
    assert model.data(index, QtCore.Qt.ItemDataRole.DisplayRole) == 'bar.png'


def test_recent_files_model_data_fontrole(view):
    model = RecentFilesModel(['foo.png', 'bar.png'])
    index = MagicMock()
    index.row.return_value = 1
    font = model.data(index, QtCore.Qt.ItemDataRole.FontRole)
    assert font.underline() is True


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
