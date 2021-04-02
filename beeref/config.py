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

import argparse
import logging


parser = argparse.ArgumentParser(description='BeeRef referance image viewer')
parser.add_argument(
    'filename',
    nargs='?',
    default=None,
    help='Bee file to open')
parser.add_argument(
    '-l', '--loglevel',
    default='INFO',
    choices=list(logging._nameToLevel.keys()),
    help='log level for console output')
parser.add_argument(
    '--draw-debug-shapes',
    default=False,
    action='store_true',
    help='draw debug shapes for bounding rects and interactable areas')


class CommandlineArgs():
    """Wrapper around argument parsing.

    Checking for unknown arugments is configurable so that it can be
    deliberately enabled from the main() function while ignored for
    other imports. This is a singleton so that arguments are only
    parsed once.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, with_check=False):
        if with_check:
            self._args = parser.parse_args()
        else:
            self._args = parser.parse_known_args()[0]

    def __getattribute__(self, name):
        if name == '_args':
            return super().__getattribute__(name)
        else:
            return getattr(self._args, name)
