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

from PyQt6 import QtGui, QtWidgets

from .actions import actions
from .menu_structure import menu_structure, MENU_SEPARATOR


class ActionsMixin:

    def actiongroup_set_enabled(self, group, value):
        for action in self.bee_actiongroups[group]:
            action.setEnabled(value)

    def create_menu_and_actions(self):
        self._create_actions()
        menu = QtWidgets.QMenu(self)
        menu = self._create_menu(
            self.bee_actions, QtWidgets.QMenu(self), menu_structure)
        return menu

    def _create_actions(self):
        self.bee_actions = {}
        self.bee_actiongroups = defaultdict(list)

        for action in actions:
            qaction = QtGui.QAction(action['text'], self)
            if 'shortcuts' in action:
                qaction.setShortcuts(action['shortcuts'])
            if action.get('checkable', False):
                qaction.toggled.connect(getattr(self, action['callback']))
            else:
                qaction.triggered.connect(getattr(self, action['callback']))
            self.addAction(qaction)
            qaction.setEnabled(action.get('enabled', True))
            qaction.setCheckable(action.get('checkable', False))
            self.bee_actions[action['id']] = qaction
            if 'group' in action:
                self.bee_actiongroups[action['group']].append(qaction)

    def _create_menu(self, actions, menu, items):
        for item in items:
            if isinstance(item, str):
                menu.addAction(actions[item])
            if item == MENU_SEPARATOR:
                menu.addSeparator()
            if isinstance(item, dict):
                submenu = menu.addMenu(item['menu'])
                self._create_menu(actions, submenu, item['items'])

        return menu
