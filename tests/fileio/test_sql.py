import os.path
from unittest.mock import MagicMock, patch

from PyQt6 import QtGui
import pytest

from beeref.fileio.errors import BeeFileIOError
from beeref.fileio.sql import SQLiteIO
from beeref.items import BeePixmapItem


def test_sqliteio_ẁrite_meta_application_id():
    io = SQLiteIO(':memory:', MagicMock(), create_new=True)
    io.write_meta()
    result = io.fetchone('PRAGMA application_id')
    assert result[0] == SQLiteIO.APPLICATION_ID


def test_sqliteio_ẁrite_meta_user_version():
    io = SQLiteIO(':memory:', MagicMock(), create_new=True)
    io.write_meta()
    result = io.fetchone('PRAGMA user_version')
    assert result[0] == SQLiteIO.USER_VERSION


def test_sqliteio_ẁrite_meta_foreign_keys():
    io = SQLiteIO(':memory:', MagicMock(), create_new=True)
    io.write_meta()
    result = io.fetchone('PRAGMA foreign_keys')
    assert result[0] == 1


def test_sqliteio_create_schema_on_new_when_create_new():
    scene_mock = MagicMock()
    io = SQLiteIO(':memory:', scene_mock, create_new=True)
    io.create_schema_on_new()
    result = io.fetchone(
        'SELECT COUNT(*) FROM sqlite_master '
        'WHERE type="table" AND name NOT LIKE "sqlite_%"')
    assert result[0] == 2
    scene_mock.clear_save_ids.assert_called_once()


def test_sqliteio_create_schema_on_new_when_not_create_new():
    scene_mock = MagicMock()
    io = SQLiteIO(':memory:', scene_mock, create_new=False)
    io.create_schema_on_new()
    result = io.fetchone(
        'SELECT COUNT(*) FROM sqlite_master '
        'WHERE type="table" AND name NOT LIKE "sqlite_%"')
    assert result[0] == 0
    scene_mock.clear_save_ids.assert_not_called()


def test_sqliteio_readonly_doesnt_allow_write(view, tmpdir):
    fname = os.path.join(tmpdir, 'test.bee')
    with open(fname, 'w') as f:
        f.write('foobar')
    io = SQLiteIO(fname, view.scene, readonly=True)

    with pytest.raises(BeeFileIOError) as exinfo:
        io.write()

    assert exinfo.value.filename == fname
    with open(fname, 'r') as f:
        f.read() == 'foobar'


def test_sqliteio_write_calls_create_schema_on_new(view):
    io = SQLiteIO(':memory:', view.scene, create_new=True)
    with patch.object(io, 'create_schema_on_new') as crmock:
        with patch.object(io, 'fetchall'):
            with patch.object(io, 'exmany'):
                io.write()
                crmock.assert_called_once()


def test_sqliteio_write_calls_write_meta(view):
    io = SQLiteIO(':memory:', view.scene, create_new=True)
    with patch.object(io, 'write_meta') as metamock:
        with patch.object(io, 'fetchall'):
            with patch.object(io, 'exmany'):
                io.write()
                metamock.assert_called_once()


def test_sqliteio_write_inserts_new_item(view):
    item = BeePixmapItem(QtGui.QImage(), filename='bee.jpg')
    view.scene.addItem(item)
    item.setScale(1.3)
    item.setPos(44, 55)
    item.setZValue(0.22)
    item.setRotation(33)
    item.do_flip()
    item.pixmap_to_bytes = MagicMock(return_value=b'abc')
    io = SQLiteIO(':memory:', view.scene, create_new=True)
    io.write()

    assert item.save_id == 1
    result = io.fetchone(
        'SELECT x, y, z, scale, rotation, flip, filename, type, '
        'sqlar.data, sqlar.name '
        'FROM items '
        'INNER JOIN sqlar on sqlar.item_id = items.id')
    assert result[0] == 44.0
    assert result[1] == 55.0
    assert result[2] == 0.22
    assert result[3] == 1.3
    assert result[4] == 33
    assert result[5] == -1
    assert result[6] == 'bee.jpg'
    assert result[7] == 'pixmap'
    assert result[8] == b'abc'
    assert result[9] == '0001-bee.png'


