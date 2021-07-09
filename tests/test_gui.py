from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt

from beeref.config import logfile_name
from beeref.gui import DebugLogDialog


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
