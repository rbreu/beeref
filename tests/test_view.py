from unittest.mock import patch

from beeref.view import BeeGraphicsView
from .base import BeeTestCase


class BeeGraphicsViewTestCase(BeeTestCase):

    @patch('beeref.view.BeeGraphicsView.open_from_file')
    def test_init_without_filename(self, open_file_mock):
        with patch('beeref.view.commandline_args') as args_mock:
            args_mock.filename = None
            BeeGraphicsView(self.app)
            open_file_mock.assert_not_called()

    @patch('beeref.view.BeeGraphicsView.open_from_file')
    def test_init_with_filename(self, open_file_mock):
        with patch('beeref.view.commandline_args') as args_mock:
            args_mock.filename = 'test.bee'
            BeeGraphicsView(self.app)
            open_file_mock.assert_called_once_with('test.bee')
