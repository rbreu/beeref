from unittest.mock import patch

from beeref.view import BeeGraphicsView
from .base import BeeTestCase


class BeeGraphicsViewTestCase(BeeTestCase):

    @patch('beeref.view.BeeGraphicsView.open_from_file')
    def test_init_without_filename(self, open_file_mock):
        BeeGraphicsView(self.app)
        open_file_mock.assert_not_called()

    @patch('beeref.view.BeeGraphicsView.open_from_file')
    def test_init_with_filename(self, open_file_mock):
        BeeGraphicsView(self.app, filename='bee.png')
        open_file_mock.assert_called_once_with('bee.png')
