from unittest.mock import patch

from PyQt6 import QtWidgets

from beeref.widgets.controls import ControlsDialog


@patch('PyQt6.QtWidgets.QMessageBox.question',
       return_value=QtWidgets.QMessageBox.StandardButton.Yes)
@patch('beeref.config.KeyboardSettings.restore_defaults')
def test_controls_dialog_on_restore_defaults(
        restore_mock,  msg_mock, kbsettings, view):
    dialog = ControlsDialog(view)
    dialog.on_restore_defaults()
    msg_mock.assert_called_once()
    restore_mock.assert_called()
