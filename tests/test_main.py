from unittest.mock import patch

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
    show_mock.assert_called_once()


@patch('PyQt6.QtWidgets.QApplication')
@patch('beeref.__main__.CommandlineArgs')
def test_main(args_mock, app_mock, qapp):
    app_mock.return_value = qapp
    args_mock.return_value.filename = None
    args_mock.return_value.loglevel = 'WARN'
    with patch.object(qapp, 'exec') as exec_mock:
        main()
        args_mock.assert_called_once_with(with_check=True)
        exec_mock.assert_called_once_with()
