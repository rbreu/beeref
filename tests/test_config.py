import os.path
import tempfile
from unittest.mock import patch

import pytest

from beeref.config import CommandlineArgs


def test_command_line_args_singleton():
    assert CommandlineArgs() is CommandlineArgs()
    assert CommandlineArgs()._args is CommandlineArgs()._args
    CommandlineArgs._instance = None


@patch('beeref.config.parser.parse_args')
def test_command_line_args_with_check_forces_new_parsing(parse_mock):
    args1 = CommandlineArgs()
    args2 = CommandlineArgs(with_check=True)
    parse_mock.assert_called_once()
    assert args1 is not args2
    CommandlineArgs._instance = None


def test_command_line_args_get():
    args = CommandlineArgs()
    assert args.loglevel == 'INFO'
    CommandlineArgs._instance = None


def test_command_line_args_get_unknown():
    args = CommandlineArgs()
    with pytest.raises(AttributeError):
        args.foo
    CommandlineArgs._instance = None


def test_settings_value_or_default_gets_default(settings):
    assert settings.valueOrDefault('Items/image_storage_format') == 'best'


def test_settings_value_or_default_gets_overriden_value(settings):
    settings.setValue('Items/image_storage_format', 'png')
    assert settings.valueOrDefault('Items/image_storage_format') == 'png'


def test_settings_value_or_default_gets_default_when_invalid(settings):
    settings.setValue('Items/image_storage_format', 'foo')
    assert settings.valueOrDefault('Items/image_storage_format') == 'best'


def test_settings_value_or_default_casts_value(settings):
    settings.setValue('Items/arrange_gap', '5')
    assert settings.valueOrDefault('Items/arrange_gap') == 5


def test_settings_value_or_default_gets_default_when_cast_error(settings):
    settings.setValue('Items/arrange_gap', 'foo')
    assert settings.valueOrDefault('Items/arrange_gap') == 0


def test_settings_restore_defaults_restores(settings):
    settings.setValue('Items/image_storage_format', 'png')
    settings.restore_defaults()
    assert settings.contains('Items/image_storage_format') is False


def test_settings_restore_defaults_leaves_other_settings(settings):
    settings.setValue('foo/bar', 'baz')
    settings.restore_defaults()
    assert settings.contains('foo/bar') is True
    assert settings.value('foo/bar') == 'baz'


def test_settings_recent_files_get_empty(settings):
    settings.get_recent_files() == []


def test_settings_recent_files_get_existing_only(settings):
    with tempfile.NamedTemporaryFile() as f:
        settings.update_recent_files('foo.bee')
        settings.update_recent_files(f.name)
    settings.get_recent_files(existing_only=True) == [f.name]


def test_settings_recent_files_update(settings):
    settings.update_recent_files('foo.bee')
    settings.update_recent_files('bar.bee')
    assert settings.get_recent_files() == [
        os.path.abspath('bar.bee'),
        os.path.abspath('foo.bee')]


def test_settings_recent_files_update_existing(settings):
    settings.update_recent_files('foo.bee')
    settings.update_recent_files('bar.bee')
    settings.update_recent_files('foo.bee')
    assert settings.get_recent_files() == [
        os.path.abspath('foo.bee'),
        os.path.abspath('bar.bee')]


def test_settings_recent_files_update_respects_max_num(settings):
    for i in range(15):
        settings.update_recent_files(f'{i}.bee')

    recent = settings.get_recent_files()
    assert len(recent) == 10
    assert recent[0] == os.path.abspath('14.bee')
    assert recent[-1] == os.path.abspath('5.bee')


def test_keyboardsettings_set_shortcuts(kbsettings):
    kbsettings.set_shortcuts('Actions', 'foo', ['Ctrl+F'])
    assert kbsettings.get_shortcuts('Actions', 'foo') == ['Ctrl+F']


def test_keyboardsettings_set_shortcuts_multiple(kbsettings):
    kbsettings.set_shortcuts('Actions', 'foo', ['Ctrl+F', 'Alt+O'])
    assert kbsettings.get_shortcuts('Actions', 'foo') == ['Ctrl+F', 'Alt+O']


def test_keyboardsettings_get_shortcuts_existing(kbsettings):
    kbsettings.set_shortcuts('Actions', 'bar', ['Ctrl+R'])
    shortcuts = kbsettings.get_shortcuts('Actions', 'bar', ['Ctrl+B'])
    assert shortcuts == ['Ctrl+R']


def test_keyboardsettings_get_shortcuts_default(kbsettings):
    shortcuts = kbsettings.get_shortcuts('Actions', 'bar', ['Ctrl+B'])
    assert shortcuts == ['Ctrl+B']


@patch('beeref.config.KeyboardSettings.setValue')
@patch('beeref.config.KeyboardSettings.remove')
def test_keyboardsettings_set_shortcuts_other_than_default_saves(
        remove_mock, set_mock, kbsettings):
    kbsettings.set_shortcuts('Actions', 'bar', ['Ctrl+R'], ['Ctrl+Z'])
    set_mock.assert_called_once_with('Actions/bar', 'Ctrl+R')
    remove_mock.assert_not_called()


@patch('beeref.config.KeyboardSettings.setValue')
@patch('beeref.config.KeyboardSettings.remove')
def test_keyboardsettings_set_shortcuts_with_than_default_doesnt_save(
        remove_mock, set_mock, kbsettings):
    kbsettings.set_shortcuts('Actions', 'bar', ['Ctrl+R'], ['Ctrl+R'])
    set_mock.assert_not_called()
    remove_mock.assert_called_once_with('Actions/bar')


def test_keyboardsettings_restore_defaults_restores(kbsettings):
    kbsettings.setValue('Actions/bar', 'Ctrl+R')
    kbsettings.restore_defaults()
    assert kbsettings.contains('Actions/bar') is False
