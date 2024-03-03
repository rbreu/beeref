from unittest.mock import patch

from PyQt6 import QtGui

from beeref.actions.actions import Action


def test_action_str():
    action = Action(id='foo', text='Foo', shortcuts=['Ctrl+R'])
    assert str(action) == 'foo'


def test_action_equals_true():
    action1 = Action(id='foo', text='Foo', shortcuts=['Ctrl+R'])
    action2 = Action(id='foo', text='Bar', shortcuts=['Ctrl+F'])
    assert action1 == action2


def test_action_equals_false():
    action1 = Action(id='foo', text='Foo', shortcuts=['Ctrl+R'])
    action2 = Action(id='bar', text='Bar', shortcuts=['Ctrl+R'])
    assert not action1 == action2


def test_action_on_restore_defaults(kbsettings, view):
    action = Action(id='foo', text='Foo', shortcuts=['Ctrl+R'])
    action.qaction = QtGui.QAction('foo', view)
    action.on_restore_defaults()
    assert action.qaction.shortcuts() == ['Ctrl+R']


def test_action_on_restore_defaults_when_no_defaults(kbsettings, view):
    action = Action(id='foo', text='Foo')
    action.qaction = QtGui.QAction('foo', view)
    action.qaction.setShortcuts(['Ctrl+R'])
    action.on_restore_defaults()
    assert action.qaction.shortcuts() == []


def test_action_get_overwritten_shortcuts(kbsettings):
    kbsettings.set_list('Actions', 'foo', ['Alt+O'])
    action = Action(id='foo', text='Foo', shortcuts=['Ctrl+F'])
    assert action.get_shortcuts() == ['Alt+O']


def test_action_get_shortcuts_gets_default(kbsettings):
    action = Action(id='foo', text='Foo', shortcuts=['Ctrl+F'])
    assert action.get_shortcuts() == ['Ctrl+F']


def test_action_set_shortcuts_when_no_qaction(kbsettings):
    action = Action(id='foo', text='Foo')
    action.qaction = None
    action.set_shortcuts(['Ctrl+F'])
    assert kbsettings.get_list('Actions', 'foo') == ['Ctrl+F']


def test_action_set_shortcuts_when_qaction(kbsettings, view):
    action = Action(id='foo', text='Foo')
    action.qaction = QtGui.QAction('foo', view)
    action.set_shortcuts(['Ctrl+F'])
    assert kbsettings.get_list('Actions', 'foo') == ['Ctrl+F']
    assert action.qaction.shortcuts() == ['Ctrl+F']


def test_action_get_qkeysequence_first(kbsettings):
    action = Action(id='foo', text='Foo', shortcuts=['Ctrl+F'])
    assert action.get_qkeysequence(0) == QtGui.QKeySequence('Ctrl+F')


def test_action_get_qkeysequence_second(kbsettings):
    action = Action(id='foo', text='Foo', shortcuts=['Ctrl+F', 'Ctrl+B'])
    assert action.get_qkeysequence(1) == QtGui.QKeySequence('Ctrl+B')


def test_action_get_qkeysequence_first_when_not_set(kbsettings):
    action = Action(id='foo', text='Foo')
    assert action.get_qkeysequence(0) == QtGui.QKeySequence()


def test_action_get_qkeysequence_second_when_not_set(kbsettings):
    action = Action(id='foo', text='Foo', shortcuts=['Ctrl+F'])
    assert action.get_qkeysequence(1) == QtGui.QKeySequence()


def test_action_shortcuts_changed_when_not_changed(kbsettings):
    action = Action(id='foo', text='Foo', shortcuts=['Ctrl+F'])
    assert action.shortcuts_changed() is False


def test_action_shortcuts_changed_when_changed(kbsettings):
    action = Action(id='foo', text='Foo', shortcuts=['Ctrl+F'])
    kbsettings.set_list('Actions', 'foo', ['Ctrl+B'])
    assert action.shortcuts_changed() is True


def test_action_shortcuts_changed_when_empty(kbsettings):
    action = Action(id='foo', text='Foo')
    assert action.shortcuts_changed() is False


def test_action_get_default_shortcut_first():
    action = Action(id='foo', text='Foo', shortcuts=['Ctrl+F'])
    assert action.get_default_shortcut(0) == 'Ctrl+F'


def test_action_get_default_shortcut_second():
    action = Action(id='foo', text='Foo', shortcuts=['Ctrl+F', 'Ctrl+B'])
    assert action.get_default_shortcut(1) == 'Ctrl+B'


def test_action_get_default_shortcut_first_when_none_set():
    action = Action(id='foo', text='Foo')
    assert action.get_default_shortcut(0) is None


def test_action_get_default_shortcut_second_when_none_set():
    action = Action(id='foo', text='Foo', shortcuts=['Ctrl+F'])
    assert action.get_default_shortcut(1) is None


@patch('beeref.actions.actions.menu_structure',
       [{'menu': 'Foo', 'items': ['bar', 'baz']}])
def test_action_menu_path():
    action = Action(id='baz', text='Foo')
    assert action.menu_path == ['Foo']


@patch('beeref.actions.actions.menu_structure',
       [{'menu': 'Foo', 'items': [{'menu': 'Bar', 'items': ['baz']}]}])
def test_action_menu_path_with_submenus():
    action = Action(id='baz', text='Foo')
    assert action.menu_path == ['Foo', 'Bar']


@patch('beeref.actions.actions.menu_structure',
       [{'menu': 'Foo', 'items': '_build_recent_files'}])
def test_action_menu_path_recent_files():
    action = Action(id='baz', text='Foo', menu_id='_build_recent_files')
    assert action.menu_path == ['Foo']


@patch('beeref.actions.actions.menu_structure',
       [{'menu': 'Foo', 'items': [
           {'menu': 'Bar', 'items': '_build_recent_files'}]}])
def test_action_menu_path_recent_files_in_submenu():
    action = Action(id='baz', text='Foo', menu_id='_build_recent_files')
    assert action.menu_path == ['Foo', 'Bar']
