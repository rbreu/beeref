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


IMG_LOADING_ERROR_MSG = (
    'Unknown format or too big?\n'
    'Check Settings -> Images & Items -> Maximum Image Size')


class BeeFileIOError(Exception):
    def __init__(self, msg, filename):
        self.msg = msg
        self.filename = filename
