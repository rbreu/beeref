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

APPNAME = 'BeeRef'
APPNAME_FULL = f'{APPNAME} Reference Image Viewer'
VERSION = '0.3.3'
WEBSITE = 'https://github.com/rbreu/beeref'
COPYRIGHT = 'Copyright © 2021-2024 Rebecca Breu'

CHANGED_SYMBOL = '✎'

COLORS = {
    # Qt:
    'Active:Base': (60, 60, 60),
    'Active:AlternateBase': (70, 70, 70),
    'Active:Window': (40, 40, 40),
    'Active:Button': (40, 40, 40),
    'Active:Text': (200, 200, 200),
    'Active:HighlightedText': (255, 255, 255),
    'Active:WindowText': (200, 200, 200),
    'Active:ButtonText': (200, 200, 200),
    'Active:Highlight': (83, 167, 165),
    'Active:Link': (90, 181, 179),

    'Disabled:Base': (40, 40, 40),
    'Disabled:Window': (40, 40, 40, 50),
    'Disabled:WindowText': (120, 120, 120),
    'Disabled:Light': (0, 0, 0, 0),
    'Disabled:Text': (140, 140, 140),

    # BeeRef specific:
    'Scene:Selection': (116, 234, 231),
    'Scene:Canvas': (60, 60, 60),
    'Scene:Text': (200, 200, 200),
}
