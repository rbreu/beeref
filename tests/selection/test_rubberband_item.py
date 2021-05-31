from PyQt6 import QtCore

from beeref.selection import RubberbandItem


def test_width():
    item = RubberbandItem()
    item.setRect(5, 5, 100, 80)
    assert item.width == 100


def test_height():
    item = RubberbandItem()
    item.setRect(5, 5, 100, 80)
    assert item.height == 80


def test_fit_topleft_to_bottomright():
    item = RubberbandItem()
    item.fit(QtCore.QPointF(-10, -20), QtCore.QPointF(30, 40))
    assert item.rect().topLeft().x() == -10
    assert item.rect().topLeft().y() == -20
    assert item.rect().bottomRight().x() == 30
    assert item.rect().bottomRight().y() == 40


def test_fit_topright_to_bottomleft():
    item = RubberbandItem()
    item.fit(QtCore.QPointF(50, -20), QtCore.QPointF(-30, 40))
    assert item.rect().topLeft().x() == -30
    assert item.rect().topLeft().y() == -20
    assert item.rect().bottomRight().x() == 50
    assert item.rect().bottomRight().y() == 40
