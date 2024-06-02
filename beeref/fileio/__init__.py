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

import datetime
import logging
import os

from PyQt6 import QtCore

from beeref import commands
from beeref.fileio.errors import BeeFileIOError
from beeref.fileio.image import load_image
from beeref.fileio.sql import (
    SQLiteIO,
    copy_bee_file,
    is_bee_file,
    read_uppdate_from_file,
)
from beeref.items import BeePixmapItem


__all__ = [
    'is_bee_file',
    'load_bee',
    'load_images',
    'read_uppdate_from_file'
    'save_bee',
    'BeeFileIOError',
    'ThreadedLoader',
]

logger = logging.getLogger(__name__)


def load_bee(filename, scene, worker=None):
    """Load BeeRef native file."""
    logger.info(f'Loading from file {filename}...')
    io = SQLiteIO(filename, scene, readonly=True, worker=worker)
    return io.read()


def save_bee(filename, scene, create_new=False, worker=None):
    """Save BeeRef native file."""
    logger.info(f'Saving to file {filename}...')
    logger.debug(f'Create new: {create_new}')
    io = SQLiteIO(filename, scene, create_new, worker=worker)
    io.write()
    logger.info('End save')


def save_backup(filename, backup_filename, scene, worker=None):
    """Save backup bee file."""
    logger.info(f'Saving backup to file {backup_filename}...')
    copy_to_backup = False
    past = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)

    if filename and os.path.exists(filename):
        upddate_original = read_uppdate_from_file(filename) or past
        if os.path.exists(backup_filename):
            upddate_backup = read_uppdate_from_file(backup_filename) or past
            if upddate_original > upddate_backup:
                copy_to_backup = True
                logger.debug('Original file newer than backup')
        else:
            copy_to_backup = True
            logger.debug('Backup file does\'t exist yet')

    if copy_to_backup:
        logger.debug('Copying original file to backup file...')
        copy_bee_file(filename, backup_filename)

    io = SQLiteIO(backup_filename,
                  scene,
                  create_new=not os.path.exists(backup_filename),
                  update_save_ids=False,
                  worker=worker)
    io.write()


def load_images(filenames, pos, scene, worker):
    """Add images to existing scene."""

    errors = []
    items = []
    worker.begin_processing.emit(len(filenames))
    for i, filename in enumerate(filenames):
        logger.info(f'Loading image from file {filename}')
        img, filename = load_image(filename)
        worker.progress.emit(i)
        if img.isNull():
            logger.info(f'Could not load file {filename}')
            errors.append(filename)
            continue

        item = BeePixmapItem(img, filename)
        item.set_pos_center(pos)
        scene.add_item_later({'item': item, 'type': 'pixmap'}, selected=True)
        items.append(item)
        if worker.canceled:
            break
        # Give main thread time to process items:
        worker.msleep(10)

    scene.undo_stack.push(
        commands.InsertItems(scene, items, ignore_first_redo=True))
    worker.finished.emit('', errors)


class ThreadedIO(QtCore.QThread):
    """Dedicated thread for loading and saving."""

    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(str, list)
    begin_processing = QtCore.pyqtSignal(int)
    user_input_required = QtCore.pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.kwargs['worker'] = self
        self.canceled = False

    def run(self):
        self.func(*self.args, **self.kwargs)

    def on_canceled(self):
        self.canceled = True
