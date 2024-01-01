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

from PyQt6 import QtWidgets, QtCore, QtGui

from beeref import constants
from beeref.actions.actions import actions
from beeref.config import BeeSettings, KeyboardSettings, settings_events


logger = logging.getLogger(__name__)


class RadioGroup(QtWidgets.QGroupBox):
    TITLE = None
    HELPTEXT = None
    KEY = None
    OPTIONS = None

    def __init__(self):
        super().__init__(self.TITLE)
        self.settings = BeeSettings()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        settings_events.restore_keyboard_defaults.connect(
            self.on_restore_defaults)

        if self.HELPTEXT:
            helptxt = QtWidgets.QLabel(self.HELPTEXT)
            helptxt.setWordWrap(True)
            layout.addWidget(helptxt)

        self.ignore_values_changed = True
        self.buttons = {}
        for (value, label, helptext) in self.OPTIONS:
            btn = QtWidgets.QRadioButton(label)
            self.buttons[value] = btn
            btn.setToolTip(helptext)
            btn.toggled.connect(
                partial(self.on_values_changed, value=value, button=btn))
            if value == self.settings.valueOrDefault(self.KEY):
                btn.setChecked(True)
            layout.addWidget(btn)

        self.ignore_values_changed = False
        layout.addStretch(100)

    def on_values_changed(self, value, button):
        if self.ignore_values_changed:
            return

        if value != self.settings.valueOrDefault(self.KEY):
            logger.debug(f'Setting {self.KEY} changed to: {value}')
            self.settings.setValue(self.KEY, value)

    def on_restore_defaults(self):
        new_value = self.settings.valueOrDefault(self.KEY)
        self.ignore_values_changed = True
        for value, btn in self.buttons.items():
            btn.setChecked(value == new_value)
        self.ignore_values_changed = False


class IntegerGroup(QtWidgets.QGroupBox):
    TITLE = None
    HELPTEXT = None
    KEY = None
    MIN = None
    MAX = None

    def __init__(self):
        super().__init__(self.TITLE)
        self.settings = BeeSettings()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        settings_events.restore_defaults.connect(self.on_restore_defaults)

        if self.HELPTEXT:
            helptxt = QtWidgets.QLabel(self.HELPTEXT)
            helptxt.setWordWrap(True)
            layout.addWidget(helptxt)

        self.input = QtWidgets.QSpinBox()
        self.input.setValue(self.settings.valueOrDefault(self.KEY))
        self.input.setRange(self.MIN, self.MAX)
        self.input.valueChanged.connect(self.on_value_changed)
        layout.addWidget(self.input)
        layout.addStretch(100)
        self.ignore_values_changed = False

    def on_value_changed(self, value):
        if self.ignore_values_changed:
            return

        if value != self.settings.valueOrDefault(self.KEY):
            logger.debug(f'Setting {self.KEY} changed to: {value}')
            self.settings.setValue(self.KEY, value)

    def on_restore_defaults(self):
        new_value = self.settings.valueOrDefault(self.KEY)
        self.ignore_values_changed = True
        self.input.setValue(new_value)
        self.ignore_values_changed = False


class ImageStorageFormatWidget(RadioGroup):
    TITLE = 'Image Storage Format:'
    HELPTEXT = ('How images are stored inside bee files.'
                ' Changes will only take effect on newly saved images.')
    KEY = 'Items/image_storage_format'
    OPTIONS = (
        ('best', 'Best Guess',
         ('Small images and images with alpha channel are stored as png,'
          ' everything else as jpg')),
        ('png', 'Always PNG', 'Lossless, but large bee file'),
        ('jpg', 'Always JPG',
         'Small bee file, but lossy and no transparency support'))


class ArrangeGapWidget(IntegerGroup):
    TITLE = 'Arrange Gap:'
    HELPTEXT = ('The gap between images when using arrange actions.')
    KEY = 'Items/arrange_gap'
    MIN = 0
    MAX = 200


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(f'{constants.APPNAME} Settings')
        tabs = QtWidgets.QTabWidget()

        # Miscellaneous
        misc = QtWidgets.QWidget()
        misc_layout = QtWidgets.QGridLayout()
        misc.setLayout(misc_layout)
        misc_layout.addWidget(ImageStorageFormatWidget(), 0, 0)
        misc_layout.addWidget(ArrangeGapWidget(), 0, 1)
        tabs.addTab(misc, '&Miscellaneous')

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
            'Do you want to restore all settings to their default values?')

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            BeeSettings().restore_defaults()


