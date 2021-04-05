import os.path
import tempfile
from unittest.mock import MagicMock, patch

from PyQt6 import QtGui
import pytest

from beeref.fileio.errors import BeeFileIOError
from beeref.fileio.sql import SQLiteIO
from beeref.items import BeePixmapItem
from beeref.scene import BeeGraphicsScene
from ..base import BeeTestCase


class SQLiteIOTestCase(BeeTestCase):

    def setUp(self):
        self.scene_mock = MagicMock()
        self.io = SQLiteIO(':memory:', self.scene_mock, create_new=True)

    def test_ẁrite_meta_application_id(self):
        self.io.write_meta()
        result = self.io.fetchone('PRAGMA application_id')
        assert result[0] == SQLiteIO.APPLICATION_ID

    def test_ẁrite_meta_user_version(self):
        self.io.write_meta()
        result = self.io.fetchone('PRAGMA user_version')
        assert result[0] == SQLiteIO.USER_VERSION

    def test_ẁrite_meta_foreign_keys(self):
        self.io.write_meta()
        result = self.io.fetchone('PRAGMA foreign_keys')
        assert result[0] == 1

    def test_create_schema_on_new_when_create_new(self):
        self.io.create_schema_on_new()
        result = self.io.fetchone(
            'SELECT COUNT(*) FROM sqlite_master '
            'WHERE type="table" AND name NOT LIKE "sqlite_%"')
        assert result[0] == 2
        self.scene_mock.clear_save_ids.assert_called_once()

    def test_create_schema_on_new_when_not_create_new(self):
        self.io.create_new = False
        self.io.create_schema_on_new()
        result = self.io.fetchone(
            'SELECT COUNT(*) FROM sqlite_master '
            'WHERE type="table" AND name NOT LIKE "sqlite_%"')
        assert result[0] == 0
        self.scene_mock.clear_save_ids.assert_not_called()

    def test_readonly_doesnt_allow_write(self):
        scene = BeeGraphicsScene(None)
        with tempfile.TemporaryDirectory() as dirname:
            fname = os.path.join(dirname, 'test.bee')
            with open(fname, 'w') as f:
                f.write('foobar')
            io = SQLiteIO(fname, scene, readonly=True)

            with pytest.raises(BeeFileIOError) as exinfo:
                io.write()

            assert exinfo.value.filename == fname
            with open(fname, 'r') as f:
                f.read() == 'foobar'


class SQLiteIOWriteTestCase(BeeTestCase):

    def setUp(self):
        self.scene = BeeGraphicsScene(None)
        self.io = SQLiteIO(':memory:', self.scene, create_new=True)

    def test_calls_create_schema_on_new(self):
        with patch.object(self.io, 'create_schema_on_new') as crmock:
            with patch.object(self.io, 'fetchall'):
                with patch.object(self.io, 'exmany'):
                    self.io.write()
                    crmock.assert_called_once()

    def test_calls_write_meta(self):
        with patch.object(self.io, 'write_meta') as metamock:
            with patch.object(self.io, 'fetchall'):
                with patch.object(self.io, 'exmany'):
                    self.io.write()
                    metamock.assert_called_once()

    def test_inserts_new_item(self):
        item = BeePixmapItem(QtGui.QImage(), filename='bee.jpg')
        self.scene.addItem(item)
        item.setScale(1.3)
        item.setPos(44, 55)
        item.setZValue(0.22)
        item.setRotation(33)
        item.pixmap_to_bytes = MagicMock(return_value=b'abc')
        self.io.write()

        assert item.save_id == 1
        result = self.io.fetchone(
            'SELECT x, y, z, scale, rotation, filename, type, '
            'sqlar.data, sqlar.name '
            'FROM items '
            'INNER JOIN sqlar on sqlar.item_id = items.id')
        assert result[0] == 44.0
        assert result[1] == 55.0
        assert result[2] == 0.22
        assert result[3] == 1.3
        assert result[4] == 33
        assert result[5] == 'bee.jpg'
        assert result[6] == 'pixmap'
        assert result[7] == b'abc'
        assert result[8] == '0001-bee.png'

    def test_inserts_new_item_without_filename(self):
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        self.io.write()

        assert item.save_id == 1
        result = self.io.fetchone(
            'SELECT filename, sqlar.name FROM items '
            'INNER JOIN sqlar on sqlar.item_id = items.id')
        assert result[0] is None
        assert result[1] == '0001.png'

    def test_updates_existing_item(self):
        item = BeePixmapItem(QtGui.QImage(), filename='bee.png')
        self.scene.addItem(item)
        item.setScale(1.3)
        item.setPos(44, 55)
        item.setZValue(0.22)
        item.setRotation(33)
        item.save_id = 1
        item.pixmap_to_bytes = MagicMock(return_value=b'abc')
        self.io.write()
        item.setScale(0.7)
        item.setPos(20, 30)
        item.setZValue(0.33)
        item.setRotation(100)
        item.filename = 'new.png'
        item.pixmap_to_bytes.return_value = b'updated'
        self.io.create_new = False
        self.io.write()

        assert self.io.fetchone('SELECT COUNT(*) from items') == (1,)
        result = self.io.fetchone(
            'SELECT x, y, z, scale, rotation, filename, sqlar.data '
            'FROM items '
            'INNER JOIN sqlar on sqlar.item_id = items.id')
        assert result[0] == 20
        assert result[1] == 30
        assert result[2] == 0.33
        assert result[3] == 0.7
        assert result[4] == 100
        assert result[5] == 'new.png'
        assert result[6] == b'abc'

    def test_removes_nonexisting_item(self):
        item = BeePixmapItem(QtGui.QImage(), filename='bee.png')
        item.setScale(1.3)
        item.setPos(44, 55)
        self.scene.addItem(item)
        self.io.write()

        self.scene.removeItem(item)
        self.io.create_new = False
        self.io.write()

        assert self.io.fetchone('SELECT COUNT(*) from items') == (0,)
        assert self.io.fetchone('SELECT COUNT(*) from sqlar') == (0,)

    def test_update_recovers_from_borked_file(self):
        item = BeePixmapItem(QtGui.QImage(), filename='bee.png')
        self.scene.addItem(item)

        with tempfile.TemporaryDirectory() as dirname:
            fname = os.path.join(dirname, 'test.bee')
            with open(fname, 'w') as f:
                f.write('foobar')

            io = SQLiteIO(fname, self.scene, create_new=False)
            io.write()
            result = io.fetchone('SELECT COUNT(*) FROM items')
            assert result[0] == 1

    def test_updates_progress(self):
        progress = MagicMock()
        io = SQLiteIO(':memory:', self.scene, create_new=True,
                      progress=progress)
        item = BeePixmapItem(QtGui.QImage())
        self.scene.addItem(item)
        io.write()
        progress.setMaximum.assert_called_once_with(1)
        progress.setValue.assert_called_once_with(0)


