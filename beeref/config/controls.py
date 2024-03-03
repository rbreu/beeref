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

"""Handling of keyboard shortcuts and mouse controls."""

import logging
import logging.config
import os.path

from beeref.config.settings import BeeSettings, settings_events

from PyQt6 import QtCore


logger = logging.getLogger(__name__)


class KeyboardSettings(QtCore.QSettings):

    def __init__(self):
        settings_format = QtCore.QSettings.Format.IniFormat
        filename = os.path.join(
            os.path.dirname(BeeSettings().fileName()),
            'KeyboardSettings.ini')
        super().__init__(filename, settings_format)

    def set_keyboard_shortcuts(self, key, values, default=None):
        if values == default:
            self.remove(f'Actions/{key}')
        else:
            self.setValue(f'Actions/{key}', ', '.join(values))

    def get_keyboard_shortcuts(self, key, default=None):
        values = self.value(f'Actions/{key}')
        if values is not None:
            values = list(filter(lambda x: x, values.split(', ')))
            return values

        return list(default or [])  # Always return new instance of default

    def restore_defaults(self):
        """Restore all the values specified in FILEDS to their default values
        by removing them from the settings file.
        """

        logger.debug('Restoring keyboard shortcuts to defaults')
        for key in self.allKeys():
            self.remove(key)
        settings_events.restore_keyboard_defaults.emit()
