from PyQt6 import QtGui

from beeref.assets import BeeAssets
from .base import BeeTestCase


class GetRectFromPointsTestCase(BeeTestCase):

    def test_singleton(self):
        assert BeeAssets() is BeeAssets()
        assert BeeAssets().logo is BeeAssets().logo

    def test_has_logo(self):
        assert isinstance(BeeAssets().logo, QtGui.QIcon)
