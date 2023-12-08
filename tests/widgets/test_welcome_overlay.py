from unittest.mock import MagicMock, patch

from PyQt6 import QtCore, QtWidgets

from beeref.view import BeeGraphicsView
from beeref.widgets.welcome_overlay import (
    RecentFilesModel,
    RecentFilesView,
    WelcomeOverlay,
)


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


@patch('beeref.widgets.welcome_overlay.BeeSettings.get_recent_files',
       return_value=[])
def test_welcome_overlay_when_no_recent_files(qapp):
    parent = QtWidgets.QMainWindow()
    view = BeeGraphicsView(qapp, parent)
    overlay = WelcomeOverlay(view)
    overlay.show()
    assert overlay.layout.indexOf(overlay.files_widget) < 0


def test_recent_files_view_size_hint(qapp):
    parent = QtWidgets.QMainWindow()
    files_view = RecentFilesView(parent, None)

    files_view.sizeHintForRow = lambda i: 10 + i
    files_view.sizeHintForColumn = lambda i: 50 + i
    files_view.update_files(['foo.png', 'bar.png'])
    assert files_view.sizeHint() == QtCore.QSize(53, 25)


def test_recent_files_view_on_click(qapp):
    parent = QtWidgets.QMainWindow()
    view = BeeGraphicsView(qapp, parent)
    view.open_from_file = MagicMock()
    overlay = WelcomeOverlay(view)
    overlay.files_view.update_files(['foo.bee', 'bar.bee'])
    overlay.files_view.on_clicked(
        RecentFilesModel(
            ['foo.bee', 'bar.bee']).createIndex(1, 0))
    view.open_from_file.assert_called_once_with('bar.bee')


@patch('beeref.widgets.welcome_overlay.BeeSettings.get_recent_files',
       return_value=['foo.bee', 'bar.bee'])
def test_welcome_overlay_when_recent_files(qapp):
    parent = QtWidgets.QMainWindow()
    view = BeeGraphicsView(qapp, parent)
    overlay = WelcomeOverlay(view)
    overlay.show()
    assert overlay.layout.indexOf(overlay.files_widget) == 0


@patch('PyQt6.QtWidgets.QGraphicsView.mousePressEvent')
def test_mouse_press_when_move_window_active(mouse_event_mock, qapp):
    parent = QtWidgets.QMainWindow()
    view = BeeGraphicsView(qapp, parent)
    overlay = WelcomeOverlay(view)
    overlay.movewin_active = True
    overlay.mousePressEvent(MagicMock())
    assert overlay.movewin_active is False
    mouse_event_mock.assert_not_called()
