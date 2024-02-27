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

"""Handling of command line args and Qt settings."""

import argparse
import logging
import logging.config
import os.path

from PyQt6 import QtCore

from beeref import constants
from beeref.logging import qt_message_handler


logger = logging.getLogger(__name__)


parser = argparse.ArgumentParser(
    description=f'{constants.APPNAME_FULL} {constants.VERSION}')
parser.add_argument(
    'filename',
    nargs='?',
    default=None,
    help='Bee file to open')
parser.add_argument(
    '--settings-dir',
    help='settings directory to use instead of default location')
parser.add_argument(
    '-l', '--loglevel',
    default='INFO',
    choices=list(logging._nameToLevel.keys()),
    help='log level for console output')
parser.add_argument(
    '--debug-boundingrects',
    default=False,
    action='store_true',
    help='draw item\'s bounding rects for debugging')
parser.add_argument(
    '--debug-shapes',
    default=False,
    action='store_true',
    help='draw item\'s mouse event shapes for debugging')
parser.add_argument(
    '--debug-handles',
    default=False,
    action='store_true',
    help='draw item\'s transform handle areas for debugging')


class CommandlineArgs:
    """Wrapper around argument parsing.

    Checking for unknown arguments is configurable so that it can be
    deliberately enabled from the main() function while ignored for
    other imports so that unit tests won't fail.

    This is a singleton so that arguments are only parsed once, unless
    ``with_check`` is ``True``.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance or kwargs.get('with_check'):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, with_check=False):
        if not hasattr(self, '_args'):
            if with_check:
                self._args = parser.parse_args()
            else:
                self._args = parser.parse_known_args()[0]

    def __getattribute__(self, name):
        if name == '_args':
            return super().__getattribute__(name)
        else:
            return getattr(self._args, name)


class BeeSettingsEvents(QtCore.QObject):
    restore_defaults = QtCore.pyqtSignal()
    restore_keyboard_defaults = QtCore.pyqtSignal()


# We want to send and receive settings events globally, not per
# BeeSettings instance. Since we can't instantiate BeeSettings
# globally on module level (because the Qt app doesn't exist yet), we
# use this events proxy
settings_events = BeeSettingsEvents()


class BeeSettings(QtCore.QSettings):

    FIELDS = {
        'Items/image_storage_format': {
            'default': 'best',
            'validate': lambda x: x in ('png', 'jpg', 'best'),
        },
        'Items/arrange_gap': {
            'default': 0,
            'cast': int,
            'validate': lambda x: 0 <= x <= 200,
        },
    }

    def __init__(self):
        settings_format = QtCore.QSettings.Format.IniFormat
        settings_scope = QtCore.QSettings.Scope.UserScope
        settings_dir = self.get_settings_dir()
        if settings_dir:
            QtCore.QSettings.setPath(
                settings_format, settings_scope, settings_dir)
        super().__init__(
            settings_format,
            settings_scope,
            constants.APPNAME,
            constants.APPNAME)

    def valueOrDefault(self, key):
        """Get the value for key, or the default value specified in FIELDS.

        This is the method to be used for configurable settings (as
        opposed to settings that BeeRef stores on its own.)

        This will validate and type cast the given value if 'cast' and
        'validate' are specified in the FIELDS entry for the given
        key. The default value will be returned if validation or type
        casting fails.

        """

        val = self.value(key)
        conf = self.FIELDS[key]
        if val is None:
            val = conf['default']
        if 'cast' in conf:
            try:
                val = conf['cast'](val)
            except (ValueError, TypeError):
                val = conf['default']
        if 'validate' in conf:
            if not conf['validate'](val):
                val = conf['default']
        return val

    def value_changed(self, key):
        """Whether the value for given key has changed from its default."""

        return self.valueOrDefault(key) != self.FIELDS[key]['default']

    def restore_defaults(self):
        """Restore all the values specified in FILEDS to their default values
        by removing them from the settings file.
        """

        logger.debug('Restoring settings to defaults')
        for key in self.FIELDS.keys():
            self.remove(key)
        settings_events.restore_defaults.emit()

    def fileName(self):
        return os.path.normpath(super().fileName())

    def get_settings_dir(self):  # pragma: no cover
        args = CommandlineArgs()
        return args.settings_dir

    def update_recent_files(self, filename):
        filename = os.path.abspath(filename)
        values = self.get_recent_files()
        if filename in values:
            values.remove(filename)
        values.insert(0, filename)

        self.beginWriteArray('RecentFiles')
        for i, filename in enumerate(values[:10]):
            self.setArrayIndex(i)
            self.setValue('path', filename)
        self.endArray()

    def get_recent_files(self, existing_only=False):
        values = []
        size = self.beginReadArray('RecentFiles')
        for i in range(size):
            self.setArrayIndex(i)
            values.append(self.value('path'))
        self.endArray()

        if existing_only:
            values = [f for f in values if os.path.exists(f)]
        return values


class KeyboardSettings(QtCore.QSettings):

    def __init__(self):
        settings_format = QtCore.QSettings.Format.IniFormat
        filename = os.path.join(
            os.path.dirname(BeeSettings().fileName()),
            'KeyboardSettings.ini')
        super().__init__(filename, settings_format)

    def set_shortcuts(self, group, key, values, default=None):
        if values == default:
            self.remove(f'{group}/{key}')
        else:
            self.setValue(f'{group}/{key}', ', '.join(values))

    def get_shortcuts(self, group, key, default=None):
        values = self.value(f'{group}/{key}')
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


def logfile_name():
    return os.path.join(
        os.path.dirname(BeeSettings().fileName()), f'{constants.APPNAME}.log')


logging_conf = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': ('{asctime} {name} {process:d} {thread:d} {message}'),
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': CommandlineArgs().loglevel,
        },
        'file': {
            'class': 'beeref.logging.BeeRotatingFileHandler',
            'formatter': 'verbose',
            'filename': logfile_name(),
            'maxBytes': 1024 * 1000,  # 1MB
            'backupCount': 1,
            'level': 'DEBUG',
            'delay': True,
        }
    },
    'loggers': {
        'beeref': {
            'handlers': ['console', 'file'],
            'level': 'TRACE',
            'propagate': False,
        },
        'Qt': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
}

logging.config.dictConfig(logging_conf)

# Redirect Qt logging to Python logger:
QtCore.qInstallMessageHandler(qt_message_handler)
