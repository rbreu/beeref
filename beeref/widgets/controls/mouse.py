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
import logging

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import Qt

from beeref import constants
from beeref.config import KeyboardSettings, settings_events
from beeref.config.controls import MouseConfig


logger = logging.getLogger(__name__)


class MouseControlsEditor(QtWidgets.QDialog):

    saved = QtCore.pyqtSignal()

    def __init__(self, parent, index):
        super().__init__(parent)
        self.action = KeyboardSettings.MOUSE_ACTIONS[index.row()]
        self.setWindowTitle(f'Mouse Controls for: {self.action.text}')
        self.old_button = self.action.get_button()
        self.old_modifiers = self.action.get_modifiers()
        self.remove_from_other = None
        self.ignore_on_changed = False

        self.setAutoFillBackground(True)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Mouse Button:'))

        self.button_input = QtWidgets.QComboBox(parent=parent)
        self.button_input.insertItems(0, self.action.BUTTON_MAP.keys())
        values = list(self.action.BUTTON_MAP.keys())
        self.button_input.setCurrentIndex(values.index(self.old_button))
        self.button_input.currentIndexChanged.connect(self.on_button_changed)
        layout.addWidget(self.button_input)

        self.checkboxes = {}
        for mod in self.action.MODIFIER_MAP.keys():
            checkbox = QtWidgets.QCheckBox(mod)
            checkbox.setChecked(mod in self.old_modifiers)
            checkbox.stateChanged.connect(
                partial(self.on_modifiers_changed, mod))
            self.checkboxes[mod] = checkbox
            layout.addWidget(checkbox)
        self.on_button_changed()

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.setModal(True)
        self.show()

    def on_button_changed(self):
        self.ignore_on_changed = True
        if self.get_button() == 'Not Configured':
            for key, checkbox in self.checkboxes.items():
                checkbox.setChecked(False)
                self.set_modifiers_enabled(False)
        else:
            if not self.get_modifiers(cleaned=False):
                self.set_modifiers_no_modifier()
                self.set_modifiers_enabled(True)

        self.ignore_on_changed = False

    def set_modifiers_no_modifier(self):
        for key, checkbox in self.checkboxes.items():
            checkbox.setChecked(key == 'No Modifier')

    def set_modifiers_enabled(self, enabled):
        for key, checkbox in self.checkboxes.items():
            checkbox.setEnabled(enabled)

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

    def get_button(self):
        values = list(self.action.BUTTON_MAP.keys())
        return values[self.button_input.currentIndex()]

    def get_modifiers(self, cleaned=True):
        if cleaned and self.get_button() == 'Not Configured':
            # In this case the list should already be empty but just
            # to make sure...
            return []

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

    def on_save(self):
        """Don't let users save the same controls on different actions."""

        temp = MouseConfig(button=self.get_button(),
                           modifiers=self.get_modifiers(),
                           group=None, text=None, invertible=None, id=None)

        self.remove_from_other = None
        for action in KeyboardSettings.MOUSE_ACTIONS.values():
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
                    self.set_button(self.old_button)
                    self.set_modifiers(self.old_modifiers)
                return
        self.accept()
        self.saved.emit()


class MouseDelegate(QtWidgets.QStyledItemDelegate):

    def createEditor(self, parent, option, index):
        if index.column() == 4:
            return super().createEditor(parent, option, index)

        widget = QtWidgets.QWidget(parent)
        widget.editor = MouseControlsEditor(widget, index)
        widget.editor.saved.connect(
            partial(self.setModelData,
                    widget.editor, index.model(), index))

    def setModelData(self, editor, model, index):
        if index.column() == 4:
            return super().setModelData(editor, model, index)

        if editor.result() == QtWidgets.QDialog.DialogCode.Accepted:
            model.setData(
                index,
                {'button': editor.get_button(),
                 'modifiers': editor.get_modifiers()},
                QtCore.Qt.ItemDataRole.EditRole,
                remove_from_other=editor.remove_from_other)


