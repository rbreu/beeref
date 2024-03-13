# This file is part of BeeRef.
#
# BeeRef is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BeeRef is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BeeRef.  If not, see <https://www.gnu.org/licenses/>.

import logging

from PyQt6 import QtWidgets

from beeref.config import KeyboardSettings
from beeref.widgets.controls.keyboard import KeyboardShortcutsView
from beeref.widgets.controls.mouse import MouseView
from beeref.widgets.controls.mousewheel import MouseWheelView


logger = logging.getLogger(__name__)


class ControlsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Keyboard & Mouse Controls')
        tabs = QtWidgets.QTabWidget()

        # Keyboard shortcuts
        keyboard = QtWidgets.QWidget(parent)
        kb_layout = QtWidgets.QVBoxLayout()
        keyboard.setLayout(kb_layout)
        table = KeyboardShortcutsView(keyboard)
        search_input = QtWidgets.QLineEdit()
        search_input.setPlaceholderText('Search...')
        search_input.textChanged.connect(table.model().setFilterFixedString)
        kb_layout.addWidget(search_input)
        kb_layout.addWidget(table)
        tabs.addTab(keyboard, '&Keyboard Shortcuts')

        # Mouse controls
        mouse = QtWidgets.QWidget(parent)
        mouse_layout = QtWidgets.QVBoxLayout()
        mouse.setLayout(mouse_layout)
        table = MouseView(mouse)
        search_input = QtWidgets.QLineEdit()
        search_input.setPlaceholderText('Search...')
        search_input.textChanged.connect(table.model().setFilterFixedString)
        mouse_layout.addWidget(search_input)
        mouse_layout.addWidget(table)
        tabs.addTab(mouse, '&Mouse')

        # Mouse wheel controls
        mousewheel = QtWidgets.QWidget(parent)
        wheel_layout = QtWidgets.QVBoxLayout()
        mousewheel.setLayout(wheel_layout)
        table = MouseWheelView(mousewheel)
        search_input = QtWidgets.QLineEdit()
        search_input.setPlaceholderText('Search...')
        search_input.textChanged.connect(table.model().setFilterFixedString)
        wheel_layout.addWidget(search_input)
        wheel_layout.addWidget(table)
        tabs.addTab(mousewheel, 'Mouse &Wheel')

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(tabs)

        # Bottom row of buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        reset_btn = QtWidgets.QPushButton('&Restore Defaults')
        reset_btn.setAutoDefault(False)
        reset_btn.clicked.connect(self.on_restore_defaults)
        buttons.addButton(reset_btn,
                          QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)

        layout.addWidget(buttons)
        self.show()

    def on_restore_defaults(self, *args, **kwargs):
        reply = QtWidgets.QMessageBox.question(
            self,
            'Restore defaults?',
            'Do you want to restore all keyboard and mouse settings '
            'to their default values?')

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            KeyboardSettings().restore_defaults()
