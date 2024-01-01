import os.path
from unittest.mock import patch, MagicMock, call

from PyQt6 import QtWidgets

from beeref.actions import ActionsMixin
from beeref.actions.actions import Action, ActionList
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
@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': ['foo']}])
@patch('beeref.actions.mixin.actions',
       ActionList([Action({
           'id': 'foo',
           'text': '&Foo',
           'shortcuts': ['Ctrl+F'],
           'callback': 'on_foo',
       })]))
@patch('beeref.config.KeyboardSettings.get_shortcuts')
def test_create_actions(kb_mock, toggle_mock, trigger_mock, qapp):
    kb_mock.side_effect = lambda group, key, default: default
    widget = FooWidget()
    widget.build_menu_and_actions()
    trigger_mock.connect.assert_called_once_with(widget.on_foo)
    toggle_mock.connect.assert_not_called()

    assert len(widget.actions()) == 1
    qaction = widget.actions()[0]
    assert qaction.text() == '&Foo'
    assert qaction.shortcut() == 'Ctrl+F'
    assert qaction.isEnabled() is True
    from beeref.actions.mixin import actions
    assert actions['foo'].qaction == qaction
    kb_mock.assert_called_once_with('Actions', 'foo', ['Ctrl+F'])


@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': ['foo']}])
def test_create_actions_with_shortcut_from_settings(qapp, kbsettings):
    with patch('beeref.actions.mixin.actions',
               ActionList([Action({
                   'id': 'foo',
                   'text': '&Foo',
                   'shortcuts': ['Ctrl+F'],
                   'callback': 'on_foo'})])):
        # Create Action inside the test function so that its
        # kbsettings get created after the kbsettings fixture changes
        # the file path
        kbsettings.set_shortcuts('Actions', 'foo', ['Alt+O'])
        widget = FooWidget()
        widget.build_menu_and_actions()
        qaction = widget.actions()[0]
        assert qaction.shortcuts() == ['Alt+O']


@patch('PyQt6.QtGui.QAction.triggered')
@patch('PyQt6.QtGui.QAction.toggled')
@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': ['foo']}])
@patch('beeref.actions.mixin.actions',
       ActionList([Action({
           'id': 'foo',
           'text': '&Foo',
           'checkable': True,
           'callback': 'on_foo',
       })]))
def test_create_actions_checkable(toggle_mock, trigger_mock, qapp):
    widget = FooWidget()
    widget.build_menu_and_actions()
    trigger_mock.connect.assert_not_called()
    toggle_mock.connect.assert_called_once_with(widget.on_foo)

    assert len(widget.actions()) == 1
    qaction = widget.actions()[0]
    assert qaction.text() == '&Foo'
    assert qaction.isEnabled() is True
    assert qaction.isChecked() is False


@patch('PyQt6.QtGui.QAction.triggered')
@patch('PyQt6.QtGui.QAction.toggled')
@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': ['foo']}])
@patch('beeref.actions.mixin.actions',
       ActionList([Action({
           'id': 'foo',
           'text': '&Foo',
           'checkable': True,
           'checked': True,
           'callback': 'on_foo',
       })]))
def test_create_actions_checkable_checked_true(
        toggle_mock, trigger_mock, qapp):
    widget = FooWidget()
    widget.build_menu_and_actions()
    trigger_mock.connect.assert_not_called()
    toggle_mock.connect.assert_called_once_with(widget.on_foo)

    assert len(widget.actions()) == 1
    qaction = widget.actions()[0]
    assert qaction.text() == '&Foo'
    assert qaction.isEnabled() is True
    assert qaction.isChecked() is True


@patch.object(FooWidget, 'on_foo')
@patch.object(FooWidget, 'settings')
@patch('PyQt6.QtGui.QAction.toggled')
@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': ['foo']}])
@patch('beeref.actions.mixin.actions',
       ActionList([Action({
           'id': 'foo',
           'text': '&Foo',
           'checkable': True,
           'settings': 'foo/bar',
           'callback': 'on_foo',
       })]))
