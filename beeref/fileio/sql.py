# This file is part of BeeRef.
#
# BeeRef is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BeeRef is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BeeRef.  If not, see <https://www.gnu.org/licenses/>.

"""BeeRef's native file format is using SQLite. Embedded files are
stored in an sqlar table so that they can be extracted using sqlite's
archive command line option.

For more info, see:

https://www.sqlite.org/appfileformat.html
https://www.sqlite.org/sqlar.html
"""

import logging
import os
import pathlib
import sqlite3

from PyQt6 import QtGui

from beeref.items import BeePixmapItem
from .errors import BeeFileIOError
from .schema import SCHEMA


logger = logging.getLogger(__name__)


def handle_sqlite_errors(func):
    def wrapper(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except sqlite3.Error as e:
            logger.exception(f'Error while reading/writing {self.filename}')
            self._close_connection()
            if self.worker:
                self.worker.finished.emit(self.filename, [str(e)])
            else:
                raise BeeFileIOError(msg=str(e), filename=self.filename) from e

    return wrapper


class SQLiteIO:
    USER_VERSION = 1
    APPLICATION_ID = 2060242126

    def __init__(self, filename, scene, create_new=False, readonly=False,
                 worker=None):
        self.scene = scene
        self.create_new = create_new
        self.filename = filename
        self.readonly = readonly
        self.worker = worker

    def __del__(self):
        self._close_connection()

    def _close_connection(self):
        if hasattr(self, '_connection'):
            self._connection.close()
            delattr(self, '_connection')
        if hasattr(self, '_cursor'):
            delattr(self, '_cursor')

    def _establish_connection(self):
        if (self.create_new
                and not self.readonly
                and os.path.exists(self.filename)):
            os.remove(self.filename)

        if self.create_new:
            self.scene.clear_save_ids()

        uri = pathlib.Path(self.filename).resolve().as_uri()
        if self.readonly:
            uri = f'{uri}?mode=ro'
        self._connection = sqlite3.connect(uri)
        self._cursor = self.connection.cursor()

    @property
    def connection(self):
        if not hasattr(self, '_connection'):
            self._establish_connection()
        return self._connection

    @property
    def cursor(self):
        if not hasattr(self, '_cursor'):
            self._establish_connection()
        return self._cursor

    def ex(self, *args, **kwargs):
        return self.cursor.execute(*args, **kwargs)

    def exmany(self, *args, **kwargs):
        return self.cursor.executemany(*args, **kwargs)

    def fetchone(self, *args, **kwargs):
        self.ex(*args, **kwargs)
        return self.cursor.fetchone()

    def fetchall(self, *args, **kwargs):
        self.ex(*args, **kwargs)
        return self.cursor.fetchall()

    def write_meta(self):
        self.ex('PRAGMA application_id=%s' % self.APPLICATION_ID)
        self.ex('PRAGMA user_version=%s' % self.USER_VERSION)
        self.ex('PRAGMA foreign_keys=1')

    def create_schema_on_new(self):
        if self.create_new:
            for schema in SCHEMA:
                self.ex(schema)

    @handle_sqlite_errors
    def read(self):
        rows = self.fetchall(
            'SELECT items.id, x, y, z, scale, rotation, flip, filename, '
            'sqlar.data '
            'FROM items INNER JOIN sqlar on sqlar.item_id = items.id')
        if self.worker:
            self.worker.begin_processing.emit(len(rows))

        for i, row in enumerate(rows):
            item = BeePixmapItem(QtGui.QImage(), filename=row[7])
            item.save_id = row[0]
            item.pixmap_from_bytes(row[8])
            item.setPos(row[1], row[2])
            item.setZValue(row[3])
            item.setScale(row[4])
            item.setRotation(row[5])
            if row[6] == -1:
                item.do_flip()
            self.scene.add_item_later(item)
            if self.worker:
                self.worker.progress.emit(i)
                if self.worker.canceled:
                    self.worker.finished.emit('', [])
                    return
        if self.worker:
            self.worker.finished.emit(self.filename, [])

    @handle_sqlite_errors
    def write(self):
        try:
            self.write_meta()
            self.create_schema_on_new()
            self.write_data()
        except sqlite3.Error:
            if self.create_new:
                # If writing to a new file fails, we can't recover
                raise
            else:
                # Updating a file failed; try creating it from scratch instead
                self.create_new = True
                self._close_connection()
                self.write()

    def write_data(self):
        to_delete = self.fetchall('SELECT id from ITEMS')
        to_save = list(self.scene.items_for_save())
        if self.worker:
            self.worker.begin_processing.emit(len(to_save))
        for i, item in enumerate(to_save):
            logger.debug(f'Saving {item} with id {item.save_id}')
            if item.save_id:
                self.update_item(item)
                to_delete.remove((item.save_id,))
            else:
                self.insert_item(item)
            if self.worker:
                self.worker.progress.emit(i)
                if self.worker.canceled:
                    break
        self.delete_items(to_delete)
        self.connection.commit()
        if self.worker:
            self.worker.finished.emit(self.filename, [])

    def delete_items(self, to_delete):
        self.exmany('DELETE FROM items WHERE id=?', to_delete)
        self.connection.commit()

    def insert_item(self, item):
        self.ex(
            'INSERT INTO items (type, x, y, z, scale, rotation, flip, '
            'filename) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            ('pixmap', item.pos().x(), item.pos().y(), item.zValue(),
             item.scale(), item.rotation(), item.flip(), item.filename))
        item.save_id = self.cursor.lastrowid
        pixmap = item.pixmap_to_bytes()

        if item.filename:
            basename = os.path.splitext(os.path.basename(item.filename))[0]
            name = '%04d-%s.png' % (item.save_id, basename)
        else:
            name = '%04d.png' % item.save_id

        self.ex(
            'INSERT INTO sqlar (item_id, name, mode, sz, data) '
            'VALUES (?, ?, ?, ?, ?)',
            (item.save_id, name, 0o644, len(pixmap), pixmap))
        self.connection.commit()

    def update_item(self, item):
        """Update item data.

        We only update the item data, not the pixmap data, as pixmap
        data never changes and is also time-consuming to save.
        """
        self.ex(
            'UPDATE items SET x=?, y=?, z=?, scale=?, rotation=?, flip=?, '
            'filename=? '
            'WHERE id=?',
            (item.pos().x(), item.pos().y(), item.zValue(), item.scale(),
             item.rotation(), item.flip(), item.filename, item.save_id))
        self.connection.commit()
