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

from functools import partial

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import Qt

from beeref.config import KeyboardSettings
from beeref import constants


class MouseControlsEditorBase(QtWidgets.QDialog):
    """Common code for MouseWheel and Mouse control editors."""

    saved = QtCore.pyqtSignal()

    def init_dialog(self, parent, index, actions, title):
        super().__init__(parent)
        self.actions = actions
        self.action = self.actions[index.row()]
        self.setWindowTitle(f'title {self.action.text}')
        self.old_modifiers = self.action.get_modifiers()
        self.remove_from_other = None
        self.ignore_on_changed = False
        self.setAutoFillBackground(True)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.setModal(True)

    def init_modifiers_input(self):
        group = QtWidgets.QGroupBox('Modifiers')
        group_layout = QtWidgets.QVBoxLayout()
        group.setLayout(group_layout)
        self.layout.addWidget(group)
        self.checkboxes = {}
        for mod in self.action.MODIFIER_MAP.keys():
            checkbox = QtWidgets.QCheckBox(mod)
            checkbox.setChecked(mod in self.old_modifiers)
            checkbox.stateChanged.connect(
                partial(self.on_modifiers_changed, mod))
            self.checkboxes[mod] = checkbox
            group_layout.addWidget(checkbox)

    def init_button_row(self):
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.on_save)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

    def set_modifiers_no_modifier(self):
        """Check 'No Modifiers', uncheck everything else."""
        for key, checkbox in self.checkboxes.items():
            checkbox.setChecked(key == 'No Modifier')

    def on_modifiers_changed(self, modifier, value):
        """Ensure that when 'No Modifiers' is checked, nothing else is
        checked at the same time.

        If everything is unchecked, set 'No Modifiers' automatically.
        """
        if self.ignore_on_changed:
            return

        checked = value == Qt.CheckState.Checked.value
        self.ignore_on_changed = True

        if checked and modifier == 'No Modifier':
            self.set_modifiers_no_modifier()

        if checked and modifier != 'No Modifier':
            self.checkboxes['No Modifier'].setChecked(False)

        if not checked and not self.get_modifiers(cleaned=False):
            self.set_modifiers_no_modifier()

        self.ignore_on_changed = False

    def get_modifiers(self, cleaned=True):
        modifiers = [key for key, checkbox in self.checkboxes.items()
                     if checkbox.isChecked()]
        if cleaned and 'No Modifier' in modifiers:
            # In this case the list already should only have the one
            # entry, but just to make sure...
            return ['No Modifier']
        return modifiers

    def set_modifiers(self, modifiers):
        for key, checkbox in self.checkboxes.items():
            checkbox.setChecked(key in modifiers)

    def get_temp_action(self):
        raise NotImplementedError  # pragma: no cover

    def reset_inputs(self):
        raise NotImplementedError  # pragma: no cover

    def on_save(self):
        """Don't let users save the same controls on different actions."""

        temp = self.get_temp_action()
        self.remove_from_other = None
        for action in self.actions.values():
            if action == self.action:
                continue
            if action.conflicts_with(temp):
                msg = ('<p>These controls are already used for:</p>'
                       f'<p>{action.text}</p>'
                       '<p>Do you want to remove the other controls'
                       ' to save these ones?</p>')
                reply = QtWidgets.QMessageBox.question(
                    self, 'Save Controls?', msg)
                if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                    self.remove_from_other = action
                    self.accept()
                    self.saved.emit()
                else:
                    self.reset_inputs()
                return
        self.accept()
        self.saved.emit()


class MouseControlsModelBase(QtCore.QAbstractTableModel):
    COLUMNS = None
    COL_ACTION = 1
    COL_CHANGED = 2
    COL_BUTTON = 3
    COL_MODIFIERS = 4
    COL_INVERTED = 5

    HEADERS = {
        COL_ACTION: 'Action',
        COL_CHANGED: constants.CHANGED_SYMBOL,
        COL_BUTTON: 'Button',
        COL_MODIFIERS: 'Modifiers',
        COL_INVERTED: 'Inverted',
    }

    def __init__(self, actions):
        super().__init__()
        self.settings = KeyboardSettings()
        self.actions = actions

    def rowCount(self, parent):
        return len(self.actions)

    def columnCount(self, parent):
        return len(self.COLUMNS)

    def headerData(self, section, orientation, role):
        if (role == QtCore.Qt.ItemDataRole.DisplayRole
                and orientation == QtCore.Qt.Orientation.Horizontal):
            key = self.COLUMNS[section]
            return self.HEADERS[key]

    def flags(self, index):
        key = self.COLUMNS[index.column()]
        base = (QtCore.Qt.ItemFlag.ItemIsEnabled
                | QtCore.Qt.ItemFlag.ItemNeverHasChildren)

        if key in (self.COL_ACTION, self.COL_CHANGED):
            return base
        elif key in (self.COL_BUTTON, self.COL_MODIFIERS):
            return (base | QtCore.Qt.ItemFlag.ItemIsEditable)
        elif key == self.COL_INVERTED:
            action = self.actions[index.row()]
            if action.invertible and action.is_configured():
                return (base
                        | QtCore.Qt.ItemFlag.ItemIsEditable
                        | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            else:
                return base

    def data(self, index, role):
        key = self.COLUMNS[index.column()]
        action = self.actions[index.row()]

        if role in (QtCore.Qt.ItemDataRole.DisplayRole,
                    QtCore.Qt.ItemDataRole.EditRole):
            if key == self.COL_ACTION:
                return action.text
            if key == self.COL_CHANGED and action.controls_changed():
                return constants.CHANGED_SYMBOL
            if key == self.COL_BUTTON:
                return action.get_button()
            if key == self.COL_MODIFIERS:
                return ' + '.join(action.get_modifiers())
            if key == self.COL_INVERTED:
                if not action.is_configured() or not action.invertible:
                    return None
                return 'Yes' if action.get_inverted() else 'No'

        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            changed = action.controls_changed()
            if not changed:
                return
            if key == self.COL_CHANGED:
                return 'Changed from default'
            if key == self.COL_BUTTON:
                if action.button == 'Not Configured':
                    default = 'Not configured'
                else:
                    default = action.button
                return f'Default: {default}'
            if key == self.COL_MODIFIERS:
                if not action.modifiers:
                    default = 'Not configured'
                else:
                    default = ' + '.join(action.modifiers)
                return f'Default: {default}'
            if key == self.COL_INVERTED and action.invertible:
                default = 'Yes' if action.inverted else 'No'
                return f'Default: {default}'

        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if (key == self.COL_INVERTED
                    and action.is_configured()
                    and action.invertible):
                return (Qt.CheckState.Checked if action.get_inverted()
                        else Qt.CheckState.Unchecked)

    def set_data_on_action(self, action, value):
        raise NotImplementedError  # pragma: no cover

    def setData(self, index, value, role, remove_from_other=None):
        key = self.COLUMNS[index.column()]
        action = self.actions[index.row()]
        if key == self.COL_INVERTED:
            action.set_inverted(
                True if value == Qt.CheckState.Checked.value else False)
        else:
            self.set_data_on_action(action, value)
            if remove_from_other:
                # These controls has conflicts with another action and the
                # user chose to remove the other controls
                remove_from_other.remove_controls()
                row = list(self.actions.keys()).index(remove_from_other.id)
                self.dataChanged.emit(
                    self.index(row, 0),
                    self.index(row, self.columnCount(None) - 1))

        # Whole row might be affected, so excpliclity emit dataChanged
        self.dataChanged.emit(
            self.index(index.row(), 0),
            self.index(index.row(), self.columnCount(None) - 1))

        return True
