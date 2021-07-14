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
        'text': '&Quit',
        'shortcuts': ['Ctrl+Q'],
        'callback': 'on_action_quit',
    },
    {
        'id': 'insert_images',
        'text': '&Images...',
        'shortcuts': ['Ctrl+I'],
        'callback': 'on_action_insert_images',
    },
    {
        'id': 'insert_text',
        'text': '&Text',
        'shortcuts': ['Ctrl+T'],
        'callback': 'on_action_insert_text',
    },
    {
        'id': 'undo',
        'text': '&Undo',
        'shortcuts': ['Ctrl+Z'],
        'callback': 'on_action_undo',
        'group': 'active_when_can_undo',
    },
    {
        'id': 'redo',
        'text': '&Redo',
        'shortcuts': ['Ctrl+Shift+Z'],
        'callback': 'on_action_redo',
        'group': 'active_when_can_redo',
    },
    {
        'id': 'copy',
        'text': '&Copy',
        'shortcuts': ['Ctrl+C'],
        'callback': 'on_action_copy',
        'group': 'active_when_selection',
    },
    {
        'id': 'cut',
        'text': 'Cu&t',
        'shortcuts': ['Ctrl+X'],
        'callback': 'on_action_cut',
        'group': 'active_when_selection',
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
    },
    {
        'id': 'raise_to_top',
        'text': '&Raise to Top',
        'shortcuts': ['PgUp'],
        'callback': 'on_action_raise_to_top',
        'group': 'active_when_selection',
    },
    {
        'id': 'lower_to_bottom',
        'text': 'Lower to Bottom',
        'shortcuts': ['PgDown'],
        'callback': 'on_action_lower_to_bottom',
        'group': 'active_when_selection',
    },
    {
        'id': 'normalize_height',
        'text': '&Height',
        'shortcuts': ['Shift+H'],
        'callback': 'on_action_normalize_height',
        'group': 'active_when_selection',
    },
    {
        'id': 'normalize_width',
        'text': '&Width',
        'shortcuts': ['Shift+W'],
        'callback': 'on_action_normalize_width',
        'group': 'active_when_selection',
    },
    {
        'id': 'normalize_size',
        'text': '&Size',
        'shortcuts': ['Shift+S'],
        'callback': 'on_action_normalize_size',
        'group': 'active_when_selection',
    },
    {
        'id': 'arrange_optimal',
        'text': '&Optimal',
        'shortcuts': ['Shift+O'],
        'callback': 'on_action_arrange_optimal',
        'group': 'active_when_selection',
    },
    {
        'id': 'arrange_horizontal',
        'text': '&Horizontal',
        'callback': 'on_action_arrange_horizontal',
        'group': 'active_when_selection',
    },
    {
        'id': 'arrange_vertical',
        'text': '&Vertical',
        'callback': 'on_action_arrange_vertical',
        'group': 'active_when_selection',
    },
    {
        'id': 'flip_horizontally',
        'text': 'Flip &Horizontally',
        'shortcuts': ['H'],
        'callback': 'on_action_flip_horizontally',
        'group': 'active_when_selection',
    },
    {
        'id': 'flip_vertically',
        'text': 'Flip &Vertically',
        'shortcuts': ['V'],
        'callback': 'on_action_flip_vertically',
        'group': 'active_when_selection',
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
    },
    {
        'id': 'reset_scale',
        'text': 'Reset &Scale',
        'callback': 'on_action_reset_scale',
        'group': 'active_when_selection',
    },
    {
        'id': 'reset_rotation',
        'text': 'Reset &Rotation',
        'callback': 'on_action_reset_rotation',
        'group': 'active_when_selection',
    },
    {
        'id': 'reset_flip',
        'text': 'Reset &Flip',
        'callback': 'on_action_reset_flip',
        'group': 'active_when_selection',
    },
    {
        'id': 'reset_transforms',
        'text': 'Reset &All',
        'shortcuts': ['R'],
        'callback': 'on_action_reset_transforms',
        'group': 'active_when_selection',
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
        'id': 'show_menubar',
        'text': 'Show &Menu Bar',
        'checkable': True,
        'settings': 'View/show_menubar',
        'callback': 'on_action_show_menubar',
    },
    {
        'id': 'show_titlebar',
        'text': 'Show &Title Bar',
        'checkable': True,
        'checked': True,
        'callback': 'on_action_show_titlebar',
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
