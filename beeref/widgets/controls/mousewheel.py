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
from beeref.config.controls import MouseWheelConfig
from beeref.widgets.controls.common import (
    MouseControlsEditorBase,
    MouseControlsModelBase,
)


logger = logging.getLogger(__name__)


class MouseWheelModifiersEditor(MouseControlsEditorBase):

    def __init__(self, parent, index):
        self.init_dialog(parent, index, KeyboardSettings.MOUSEWHEEL_ACTIONS,
                         'MouseWheel Controls for:')
        self.init_modifiers_input()
        self.init_button_row()
        self.show()

    def get_temp_action(self):
        return MouseWheelConfig(
            modifiers=self.get_modifiers(),
            group=None, text=None, invertible=None, id=None)

    def reset_inputs(self):
        self.set_modifiers(self.old_modifiers)


class MouseWheelDelegate(QtWidgets.QStyledItemDelegate):

    def createEditor(self, parent, option, index):
        widget = QtWidgets.QWidget(parent)
        widget.editor = MouseWheelModifiersEditor(widget, index)
        widget.editor.saved.connect(
            partial(self.setModelData, widget, index.model(), index))
        return widget

    def setModelData(self, editor, model, index):
        editor = editor.editor
        if editor.result() == QtWidgets.QDialog.DialogCode.Accepted:
            model.setData(
                index,
                editor.get_modifiers(),
                QtCore.Qt.ItemDataRole.EditRole,
                remove_from_other=editor.remove_from_other)


class MouseWheelModel(MouseControlsModelBase):
    """An entry in the keyboard shortcuts table."""

    COLUMNS = (MouseControlsModelBase.COL_ACTION,
               MouseControlsModelBase.COL_CHANGED,
               MouseControlsModelBase.COL_MODIFIERS,
               MouseControlsModelBase.COL_INVERTED)

    def __init__(self):
        super().__init__(KeyboardSettings.MOUSEWHEEL_ACTIONS)

    def set_data_on_action(self, action, value):
        action.set_modifiers(value)


class MouseWheelProxy(QtCore.QSortFilterProxyModel):

    def __init__(self):
        super().__init__()
        self.setSourceModel(MouseWheelModel())
        self.setFilterCaseSensitivity(
            QtCore.Qt.CaseSensitivity.CaseInsensitive)

    def setData(self, index, value, role, remove_from_other=None):
        result = self.sourceModel().setData(
            self.mapToSource(index),
            value,
            role,
            remove_from_other=remove_from_other)
        return result


class MouseWheelView(QtWidgets.QTableView):

    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumSize(QtCore.QSize(400, 200))
        self.setItemDelegate(MouseWheelDelegate())
        self.setShowGrid(False)
        self.setModel(MouseWheelProxy())
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
