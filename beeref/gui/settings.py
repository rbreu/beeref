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

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt

from beeref import constants
from beeref.config import KeyboardSettings


logger = logging.getLogger(__name__)


class KeyboardShortcutsModel(QtCore.QAbstractTableModel):

    def __init__(self, actions):
        super().__init__()
        self.actions = list(actions.values())
        self.kbsettings = KeyboardSettings()

    def rowCount(self, parent):
        return len(self.actions)

    def columnCount(self, parent):
        return 3

    def headerData(self, section, orientation, role):
        if role != Qt.ItemDataRole.DisplayRole:
            return

        if orientation == Qt.Orientation.Horizontal:
            return ['Action', 'Shortcut', 'Alternate'][section]
        else:
            return str(section + 1)

    def data(self, index, role):
        if role != Qt.ItemDataRole.DisplayRole:
            return

        action = self.actions[index.row()]
        if index.column() == 0:
            return action.iconText()

        try:
            return action.shortcuts()[index.column() - 1].toString()
        except IndexError:
            return ''

    def flags(self, index):
        if index.column() > 0:
            return Qt.ItemFlag.ItemIsEditable | super().flags(index)
        return super().flags(index)

    def setData(self, index, value, role):
        if role != Qt.ItemDataRole.EditRole or index.column() == 0:
            return False

        action = self.actions[index.row()]
        shortcuts = action.shortcuts()
        if len(shortcuts) == 1:
            shortcuts.append(None)
        shortcuts[index.column() - 1] = value
        shortcuts = [sc for sc in shortcuts if sc]

        action.setShortcuts(shortcuts)
        #self.kbsettings.set_shortcuts(
        #    'Actions', action['id'], action.get('shortcuts')

        self.dataChanged.emit(
            self.createIndex(index.row(), 1),
            self.createIndex(index.row(), 2))
        return True


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(f'{constants.APPNAME} Settings')
        tabs = QtWidgets.QTabWidget()

        # Keyboard Shordcuts
        model = KeyboardShortcutsModel(self.parent().bee_actions)
        table = QtWidgets.QTreeView(self)
        table.setModel(model)
        tabs.addTab(table, '&Keybord Shortcuts')

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(tabs)
        self.show()
