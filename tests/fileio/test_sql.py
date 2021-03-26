import os.path
from unittest.mock import MagicMock, patch

from PyQt6 import QtGui

from beeref.fileio.sql import SQLiteIO
from beeref.items import BeePixmapItem
from beeref.scene import BeeGraphicsScene
from ..base import BeeTestCase


class SQLiteIOTestCase(BeeTestCase):

    def setUp(self):
        self.io = SQLiteIO(':memory:', None, create_new=True)

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

    def test_create_schema_on_new_when_not_create_new(self):
        self.io.create_new = False
        self.io.create_schema_on_new()
        result = self.io.fetchone(
            'SELECT COUNT(*) FROM sqlite_master '
            'WHERE type="table" AND name NOT LIKE "sqlite_%"')
        assert result[0] == 0


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
        item = BeePixmapItem(QtGui.QImage(), filename='bee.png')
        item.setScale(1.3)
        item.setPos(44, 55)
        item.pixmap_to_bytes = MagicMock(return_value=b'abc')
        self.scene.addItem(item)
        self.io.write()

        assert item.save_id == 1
        result = self.io.fetchone(
            'SELECT pos_x, pos_y, scale, filename, imgdata.data, type '
            'FROM items '
            'INNER JOIN imgdata on imgdata.item_id = items.id')
        assert result[0] == 44.0
        assert result[1] == 55.0
        assert result[2] == 1.3
        assert result[3] == 'bee.png'
        assert result[4] == b'abc'
        assert result[5] == 'pixmap'

    def test_updates_existing_item(self):
        item = BeePixmapItem(QtGui.QImage(), filename='bee.png')
        item.setScale(1.3)
        item.setPos(44, 55)
        item.save_id = 1
        self.scene.addItem(item)
        item.pixmap_to_bytes = MagicMock(return_value=b'abc')
        self.io.write()

        item.setScale(0.7)
        item.setPos(20, 30)
        item.filename = 'new.png'
        item.pixmap_to_bytes.return_value = b'updated'
        self.io.create_new = False
        self.io.write()

        assert self.io.fetchone('SELECT COUNT(*) from items') == (1,)
        result = self.io.fetchone(
            'SELECT pos_x, pos_y, scale, filename, imgdata.data '
            'FROM items '
            'INNER JOIN imgdata on imgdata.item_id = items.id')
        assert result[0] == 20
        assert result[1] == 30
        assert result[2] == 0.7
        assert result[3] == 'new.png'
        assert result[4] == b'abc'

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
        assert self.io.fetchone('SELECT COUNT(*) from imgdata') == (0,)


class SQLiteIOLOadTestCase(BeeTestCase):

    def setUp(self):
        self.scene = BeeGraphicsScene(None)
        self.io = SQLiteIO(':memory:', self.scene, create_new=True)

    def test_loads(self):
        root = os.path.dirname(__file__)
        filename = os.path.join(root, '..', 'assets', 'test3x3.png')
        with open(filename, 'rb') as f:
            imgdata = f.read()
        self.io.create_schema_on_new()
        self.io.ex(
            'INSERT INTO items (type, pos_x, pos_y, scale, filename) '
            'VALUES (?, ?, ?, ?, ?) ',
            ('pixmap', 22.2, 33.3, 3.4, 'bee.png'))
        self.io.ex('INSERT INTO imgdata (item_id, data) VALUES (?, ?)',
                   (1, imgdata))
        self.io.read()
        assert len(self.scene.items()) == 1
        item = self.scene.items()[0]
        assert item.save_id == 1
        assert item.pos().x() == 22.2
        assert item.pos().y() == 33.3
        assert item.scale_factor == 3.4
        assert item.filename == 'bee.png'
        assert item.width == 3
        assert item.height == 3
