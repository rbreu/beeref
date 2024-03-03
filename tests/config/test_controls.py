from unittest.mock import patch


def test_keyboardsettings_set_keyboard_shortcuts(kbsettings):
    kbsettings.set_keyboard_shortcuts('foo', ['Ctrl+F'])
    assert kbsettings.get_keyboard_shortcuts('foo') == ['Ctrl+F']


def test_keyboardsettings_set_keyboard_shortcuts_multiple(kbsettings):
    kbsettings.set_keyboard_shortcuts('foo', ['Ctrl+F', 'Alt+O'])
    assert kbsettings.get_keyboard_shortcuts('foo') == ['Ctrl+F', 'Alt+O']


def test_keyboardsettings_get_keyboard_shortcuts_existing(kbsettings):
    kbsettings.set_keyboard_shortcuts('bar', ['Ctrl+R'])
    shortcuts = kbsettings.get_keyboard_shortcuts('bar', ['Ctrl+B'])
    assert shortcuts == ['Ctrl+R']


def test_keyboardsettings_get_keyboard_shortcuts_default(kbsettings):
    shortcuts = kbsettings.get_keyboard_shortcuts('bar', ['Ctrl+B'])
    assert shortcuts == ['Ctrl+B']


@patch('beeref.config.KeyboardSettings.setValue')
@patch('beeref.config.KeyboardSettings.remove')
def test_keyboardsettings_set_keyboard_shortcuts_other_than_default_saves(
        remove_mock, set_mock, kbsettings):
    kbsettings.set_keyboard_shortcuts('bar', ['Ctrl+R'], ['Ctrl+Z'])
    set_mock.assert_called_once_with('Actions/bar', 'Ctrl+R')
    remove_mock.assert_not_called()


@patch('beeref.config.KeyboardSettings.setValue')
@patch('beeref.config.KeyboardSettings.remove')
def test_keyboardsettings_set_keyboard_shortcuts_with_than_default_doesnt_save(
        remove_mock, set_mock, kbsettings):
    kbsettings.set_keyboard_shortcuts('bar', ['Ctrl+R'], ['Ctrl+R'])
    set_mock.assert_not_called()
    remove_mock.assert_called_once_with('Actions/bar')


def test_keyboardsettings_restore_defaults_restores(kbsettings):
    kbsettings.setValue('Actions/bar', 'Ctrl+R')
    kbsettings.restore_defaults()
    assert kbsettings.contains('Actions/bar') is False
