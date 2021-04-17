from unittest.mock import patch

from PyQt6 import QtWidgets

from beeref.actions import ActionsMixin
from beeref.actions.menu_structure import MENU_SEPARATOR
from ..base import BeeTestCase


class FooWidget(QtWidgets.QWidget, ActionsMixin):
    def on_foo(self):
        pass


class ActionsMixinTestCase(BeeTestCase):

    def setUp(self):
        menu_patcher = patch('beeref.actions.mixin.menu_structure')
        self.menu_mock = menu_patcher.start()
        self.addCleanup(menu_patcher.stop)
        actions_patcher = patch('beeref.actions.mixin.actions')
        self.actions_mock = actions_patcher.start()
        self.addCleanup(actions_patcher.stop)
        self.widget = FooWidget()

    @patch('PyQt6.QtGui.QAction.triggered')
    @patch('PyQt6.QtGui.QAction.toggled')
    def test_create_actions(self, toggle_mock, trigger_mock):
        self.actions_mock.__iter__.return_value = [{
            'id': 'foo',
            'text': '&Foo',
            'shortcuts': ['Ctrl+F'],
            'callback': 'on_foo',
        }]

        self.widget._create_actions()
        trigger_mock.connect.assert_called_once_with(self.widget.on_foo)
        toggle_mock.connect.assert_not_called()

        assert len(self.widget.actions()) == 1
        qaction = self.widget.actions()[0]
        qaction.text() == '&Foo'
        qaction.shortcut() == 'Ctrl+F'
        qaction.isEnabled() is True
        assert self.widget.bee_actions['foo'] == qaction

    @patch('PyQt6.QtGui.QAction.triggered')
    @patch('PyQt6.QtGui.QAction.toggled')
    def test_create_actions_checkable(self, toggle_mock, trigger_mock):
        self.actions_mock.__iter__.return_value = [{
            'id': 'foo',
            'text': '&Foo',
            'checkable': True,
            'callback': 'on_foo',
        }]

        self.widget._create_actions()
        trigger_mock.connect.assert_not_called()
        toggle_mock.connect.assert_called_once_with(self.widget.on_foo)

        assert len(self.widget.actions()) == 1
        qaction = self.widget.actions()[0]
        qaction.text() == '&Foo'
        qaction.isEnabled() is True
        assert self.widget.bee_actions['foo'] == qaction

    def test_create_actions_enabled_false(self):
        self.actions_mock.__iter__.return_value = [{
            'id': 'foo',
            'text': '&Foo',
            'callback': 'on_foo',
            'enabled': False,
        }]
        self.widget._create_actions()
        qaction = self.widget.actions()[0]
        qaction.isEnabled() is False

    def test_create_actions_with_group(self):
        self.actions_mock.__iter__.return_value = [{
            'id': 'foo',
            'text': '&Foo',
            'callback': 'on_foo',
            'group': 'bar',
        }]
        self.widget._create_actions()
        qaction = self.widget.actions()[0]
        len(self.widget.bee_actiongroups) == 1
        self.widget.bee_actiongroups['bar'] == [qaction]

    def test_create_menu_and_actions_with_actions(self):
        self.actions_mock.__iter__.return_value = [{
            'id': 'foo',
            'text': '&Foo',
            'callback': 'on_foo',
            'group': 'bar',
        }]
        self.menu_mock.__iter__.return_value = ['foo']
        with patch('PyQt6.QtWidgets.QMenu.addAction') as add_mock:
            menu = self.widget.create_menu_and_actions()
            assert isinstance(menu, QtWidgets.QMenu)
            add_mock.assert_called_once_with(self.widget.bee_actions['foo'])

    def test_create_menu_and_actions_with_separator(self):
        self.menu_mock.__iter__.return_value = [MENU_SEPARATOR]
        with patch('PyQt6.QtWidgets.QMenu.addSeparator') as sep_mock:
            menu = self.widget.create_menu_and_actions()
            assert isinstance(menu, QtWidgets.QMenu)
            sep_mock.assert_called_once_with()

    def test_create_menu_and_actions_with_submenu(self):
        self.actions_mock.__iter__.return_value = [{
            'id': 'foo',
            'text': '&Foo',
            'callback': 'on_foo',
            'group': 'bar',
        }]
        self.menu_mock.__iter__.return_value = [
            {'menu': '&Bar', 'items': ['foo']}]
        with patch('PyQt6.QtWidgets.QMenu.addAction') as add_mock:
            with patch('PyQt6.QtWidgets.QMenu.addMenu') as addmenu_mock:
                addmenu_mock.return_value = QtWidgets.QMenu()
                menu = self.widget.create_menu_and_actions()
                assert isinstance(menu, QtWidgets.QMenu)
                addmenu_mock.assert_called_once_with('&Bar')
                add_mock.assert_called_once_with(
                    self.widget.bee_actions['foo'])

    def test_actiongroup_set_enabled(self):
        self.actions_mock.__iter__.return_value = [
            {
                'id': 'foo',
                'text': '&Foo',
                'callback': 'on_foo',
                'group': 'g1',
            },
            {
                'id': 'bar',
                'text': '&Bar',
                'callback': 'on_foo',
                'group': 'g2',
            },
        ]

        self.widget._create_actions()
        self.widget.actiongroup_set_enabled('g1', False)
        assert self.widget.bee_actions['foo'].isEnabled() is False
        assert self.widget.bee_actions['bar'].isEnabled() is True
