import os.path
from unittest.mock import patch, MagicMock

from PyQt6 import QtWidgets

from beeref.actions import ActionsMixin
from beeref.actions.menu_structure import MENU_SEPARATOR


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


@patch('PyQt6.QtGui.QAction.triggered')
@patch('PyQt6.QtGui.QAction.toggled')
@patch('beeref.actions.mixin.menu_structure')
@patch('beeref.actions.mixin.actions')
def test_create_actions(
        actions_mock, menu_mock, toggle_mock, trigger_mock, qapp):
    widget = FooWidget()
    actions_mock.__iter__.return_value = [{
        'id': 'foo',
        'text': '&Foo',
        'shortcuts': ['Ctrl+F'],
        'callback': 'on_foo',
    }]

    menu_mock.__iter__.return_value = ['foo']
    widget.build_menu_and_actions()
    trigger_mock.connect.assert_called_once_with(widget.on_foo)
    toggle_mock.connect.assert_not_called()

    assert len(widget.actions()) == 1
    qaction = widget.actions()[0]
    assert qaction.text() == '&Foo'
    assert qaction.shortcut() == 'Ctrl+F'
    assert qaction.isEnabled() is True
    assert widget.bee_actions['foo'] == qaction


@patch('PyQt6.QtGui.QAction.triggered')
@patch('PyQt6.QtGui.QAction.toggled')
@patch('beeref.actions.mixin.menu_structure')
@patch('beeref.actions.mixin.actions')
def test_create_actions_checkable(
        actions_mock, menu_mock, toggle_mock, trigger_mock, qapp):
    widget = FooWidget()
    actions_mock.__iter__.return_value = [{
        'id': 'foo',
        'text': '&Foo',
        'checkable': True,
        'callback': 'on_foo',
    }]

    menu_mock.__iter__.return_value = ['foo']
    widget.build_menu_and_actions()
    trigger_mock.connect.assert_not_called()
    toggle_mock.connect.assert_called_once_with(widget.on_foo)

    assert len(widget.actions()) == 1
    qaction = widget.actions()[0]
    assert qaction.text() == '&Foo'
    assert qaction.isEnabled() is True
    assert qaction.isChecked() is False
    assert widget.bee_actions['foo'] == qaction


@patch('PyQt6.QtGui.QAction.triggered')
@patch('PyQt6.QtGui.QAction.toggled')
@patch('beeref.actions.mixin.menu_structure')
@patch('beeref.actions.mixin.actions')
def test_create_actions_checkable_checked_true(
        actions_mock, menu_mock, toggle_mock, trigger_mock, qapp):
    widget = FooWidget()
    actions_mock.__iter__.return_value = [{
        'id': 'foo',
        'text': '&Foo',
        'checkable': True,
        'checked': True,
        'callback': 'on_foo',
    }]

    menu_mock.__iter__.return_value = ['foo']
    widget.build_menu_and_actions()
    trigger_mock.connect.assert_not_called()
    toggle_mock.connect.assert_called_once_with(widget.on_foo)

    assert len(widget.actions()) == 1
    qaction = widget.actions()[0]
    assert qaction.text() == '&Foo'
    assert qaction.isEnabled() is True
    assert qaction.isChecked() is True
    assert widget.bee_actions['foo'] == qaction


@patch.object(FooWidget, 'on_foo')
@patch.object(FooWidget, 'settings')
@patch('PyQt6.QtGui.QAction.toggled')
@patch('beeref.actions.mixin.menu_structure')
@patch('beeref.actions.mixin.actions')
def test_create_actions_checkable_with_settings(
        actions_mock, menu_mock, toggle_mock, settings_mock, callback_mock,
        qapp):
    widget = FooWidget()
    actions_mock.__iter__.return_value = [{
        'id': 'foo',
        'text': '&Foo',
        'checkable': True,
        'callback': 'on_foo',
        'settings': 'foo/bar',
    }]

    menu_mock.__iter__.return_value = ['foo']
    settings_mock.value.return_value = True
    widget.build_menu_and_actions()
    settings_mock.value.assert_called_once_with(
        'foo/bar', False, type=bool)
    qaction = widget.actions()[0]
    assert qaction.isChecked() is True
    assert toggle_mock.connect.call_count == 2
    callback_mock.assert_called_once_with(True)


@patch('beeref.actions.mixin.menu_structure')
@patch('beeref.actions.mixin.actions')
def test_create_actions_with_group(actions_mock, menu_mock, qapp):
    widget = FooWidget()
    actions_mock.__iter__.return_value = [{
        'id': 'foo',
        'text': '&Foo',
        'callback': 'on_foo',
        'group': 'bar',
    }]
    menu_mock.__iter__.return_value = ['foo']
    widget.build_menu_and_actions()
    assert len(widget.actions()) == 1
    qaction = widget.actions()[0]
    assert widget.bee_actiongroups['bar'] == [qaction]


@patch('beeref.actions.mixin.menu_structure')
@patch('beeref.actions.mixin.actions')
def test_build_menu_and_actions_with_actions(actions_mock, menu_mock, qapp):
    widget = FooWidget()
    actions_mock.__iter__.return_value = [{
        'id': 'foo',
        'text': '&Foo',
        'callback': 'on_foo',
        'group': 'bar',
    }]
    menu_mock.__iter__.return_value = ['foo']
    with patch('PyQt6.QtWidgets.QMenu.addAction') as add_mock:
        widget.build_menu_and_actions()
        assert isinstance(widget.context_menu, QtWidgets.QMenu)
        add_mock.assert_called_once_with(widget.bee_actions['foo'])


