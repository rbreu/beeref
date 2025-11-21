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

from beeref.config import KeyboardSettings, settings_events
from beeref.config.controls import MouseConfig
from beeref.widgets.controls.common import (
    MouseControlsEditorBase,
    MouseControlsModelBase,
)


logger = logging.getLogger(__name__)


class MouseControlsEditor(MouseControlsEditorBase):

    def __init__(self, parent, index):
        self.init_dialog(parent, index, KeyboardSettings.MOUSE_ACTIONS,
                         'Mouse Controls for:')
        self.old_button = self.action.get_button()

        self.layout.addWidget(QtWidgets.QLabel('Mouse Button:'))
        self.button_input = QtWidgets.QComboBox(parent=parent)
        self.button_input.setMinimumWidth(40)
        self.button_input.insertItems(0, self.action.BUTTON_MAP.keys())
        values = list(self.action.BUTTON_MAP.keys())
        self.button_input.setCurrentIndex(values.index(self.old_button))
        self.layout.addWidget(self.button_input)

        self.init_modifiers_input()
        self.init_button_row()
        self.on_button_changed()
        self.button_input.currentIndexChanged.connect(self.on_button_changed)
        self.show()

    def on_button_changed(self):
        """Disable modifier inputs when no button configured; enable
        otherwise.
        """
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

    def set_modifiers_enabled(self, enabled):
        for key, checkbox in self.checkboxes.items():
            checkbox.setEnabled(enabled)

    def get_button(self):
        values = list(self.action.BUTTON_MAP.keys())
        return values[self.button_input.currentIndex()]

    def set_button(self, value):
        values = list(self.action.BUTTON_MAP.keys())
        self.button_input.setCurrentIndex(values.index(value))

    def get_modifiers(self, cleaned=True):
        if cleaned and self.get_button() == 'Not Configured':
            # In this case the list should already be empty but just
            # to make sure...
            return []
        return super().get_modifiers(cleaned=True)

    def get_temp_action(self):
        return MouseConfig(button=self.get_button(),
                           modifiers=self.get_modifiers(),
                           group=None, text=None, invertible=None, id=None)

    def reset_inputs(self):
        self.set_button(self.old_button)
        self.set_modifiers(self.old_modifiers)


class MouseDelegate(QtWidgets.QStyledItemDelegate):

    def createEditor(self, parent, option, index):
        widget = QtWidgets.QWidget(parent)
        widget.editor = MouseControlsEditor(widget, index)
        widget.editor.saved.connect(
            partial(self.setModelData, widget, index.model(), index))
        return widget

    def setModelData(self, editor, model, index):
        editor = editor.editor
        if editor.result() == QtWidgets.QDialog.DialogCode.Accepted:
            model.setData(
                index,
                {'button': editor.get_button(),
                 'modifiers': editor.get_modifiers()},
                QtCore.Qt.ItemDataRole.EditRole,
                remove_from_other=editor.remove_from_other)


class MouseModel(MouseControlsModelBase):
    """An entry in the keyboard shortcuts table."""

    COLUMNS = (MouseControlsModelBase.COL_ACTION,
               MouseControlsModelBase.COL_CHANGED,
               MouseControlsModelBase.COL_BUTTON,
               MouseControlsModelBase.COL_MODIFIERS,
               MouseControlsModelBase.COL_INVERTED)

    def __init__(self):
        super().__init__(KeyboardSettings.MOUSE_ACTIONS)

    def set_data_on_action(self, action, value):
        action.set_button(value['button'])
        action.set_modifiers(value['modifiers'])


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
