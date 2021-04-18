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

MENU_SEPARATOR = 0

menu_structure = [
    {
        'menu': '&File',
        'items': [
            'new_scene',
            'open',
            MENU_SEPARATOR,
            'save',
            'save_as',
            MENU_SEPARATOR,
            'quit',
        ],
    },
    {
        'menu': '&Edit',
        'items': [
            'undo',
            'redo',
            MENU_SEPARATOR,
            'select_all',
            'deselect_all',
            MENU_SEPARATOR,
            'paste',
            'delete',
        ],
    },
    {
        'menu': '&View',
        'items': [
            'fit_scene',
            'fit_selection',
            MENU_SEPARATOR,
            'fullscreen',
            'always_on_top',
            'show_scrollbars',
        ],
    },
    'insert_images',
    {
        'menu': '&Transform',
        'items': [
            'flip_horizontally',
            'flip_vertically',
            MENU_SEPARATOR,
            'reset_scale',
            'reset_rotation',
            'reset_flip',
            'reset_transforms',
        ],
    },
    {
        'menu': '&Normalize',
        'items': [
            'normalize_height',
            'normalize_width',
            'normalize_size',
        ],
    },
    {
        'menu': '&Help',
        'items': [
            'help',
        ],
    },
]
