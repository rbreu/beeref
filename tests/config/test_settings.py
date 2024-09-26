import os
import os.path
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from PyQt6 import QtGui

from beeref.config.settings import CommandlineArgs


def test_command_line_args_singleton():
    assert CommandlineArgs() is CommandlineArgs()
    assert CommandlineArgs()._args is CommandlineArgs()._args
    CommandlineArgs._instance = None


@patch('beeref.config.settings.parser.parse_args')
def test_command_line_args_with_check_forces_new_parsing(parse_mock):
    args1 = CommandlineArgs()
    parse_mock.assert_called_with([])
    args2 = CommandlineArgs(with_check=True)
    parse_mock.assert_called_with()
    args3 = CommandlineArgs()
    assert parse_mock.call_count == 2
    assert args1 is args2
    assert args2 is args3
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


def test_settings_on_startup_sets_alloc_from_settings(settings):
    settings.setValue('Items/image_allocation_limit', 66)
    QtGui.QImageReader.setAllocationLimit(100)
    settings.on_startup()
    assert QtGui.QImageReader.allocationLimit() == 66


def test_settings_on_startup_sets_alloc_from_environment(settings):
    settings.setValue('Items/image_allocation_limit', 66)
    os.environ['QT_IMAGEIO_MAXALLOC'] = '42'
    QtGui.QImageReader.setAllocationLimit(100)
    settings.on_startup()
    assert QtGui.QImageReader.allocationLimit() == 42


def test_settings_set_value_without_callback(settings):
    settings.FIELDS = {'foo/bar': {}}
    settings.setValue('foo/bar', 100)
    assert settings.value('foo/bar') == 100


def test_settings_set_value_with_callback(settings):
    foo_callback = MagicMock()
    settings.FIELDS = {'foo/bar': {'post_save_callback': foo_callback}}
    settings.setValue('foo/bar', 100)
    foo_callback.assert_called_once_with(100)
    assert settings.value('foo/bar') == 100


def test_settings_remove_without_callback(settings):
    settings.FIELDS = {'foo/bar': {}}
    settings.remove('foo/bar')
    assert settings.value('foo/bar') is None


def test_settings_remove_with_callback(settings):
    foo_callback = MagicMock()
    settings.FIELDS = {
        'foo/bar': {'default': 66,
                    'post_save_callback': foo_callback}
    }
    settings.remove('foo/bar')
    foo_callback.assert_called_once_with(66)
    assert settings.value('foo/bar') is None


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


def test_settings_value_changed_when_default(settings):
    assert settings.value_changed('Items/image_storage_format') is False


def test_settings_value_changed_when_chagned(settings):
    settings.setValue('Items/image_storage_format', 'jpg')
    assert settings.value_changed('Items/image_storage_format') is True


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