class SQLiteIOReadTestCase(BeeTestCase):

    def setUp(self):
        self.scene = BeeGraphicsScene(None)

    def test_reads_readonly(self):
        with tempfile.TemporaryDirectory() as dirname:
            fname = os.path.join(dirname, 'test.bee')
            io = SQLiteIO(fname, self.scene, create_new=True)
            io.create_schema_on_new()
            io.ex('INSERT INTO items '
                  '(type, x, y, z, scale, rotation, filename) '
                  'VALUES (?, ?, ?, ?, ?, ?, ?) ',
                  ('pixmap', 22.2, 33.3, 0.22, 3.4, 45, 'bee.png'))
            io.ex('INSERT INTO sqlar (item_id, data) VALUES (?, ?)',
                  (1, self.imgdata3x3))
            io.connection.commit()
            del(io)

            io = SQLiteIO(fname, self.scene, readonly=True)
            io.read()
            assert len(self.scene.items()) == 1
            item = self.scene.items()[0]
            assert item.save_id == 1
            assert item.pos().x() == 22.2
            assert item.pos().y() == 33.3
            assert item.zValue() == 0.22
            assert item.scale() == 3.4
            assert item.rotation() == 45
            assert item.filename == 'bee.png'
            assert item.width == 3
            assert item.height == 3

    def test_updates_progress(self):
        progress = MagicMock()
        io = SQLiteIO(':memory:', self.scene, create_new=True,
                      progress=progress)

        io.create_schema_on_new()
        io.ex('INSERT INTO items (type, x, y, z, scale, filename) '
              'VALUES (?, ?, ?, ?, ?, ?) ',
              ('pixmap', 0, 0, 0, 1, 'bee.png'))
        io.ex('INSERT INTO sqlar (item_id, data) VALUES (?, ?)', (1, b''))
        io.connection.commit()
        io.read()
        progress.setMaximum.assert_called_once_with(1)
        progress.setValue.assert_called_once_with(0)

    def test_raises_error_when_file_borked(self):
        with tempfile.TemporaryDirectory() as dirname:
            fname = os.path.join(dirname, 'test.bee')
            with open(fname, 'w') as f:
                f.write('foobar')

            io = SQLiteIO(fname, self.scene, readonly=True)
            with pytest.raises(BeeFileIOError) as exinfo:
                io.read()
            assert exinfo.value.filename == fname

    def test_reads_raises_error_when_file_empty(self):
        with tempfile.TemporaryDirectory() as dirname:
            fname = os.path.join(dirname, 'test.bee')
            io = SQLiteIO(fname, self.scene, readonly=True)
            with pytest.raises(BeeFileIOError) as exinfo:
                io.read()
            assert exinfo.value.filename == fname

            # should not create a file on reading!
            assert os.path.isfile(fname) is False
