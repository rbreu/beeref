import pytest

from PyQt6 import QtCore

from beeref import utils
from .base import BeeTestCase


class GetRectFromPointsTestCase(BeeTestCase):

    def test_given_topleft_bottomright(self):
        rect = utils.get_rect_from_points(QtCore.QPointF(-10, -20),
                                          QtCore.QPointF(30, 40))
        assert rect.topLeft().x() == -10
        assert rect.topLeft().y() == -20
        assert rect.bottomRight().x() == 30
        assert rect.bottomRight().y() == 40

    def test_given_topright_bottomleft(self):
        rect = utils.get_rect_from_points(QtCore.QPointF(50, -20),
                                          QtCore.QPointF(-30, 40))
        assert rect.topLeft().x() == -30
        assert rect.topLeft().y() == -20
        assert rect.bottomRight().x() == 50
        assert rect.bottomRight().y() == 40


@pytest.mark.parametrize('number,base,expected',
                         [(33, 5, 35),
                          (-33, 5, -35),
                          (50, 5, 50),
                          (3.1, 0.5, 3.0)])
def test_round_to(number, base, expected):
    assert utils.round_to(number, base) == expected
