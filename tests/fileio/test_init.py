import os.path
import tempfile
from unittest.mock import MagicMock, patch

from PyQt6 import QtCore

from beeref import fileio
from beeref import commands
from beeref.scene import BeeGraphicsScene
from ..base import BeeTestCase


@patch('beeref.fileio.sql.SQLiteIO.write')
def test_save_bee_create_new_false(write_mock):
    with tempfile.TemporaryDirectory() as dirname:
        fname = os.path.join(dirname, 'test.bee')
        fileio.save_bee(fname, 'myscene', create_new=False)
        write_mock.assert_called_once()


@patch('beeref.fileio.sql.SQLiteIO.read')
def test_read_bee(read_mock):
    with tempfile.TemporaryDirectory() as dirname:
        fname = os.path.join(dirname, 'test.bee')
        fileio.load_bee(fname, 'myscene')
        read_mock.assert_called_once()


class LoadImagesTestCase(BeeTestCase):

    def setUp(self):
        self.scene = BeeGraphicsScene(MagicMock())

    def test_loads(self):
        worker = MagicMock(canceled=False)
        fileio.load_images([self.imgfilename3x3],
                           QtCore.QPointF(5, 6), self.scene, worker)
        worker.begin_processing.emit.assert_called_once_with(1)
        worker.progress.emit.assert_called_once_with(0)
        worker.finished.emit.assert_called_once_with('', [])
        items = self.queue2list(self.scene.items_to_add)
        assert len(items) == 1
        item = items[0][0]
        args = self.scene.undo_stack.push.call_args_list[0][0]
        cmd = args[0]
        assert isinstance(cmd, commands.InsertItems)
        assert cmd.items == [item]
        assert cmd.scene == self.scene
        assert cmd.ignore_first_redo is True
        assert item.pos() == QtCore.QPointF(3.5, 4.5)

    def test_canceled(self):
        worker = MagicMock(canceled=True)
        fileio.load_images([self.imgfilename3x3, self.imgfilename3x3],
                           QtCore.QPointF(5, 6), self.scene, worker)
        worker.begin_processing.emit.assert_called_once_with(2)
        worker.progress.emit.assert_called_once_with(0)
        worker.finished.emit.assert_called_once_with('', [])
        items = self.queue2list(self.scene.items_to_add)
        assert len(items) == 1
        item = items[0][0]
        args = self.scene.undo_stack.push.call_args_list[0][0]
        cmd = args[0]
        assert isinstance(cmd, commands.InsertItems)
        assert cmd.items == [item]
        assert cmd.scene == self.scene
        assert cmd.ignore_first_redo is True
        assert item.pos() == QtCore.QPointF(3.5, 4.5)

    def test_error(self):
        worker = MagicMock(canceled=False)
        fileio.load_images(['foo.jpg', self.imgfilename3x3],
                           QtCore.QPointF(5, 6), self.scene, worker)
        worker.begin_processing.emit.assert_called_once_with(2)
        worker.progress.emit.assert_any_call(0)
        worker.progress.emit.assert_any_call(1)
        worker.finished.emit.assert_called_once_with('', ['foo.jpg'])
        items = self.queue2list(self.scene.items_to_add)
        assert len(items) == 1
        item = items[0][0]
        args = self.scene.undo_stack.push.call_args_list[0][0]
        cmd = args[0]
        assert isinstance(cmd, commands.InsertItems)
        assert cmd.items == [item]
        assert cmd.scene == self.scene
        assert cmd.ignore_first_redo is True
        assert item.pos() == QtCore.QPointF(3.5, 4.5)
