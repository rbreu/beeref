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

from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt

from beeref import constants
from beeref.config import BeeSettings, settings_events


logger = logging.getLogger(__name__)


class GroupBase(QtWidgets.QGroupBox):
    TITLE = None
    HELPTEXT = None
    KEY = None

    def __init__(self):
        super().__init__()
        self.settings = BeeSettings()
        self.update_title()
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        settings_events.restore_defaults.connect(self.on_restore_defaults)

        if self.HELPTEXT:
            helptxt = QtWidgets.QLabel(self.HELPTEXT)
            helptxt.setWordWrap(True)
            self.layout.addWidget(helptxt)

    def update_title(self):
        title = [self.TITLE]
        if self.settings.value_changed(self.KEY):
            title.append(constants.CHANGED_SYMBOL)
        self.setTitle(' '.join(title))

    def on_value_changed(self, value):
        if self.ignore_value_changed:
            return

        value = self.convert_value_from_qt(value)
        if value != self.settings.valueOrDefault(self.KEY):
            logger.debug(f'Setting {self.KEY} changed to: {value}')
            self.settings.setValue(self.KEY, value)
            self.update_title()

    def convert_value_from_qt(self, value):
        return value

    def on_restore_defaults(self):
        new_value = self.settings.valueOrDefault(self.KEY)
        self.ignore_value_changed = True
        self.set_value(new_value)
        self.ignore_value_changed = False
        self.update_title()


class RadioGroup(GroupBase):
    OPTIONS = None

    def __init__(self):
        super().__init__()

        self.ignore_value_changed = True
        self.buttons = {}
        for (value, label, helptext) in self.OPTIONS:
            btn = QtWidgets.QRadioButton(label)
            self.buttons[value] = btn
            btn.setToolTip(helptext)
            btn.toggled.connect(partial(self.on_value_changed, value=value))
            if value == self.settings.valueOrDefault(self.KEY):
                btn.setChecked(True)
            self.layout.addWidget(btn)

        self.ignore_value_changed = False
        self.layout.addStretch(100)

    def set_value(self, value):
        for old_value, btn in self.buttons.items():
            btn.setChecked(old_value == value)


class IntegerGroup(GroupBase):
    MIN = None
    MAX = None

    def __init__(self):
        super().__init__()
        self.input = QtWidgets.QSpinBox()
        self.input.setRange(self.MIN, self.MAX)
        self.set_value(self.settings.valueOrDefault(self.KEY))
        self.input.valueChanged.connect(self.on_value_changed)
        self.layout.addWidget(self.input)
        self.layout.addStretch(100)
        self.ignore_value_changed = False

    def set_value(self, value):
        self.input.setValue(value)


class SingleCheckboxGroup(GroupBase):
    LABEL = None

    def __init__(self):
        super().__init__()
        self.input = QtWidgets.QCheckBox(self.LABEL)
        self.set_value(self.settings.valueOrDefault(self.KEY))
        self.input.checkStateChanged.connect(self.on_value_changed)
        self.layout.addWidget(self.input)
        self.layout.addStretch(100)
        self.ignore_value_changed = False

    def set_value(self, value):
        self.input.setChecked(value)

    def convert_value_from_qt(self, value):
        return value == Qt.CheckState.Checked


class ArrangeDefaultWidget(RadioGroup):
    TITLE = 'Default Arrange Method:'
    HELPTEXT = ('How images are arranged when inserted in batch')
    KEY = 'Items/arrange_default'
    OPTIONS = (
        ('optimal', 'Optimal', 'Arrange Optimal'),
        ('horizontal', 'Horizontal (by filename)',
         'Arrange Horizontal (by filename)'),
        ('vertical', 'Vertical (by filename)',
         'Arrange Vertical (by filename)'),
        ('square', 'Square (by filename)', 'Arrannge Square (by filename)'))


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


class AllocationLimitWidget(IntegerGroup):
    TITLE = 'Maximum Image Size:'
    HELPTEXT = ('The maximum image size that can be loaded (in megabytes). '
                'Set to 0 for no limitation.')
    KEY = 'Items/image_allocation_limit'
    MIN = 0
    MAX = 10000


class ConfirmCloseUnsavedWidget(SingleCheckboxGroup):
    TITLE = 'Confirm when closing an unsaved file:'
    HELPTEXT = (
        'When about to close an unsaved file, should BeeRef ask for '
        'confirmation?')
    LABEL = 'Confirm when closing'
    KEY = 'Save/confirm_close_unsaved'


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(f'{constants.APPNAME} Settings')
        tabs = QtWidgets.QTabWidget()

        # Miscellaneous
        misc = QtWidgets.QWidget()
        misc_layout = QtWidgets.QGridLayout()
        misc.setLayout(misc_layout)
        misc_layout.addWidget(ConfirmCloseUnsavedWidget(), 0, 0)
        tabs.addTab(misc, '&Miscellaneous')

        # Images & Items
        items = QtWidgets.QWidget()
        items_layout = QtWidgets.QGridLayout()
        items.setLayout(items_layout)
        items_layout.addWidget(ImageStorageFormatWidget(), 0, 0)
        items_layout.addWidget(AllocationLimitWidget(), 0, 1)
        items_layout.addWidget(ArrangeGapWidget(), 1, 0)
        items_layout.addWidget(ArrangeDefaultWidget(), 1, 1)
        tabs.addTab(items, '&Images && Items')

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
