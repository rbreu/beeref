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

"""BeeRef's native file handling.

BeeRef files are JSON files with images embedded as base64-encoded PNG data.
"""

import json

from beeref.items import BeePixmapItem


class BeeJSONEncoder(json.JSONEncoder):
    """If an object defines the method ``to_bee_json``, use it to
    serialize the object to JSON."""

    def default(self, obj):
        if hasattr(obj, 'to_bee_json'):
            return obj.to_bee_json()
        return json.JSONEncoder.default(self, obj)


def dumps(obj):
    return json.dumps(obj, cls=BeeJSONEncoder)


class BeeJSONDecoder(json.JSONDecoder):
    """If a dictionary in the JSON file defines the key ``cls``, we use
    that class name and run the classmethod ``from_bee_json`` on it to
    deserialize the object."""

    bee_classes = [BeePixmapItem]

    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def get_bee_class(self, cls):
        for bee_class in self.bee_classes:
            if bee_class.__name__ == cls:
                return bee_class

    def object_hook(self, obj):
        if 'cls' in obj:
            bee_class = self.get_bee_class(obj['cls'])
            return bee_class.from_bee_json(obj)
        return obj


def loads(obj):
    return json.loads(obj, cls=BeeJSONDecoder)
