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

from PyQt6 import QtWidgets, QtCore

from beeref import constants
from beeref.actions.actions import actions
from beeref.config import KeyboardSettings, settings_events


logger = logging.getLogger(__name__)


class MouseWheelModel(QtCore.QAbstractTableModel):
    """An entry in the keyboard shortcuts table."""

    HEADER = ('Action', constants.CHANGED_SYMBOL, 'Modifiers', 'Inverted')

    def __init__(self):
        super().__init__()
        self.settings = KeyboardSettings()

    def rowCount(self, parent):
        return len(self.settings.MOUSEWHEEL_FIELDS)

    def columnCount(self, parent):
        return len(self.HEADER)

    def data(self, index, role):
        if role in (QtCore.Qt.ItemDataRole.DisplayRole,
                    QtCore.Qt.ItemDataRole.EditRole):
            action = actions[index.row()]
            txt = ': '.join(action.menu_path + [action['text']])
            if index.column() == 0:
                return txt.replace('&', '').removesuffix('...')
            if index.column() == 1 and action.shortcuts_changed():
                return constants.CHANGED_SYMBOL
            if index.column() > 1:
                return action.get_qkeysequence(index.column() - 2)

        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            action = actions[index.row()]
            changed = action.shortcuts_changed()
            if changed and index.column() == 1:
                return 'Changed from default'
            if changed and index.column() > 1:
                default = action.get_default_shortcut(index.column() - 2)
                default = default or '-'
                return f'Default: {default}'

    def setData(self, index, value, role, remove_from_other=None):
        action = actions[index.row()]
        shortcuts = action.get_shortcuts() + [None, None]
        shortcuts[index.column() - 2] = value.toString()
        shortcuts = list(filter(bool, shortcuts))
        if len(shortcuts) != len(set(shortcuts)):
            # We got the same shortcut twice
            shortcuts = set(shortcuts)
        action.set_shortcuts(shortcuts)
        # Whole row might be affected, so excpliclity emit dataChanged
        self.dataChanged.emit(self.index(index.row(), 1),
                              self.index(index.row(), 3))

        if remove_from_other:
            # This shortcut has conflicts with another action and the
            # user chose to remove the other shortcut
            shortcuts = remove_from_other.get_shortcuts()
            shortcuts.remove(value.toString())
            remove_from_other.set_shortcuts(shortcuts)
            row = list(actions.keys()).index(remove_from_other['id'])
            self.dataChanged.emit(self.index(row, 1),
                                  self.index(row, 3))

        return True

    def headerData(self, section, orientation, role):
        if (role == QtCore.Qt.ItemDataRole.DisplayRole
                and orientation == QtCore.Qt.Orientation.Horizontal):
            return self.HEADER[section]

    def flags(self, index):
        base = (QtCore.Qt.ItemFlag.ItemIsEnabled
                | QtCore.Qt.ItemFlag.ItemNeverHasChildren)
        if index.column() <= 1:
            return base
        else:
            return (base | QtCore.Qt.ItemFlag.ItemIsEditable)
