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

from collections import OrderedDict
from functools import cached_property
import logging
import logging.config
import os.path

from beeref.config.settings import BeeSettings, settings_events
from beeref.utils import ActionList

from PyQt6 import QtCore
from PyQt6.QtCore import Qt


logger = logging.getLogger(__name__)


class MouseConfig:

    MODIFIER_MAP = OrderedDict((
        ('No Modifier', Qt.KeyboardModifier.NoModifier),
        ('Shift', Qt.KeyboardModifier.ShiftModifier),
        ('Ctrl', Qt.KeyboardModifier.ControlModifier),
        ('Alt', Qt.KeyboardModifier.AltModifier),
        ('Meta', Qt.KeyboardModifier.MetaModifier),
        ('Keypad', Qt.KeyboardModifier.KeypadModifier),
    ))

    def __init__(self, id, group, text, modifiers, invertible):
        self.id = id
        self.group = group
        self.text = text
        self.modifiers = modifiers
        self.invertible = invertible
        self.inverted = False

    def __eq__(self, other):
        return self.id == other.id

    @cached_property
    def kb_settings(self):
        return KeyboardSettings()

    def get_modifiers(self):
        return self.kb_settings.get_list(
            'MouseWheel', f'{self.id}_modifiers', self.modifiers)

    def set_modifiers(self, value):
        logger.debug(
            f'Setting mouse wheel modifiers for "{self.id}" to: {value}')
        self.kb_settings.set_list(
            'MouseWheel', f'{self.id}_modifiers', value, self.modifiers)

    def get_inverted(self):
        return self.kb_settings.get_value(
            'MouseWheel', f'{self.id}_inverted', self.inverted)

    def set_inverted(self, value):
        logger.debug(
            f'Setting mouse wheel inverted for "{self.id}" to: {value}')
        self.kb_settings.set_value(
            'MouseWheel', f'{self.id}_inverted', value, self.inverted)

    def controls_changed(self):
        """Whether controls have changed from their defaults."""
        return (set(self.get_modifiers()) != set(self.modifiers)
                or self.get_inverted() != self.inverted)

    def matches_event(self, event):
        modifiers = self.get_modifiers()
        if not modifiers:
            return False

        combined = self.MODIFIER_MAP[modifiers[0]]
        for mod in modifiers[1:]:
            combined = combined | self.MODIFIER_MAP[mod]

        return combined == event.modifiers()


class KeyboardSettings(QtCore.QSettings):

    MOUSEWHEEL_ACTIONS = ActionList([
        MouseConfig(
            id='zoom1',
            group='zoom',
            text='Zoom',
            modifiers=('No Modifier',),
            invertible=True,
        ),
        MouseConfig(
            id='zoom2',
            group='zoom',
            text='Zoom (alternative)',
            modifiers=(),
            invertible=True,
        ),
        MouseConfig(
            id='pan_horizontal1',
            group='pan_horizontal',
            text='Pan horizontally',
            modifiers=('Shift',),
            invertible=True,
        ),
        MouseConfig(
            id='pan_horizontal2',
            group='pan_horizontal',
            text='Pan horizontally (alternative)',
            modifiers=(),
            invertible=True,
        ),
        MouseConfig(
            id='pan_vertical1',
            group='pan_vertical',
            text='Pan vertically',
            modifiers=('Shift', 'Ctrl'),
            invertible=True,
        ),
        MouseConfig(
            id='pan_vertical2',
            group='pan_vertical',
            text='Pan vertically (alternative)',
            modifiers=(),
            invertible=True,
        ),
    ])

    def __init__(self):
        settings_format = QtCore.QSettings.Format.IniFormat
        filename = os.path.join(
            os.path.dirname(BeeSettings().fileName()),
            'KeyboardSettings.ini')
        super().__init__(filename, settings_format)

    def set_list(self, group, key, values, default=None):
        if values == default:
            self.remove(f'{group}/{key}')
        else:
            self.setValue(f'{group}/{key}', ', '.join(values))

    def get_list(self, group, key, default=None):
        values = self.value(f'{group}/{key}')
        if values is not None:
            values = list(filter(lambda x: x, values.split(', ')))
            return values

        return list(default or [])  # Always return new instance of default

    def get_value(self, group, key, default=None):
        value = self.value(f'{group}/{key}')
        return default if value is None else value

    def set_value(self, group, key, value, default=None):
        if value == default:
            self.remove(f'{group}/{key}')
        else:
            self.setValue(f'{group}/{key}', value)

    def restore_defaults(self):
        """Restore all the values specified in FILEDS to their default values
        by removing them from the settings file.
        """

        logger.debug('Restoring keyboard and mouse controls to defaults')
        for key in self.allKeys():
            self.remove(key)
        settings_events.restore_keyboard_defaults.emit()

    def mousewheel_action_for_event(self, event):
        for action in self.MOUSEWHEEL_ACTIONS.values():
            if action.matches_event(event):
                return action.group, action.get_inverted()
        return None, None