def test_create_actions_checkable_with_settings(
        toggle_mock, settings_mock, callback_mock, qapp):
    widget = FooWidget()
    settings_mock.value.return_value = True
    widget.build_menu_and_actions()
    settings_mock.value.assert_called_once_with(
        'foo/bar', False, type=bool)
    qaction = widget.actions()[0]
    assert qaction.isChecked() is True
    assert toggle_mock.connect.call_count == 2
    callback_mock.assert_called_once_with(True)


@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': ['foo']}])
@patch('beeref.actions.mixin.actions',
       ActionList([Action({
           'id': 'foo',
           'text': '&Foo',
           'callback': 'on_foo',
           'group': 'bar',
       })]))
def test_create_actions_with_group(qapp):
    widget = FooWidget()
    widget.build_menu_and_actions()
    assert len(widget.actions()) == 1
    qaction = widget.actions()[0]
    assert widget.bee_actiongroups['bar'] == [qaction]


@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': ['foo']}])
@patch('beeref.actions.mixin.actions',
       ActionList([Action({
           'id': 'foo',
           'text': '&Foo',
           'callback': 'on_foo',
       })]))
def test_build_menu_and_actions_with_actions(qapp):
    widget = FooWidget()
    with patch('PyQt6.QtWidgets.QMenu.addAction') as add_mock:
        widget.build_menu_and_actions()
        assert isinstance(widget.context_menu, QtWidgets.QMenu)
        from beeref.actions.mixin import actions
        add_mock.assert_called_once_with(actions['foo'].qaction)


@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': [MENU_SEPARATOR]}])
@patch('beeref.actions.mixin.actions', ActionList([]))
def test_build_menu_and_actions_with_separator(qapp):
    widget = FooWidget()
    with patch('PyQt6.QtWidgets.QMenu.addSeparator') as sep_mock:
        widget.build_menu_and_actions()
        assert isinstance(widget.context_menu, QtWidgets.QMenu)
        sep_mock.assert_called_once_with()


@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': [{'menu': 'Bar', 'items': ['foo']}]}])
@patch('beeref.actions.mixin.actions',
       ActionList([Action({
           'id': 'foo',
           'text': '&Foo',
           'callback': 'on_foo',
       })]))
def test_build_menu_and_actions_with_submenu(qapp):
    widget = FooWidget()
    with patch('PyQt6.QtWidgets.QMenu.addAction') as add_mock:
        with patch('PyQt6.QtWidgets.QMenu.addMenu') as addmenu_mock:
            addmenu_mock.return_value = QtWidgets.QMenu()
            widget.build_menu_and_actions()
            assert isinstance(widget.context_menu, QtWidgets.QMenu)
            addmenu_mock.assert_called_with('Bar')
            from beeref.actions.mixin import actions
            add_mock.assert_called_once_with(actions['foo'].qaction)


@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': ['foo']}])
@patch('beeref.actions.mixin.actions',
       ActionList([
           Action({
               'id': 'foo',
               'text': '&Foo',
               'callback': 'on_foo',
               'group': 'g1',
           }),
           Action({
               'id': 'bar',
               'text': '&Bar',
               'callback': 'on_foo',
               'group': 'g2',
           }),
       ]))
def test_actiongroup_set_enabled(qapp):
    widget = FooWidget()
    widget.build_menu_and_actions()
    widget.actiongroup_set_enabled('g1', True)
    from beeref.actions.mixin import actions
    assert actions['foo'].qaction.isEnabled() is True
    assert actions['bar'].qaction.isEnabled() is False


@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': ['foo']}])
@patch('beeref.actions.mixin.actions',
       ActionList([Action({
           'id': 'foo',
           'text': '&Foo',
           'callback': 'on_foo',
           'group': 'active_when_selection',
       })]))
def test_build_menu_and_actions_disables_actiongroups(qapp):
    widget = FooWidget()
    widget.scene.has_selection.return_value = False
    widget.build_menu_and_actions()
    qaction = widget.actions()[0]
    assert qaction.isEnabled() is False


