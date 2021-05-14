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
import os.path
import tempfile
from urllib.error import URLError
from urllib import request

from PyQt6 import QtGui


logger = logging.getLogger(__name__)


def load_image(path):
    if isinstance(path, str):
        return (QtGui.QImage(path), path)
    if path.isLocalFile():
        return (QtGui.QImage(path.path()), path.path())

    img = QtGui.QImage()
    try:
        imgdata = request.urlopen(path.url()).read()
    except URLError as e:
        logger.debug(f'Downloading image failed: {e.reason}')
    else:
        with tempfile.TemporaryDirectory() as tmp:
            fname = os.path.join(tmp, 'img')
            with open(fname, 'wb') as f:
                f.write(imgdata)
                logger.debug(f'Temporarily saved in: {fname}')
            img = QtGui.QImage(fname)
    return (img, path.url())
