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

import json
import logging
import os
import pathlib
import shutil
import sqlite3
import tempfile

from PyQt6 import QtGui

from beeref import constants
from beeref.items import BeePixmapItem
from .errors import BeeFileIOError
from .schema import SCHEMA, USER_VERSION, MIGRATIONS, APPLICATION_ID


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
        if hasattr(self, '_tmpdir'):
            self._tmpdir.cleanup()
            delattr(self, '_tmpdir')

    def _establish_connection(self):
        if (self.create_new
                and not self.readonly
                and os.path.exists(self.filename)):
            os.remove(self.filename)

        if self.create_new:
            self.scene.clear_save_ids()

        uri = pathlib.Path(self.filename).resolve().as_uri()
        if self.readonly:
            uri = f'{uri}?mode=rw'
        self._connection = sqlite3.connect(uri, uri=True)
        self._cursor = self.connection.cursor()
        if not self.create_new:
            self._migrate()

    def _migrate(self):
        """Migrate database if necessary."""

        version = self.fetchone('PRAGMA user_version')[0]
        logger.debug(f'Found bee file version: {version}')
        if version == USER_VERSION:
            logger.debug('Version ok; no migrations necessary')
            return

        if self.readonly:
            try:
                # See whether file is writable so we can migrate it directly
                self.ex('PRAGMA application_id=%s' % APPLICATION_ID)
            except sqlite3.Error:
                logger.debug('File not writable; use temporary copy instead')
                self._connection.close()
                self._tmpdir = tempfile.TemporaryDirectory(
                    prefix=constants.APPNAME)
                tmpname = os.path.join(self._tmpdir.name, 'mig.bee')
                shutil.copyfile(self.filename, tmpname)
                self._connection = sqlite3.connect(tmpname)
                self._cursor = self.connection.cursor()

        for i in range(version, USER_VERSION):
            logger.debug(f'Migrating from version {i} to {i + 1}...')
            for migration in MIGRATIONS[i + 1]:
                self.ex(migration)
        self.write_meta()
        self.connection.commit()
        logger.debug('Migration finished')

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
        self.ex('PRAGMA application_id=%s' % APPLICATION_ID)
        self.ex('PRAGMA user_version=%s' % USER_VERSION)
        self.ex('PRAGMA foreign_keys=1')

    def create_schema_on_new(self):
        if self.create_new:
            self.write_meta()
            for schema in SCHEMA:
                self.ex(schema)

    @handle_sqlite_errors
    def read(self):
        rows = self.fetchall(
            'SELECT items.id, type, x, y, z, scale, rotation, flip, '
            'items.data, sqlar.data '
            'FROM items LEFT OUTER JOIN sqlar on sqlar.item_id = items.id')
        if self.worker:
            self.worker.begin_processing.emit(len(rows))

        for i, row in enumerate(rows):
            data = {
                'save_id': row[0],
                'type': row[1],
                'x': row[2],
                'y': row[3],
                'z': row[4],
                'scale': row[5],
                'rotation': row[6],
                'flip': row[7],
                'data': json.loads(row[8]),
            }

            if data['type'] == 'pixmap':
                data['item'] = BeePixmapItem(QtGui.QImage(), **data['data'])
                data['item'].pixmap_from_bytes(row[9])

            self.scene.add_item_later(data)

            if self.worker:
                logger.trace(f'Emit progress: {i}')
                self.worker.progress.emit(i)
                if self.worker.canceled:
                    self.worker.finished.emit('', [])
                    return
                # Give main thread time to process items:
                self.worker.msleep(10)
        if self.worker:
            self.worker.finished.emit(self.filename, [])

    @handle_sqlite_errors
    def write(self):
        if self.readonly:
            raise sqlite3.OperationalError(
                'attempt to write a readonly database')
        try:
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
            'data) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (item.TYPE, item.pos().x(), item.pos().y(), item.zValue(),
             item.scale(), item.rotation(), item.flip(),
             json.dumps(item.get_extra_save_data())))
        item.save_id = self.cursor.lastrowid

        if hasattr(item, 'pixmap_to_bytes'):
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
            'data=? '
            'WHERE id=?',
            (item.pos().x(), item.pos().y(), item.zValue(), item.scale(),
             item.rotation(), item.flip(),
             json.dumps(item.get_extra_save_data()),
             item.save_id))
        self.connection.commit()
