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

from functools import cached_property
import logging

from PyQt6 import QtGui

from beeref.actions.menu_structure import menu_structure
from beeref.config import KeyboardSettings, settings_events
from beeref.utils import ActionList


logger = logging.getLogger(__name__)


class Action:
    SETTINGS_GROUP = 'Actions'

    def __init__(self, id, text, callback=None, shortcuts=None,
                 checkable=False, checked=False, group=None, settings=None,
                 enabled=True, menu_item=None, menu_id=None):
        self.id = id
        self.text = text
        self.callback = callback
        self.shortcuts = shortcuts or []
        self.checkable = checkable
        self.checked = checked
        self.group = group
        self.settings = settings
        self.enabled = enabled
        self.menu_item = menu_item
        self.menu_id = menu_id
        self.qaction = None
        self.kb_settings = KeyboardSettings()
        settings_events.restore_keyboard_defaults.connect(
            self.on_restore_defaults)

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return self.id

    def on_restore_defaults(self):
        if self.qaction:
            self.qaction.setShortcuts(self.get_shortcuts())

    @cached_property
    def menu_path(self):
        path = []

        def _get_path(menu_item):
            if isinstance(menu_item['items'], list):
                # This is a normal menu
                for item in menu_item['items']:
                    if item == self.id:
                        path.append(menu_item['menu'])
                        return True
                    if isinstance(item, dict):
                        # This is a submenu
                        if _get_path(item):
                            path.append(menu_item['menu'])
                            return True
            elif menu_item['items'] == self.menu_id:
                # This is a dynamic submenu (e.g. Recent Files)
                path.append(menu_item['menu'])
                return True

        for menu_item in menu_structure:
            _get_path(menu_item)

        return path[::-1]

    def get_shortcuts(self):
        return self.kb_settings.get_list(
            self.SETTINGS_GROUP, self.id, self.shortcuts)

    def set_shortcuts(self, value):
        logger.debug(f'Setting shortcut "{self.id}" to: {value}')
        self.kb_settings.set_list(
            self.SETTINGS_GROUP, self.id, value, self.shortcuts)
        if self.qaction:
            self.qaction.setShortcuts(value)

    def get_qkeysequence(self, index):
        """Current shortcuts as QKeySequence"""
        try:
            return QtGui.QKeySequence(self.get_shortcuts()[index])
        except IndexError:
            return QtGui.QKeySequence()

    def shortcuts_changed(self):
        """Whether shortcuts have changed from their defaults."""
        return self.get_shortcuts() != self.shortcuts

    def get_default_shortcut(self, index):
        try:
            return self.shortcuts[index]
        except IndexError:
            return None


