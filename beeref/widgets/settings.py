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

from beeref import constants
from beeref.config import BeeSettings, settings_events


logger = logging.getLogger(__name__)


class ImageStorageFormatWidget(QtWidgets.QGroupBox):
    KEY = 'FileIO/image_storage_format'
    OPTIONS = (
        ('best', 'Best Guess',
         ('Small images and images with alpha channel are stored as png,'
          ' everything else as jpg')),
        ('png', 'Always PNG', 'Lossless, but large bee file'),
        ('jpg', 'Always JPG',
         'Small bee file, but lossy and no transparency support'))

    def __init__(self, parent):
        super().__init__('Image Storage Format:')
        parent.settings_widgets.append(self)
        self.settings = BeeSettings()
        settings_events.restore_defaults.connect(self.on_restore_defaults)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        helptxt = QtWidgets.QLabel(
            'How images are stored inside bee files.'
            ' Changes will only take effect on newly saved images.')
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


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(f'{constants.APPNAME} Settings')
        tabs = QtWidgets.QTabWidget()

        self.settings_widgets = []

        # Miscellaneous
        misc = QtWidgets.QWidget()
        misc_layout = QtWidgets.QGridLayout()
        misc.setLayout(misc_layout)
        misc_layout.addWidget(ImageStorageFormatWidget(self), 0, 0)
        tabs.addTab(misc, '&Miscellaneous')

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(tabs)

        # Bottom row of buttons
        buttons = QtWidgets.QWidget()
        btn_layout = QtWidgets.QHBoxLayout()
        buttons.setLayout(btn_layout)
        reset_btn = QtWidgets.QPushButton('&Restore Defaults')
        reset_btn.setAutoDefault(False)
        reset_btn.clicked.connect(self.on_restore_defaults)
        btn_layout.addWidget(reset_btn)

        close_btn = QtWidgets.QPushButton('&Close')
        close_btn.setAutoDefault(True)
        close_btn.clicked.connect(self.on_close)
        btn_layout.addWidget(close_btn)
        btn_layout.insertStretch(1)

        layout.addWidget(buttons)
        self.show()

    def on_close(self, *args, **kwargs):
        self.close()

    def on_restore_defaults(self, *args, **kwargs):
        reply = QtWidgets.QMessageBox.question(
            self,
            'Restore defaults?',
            'Do you want to restore all settings to their default values?')

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            BeeSettings().restore_defaults()