def test_sqliteio_write_inserts_new_item_without_filename(view, item):
    view.scene.addItem(item)
    io = SQLiteIO(':memory:', view.scene, create_new=True)
    io.write()

    assert item.save_id == 1
    result = io.fetchone(
        'SELECT filename, sqlar.name FROM items '
        'INNER JOIN sqlar on sqlar.item_id = items.id')
    assert result[0] is None
    assert result[1] == '0001.png'


def test_sqliteio_write_updates_existing_item(view):
    item = BeePixmapItem(QtGui.QImage(), filename='bee.png')
    view.scene.addItem(item)
    item.setScale(1.3)
    item.setPos(44, 55)
    item.setZValue(0.22)
    item.setRotation(33)
    item.save_id = 1
    item.pixmap_to_bytes = MagicMock(return_value=b'abc')
    io = SQLiteIO(':memory:', view.scene, create_new=True)
    io.write()
    item.setScale(0.7)
    item.setPos(20, 30)
    item.setZValue(0.33)
    item.setRotation(100)
    item.do_flip()
    item.filename = 'new.png'
    item.pixmap_to_bytes.return_value = b'updated'
    io.create_new = False
    io.write()

    assert io.fetchone('SELECT COUNT(*) from items') == (1,)
    result = io.fetchone(
        'SELECT x, y, z, scale, rotation, flip, filename, sqlar.data '
        'FROM items '
        'INNER JOIN sqlar on sqlar.item_id = items.id')
    assert result[0] == 20
    assert result[1] == 30
    assert result[2] == 0.33
    assert result[3] == 0.7
    assert result[4] == 100
    assert result[5] == -1
    assert result[6] == 'new.png'
    assert result[7] == b'abc'


def test_sqliteio_write_removes_nonexisting_item(view):
    item = BeePixmapItem(QtGui.QImage(), filename='bee.png')
    item.setScale(1.3)
    item.setPos(44, 55)
    view.scene.addItem(item)
    io = SQLiteIO(':memory:', view.scene, create_new=True)
    io.write()

    view.scene.removeItem(item)
    io.create_new = False
    io.write()

    assert io.fetchone('SELECT COUNT(*) from items') == (0,)
    assert io.fetchone('SELECT COUNT(*) from sqlar') == (0,)


def test_sqliteio_write_update_recovers_from_borked_file(view, tmpdir):
    item = BeePixmapItem(QtGui.QImage(), filename='bee.png')
    view.scene.addItem(item)

    fname = os.path.join(tmpdir, 'test.bee')
    with open(fname, 'w') as f:
        f.write('foobar')

    io = SQLiteIO(fname, view.scene, create_new=False)
    io.write()
    result = io.fetchone('SELECT COUNT(*) FROM items')
    assert result[0] == 1


def test_sqliteio_write_updates_progress(view):
    worker = MagicMock(canceled=False)
    io = SQLiteIO(':memory:', view.scene, create_new=True, worker=worker)
    item = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item)
    io.write()
    worker.begin_processing.emit.assert_called_once_with(1)
    worker.progress.emit.assert_called_once_with(0)
    worker.finished.emit.assert_called_once_with(':memory:', [])


def test_sqliteio_write_canceled(view):
    worker = MagicMock(canceled=True)
    io = SQLiteIO(':memory:', view.scene, create_new=True, worker=worker)
    item = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item)
    item = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item)
    io.write()
    worker.begin_processing.emit.assert_called_once_with(2)
    worker.progress.emit.assert_called_once_with(0)
    worker.finished.emit.assert_called_once_with(':memory:', [])


