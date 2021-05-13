import os.path
import tempfile
from unittest.mock import patch

import pytest

from beeref.config import CommandlineArgs, BeeSettings
from .base import BeeTestCase


class CommandlineArgsTestCase(BeeTestCase):

    def test_singleton(self):
        assert CommandlineArgs() is CommandlineArgs()
        assert CommandlineArgs()._args is CommandlineArgs()._args

    @patch('beeref.config.parser.parse_args')
    def test_with_check_forces_new_parsing(self, parse_mock):
        args1 = CommandlineArgs()
        args2 = CommandlineArgs(with_check=True)
        parse_mock.assert_called_once()
        assert args1 is not args2

    def test_get(self):
        args = CommandlineArgs()
        assert args.loglevel == 'INFO'

    def test_get_unknown(self):
        args = CommandlineArgs()
        with pytest.raises(AttributeError):
            args.foo


class BeeSettingsRecentFilesTestCase(BeeTestCase):

    def setUp(self):
        self.settings = BeeSettings()

    def test_get_empty(self):
        self.settings.get_recent_files() == []

    def test_get_existing_only(self):
        with tempfile.NamedTemporaryFile() as f:
            self.settings.update_recent_files('foo.bee')
            self.settings.update_recent_files(f.name)
        self.settings.get_recent_files(existing_only=True) == [f.name]

    def test_update(self):
        self.settings.update_recent_files('foo.bee')
        self.settings.update_recent_files('bar.bee')
        assert self.settings.get_recent_files() == [
            os.path.abspath('bar.bee'),
            os.path.abspath('foo.bee')]

    def test_update_existing(self):
        self.settings.update_recent_files('foo.bee')
        self.settings.update_recent_files('bar.bee')
        self.settings.update_recent_files('foo.bee')
        assert self.settings.get_recent_files() == [
            os.path.abspath('foo.bee'),
            os.path.abspath('bar.bee')]

    def test_update_respects_max_num(self):
        for i in range(15):
            self.settings.update_recent_files(f'{i}.bee')

        recent = self.settings.get_recent_files()
        assert len(recent) == 10
        assert recent[0] == os.path.abspath('14.bee')
        assert recent[-1] == os.path.abspath('5.bee')