class KeyboardShortcutsEditor(QtWidgets.QKeySequenceEdit):

    def __init__(self, parent, index):
        super().__init__(parent)
        self.action = actions[index.row()]
        try:
            self.old_value = self.action.get_shortcuts()[index.column() - 2]
        except IndexError:
            self.old_value = ''
        self.setClearButtonEnabled(True)
        self.setMaximumSequenceLength(1)
        self.editingFinished.connect(self.on_editing_finished)
        self.finished_last_called_with = None
        self.remove_from_other = None

    def on_editing_finished(self):
        shortcut = self.keySequence().toString()

        if self.finished_last_called_with == shortcut:
            # Workaround for bug
            # https://bugreports.qt.io/browse/QTBUG-40
            # editingFinished signal is emitted twice because of
            # the QMessageBox below
            return

        self.remove_from_other = None
        self.finished_last_called_with = shortcut
        for action in actions.values():
            if action == self.action:
                continue
            if shortcut in action.get_shortcuts():
                txt = ': '.join(action.menu_path + [action['text']])
                txt = txt.replace('&', '').removesuffix('...')
                msg = ('<p>This shortcut is already used for:</p>'
                       f'<p>{txt}</p>'
                       '<p>Do you want to remove the other shortcut'
                       ' to save this one?</p>')
                reply = QtWidgets.QMessageBox.question(
                    self, 'Save Shortcut?', msg)
                if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                    self.remove_from_other = action
                else:
                    self.setKeySequence(self.old_value)


class KeyboardShortcutsDelegate(QtWidgets.QStyledItemDelegate):

    def createEditor(self, parent, option, index):
        return KeyboardShortcutsEditor(parent, index)

    def setModelData(self, editor, model, index):
        model.setData(
            index,
            editor.keySequence(),
            QtCore.Qt.ItemDataRole.EditRole,
            remove_from_other=editor.remove_from_other)


class KeyboardShortcutsModel(QtCore.QAbstractTableModel):
    """An entry in the keyboard shortcuts table."""

    HEADER = ('Action', '✎', 'Shortcut', 'Alternative')

    def __init__(self):
        super().__init__()
        self.settings = KeyboardSettings()

    def rowCount(self, parent):
        return len(actions)

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
                return '✎'
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


class KeyboardShortcutsProxy(QtCore.QSortFilterProxyModel):

    def __init__(self):
        super().__init__()
        self.setSourceModel(KeyboardShortcutsModel())
        self.setFilterCaseSensitivity(
            QtCore.Qt.CaseSensitivity.CaseInsensitive)

    def data(self, index, role):
        if (role == QtCore.Qt.ItemDataRole.BackgroundRole
                and index.row() % 2):
            return QtGui.QColor(*constants.COLORS['Table:AlternativeRow'])
        else:
            return super().data(index, role)

    def setData(self, index, value, role, remove_from_other=None):
        result = self.sourceModel().setData(
            self.mapToSource(index),
            value,
            role,
            remove_from_other=remove_from_other)
        return result


class KeyboardShortcutsView(QtWidgets.QTableView):

    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumSize(QtCore.QSize(400, 200))
        self.setItemDelegate(KeyboardShortcutsDelegate())
        self.setShowGrid(False)
        self.setModel(KeyboardShortcutsProxy())
        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.setSelectionMode(
            QtWidgets.QHeaderView.SelectionMode.SingleSelection)
        settings_events.restore_defaults.connect(self.on_restore_defaults)

    def on_restore_defaults(self):
        self.viewport().update()


class KeyboardSettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Keyboard Shortcuts')
        tabs = QtWidgets.QTabWidget()

        # Keyboard shortcuts
        keyboard = QtWidgets.QWidget(parent)
        kb_layout = QtWidgets.QVBoxLayout()
        keyboard.setLayout(kb_layout)
        table = KeyboardShortcutsView(keyboard)
        search_input = QtWidgets.QLineEdit()
        search_input.setPlaceholderText('Search...')
        search_input.textChanged.connect(
            lambda value: table.model().setFilterFixedString(value))
        kb_layout.addWidget(search_input)
        kb_layout.addWidget(table)
        tabs.addTab(keyboard, '&Keyboard Shortcuts')

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
            'Do you want to restore all settings to their default values?')

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            KeyboardSettings().restore_defaults()
