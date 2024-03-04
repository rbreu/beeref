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

import json
import logging
import logging.config
import os.path

from beeref.config.settings import BeeSettings, settings_events
from beeref.utils import ActionList

from PyQt6 import QtCore
from PyQt6.QtCore import Qt


logger = logging.getLogger(__name__)


class MouseConfig:

    MODIFIER_MAP = {
        'ctrl': Qt.KeyboardModifier.ControlModifier,
        'alt': Qt.KeyboardModifier.AltModifier,
        'shift': Qt.KeyboardModifier.ShiftModifier,
        'none': Qt.KeyboardModifier.NoModifier,
    }

    def __init__(self, id, text, default, invertible):
        self.id = id
        self.text = text
        self.default = default
        self.invertible = invertible

    def load(self, raw):
        if raw:
            values = json.loads(raw)
        else:
            values = {}

        self.modifiers = values.get('modifiers', self.default)
        self.inverted = values.get('inverted', False)

    def matches_event(self, event, with_buttons):
        if self.modifiers is None:
            return False

        if len(self.modifiers) == 0:
            combined = Qt.KeyboardModifier.NoModifier
        else:
            combined = self.MODIFIER_MAP[self.modifiers[0]]
            for mod in self.modifiers[1:]:
                combined = combined | self.MODIFIER_MAP[mod]

        return combined == event.modifiers()


class KeyboardSettings(QtCore.QSettings):

    MOUSEWHEEL_ACTIONS = ActionList([
        MouseConfig(
            id='zoom',
            text='Zoom',
            default=(),
            invertible=True,
        ),
        MouseConfig(
            id='pan_horizontal',
            text='Pan horizontally',
            default=('shift',),
            invertible=True,
        ),
        MouseConfig(
            id='pan_vertical',
            text='Pan vertically',
            default=('shift', 'ctrl'),
            invertible=True,
        ),
        MouseConfig(
            id='movewin_horizontal',
            text='Move window horizontally',
            default=None,
            invertible=False,
        ),
        MouseConfig(
            id='movewin_vertical',
            text='Move window vertically',
            default=None,
            invertible=False,
        ),
    ])

    def __init__(self):
        settings_format = QtCore.QSettings.Format.IniFormat
        filename = os.path.join(
            os.path.dirname(BeeSettings().fileName()),
            'KeyboardSettings.ini')
        super().__init__(filename, settings_format)

        for action in self.MOUSEWHEEL_ACTIONS:
            self.get_mousewheel_config(action)

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

        logger.debug('Restoring keyboard and mouse controls to defaults')
        for key in self.allKeys():
            self.remove(key)
        settings_events.restore_keyboard_defaults.emit()

    def get_mousewheel_config(self,  key):
        conf = self.MOUSEWHEEL_ACTIONS[key]
        conf.load(self.value(f'MouseWheel/{key}'))
        return conf

    def mousewheel_action_for_event(self, event):
        for action in self.MOUSEWHEEL_ACTIONS.values():
            if action.matches_event(event, with_buttons=False):
                return action.id, action.inverted
