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

from collections import defaultdict
from functools import partial
import os.path

from PyQt6 import QtGui, QtWidgets

from .actions import actions
from .menu_structure import menu_structure, MENU_SEPARATOR

from beeref.config import KeyboardSettings


class ActionsMixin:

    def actiongroup_set_enabled(self, group, value):
        for action in self.bee_actiongroups[group]:
            action.setEnabled(value)

    def build_menu_and_actions(self):
        """Creates a new menu or rebuilds the given menu."""
        self.context_menu = QtWidgets.QMenu(self)
        self.toplevel_menus = []
        self.bee_actions = {}
        self.bee_actiongroups = defaultdict(list)
        self._post_create_functions = []
        self._create_actions()
        self._create_menu(self.bee_actions, self.context_menu, menu_structure)
        for func, arg in self._post_create_functions:
            func(arg)
        del self._post_create_functions

    def update_menu_and_actions(self):
        self._build_recent_files()

    def create_menubar(self):
        menu_bar = QtWidgets.QMenuBar()
        for menu in self.toplevel_menus:
            menu_bar.addMenu(menu)
        return menu_bar

    def _store_checkable_setting(self, key, value):
        self.settings.setValue(key, value)

    def _init_action_checkable(self, actiondef, qaction):
        qaction.setCheckable(True)
        callback = getattr(self, actiondef['callback'])
        qaction.toggled.connect(callback)
        settings_key = actiondef.get('settings')
        checked = actiondef.get('checked', False)
        qaction.setChecked(checked)
        if settings_key:
            val = self.settings.value(settings_key, checked, type=bool)
            qaction.setChecked(val)
            self._post_create_functions.append((callback, val))
            qaction.toggled.connect(
                partial(self._store_checkable_setting, settings_key))

    def _create_actions(self):
        for action in actions:
            qaction = QtGui.QAction(action['text'], self)
            shortcuts = KeyboardSettings().get_shortcuts(
                'Actions', action['id'], action.get('shortcuts'))
            if shortcuts:
                qaction.setShortcuts(shortcuts)
            if action.get('checkable', False):
                self._init_action_checkable(action, qaction)
            else:
                qaction.triggered.connect(getattr(self, action['callback']))
            self.addAction(qaction)
            qaction.setEnabled(action.get('enabled', True))
            self.bee_actions[action['id']] = qaction
            if 'group' in action:
                self.bee_actiongroups[action['group']].append(qaction)
                qaction.setEnabled(False)

    def _create_menu(self, actions, menu, items):
        if isinstance(items, str):
            getattr(self, items)(menu)
            return menu
        for item in items:
            if isinstance(item, str):
                menu.addAction(actions[item])
            if item == MENU_SEPARATOR:
                menu.addSeparator()
            if isinstance(item, dict):
                submenu = menu.addMenu(item['menu'])
                if menu == self.context_menu:
                    self.toplevel_menus.append(submenu)
                self._create_menu(actions, submenu, item['items'])

        return menu

    def _build_recent_files(self, menu=None):
        if menu:
            self._recent_files_submenu = menu
        self._clear_recent_files()

        files = self.settings.get_recent_files(existing_only=True)
        items = []
        i = -1
        for i, filename in enumerate(files):
            qaction = QtGui.QAction(os.path.basename(filename), self)
            action_id = f'recent_files_{i}'
            key = 0 if i == 9 else i + 1
            if key < 10:
                shortcuts = KeyboardSettings().get_shortcuts(
                    'Actions', action_id, [f'Ctrl+{key}'])
                qaction.setShortcuts(shortcuts)
            qaction.triggered.connect(partial(self.open_from_file, filename))
            self.addAction(qaction)
            self._recent_files_submenu.addAction(qaction)
            self.bee_actions[action_id] = qaction
            items.append(action_id)

        # Set shorcuts in settings file for remaining slots:
        for j in range(i + 1, 10):
            key = 0 if j == 9 else j + 1
            KeyboardSettings().get_shortcuts(
                'Actions', f'recent_files_{j}', [f'Ctrl+{key}'])

    def _clear_recent_files(self):
        for action in self._recent_files_submenu.actions():
            self.removeAction(action)
        self._recent_files_submenu.clear()
        for key in list(self.bee_actions.keys()):
            if key.startswith('recent_files_'):
                self.bee_actions.pop(key)
