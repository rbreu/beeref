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

import logging

from beeref.fileio.errors import BeeFileIOError
from beeref.fileio.sql import SQLiteIO


__all__ = ['load', 'save', 'BeeFileIOError']
logger = logging.getLogger('BeeRef')


def load(filename, scene, progress=None):
    logger.info(f'Loading from file {filename}...')
    io = SQLiteIO(filename, scene, readonly=True, progress=progress)
    return io.read()


def save(filename, scene, create_new=False, progress=None):
    logger.info(f'Saving to file {filename}...')
    logger.debug(f'Create new: {create_new}')
    io = SQLiteIO(filename, scene, create_new, progress=progress)
    io.write()
    logger.debug('Saved!')