actions = ActionList([
    Action(
        id='open',
        text='&Open',
        shortcuts=['Ctrl+O'],
        callback='on_action_open',
    ),
    Action(
        id='save',
        text='&Save',
        shortcuts=['Ctrl+S'],
        callback='on_action_save',
        group='active_when_items_in_scene',
    ),
    Action(
        id='save_as',
        text='Save &As...',
        shortcuts=['Ctrl+Shift+S'],
        callback='on_action_save_as',
        group='active_when_items_in_scene',
    ),
    Action(
        id='export_scene',
        text='E&xport Scene...',
        shortcuts=['Ctrl+Shift+E'],
        callback='on_action_export_scene',
        group='active_when_items_in_scene',
    ),
    Action(
        id='export_images',
        text='Export &Images...',
        callback='on_action_export_images',
        group='active_when_items_in_scene',
    ),
    Action(
        id='quit',
        text='&Quit',
        shortcuts=['Ctrl+Q'],
        callback='on_action_quit',
    ),
    Action(
        id='insert_images',
        text='&Images...',
        shortcuts=['Ctrl+I'],
        callback='on_action_insert_images',
    ),
    Action(
        id='insert_text',
        text='&Text',
        shortcuts=['Ctrl+T'],
        callback='on_action_insert_text',
    ),
    Action(
        id='insert_draw',
        text='&Draw',
        shortcuts=['Ctrl+D'],
        callback='on_action_insert_draw',
    ),
    Action(
        id='undo',
        text='&Undo',
        shortcuts=['Ctrl+Z'],
        callback='on_action_undo',
        group='active_when_can_undo',
    ),
    Action(
        id='redo',
        text='&Redo',
        shortcuts=['Ctrl+Shift+Z'],
        callback='on_action_redo',
        group='active_when_can_redo',
    ),
    Action(
        id='copy',
        text='&Copy',
        shortcuts=['Ctrl+C'],
        callback='on_action_copy',
        group='active_when_selection',
    ),
    Action(
        id='cut',
        text='Cu&t',
        shortcuts=['Ctrl+X'],
        callback='on_action_cut',
        group='active_when_selection',
    ),
    Action(
        id='paste',
        text='&Paste',
        shortcuts=['Ctrl+V'],
        callback='on_action_paste',
    ),
    Action(
        id='delete',
        text='&Delete',
        shortcuts=['Del', 'Backspace'],
        callback='on_action_delete_items',
        group='active_when_selection',
    ),
    Action(
        id='raise_to_top',
        text='&Raise to Top',
        shortcuts=['PgUp'],
        callback='on_action_raise_to_top',
        group='active_when_selection',
    ),
    Action(
        id='lower_to_bottom',
        text='Lower to Bottom',
        shortcuts=['PgDown'],
        callback='on_action_lower_to_bottom',
        group='active_when_selection',
    ),
    Action(
        id='normalize_height',
        text='&Height',
        shortcuts=['Shift+H'],
        callback='on_action_normalize_height',
        group='active_when_selection',
    ),
    Action(
        id='normalize_width',
        text='&Width',
        shortcuts=['Shift+W'],
        callback='on_action_normalize_width',
        group='active_when_selection',
    ),
    Action(
        id='normalize_size',
        text='&Size',
        shortcuts=['Shift+S'],
        callback='on_action_normalize_size',
        group='active_when_selection',
    ),
    Action(
        id='arrange_optimal',
        text='&Optimal',
        shortcuts=['Shift+O'],
        callback='on_action_arrange_optimal',
        group='active_when_selection',
    ),
    Action(
        id='arrange_horizontal',
        text='&Horizontal (by filename)',
        callback='on_action_arrange_horizontal',
        group='active_when_selection',
    ),
    Action(
        id='arrange_vertical',
        text='&Vertical (by filename)',
        callback='on_action_arrange_vertical',
        group='active_when_selection',
    ),
    Action(
        id='arrange_square',
        text='&Square (by filename)',
        callback='on_action_arrange_square',
        group='active_when_selection',
    ),
    Action(
        id='change_opacity',
        text='Change &Opacity...',
        callback='on_action_change_opacity',
        group='active_when_selection',
    ),
    Action(
        id='grayscale',
        text='&Grayscale',
        shortcuts=['G'],
        checkable=True,
        callback='on_action_grayscale',
        group='active_when_selection',
    ),
    Action(
        id='show_color_gamut',
        text='Show &Color Gamut',
        callback='on_action_show_color_gamut',
        group='active_when_single_image',
    ),
    Action(
        id='sample_color',
        text='Sample Color',
        shortcuts=['S'],
        callback='on_action_sample_color',
        group='active_when_items_in_scene',
    ),
    Action(
        id='crop',
        text='&Crop',
        shortcuts=['Shift+C'],
        callback='on_action_crop',
        group='active_when_single_image',
    ),
    Action(
        id='flip_horizontally',
        text='Flip &Horizontally',
        shortcuts=['H'],
        callback='on_action_flip_horizontally',
        group='active_when_selection',
    ),
    Action(
        id='flip_vertically',
        text='Flip &Vertically',
        shortcuts=['V'],
        callback='on_action_flip_vertically',
        group='active_when_selection',
    ),
    Action(
        id='new_scene',
        text='&New Scene',
        shortcuts=['Ctrl+N'],
        callback='on_action_new_scene',
    ),
    Action(
        id='fit_scene',
        text='&Fit Scene',
        shortcuts=['1'],
        callback='on_action_fit_scene',
    ),
    Action(
        id='fit_selection',
        text='Fit &Selection',
        shortcuts=['2'],
        callback='on_action_fit_selection',
        group='active_when_selection',
    ),
    Action(
        id='reset_scale',
        text='Reset &Scale',
        callback='on_action_reset_scale',
        group='active_when_selection',
    ),
    Action(
        id='reset_rotation',
        text='Reset &Rotation',
        callback='on_action_reset_rotation',
        group='active_when_selection',
    ),
    Action(
        id='reset_flip',
        text='Reset &Flip',
        callback='on_action_reset_flip',
        group='active_when_selection',
    ),
    Action(
        id='reset_crop',
        text='Reset Cro&p',
        callback='on_action_reset_crop',
        group='active_when_selection',
    ),
    Action(
        id='reset_transforms',
        text='Reset &All',
        shortcuts=['R'],
        callback='on_action_reset_transforms',
        group='active_when_selection',
    ),
    Action(
        id='select_all',
        text='&Select All',
        shortcuts=['Ctrl+A'],
        callback='on_action_select_all',
    ),
    Action(
        id='deselect_all',
        text='Deselect &All',
        shortcuts=['Ctrl+Shift+A'],
        callback='on_action_deselect_all',
    ),
    Action(
        id='help',
        text='&Help',
        shortcuts=['F1', 'Ctrl+H'],
        callback='on_action_help',
    ),
    Action(
        id='about',
        text='&About',
        callback='on_action_about',
    ),
    Action(
        id='debuglog',
        text='Show &Debug Log',
        callback='on_action_debuglog',
    ),
    Action(
        id='show_scrollbars',
        text='Show &Scrollbars',
        checkable=True,
        settings='View/show_scrollbars',
        callback='on_action_show_scrollbars',
    ),
    Action(
        id='show_menubar',
        text='Show &Menu Bar',
        checkable=True,
        settings='View/show_menubar',
        callback='on_action_show_menubar',
    ),
    Action(
        id='show_titlebar',
        text='Show &Title Bar',
        checkable=True,
        checked=True,
        callback='on_action_show_titlebar',
    ),
    Action(
        id='move_window',
        text='Move &Window',
        shortcuts=['Ctrl+M'],
        callback='on_action_move_window',
    ),
    Action(
        id='fullscreen',
        text='&Fullscreen',
        shortcuts=['F11'],
        checkable=True,
        callback='on_action_fullscreen',
    ),
    Action(
        id='always_on_top',
        text='&Always On Top',
        checkable=True,
        callback='on_action_always_on_top',
    ),
    Action(
        id='settings',
        text='&Settings',
        callback='on_action_settings',
    ),
    Action(
        id='keyboard_settings',
        text='&Keyboard && Mouse',
        callback='on_action_keyboard_settings',
    ),
    Action(
        id='open_settings_dir',
        text='&Open Settings Folder',
        callback='on_action_open_settings_dir',
    ),
])