@patch('beeref.actions.mixin.menu_structure')
@patch('beeref.actions.mixin.actions')
def test_build_menu_and_actions_with_separator(actions_mock, menu_mock, qapp):
    widget = FooWidget()
    menu_mock.__iter__.return_value = [MENU_SEPARATOR]
    with patch('PyQt6.QtWidgets.QMenu.addSeparator') as sep_mock:
        widget.build_menu_and_actions()
        assert isinstance(widget.context_menu, QtWidgets.QMenu)
        sep_mock.assert_called_once_with()


@patch('beeref.actions.mixin.menu_structure')
@patch('beeref.actions.mixin.actions')
def test_build_menu_and_actions_with_submenu(actions_mock, menu_mock, qapp):
    widget = FooWidget()
    actions_mock.__iter__.return_value = [{
        'id': 'foo',
        'text': '&Foo',
        'callback': 'on_foo',
        'group': 'bar',
    }]
    menu_mock.__iter__.return_value = [
        {'menu': '&Bar', 'items': ['foo']}]
    with patch('PyQt6.QtWidgets.QMenu.addAction') as add_mock:
        with patch('PyQt6.QtWidgets.QMenu.addMenu') as addmenu_mock:
            addmenu_mock.return_value = QtWidgets.QMenu()
            widget.build_menu_and_actions()
            assert isinstance(widget.context_menu, QtWidgets.QMenu)
            addmenu_mock.assert_called_once_with('&Bar')
            add_mock.assert_called_once_with(widget.bee_actions['foo'])


@patch('beeref.actions.mixin.menu_structure')
@patch('beeref.actions.mixin.actions')
def test_actiongroup_set_enabled(actions_mock, menu_mock, qapp):
    widget = FooWidget()
    actions_mock.__iter__.return_value = [
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

    menu_mock.__iter__.return_value = ['foo']
    widget.build_menu_and_actions()
    widget.actiongroup_set_enabled('g1', True)
    assert widget.bee_actions['foo'].isEnabled() is True
    assert widget.bee_actions['bar'].isEnabled() is False


@patch('beeref.actions.mixin.menu_structure')
@patch('beeref.actions.mixin.actions')
def test_build_menu_and_actions_disables_actiongroups(
        actions_mock, menu_mock, qapp):
    widget = FooWidget()
    widget.scene.has_selection.return_value = False
    actions_mock.__iter__.return_value = [
        {
            'id': 'foo',
            'text': '&Foo',
            'callback': 'on_foo',
            'group': 'active_when_selection',
        },
    ]

    menu_mock.__iter__.return_value = ['foo']
    widget.build_menu_and_actions()
    qaction = widget.actions()[0]
    assert qaction.isEnabled() is False


@patch('beeref.config.BeeSettings.get_recent_files')
@patch('PyQt6.QtGui.QAction.triggered')
@patch('beeref.actions.mixin.menu_structure')
@patch('beeref.actions.mixin.actions')
def test_create_recent_files(
        actions_mock, menu_mock, triggered_mock, files_mock, qapp):
    widget = FooWidget()
    files_mock.return_value = [
        os.path.abspath(f'{i}.bee') for i in range(15)]
    menu_mock.__iter__.return_value = [{
        'menu': 'Open &Recent',
        'items': '_build_recent_files',
    }]

    widget.build_menu_and_actions()
    triggered_mock.connect.assert_called()
    assert len(widget.actions()) == 15
    qaction1 = widget.actions()[0]
    assert qaction1.text() == '0.bee'
    assert qaction1.shortcut() == 'Ctrl+1'
    assert qaction1.isEnabled() is True
    assert widget.bee_actions['recent_files_0'] == qaction1
    qaction10 = widget.actions()[9]
    assert qaction10.text() == '9.bee'
    assert qaction10.shortcut() == 'Ctrl+0'
    assert qaction10.isEnabled() is True
    assert widget.bee_actions['recent_files_9'] == qaction10
    qaction15 = widget.actions()[-1]
    assert qaction15.text() == '14.bee'
    assert qaction15.shortcut() == ''
    assert qaction15.isEnabled() is True
    assert widget.bee_actions['recent_files_14'] == qaction15


@patch('beeref.config.BeeSettings.get_recent_files')
@patch('PyQt6.QtGui.QAction.triggered')
@patch('beeref.actions.mixin.menu_structure')
@patch('beeref.actions.mixin.actions')
def test_update_recent_files(
        actions_mock, menu_mock, triggered_mock, files_mock, qapp):
    widget = FooWidget()
    files_mock.return_value = [os.path.abspath('foo.bee')]
    menu_mock.__iter__.return_value = [{
        'menu': 'Open &Recent',
        'items': '_build_recent_files',
    }]

    widget.build_menu_and_actions()
    triggered_mock.connect.reset_mock()
    assert len(widget.actions()) == 1
    qaction1 = widget.actions()[0]
    assert qaction1.text() == 'foo.bee'

    files_mock.return_value = [os.path.abspath('bar.bee')]
    widget.update_menu_and_actions()
    triggered_mock.connect.assert_called()
    assert len(widget.actions()) == 1
    qaction1 = widget.actions()[0]
    assert qaction1.text() == 'bar.bee'


def test_create_menubar(qapp):
    widget = FooWidget()
    widget.toplevel_menus = [QtWidgets.QMenu('Foo')]
    menubar = widget.create_menubar()
    assert isinstance(menubar, QtWidgets.QMenuBar)
    assert len(menubar.actions()) == 1