def test_sqliteio_read_reads_readonly(view, tmpdir, imgdata3x3):
    fname = os.path.join(tmpdir, 'test.bee')
    io = SQLiteIO(fname, view.scene, create_new=True)
    io.create_schema_on_new()
    io.ex('INSERT INTO items '
          '(type, x, y, z, scale, rotation, flip, filename) '
          'VALUES (?, ?, ?, ?, ?, ?, ?, ?) ',
          ('pixmap', 22.2, 33.3, 0.22, 3.4, 45, -1, 'bee.png'))
    io.ex('INSERT INTO sqlar (item_id, data) VALUES (?, ?)',
          (1, imgdata3x3))
    io.connection.commit()
    del(io)

    io = SQLiteIO(fname, view.scene, readonly=True)
    io.read()
    item, selected = view.scene.items_to_add.get()
    assert selected is False
    assert item.save_id == 1
    assert item.pos().x() == 22.2
    assert item.pos().y() == 33.3
    assert item.zValue() == 0.22
    assert item.scale() == 3.4
    assert item.rotation() == 45
    assert item.flip() == -1
    assert item.filename == 'bee.png'
    assert item.width == 3
    assert item.height == 3
    assert view.scene.items_to_add.empty() is True


def test_sqliteio_read_updates_progress(view):
    worker = MagicMock(canceled=False)
    io = SQLiteIO(':memory:', view.scene, create_new=True,
                  worker=worker)

    io.create_schema_on_new()
    io.ex('INSERT INTO items (type, x, y, z, scale, filename) '
          'VALUES (?, ?, ?, ?, ?, ?) ',
          ('pixmap', 0, 0, 0, 1, 'bee.png'))
    io.ex('INSERT INTO sqlar (item_id, data) VALUES (?, ?)', (1, b''))
    io.connection.commit()
    io.read()
    worker.begin_processing.emit.assert_called_once_with(1)
    worker.progress.emit.assert_called_once_with(0)
    worker.finished.emit.assert_called_once_with(':memory:', [])


def test_sqliteio_read_canceled(view):
    worker = MagicMock(canceled=True)
    io = SQLiteIO(':memory:', view.scene, create_new=True, worker=worker)

    io.create_schema_on_new()
    io.ex('INSERT INTO items (type, x, y, z, scale, filename) '
          'VALUES (?, ?, ?, ?, ?, ?) ',
          ('pixmap', 0, 0, 0, 1, 'bee.png'))
    io.ex('INSERT INTO sqlar (item_id, data) VALUES (?, ?)', (1, b''))
    io.ex('INSERT INTO items (type, x, y, z, scale, filename) '
          'VALUES (?, ?, ?, ?, ?, ?) ',
          ('pixmap', 50, 50, 0, 1, 'bee2.png'))
    io.ex('INSERT INTO sqlar (item_id, data) VALUES (?, ?)', (1, b''))
    io.connection.commit()
    io.read()
    worker.begin_processing.emit.assert_called_once_with(2)
    worker.progress.emit.assert_called_once_with(0)
    worker.finished.emit.assert_called_once_with('', [])


def test_sqliteio_read_raises_error_when_file_borked(view, tmpdir):
    fname = os.path.join(tmpdir, 'test.bee')
    with open(fname, 'w') as f:
        f.write('foobar')

    io = SQLiteIO(fname, view.scene, readonly=True)
    with pytest.raises(BeeFileIOError) as exinfo:
        io.read()
    assert exinfo.value.filename == fname


def test_sqliteio_read_emits_error_message_when_file_borked(view, tmpdir):
    fname = os.path.join(tmpdir, 'test.bee')
    with open(fname, 'w') as f:
        f.write('foobar')

    worker = MagicMock()
    io = SQLiteIO(fname, view.scene, readonly=True, worker=worker)
    io.read()
    worker.finished.emit.assert_called_once()
    args = worker.finished.emit.call_args_list[0][0]
    assert args[0] == fname
    assert len(args[1]) == 1


def test_sqliteio_read_raises_error_when_file_empty(view, tmpdir):
    fname = os.path.join(tmpdir, 'test.bee')
    io = SQLiteIO(fname, view.scene, readonly=True)
    with pytest.raises(BeeFileIOError) as exinfo:
        io.read()
    assert exinfo.value.filename == fname

    # should not create a file on reading!
    assert os.path.isfile(fname) is False