class MouseModel(QtCore.QAbstractTableModel):
    """An entry in the keyboard shortcuts table."""

    HEADER = (
        'Action', constants.CHANGED_SYMBOL, 'Button', 'Modifiers', 'Inverted')

    def __init__(self):
        super().__init__()
        self.settings = KeyboardSettings()
        self.actions = self.settings.MOUSE_ACTIONS

    def rowCount(self, parent):
        return len(self.actions)

    def columnCount(self, parent):
        return len(self.HEADER)

    def data(self, index, role):
        action = self.actions[index.row()]

        if role in (QtCore.Qt.ItemDataRole.DisplayRole,
                    QtCore.Qt.ItemDataRole.EditRole):
            if index.column() == 0:
                return action.text
            if index.column() == 1 and action.controls_changed():
                return constants.CHANGED_SYMBOL
            if index.column() == 2:
                return action.get_button()
            if index.column() == 3:
                return ' + '.join(action.get_modifiers())
            if index.column() == 4:
                if not action.is_configured() or not action.invertible:
                    return ''
                return 'Yes' if action.get_inverted() else 'No'

        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            changed = action.controls_changed()
            if changed and index.column() == 1:
                return 'Changed from default'
            if changed and index.column() == 2:
                if action.button is None:
                    return 'Not configured'
                else:
                    default = ' + '.join(action.button)

                return f'Default: {default}'
            if changed and index.column() == 3:
                if action.button is None:
                    return 'Not configured'
                else:
                    default = ' + '.join(action.modifiers)

                return f'Default: {default}'
            if changed and index.column() == 4:
                default = 'Yes' if action.inverted else 'No'
                return f'Default: {default}'

        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if (index.column() == 4
                    and action.is_configured()
                    and action.invertible):
                return (Qt.CheckState.Checked if action.get_inverted()
                        else Qt.CheckState.Unchecked)

    def setData(self, index, value, role, remove_from_other=None):
        action = self.actions[index.row()]
        if index.column() == 4:
            action.set_inverted(
                True if value == Qt.CheckState.Checked.value else False)
        else:
            action.set_button(value['button'])
            action.set_modifiers(value['modifiers'])
            if remove_from_other:
                # These controls has conflicts with another action and the
                # user chose to remove the other controls
                remove_from_other.set_button('Not Configured')
                remove_from_other.set_modifiers([])
                row = list(self.actions.keys()).index(remove_from_other.id)
                self.dataChanged.emit(self.index(row, 1),
                                      self.index(row, 3))

        # Whole row might be affected, so excpliclity emit dataChanged
        self.dataChanged.emit(self.index(index.row(), 1),
                              self.index(index.row(), 3))
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
        elif index.column() in (2, 3):
            return (base | QtCore.Qt.ItemFlag.ItemIsEditable)
        elif index.column() == 4:
            action = self.actions[index.row()]
            if action.invertible and action.is_configured():
                return (base
                        | QtCore.Qt.ItemFlag.ItemIsEditable
                        | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            else:
                return base


class MouseProxy(QtCore.QSortFilterProxyModel):

    def __init__(self):
        super().__init__()
        self.setSourceModel(MouseModel())
        self.setFilterCaseSensitivity(
            QtCore.Qt.CaseSensitivity.CaseInsensitive)

    def setData(self, index, value, role, remove_from_other=None):
        result = self.sourceModel().setData(
            self.mapToSource(index),
            value,
            role,
            remove_from_other=remove_from_other)
        return result


class MouseView(QtWidgets.QTableView):

    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumSize(QtCore.QSize(400, 200))
        self.setItemDelegate(MouseDelegate())
        self.setShowGrid(False)
        self.setModel(MouseProxy())
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.setSelectionMode(
            QtWidgets.QHeaderView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        settings_events.restore_defaults.connect(
            self.on_restore_defaults)

    def on_restore_defaults(self):
        self.viewport().update()
