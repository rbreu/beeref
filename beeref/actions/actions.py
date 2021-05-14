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
    {
        'id': 'arrange_optimal',
        'text': '&Optimal',
        'shortcuts': ['Shift+O'],
        'callback': 'on_action_arrange_optimal',
        'group': 'active_when_selection',
        'enabled': False,
    },
    {
        'id': 'arrange_horizontal',
        'text': '&Horizontal',
        'callback': 'on_action_arrange_horizontal',
        'group': 'active_when_selection',
        'enabled': False,
    },
    {
        'id': 'arrange_vertical',
        'text': '&Vertical',
        'callback': 'on_action_arrange_vertical',
        'group': 'active_when_selection',
        'enabled': False,
    },
    {
        'id': 'flip_horizontally',
        'text': 'Flip &Horizontally',
        'shortcuts': ['H'],
        'callback': 'on_action_flip_horizontally',
        'group': 'active_when_selection',
        'enabled': False,
    },
    {
        'id': 'flip_vertically',
        'text': 'Flip &Vertically',
        'shortcuts': ['V'],
        'callback': 'on_action_flip_vertically',
        'group': 'active_when_selection',
        'enabled': False,
    },
    {
        'id': 'new_scene',
        'text': '&New Scene',
        'shortcuts': ['Ctrl+N'],
        'callback': 'clear_scene',
    },
    {
        'id': 'fit_scene',
        'text': '&Fit Scene',
        'shortcuts': ['1'],
        'callback': 'on_action_fit_scene',
    },
    {
        'id': 'fit_selection',
        'text': 'Fit &Selection',
        'shortcuts': ['2'],
        'callback': 'on_action_fit_selection',
        'group': 'active_when_selection',
        'enabled': False,
    },
    {
        'id': 'reset_scale',
        'text': 'Reset &Scale',
        'callback': 'on_action_reset_scale',
        'group': 'active_when_selection',
        'enabled': False,
    },
    {
        'id': 'reset_rotation',
        'text': 'Reset &Rotation',
        'callback': 'on_action_reset_rotation',
        'group': 'active_when_selection',
        'enabled': False,
    },
    {
        'id': 'reset_flip',
        'text': 'Reset &Flip',
        'callback': 'on_action_reset_flip',
        'group': 'active_when_selection',
        'enabled': False,
    },
    {
        'id': 'reset_transforms',
        'text': 'Reset &All',
        'shortcuts': ['R'],
        'callback': 'on_action_reset_transforms',
        'group': 'active_when_selection',
        'enabled': False,
    },
    {
        'id': 'select_all',
        'text': '&Select All',
        'shortcuts': ['Ctrl+A'],
        'callback': 'on_action_select_all',
    },
    {
        'id': 'deselect_all',
        'text': 'Deselect &All',
        'shortcuts': ['Ctrl+Shift+A'],
        'callback': 'on_action_deselect_all',
    },
    {
        'id': 'help',
        'text': '&Help',
        'shortcuts': ['F1', 'Ctrl+H'],
        'callback': 'on_action_help',
    },
    {
        'id': 'about',
        'text': '&About',
        'callback': 'on_action_about',
    },
    {
        'id': 'debuglog',
        'text': 'Show &Debug Log',
        'callback': 'on_action_debuglog',
    },
    {
        'id': 'show_scrollbars',
        'text': 'Show &Scrollbars',
        'checkable': True,
        'settings': 'View/show_scrollbars',
        'callback': 'on_action_show_scrollbars',
    },
    {
        'id': 'fullscreen',
        'text': '&Fullscreen',
        'shortcuts': ['F11'],
        'checkable': True,
        'callback': 'on_action_fullscreen',
    },
    {
        'id': 'always_on_top',
        'text': '&Always On Top',
        'checkable': True,
        'callback': 'on_action_always_on_top',
    },
]
