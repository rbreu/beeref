import math
from unittest.mock import patch, MagicMock

from beeref.scene import BeeGraphicsScene
from .base import BeeTestCase


class BeeGraphicsSceneNormalizeTestCase(BeeTestCase):

    def test_normalize_height(self):
        item1 = MagicMock(height=100)
        item2 = MagicMock(height=200)
        scene = BeeGraphicsScene()

        with patch.object(scene, 'selectedItems',
                          return_value=[item1, item2]):
            scene.normalize_height()

        item1.setScale.assert_called_once_with(1.5)
        item2.setScale.assert_called_once_with(0.75)

    def test_normalize_width(self):
        item1 = MagicMock(width=100)
        item2 = MagicMock(width=200)
        scene = BeeGraphicsScene()

        with patch.object(scene, 'selectedItems',
                          return_value=[item1, item2]):
            scene.normalize_width()

        item1.setScale.assert_called_once_with(1.5)
        item2.setScale.assert_called_once_with(0.75)

    def test_normalize_size(self):
        item1 = MagicMock(width=100, height=200)
        item2 = MagicMock(width=400, height=100)
        scene = BeeGraphicsScene()

        with patch.object(scene, 'selectedItems',
                          return_value=[item1, item2]):
            scene.normalize_size()

        item1.setScale.assert_called_once_with(math.sqrt(1.5))
        item2.setScale.assert_called_once_with(math.sqrt(0.75))
