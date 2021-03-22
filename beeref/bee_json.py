import json

from beeref.items import BeePixmapItem


class BeeJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, 'to_bee_json'):
            return obj.to_bee_json()
        return json.JSONEncoder.default(self, obj)


def dumps(obj):
    return json.dumps(obj, cls=BeeJSONEncoder)


class BeeJSONDecoder(json.JSONDecoder):

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
