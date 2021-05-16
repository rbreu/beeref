import os.path
from unittest.mock import patch, MagicMock

from PyQt6 import QtWidgets

from beeref.actions import ActionsMixin
from beeref.actions.menu_structure import MENU_SEPARATOR
from ..base import BeeTestCase


class FooWidget(QtWidgets.QWidget, ActionsMixin):
    settings = MagicMock()
    undo_stack = MagicMock()
    scene = MagicMock()

    def on_foo(self):
        pass

    def on_bar(self):
        pass

    def open_from_file(self):
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

        self.menu_mock.__iter__.return_value = ['foo']
        self.widget.build_menu_and_actions()
        trigger_mock.connect.assert_called_once_with(self.widget.on_foo)
        toggle_mock.connect.assert_not_called()

        assert len(self.widget.actions()) == 1
        qaction = self.widget.actions()[0]
        assert qaction.text() == '&Foo'
        assert qaction.shortcut() == 'Ctrl+F'
        assert qaction.isEnabled() is True
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

        self.menu_mock.__iter__.return_value = ['foo']
        self.widget.build_menu_and_actions()
        trigger_mock.connect.assert_not_called()
        toggle_mock.connect.assert_called_once_with(self.widget.on_foo)

        assert len(self.widget.actions()) == 1
        qaction = self.widget.actions()[0]
        assert qaction.text() == '&Foo'
        assert qaction.isEnabled() is True
        assert qaction.isChecked() is False
        assert self.widget.bee_actions['foo'] == qaction

    @patch.object(FooWidget, 'on_foo')
    @patch.object(FooWidget, 'settings')
    @patch('PyQt6.QtGui.QAction.toggled')
    def test_create_actions_checkable_with_settings(
            self, toggle_mock, settings_mock, callback_mock):
        self.actions_mock.__iter__.return_value = [{
            'id': 'foo',
            'text': '&Foo',
            'checkable': True,
            'callback': 'on_foo',
            'settings': 'foo/bar',
        }]

        self.menu_mock.__iter__.return_value = ['foo']
        settings_mock.value.return_value = True
        self.widget.build_menu_and_actions()
        settings_mock.value.assert_called_once_with(
            'foo/bar', False, type=bool)
        qaction = self.widget.actions()[0]
        assert qaction.isChecked() is True
        assert toggle_mock.connect.call_count == 2
        callback_mock.assert_called_once_with(True)

    def test_create_actions_enabled_false(self):
        self.actions_mock.__iter__.return_value = [{
            'id': 'foo',
            'text': '&Foo',
            'callback': 'on_foo',
            'enabled': False,
        }]
        self.menu_mock.__iter__.return_value = ['foo']
        self.widget.build_menu_and_actions()
        qaction = self.widget.actions()[0]
        qaction.isEnabled() is False

    def test_create_actions_with_group(self):
        self.actions_mock.__iter__.return_value = [{
            'id': 'foo',
            'text': '&Foo',
            'callback': 'on_foo',
            'group': 'bar',
        }]
        self.menu_mock.__iter__.return_value = ['foo']
        self.widget.build_menu_and_actions()
        assert len(self.widget.actions()) == 1
        qaction = self.widget.actions()[0]
        assert self.widget.bee_actiongroups['bar'] == [qaction]

    def test_build_menu_and_actions_with_actions(self):
        self.actions_mock.__iter__.return_value = [{
            'id': 'foo',
            'text': '&Foo',
            'callback': 'on_foo',
            'group': 'bar',
        }]
        self.menu_mock.__iter__.return_value = ['foo']
        with patch('PyQt6.QtWidgets.QMenu.addAction') as add_mock:
            menu = self.widget.build_menu_and_actions()
            assert isinstance(menu, QtWidgets.QMenu)
            add_mock.assert_called_once_with(self.widget.bee_actions['foo'])

    def test_build_menu_and_actions_with_separator(self):
        self.menu_mock.__iter__.return_value = [MENU_SEPARATOR]
        with patch('PyQt6.QtWidgets.QMenu.addSeparator') as sep_mock:
            menu = self.widget.build_menu_and_actions()
            assert isinstance(menu, QtWidgets.QMenu)
            sep_mock.assert_called_once_with()

    def test_build_menu_and_actions_with_submenu(self):
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
                menu = self.widget.build_menu_and_actions()
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

        self.menu_mock.__iter__.return_value = ['foo']
        self.widget.build_menu_and_actions()
        self.widget.actiongroup_set_enabled('g1', False)
        assert self.widget.bee_actions['foo'].isEnabled() is False
        assert self.widget.bee_actions['bar'].isEnabled() is True

    def test_build_menu_and_actions_enables_actiongroups(self):
        self.widget.scene.has_selection.return_value = True
        self.actions_mock.__iter__.return_value = [
            {
                'id': 'foo',
                'text': '&Foo',
                'callback': 'on_foo',
                'group': 'active_when_selection',
            },
        ]

        self.menu_mock.__iter__.return_value = ['foo']
        self.widget.build_menu_and_actions()
        qaction = self.widget.actions()[0]
        assert qaction.isEnabled() is True

    def test_build_menu_and_actions_disables_actiongroups(self):
        self.widget.scene.has_selection.return_value = False
        self.actions_mock.__iter__.return_value = [
            {
                'id': 'foo',
                'text': '&Foo',
                'callback': 'on_foo',
                'group': 'active_when_selection',
            },
        ]

        self.menu_mock.__iter__.return_value = ['foo']
        self.widget.build_menu_and_actions()
        qaction = self.widget.actions()[0]
        assert qaction.isEnabled() is False

    @patch('beeref.config.BeeSettings.get_recent_files')
    @patch('PyQt6.QtGui.QAction.triggered')
    def test_recent_files(self, triggered_mock, files_mock):
        files_mock.return_value = [
            os.path.abspath(f'{i}.bee') for i in range(15)]

        self.menu_mock.__iter__.return_value = [{
            'menu': 'Open &Recent',
            'items': '_build_recent_files',
        }]

        self.widget.build_menu_and_actions()
        triggered_mock.connect.assert_called()

        assert len(self.widget.actions()) == 15
        qaction1 = self.widget.actions()[0]
        assert qaction1.text() == '0.bee'
        assert qaction1.shortcut() == 'Ctrl+1'
        assert qaction1.isEnabled() is True
        assert self.widget.bee_actions['recent_files_0'] == qaction1
        qaction10 = self.widget.actions()[9]
        assert qaction10.text() == '9.bee'
        assert qaction10.shortcut() == 'Ctrl+0'
        assert qaction10.isEnabled() is True
        assert self.widget.bee_actions['recent_files_9'] == qaction10
        qaction15 = self.widget.actions()[-1]
        assert qaction15.text() == '14.bee'
        assert qaction15.shortcut() == ''
        assert qaction15.isEnabled() is True
        assert self.widget.bee_actions['recent_files_14'] == qaction15

    def test_build_menu_and_actions_updates_given_menu(self):
        self.actions_mock.__iter__.return_value = [{
            'id': 'foo',
            'text': '&Foo',
            'callback': 'on_foo',
            'group': 'foo',
        }]
        self.menu_mock.__iter__.return_value = ['foo']
        menu = self.widget.build_menu_and_actions()
        qaction = self.widget.actions()[0]
        assert qaction.text() == '&Foo'

        self.actions_mock.__iter__.return_value = [{
            'id': 'bar',
            'text': '&Bar',
            'callback': 'on_bar',
            'group': 'bar',
        }]
        self.menu_mock.__iter__.return_value = ['bar']
        self.widget.build_menu_and_actions(menu)
        assert len(self.widget.actions()) == 1
        assert len(menu.actions()) == 1
        qaction = self.widget.actions()[0]
        assert qaction.text() == '&Bar'
        assert self.widget.bee_actions == {'bar': qaction}
        assert self.widget.bee_actiongroups['bar'] == [qaction]

    def test_clear_actions(self):
        self.actions_mock.__iter__.return_value = [{
            'id': 'foo',
            'text': '&Foo',
            'callback': 'on_foo',
            'group': 'bar',
        }]
        self.menu_mock.__iter__.return_value = ['foo']
        menu = self.widget.build_menu_and_actions()
        assert menu.actions()
        assert self.widget.actions()
        self.widget.clear_actions(menu)
        assert menu.actions() == []
        assert self.widget.actions() == []
        assert self.widget.bee_actions == {}
        assert self.widget.bee_actiongroups == {}
