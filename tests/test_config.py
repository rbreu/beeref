import os.path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from PyQt6 import QtCore

from beeref.config import CommandlineArgs, qt_message_handler


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


@patch('beeref.config.qtlogger.info')
def test_qt_message_handler_without(log_mock, qapp):
    qt_message_handler(QtCore.QtMsgType.QtInfoMsg, None, 'foo')
    log_mock.assert_called_once_with('foo')


@patch('beeref.config.qtlogger.warning')
def test_qt_message_handler_with_context(log_mock, qapp):
    ctx = SimpleNamespace(file='bla.txt', line='1', function='myfunc')
    qt_message_handler(QtCore.QtMsgType.QtWarningMsg, ctx, 'foo')
    log_mock.assert_called_once_with('foo: File bla.txt, line 1, in myfunc')
