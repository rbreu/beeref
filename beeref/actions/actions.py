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

actions = [
    {
        'id': 'open',
        'text': '&Open',
        'shortcuts': ['Ctrl+O'],
        'callback': 'on_action_open',
    },
    {
        'id': 'save',
        'text': '&Save',
        'shortcuts': ['Ctrl+S'],
        'callback': 'on_action_save',
    },
    {
        'id': 'save_as',
        'text': 'Save &As...',
        'shortcuts': ['Ctrl+Shift+S'],
        'callback': 'on_action_save_as',
    },
    {
        'id': 'quit',
        'text': '&Quit...',
        'shortcuts': ['Ctrl+Q'],
        'callback': 'on_action_quit',
    },
    {
        'id': 'insert_images',
        'text': '&Insert Images...',
        'shortcuts': ['Ctrl+I'],
        'callback': 'on_action_insert_images',
    },
    {
        'id': 'undo',
        'text': '&Undo',
        'shortcuts': ['Ctrl+Z'],
        'callback': 'on_action_undo',
        'group': 'active_when_can_undo',
        'enabled': False,
    },
    {
        'id': 'redo',
        'text': '&Redo',
        'shortcuts': ['Ctrl+Shift+Z'],
        'callback': 'on_action_redo',
        'group': 'active_when_can_redo',
        'enabled': False,
    },
    {
        'id': 'paste',
        'text': '&Paste',
        'shortcuts': ['Ctrl+V'],
        'callback': 'on_action_paste',
    },
    {
        'id': 'delete',
        'text': '&Delete',
        'shortcuts': ['Del'],
        'callback': 'on_action_delete_items',
        'group': 'active_when_selection',
        'enabled': False,
    },
    {
        'id': 'normalize_height',
        'text': '&Height',
        'shortcuts': ['Shift+H'],
        'callback': 'on_action_normalize_height',
        'group': 'active_when_selection',
        'enabled': False,
    },
    {
        'id': 'normalize_width',
        'text': '&Width',
        'shortcuts': ['Shift+W'],
        'callback': 'on_action_normalize_width',
        'group': 'active_when_selection',
        'enabled': False,
    },
    {
        'id': 'normalize_size',
        'text': '&Size',
        'shortcuts': ['Shift+S'],
        'callback': 'on_action_normalize_size',
        'group': 'active_when_selection',
        'enabled': False,
    },
]
