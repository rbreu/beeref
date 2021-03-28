import math
from unittest.mock import patch, MagicMock

from PyQt6 import QtGui

from beeref.scene import BeeGraphicsScene
from .base import BeeTestCase


class BeeGraphicsSceneNormalizeTestCase(BeeTestCase):

    def setUp(self):
        self.undo_stack = QtGui.QUndoStack()
        self.scene = BeeGraphicsScene(self.undo_stack)

    def test_normalize_height(self):
        item1 = MagicMock(height=100, scale_factor=1)
        item2 = MagicMock(height=200, scale_factor=3)

        with patch.object(self.scene, 'selectedItems',
                          return_value=[item1, item2]):
            self.scene.normalize_height()

        item1.setScale.assert_called_once_with(1.5)
        item2.setScale.assert_called_once_with(0.75)

    def test_normalize_height_when_no_items(self):
        self.scene.normalize_height()

    def test_normalize_width(self):
        item1 = MagicMock(width=100, scale_factor=1)
        item2 = MagicMock(width=200, scale_factor=3)

        with patch.object(self.scene, 'selectedItems',
                          return_value=[item1, item2]):
            self.scene.normalize_width()

        item1.setScale.assert_called_once_with(1.5)
        item2.setScale.assert_called_once_with(0.75)

    def test_normalize_width_when_no_items(self):
        self.scene.normalize_width()

    def test_normalize_size(self):
        item1 = MagicMock(width=100, height=200, scale_factor=1)
        item2 = MagicMock(width=400, height=100, scale_factor=3)

        with patch.object(self.scene, 'selectedItems',
                          return_value=[item1, item2]):
            self.scene.normalize_size()

        item1.setScale.assert_called_once_with(math.sqrt(1.5))
        item2.setScale.assert_called_once_with(math.sqrt(0.75))

    def test_normalize_size_when_no_items(self):
        self.scene.normalize_size()