@patch('PyQt6.QtGui.QAction.triggered')
@patch('beeref.config.KeyboardSettings.get_shortcuts')
@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': '_build_recent_files'}])
@patch('beeref.actions.mixin.actions', ActionList([]))
def test_create_recent_files_more_than_10_files(
        kb_mock, triggered_mock, qapp):
    kb_mock.side_effect = lambda group, key, default: default
    widget = FooWidget()
    widget.settings.get_recent_files.return_value = [
        os.path.abspath(f'{i}.bee') for i in range(15)]

    widget.build_menu_and_actions()
    triggered_mock.connect.assert_called()
    assert len(widget.actions()) == 10

    from beeref.actions.mixin import actions
    qaction1 = widget.actions()[0]
    assert qaction1.text() == '0.bee'
    assert qaction1.shortcut() == 'Ctrl+1'
    assert qaction1.isEnabled() is True
    assert actions['recent_files_0'].qaction == qaction1
    qaction10 = widget.actions()[9]
    assert qaction10.text() == '9.bee'
    assert qaction10.shortcut() == 'Ctrl+0'
    assert qaction10.isEnabled() is True
    assert actions['recent_files_9'].qaction == qaction10

    assert kb_mock.call_count == 10
    kb_mock.assert_has_calls(
        [call('Actions', 'recent_files_0', ['Ctrl+1']),
         call('Actions', 'recent_files_9', ['Ctrl+0'])],
        any_order=True)


@patch('PyQt6.QtGui.QAction.triggered')
@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': '_build_recent_files'}])
@patch('beeref.actions.mixin.actions', ActionList([]))
@patch('beeref.config.KeyboardSettings.get_shortcuts')
def test_create_recent_files_fewer_files_than_10_files(
        kb_mock, triggered_mock, qapp):
    kb_mock.side_effect = lambda group, key, default: default
    widget = FooWidget()
    widget.settings.get_recent_files.return_value = [
        os.path.abspath(f'{i}.bee') for i in range(5)]

    widget.build_menu_and_actions()
    triggered_mock.connect.assert_called()
    assert len(widget.actions()) == 5

    from beeref.actions.mixin import actions
    qaction1 = widget.actions()[0]
    assert qaction1.text() == '0.bee'
    assert qaction1.shortcut() == 'Ctrl+1'
    assert qaction1.isEnabled() is True
    assert actions['recent_files_0'].qaction == qaction1
    qaction5 = widget.actions()[4]
    assert qaction5.text() == '4.bee'
    assert qaction5.shortcut() == 'Ctrl+5'
    assert qaction5.isEnabled() is True
    assert actions['recent_files_4'].qaction == qaction5
    assert actions['recent_files_5'].qaction is None

    assert kb_mock.call_count == 5
    kb_mock.assert_has_calls(
        [call('Actions', 'recent_files_0', ['Ctrl+1']),
         call('Actions', 'recent_files_4', ['Ctrl+5'])],
        any_order=True)


@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': '_build_recent_files'}])
@patch('beeref.actions.mixin.actions', ActionList([]))
@patch('beeref.config.KeyboardSettings.get_shortcuts')
def test_create_recent_files_when_no_files(kb_mock, qapp):
    kb_mock.side_effect = lambda group, key, default: default
    widget = FooWidget()
    widget.settings.get_recent_files.return_value = []
    widget.build_menu_and_actions()
    assert len(widget.actions()) == 0
    kb_mock.assert_not_called()


@patch('PyQt6.QtGui.QAction.triggered')
@patch('beeref.actions.mixin.menu_structure',
       [{'menu': 'Foo', 'items': '_build_recent_files'}])
@patch('beeref.actions.mixin.actions', ActionList([]))
def test_update_recent_files(triggered_mock, qapp):
    widget = FooWidget()
    widget.settings.get_recent_files.return_value = [
        os.path.abspath('foo.bee')]

    widget.build_menu_and_actions()
    triggered_mock.connect.reset_mock()
    assert len(widget.actions()) == 1
    qaction1 = widget.actions()[0]
    assert qaction1.text() == 'foo.bee'

    widget.settings.get_recent_files.return_value = [
        os.path.abspath('bar.bee')]
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
