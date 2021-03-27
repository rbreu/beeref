import os.path
import tempfile
from unittest.mock import patch

from beeref import fileio


@patch('beeref.fileio.sql.SQLiteIO.write')
def test_save_create_new_false(write_mock):
    with tempfile.TemporaryDirectory() as dirname:
        fname = os.path.join(dirname, 'test.bee')
        fileio.save(fname, 'myscene', create_new=False)
        write_mock.assert_called_once()


@patch('beeref.fileio.sql.SQLiteIO.read')
def test_write(read_mock):
    with tempfile.TemporaryDirectory() as dirname:
        fname = os.path.join(dirname, 'test.bee')
        fileio.load(fname, 'myscene')
        read_mock.assert_called_once()
