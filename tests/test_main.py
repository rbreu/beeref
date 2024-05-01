from unittest.mock import patch, MagicMock

from PyQt6 import QtCore

from beeref.__main__ import BeeRefMainWindow, main
from beeref.assets import BeeAssets
from beeref.view import BeeGraphicsView


@patch('PyQt6.QtWidgets.QWidget.show')
def test_beeref_mainwindow_init(show_mock, qapp):
    window = BeeRefMainWindow(qapp)
    assert window.windowTitle() == 'BeeRef'
    assert BeeAssets().logo == BeeAssets().logo
    assert window.windowIcon()
    assert window.contentsMargins() == QtCore.QMargins(0, 0, 0, 0)
    assert isinstance(window.view, BeeGraphicsView)
    show_mock.assert_called()


@patch('beeref.view.BeeGraphicsView.open_from_file')
def test_beerefapplication_fileopenevent(open_mock, qapp, main_window):
    event = MagicMock()
    event.type.return_value = QtCore.QEvent.Type.FileOpen
    event.file.return_value = 'test.bee'
    assert qapp.event(event) is True
    open_mock.assert_called_once_with('test.bee')


@patch('beeref.__main__.BeeRefApplication')
@patch('beeref.__main__.CommandlineArgs')
def test_main(args_mock, app_mock, qapp):
    app_mock.return_value = qapp
    args_mock.return_value.filename = None
    args_mock.return_value.loglevel = 'WARN'
    args_mock.return_value.debug_raise_error = ''
    with patch.object(qapp, 'exec') as exec_mock:
        main()
        args_mock.assert_called_once_with(with_check=True)
        exec_mock.assert_called_once_with()
