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

"""BeeRef's native file format is using SQLite. For more info, see:

https://www.sqlite.org/appfileformat.html
"""

import os
import sqlite3

from PyQt6 import QtGui

from beeref.items import BeePixmapItem


SCHEMA = [
    """
    CREATE TABLE items (
        id INTEGER PRIMARY KEY,
        type TEXT NOT NULL,
        pos_x REAL DEFAULT 0,
        pos_y REAL DEFAULT 0,
        scale REAL DEFAULT 1,
        rotation REAL DEFAULT 0,
        flip_h INTEGER DEFAULT 0,
        flip_v INTEGER DEFAULT 0,
        filename TEXT
    )
    """,
    """
    CREATE TABLE imgdata (
        id INTEGER PRIMARY KEY,
        item_id INTEGER NOT NULL,
        data BLOB,
        FOREIGN KEY (item_id)
          REFERENCES items (id)
             ON DELETE CASCADE
             ON UPDATE NO ACTION
    )
    """,
]


class SQLiteIO:
    USER_VERSION = 1
    APPLICATION_ID = 2060242126

    def __init__(self, filename, scene, create_new=False):
        self.scene = scene
        self.filename = filename
        self.create_new = create_new
        # TBD: error handling (different for existing files/new files...)
        if self.create_new and os.path.exists(self.filename):
            os.remove(self.filename)
        self.connection = sqlite3.connect(self.filename)
        self.cursor = self.connection.cursor()

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

    def read(self):
        rows = self.fetchall(
            'SELECT pos_x, pos_y, scale, filename, imgdata.data '
            'FROM items '
            'INNER JOIN imgdata on imgdata.item_id = items.id')
        for row in rows:
            item = BeePixmapItem(QtGui.QImage(), filename=row[3])
            item.pixmap_from_bytes(row[4])
            item.setPos(row[0], row[1])
            item.setScale(row[2])
            self.scene.addItem(item)

    def write(self):
        self.write_meta()
        self.create_schema_on_new()

        to_delete = self.fetchall('SELECT id from ITEMS')
        for item in self.scene.items_for_save():
            if item.save_id and not self.create_new:
                self.update_item(item)
                to_delete.remove((item.save_id,))
            else:
                self.insert_item(item)
        self.delete_items(to_delete)
        self.connection.commit()

    def delete_items(self, to_delete):
        self.exmany('DELETE FROM items WHERE id=?', to_delete)
        self.connection.commit()

    def insert_item(self, item):
        self.ex(
            'INSERT INTO items (type, pos_x, pos_y, scale, filename) '
            'VALUES (?, ?, ?, ?, ?) ',
            ('pixmap', item.pos().x(), item.pos().y(), item.scale_factor,
             item.filename))
        item.save_id = self.cursor.lastrowid
        self.ex('INSERT INTO imgdata (item_id, data) VALUES (?, ?)',
                (item.save_id, item.pixmap_to_bytes()))
        self.connection.commit()

    def update_item(self, item):
        """Update item data.

        We only update the item data, not the pixmap data, as pixmap
        data never changes and is also time-consuming to save.
        """
        self.ex(
            'UPDATE items SET pos_x=?, pos_y=?, scale=?, filename=? '
            'WHERE id=?',
            (item.pos().x(), item.pos().y(), item.scale_factor,
             item.filename, item.save_id))
        self.connection.commit()
