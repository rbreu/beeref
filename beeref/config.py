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

commandline_args = parser.parse_args()
