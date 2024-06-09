import math
from unittest.mock import patch, MagicMock

import pytest
from pytest import approx

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref import commands
from beeref.items import BeePixmapItem, BeeTextItem


def test_add_remove_item(view, item):
    view.scene.addItem(item)
    assert view.scene.items() == [item]
    view.scene.removeItem(item)
    assert view.scene.items() == []


def test_cancel_crop_mode_when_crop(view, item):
    view.scene.crop_item = item
    item.exit_crop_mode = MagicMock()
    view.scene.cancel_crop_mode()
    item.exit_crop_mode.assert_called_once_with(confirm=True)


def test_cancel_crop_mode_when_no_crop(view, item):
    view.scene.cancel_crop_mode()


def test_copy_selection_to_internal_clipboard(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item3 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item3)

    view.scene.copy_selection_to_internal_clipboard()
    assert set(view.scene.internal_clipboard) == {item1, item2}
    assert set(view.scene.items_for_save()) == {item1, item2, item3}


def test_paste_from_internal_clipboard(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    item2.setScale(3.3)
    view.scene.internal_clipboard = [item2]

    view.scene.paste_from_internal_clipboard(None)
    assert len(list(view.scene.items_for_save())) == 2
    assert item1.isSelected() is False
    new_item = view.scene.selectedItems(user_only=True)[0]
    assert new_item.scale() == 3.3
    assert new_item is not item2


def test_raise_to_top(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.setZValue(0.06)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setZValue(0.02)
    item3 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item3)
    item3.setZValue(0.07)
    view.scene.cancel_crop_mode = MagicMock()

    view.scene.raise_to_top()
    assert item1.zValue() == 0.11 + view.scene.Z_STEP
    assert item2.zValue() == 0.07 + view.scene.Z_STEP
    assert item3.zValue() == 0.07
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_lower_to_bottom(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.setZValue(-0.06)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setZValue(-0.02)
    item3 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item3)
    item3.setZValue(-0.07)
    view.scene.cancel_crop_mode = MagicMock()

    view.scene.lower_to_bottom()
    assert item1.zValue() == -0.11 - view.scene.Z_STEP
    assert item2.zValue() == -0.07 - view.scene.Z_STEP
    assert item3.zValue() == -0.07
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_normalize_height(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setScale(3)
    view.scene.cancel_crop_mode = MagicMock()

    with patch.object(item1, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 80)):
        with patch.object(item2, 'bounding_rect_unselected',
                          return_value=QtCore.QRectF(0, 0, 100, 80)):
            view.scene.normalize_height()

    assert item1.scale() == 2
    assert item1.pos() == QtCore.QPointF(-50, -40)
    assert item2.scale() == 2
    assert item2.pos() == QtCore.QPointF(50, 40)
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_normalize_height_with_rotation(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setRotation(90)
    view.scene.cancel_crop_mode = MagicMock()

    with patch.object(item1, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 200)):
        with patch.object(item2, 'bounding_rect_unselected',
                          return_value=QtCore.QRectF(0, 0, 100, 200)):
            view.scene.normalize_height()

    assert item1.scale() == 0.75
    assert item2.scale() == 1.5
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_normalize_height_when_no_items(view):
    view.scene.cancel_crop_mode = MagicMock()
    view.scene.normalize_height()
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_normalize_width(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setScale(3)
    view.scene.cancel_crop_mode = MagicMock()

    with patch.object(item1, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 80, 100)):
        with patch.object(item2, 'bounding_rect_unselected',
                          return_value=QtCore.QRectF(0, 0, 80, 100)):
            view.scene.normalize_width()

    assert item1.scale() == 2
    assert item1.pos() == QtCore.QPointF(-40, -50)
    assert item2.scale() == 2
    assert item2.pos() == QtCore.QPointF(40, 50)
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_normalize_width_with_rotation(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setRotation(90)
    view.scene.cancel_crop_mode = MagicMock()

    with patch.object(item1, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 200, 100)):
        with patch.object(item2, 'bounding_rect_unselected',
                          return_value=QtCore.QRectF(0, 0, 200, 100)):
            view.scene.normalize_height()

    assert item1.scale() == 1.5
    assert item2.scale() == 0.75
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_normalize_width_when_no_items(view):
    view.scene.cancel_crop_mode = MagicMock()
    view.scene.normalize_width()
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_normalize_size(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setScale(2)
    view.scene.cancel_crop_mode = MagicMock()

    with patch.object(item1, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 100)):
        with patch.object(item2, 'bounding_rect_unselected',
                          return_value=QtCore.QRectF(0, 0, 100, 100)):
            view.scene.normalize_size()

    assert item1.scale() == approx(math.sqrt(2.5))
    assert item2.scale() == approx(math.sqrt(2.5))
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_normalize_size_with_rotation(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setRotation(90)
    view.scene.cancel_crop_mode = MagicMock()

    with patch.object(item1, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 200)):
        with patch.object(item2, 'bounding_rect_unselected',
                          return_value=QtCore.QRectF(0, 0, 100, 200)):
            view.scene.normalize_size()

    assert item1.scale() == 1
    assert item2.scale() == 1
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_normalize_size_when_no_items(view):
    view.scene.cancel_crop_mode = MagicMock()
    view.scene.normalize_size()
    view.scene.cancel_crop_mode.assert_called_once_with()


@pytest.mark.parametrize('value,expected_func,expected_kwargs',
                         [('optimal', 'arrange_optimal', {}),
                          ('horizontal', 'arrange', {}),
                          ('vertical', 'arrange', {'vertical': True}),
                          ('square', 'arrange_square', {})])
def test_arrange_default(
        value, expected_func, expected_kwargs, settings, view):
    settings.setValue('Items/arrange_default', value)
    setattr(view.scene, expected_func, MagicMock())
    view.scene.arrange_default()
    getattr(view.scene, expected_func).assert_called_once_with(
        **expected_kwargs)


def test_arrange_horizontal(view):
    item1 = BeePixmapItem(QtGui.QImage())
    item1.filename = 'foo.png'
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.setPos(10, -100)
    item1.crop = QtCore.QRectF(0, 0, 100, 80)

    item2 = BeePixmapItem(QtGui.QImage())
    item2.filename = 'bar.png'
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setPos(-10, 40)
    item2.crop = QtCore.QRectF(0, 0, 100, 80)

    view.scene.cancel_crop_mode = MagicMock()
    view.scene.arrange()

    assert item2.pos() == QtCore.QPointF(-50, -30)
    assert item1.pos() == QtCore.QPointF(50, -30)
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_arrange_horizontal_with_gap(view, settings):
    settings.setValue('Items/arrange_gap', 6)

    item1 = BeePixmapItem(QtGui.QImage())
    item1.filename = 'foo.png'
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.setPos(10, -100)
    item1.crop = QtCore.QRectF(0, 0, 100, 80)

    item2 = BeePixmapItem(QtGui.QImage())
    item2.filename = 'bar.png'
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setPos(-10, 40)
    item2.crop = QtCore.QRectF(0, 0, 100, 80)

    view.scene.cancel_crop_mode = MagicMock()
    view.scene.arrange()

    assert item2.pos() == QtCore.QPointF(-50, -30)
    assert item1.pos() == QtCore.QPointF(56, -30)
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_arrange_vertical(view):
    item1 = BeePixmapItem(QtGui.QImage())
    item1.filename = 'foo.png'
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.setPos(10, -100)
    item1.crop = QtCore.QRectF(0, 0, 100, 80)

    item2 = BeePixmapItem(QtGui.QImage())
    item2.filename = 'bar.png'
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setPos(-10, 40)
    item2.crop = QtCore.QRectF(0, 0, 100, 80)

    view.scene.cancel_crop_mode = MagicMock()
    view.scene.arrange(vertical=True)

    assert item1.pos() == QtCore.QPointF(0, -70)
    assert item2.pos() == QtCore.QPointF(0, 10)
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_arrange_vertical_with_gap(view, settings):
    settings.setValue('Items/arrange_gap', 6)

    item1 = BeePixmapItem(QtGui.QImage())
    item1.filename = 'foo.png'
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.setPos(10, -100)
    item1.crop = QtCore.QRectF(0, 0, 100, 80)

    item2 = BeePixmapItem(QtGui.QImage())
    item2.filename = 'bar.png'
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setPos(-10, 40)
    item2.crop = QtCore.QRectF(0, 0, 100, 80)

    view.scene.cancel_crop_mode = MagicMock()
    view.scene.arrange(vertical=True)

    assert item1.pos() == QtCore.QPointF(0, -70)
    assert item2.pos() == QtCore.QPointF(0, 16)
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_arrange_when_rotated(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.setPos(10, -100)
    item1.setRotation(90)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setPos(-10, 40)
    item2.setRotation(90)
    view.scene.cancel_crop_mode = MagicMock()

    with patch.object(item1, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 80)):
        with patch.object(item2, 'bounding_rect_unselected',
                          return_value=QtCore.QRectF(0, 0, 100, 80)):
            view.scene.arrange()

    assert item2.pos() == QtCore.QPointF(-40, -30)
    assert item1.pos() == QtCore.QPointF(40, -30)
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_arrange_when_no_items(view):
    view.scene.cancel_crop_mode = MagicMock()
    view.scene.arrange()
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_arrange_optimal(view):
    for i in range(4):
        item = BeePixmapItem(QtGui.QImage())
        view.scene.addItem(item)
        item.setSelected(True)
        item.crop = QtCore.QRectF(0, 0, 100, 80)

    view.scene.cancel_crop_mode = MagicMock()
    view.scene.arrange_optimal()
    expected_positions = {(-50, -40), (50, -40), (-50, 40), (50, 40)}
    actual_positions = {
        (i.pos().x(), i.pos().y())
        for i in view.scene.selectedItems(user_only=True)}
    assert expected_positions == actual_positions
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_arrange_optimal_with_gap(view, settings):
    settings.setValue('Items/arrange_gap', 6)
    for i in range(4):
        item = BeePixmapItem(QtGui.QImage())
        view.scene.addItem(item)
        item.setSelected(True)
        item.crop = QtCore.QRectF(0, 0, 100, 80)

    view.scene.cancel_crop_mode = MagicMock()
    view.scene.arrange_optimal()
    expected_positions = {(-56, -46), (50, -46), (-56, 40), (50, 40)}
    actual_positions = {
        (i.pos().x(), i.pos().y())
        for i in view.scene.selectedItems(user_only=True)}
    assert expected_positions == actual_positions
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_arrange_optimal_when_rotated(view):
    for i in range(4):
        item = BeePixmapItem(QtGui.QImage())
        view.scene.addItem(item)
        item.setRotation(90)
        item.setSelected(True)
        item.crop = QtCore.QRectF(0, 0, 100, 80)

    view.scene.cancel_crop_mode = MagicMock()
    view.scene.arrange_optimal()

    expected_positions = {(-40, -50), (40, -50), (-40, 50), (40, 50)}
    actual_positions = {
        (i.pos().x(), i.pos().y())
        for i in view.scene.selectedItems(user_only=True)}
    assert expected_positions == actual_positions
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_arrange_optimal_when_no_items(view):
    view.scene.cancel_crop_mode = MagicMock()
    view.scene.arrange_optimal()
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_arrange_square(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.crop = QtCore.QRectF(0, 0, 100, 80)

    item2 = BeePixmapItem(QtGui.QImage())
    item2.filename = 'foo.png'
    item2.save_id = 66
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.crop = QtCore.QRectF(0, 0, 80, 60)

    item3 = BeePixmapItem(QtGui.QImage())
    item3.save_id = 33
    view.scene.addItem(item3)
    item3.setSelected(True)
    item3.crop = QtCore.QRectF(0, 0, 100, 80)

    item4 = BeePixmapItem(QtGui.QImage())
    item4.filename = 'bar.png'
    item4.save_id = 77
    view.scene.addItem(item4)
    item4.setSelected(True)
    item4.crop = QtCore.QRectF(0, 0, 100, 80)

    view.scene.cancel_crop_mode = MagicMock()
    view.scene.arrange_square()

    assert item4.pos() == QtCore.QPointF(-50, -40)
    assert item2.pos() == QtCore.QPointF(60, -30)
    assert item3.pos() == QtCore.QPointF(-50, 40)
    assert item1.pos() == QtCore.QPointF(50, 40)
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_arrange_square_with_gap(view, settings):
    settings.setValue('Items/arrange_gap', 6)
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.crop = QtCore.QRectF(0, 0, 100, 80)

    item2 = BeePixmapItem(QtGui.QImage())
    item2.filename = 'foo.png'
    item2.save_id = 66
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.crop = QtCore.QRectF(0, 0, 80, 60)

    item3 = BeePixmapItem(QtGui.QImage())
    item3.save_id = 33
    view.scene.addItem(item3)
    item3.setSelected(True)
    item3.crop = QtCore.QRectF(0, 0, 100, 80)

    item4 = BeePixmapItem(QtGui.QImage())
    item4.filename = 'bar.png'
    item4.save_id = 77
    view.scene.addItem(item4)
    item4.setSelected(True)
    item4.crop = QtCore.QRectF(0, 0, 100, 80)

    view.scene.cancel_crop_mode = MagicMock()
    view.scene.arrange_square()

    assert item4.pos() == QtCore.QPointF(-53, -43)
    assert item2.pos() == QtCore.QPointF(63, -33)
    assert item3.pos() == QtCore.QPointF(-53, 43)
    assert item1.pos() == QtCore.QPointF(53, 43)
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_arrange_square_when_no_items(view):
    view.scene.cancel_crop_mode = MagicMock()
    view.scene.arrange_square()
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_flip_items(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    view.scene.undo_stack = MagicMock(push=MagicMock())
    view.scene.cancel_crop_mode = MagicMock()
    with patch('beeref.scene.BeeGraphicsScene.itemsBoundingRect',
               return_value=QtCore.QRectF(10, 20, 100, 60)):
        view.scene.flip_items(vertical=True)
        args = view.scene.undo_stack.push.call_args_list[0][0]
        cmd = args[0]
        assert isinstance(cmd, commands.FlipItems)
        assert cmd.items == [item]
        assert cmd.anchor == QtCore.QPointF(60, 50)
        assert cmd.vertical is True
        view.scene.cancel_crop_mode.assert_called_once_with()


def test_crop_items(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    item.enter_crop_mode = MagicMock()

    view.scene.crop_items()
    item.enter_crop_mode.assert_called_once_with()


def test_crop_items_when_in_crop_mode(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    item.enter_crop_mode = MagicMock()
    view.scene.crop_item = item

    view.scene.crop_items()
    item.enter_crop_mode.assert_not_called()


def test_crop_item_multi_select(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    item.enter_crop_mode = MagicMock()
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)

    view.scene.crop_items()
    item.enter_crop_mode.assert_not_called()


def test_crop_item_no_selection(view, item):
    view.scene.addItem(item)
    item.setSelected(False)
    item.enter_crop_mode = MagicMock()

    view.scene.crop_items()
    item.enter_crop_mode.assert_not_called()


def test_crop_item_when_not_image(view):
    item = BeeTextItem('foo')
    item.setSelected(True)
    item.enter_crop_mode = MagicMock()

    view.scene.crop_items()
    item.enter_crop_mode.assert_not_called()


def test_sample_color_at_when_pixmap_item(view):
    color = QtGui.QColor(255, 0, 0, 3)
    img = QtGui.QImage(10, 10, QtGui.QImage.Format.Format_ARGB32)
    img.fill(color)
    item = BeePixmapItem(img, 'foo.png')
    view.scene.addItem(item)
    assert view.scene.sample_color_at(QtCore.QPointF(2, 2)) == color


def test_sample_color_at_when_text_item(view):
    item = BeeTextItem('foo bar baz')
    view.scene.addItem(item)
    assert view.scene.sample_color_at(QtCore.QPointF(2, 2)) is None


def test_sample_color_at_when_no_item(view):
    assert view.scene.sample_color_at(QtCore.QPointF(2, 2)) is None


def test_select_all_items_when_true(view):
    item1 = BeeTextItem('foo')
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeeTextItem('bar')
    view.scene.addItem(item2)
    item2.setSelected(True)
    view.scene.cancel_crop_mode = MagicMock()

    view.scene.select_all_items()
    assert item1.isSelected() is True
    assert item2.isSelected() is True
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_deselect_all_items_when_false(view):
    item1 = BeeTextItem('foo')
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeeTextItem('bar')
    view.scene.addItem(item2)
    item2.setSelected(True)
    view.scene.cancel_crop_mode = MagicMock()

    view.scene.deselect_all_items()
    assert item1.isSelected() is False
    assert item2.isSelected() is False
    view.scene.cancel_crop_mode.assert_called_once_with()


def test_has_selection_when_no_selection(view, item):
    view.scene.addItem(item)
    assert view.scene.has_selection() is False


def test_has_selection_when_selection(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    assert view.scene.has_selection() is True


def test_has_single_selection_when_no_selection(view, item):
    view.scene.addItem(item)
    assert view.scene.has_single_selection() is False


def test_has_single_selection_when_single_selection(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    assert view.scene.has_single_selection() is True


def test_has_single_selection_when_multi_selection(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    assert view.scene.has_single_selection() is False


def test_has_multi_selection_when_no_selection(view, item):
    view.scene.addItem(item)
    assert view.scene.has_multi_selection() is False


def test_has_multi_selection_when_single_selection(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    assert view.scene.has_multi_selection() is False


def test_has_multi_selection_when_multi_selection(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    assert view.scene.has_multi_selection() is True


def test_has_single_image_selection(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    assert view.scene.has_single_image_selection() is True


def test_has_single_image_selection_when_item_not_image(view):
    item = BeeTextItem('foo')
    view.scene.addItem(item)
    item.setSelected(True)
    assert view.scene.has_single_image_selection() is False


def test_has_single_image_selection_when_no_selection(view, item):
    view.scene.addItem(item)
    item.setSelected(False)
    assert view.scene.has_single_image_selection() is False


def test_has_single_image_selection_when_multi_selection(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    assert view.scene.has_single_image_selection() is False


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
def test_mouse_press_event_when_right_click(mouse_mock, view):
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.RightButton))
    view.scene.mousePressEvent(event)
    event.accept.assert_not_called()
    mouse_mock.assert_not_called()


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
def test_mouse_press_event_when_left_click_over_item(mouse_mock, view, item):
    view.scene.itemAt = MagicMock(return_value=item)
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
        scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)),
    )
    view.scene.mousePressEvent(event)
    event.accept.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    assert view.scene.active_mode == view.scene.MOVE_MODE
    assert view.scene.event_start == QtCore.QPointF(10, 20)


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
def test_mouse_press_event_when_left_click_over_item_in_edit_mode(
        mouse_mock, view):
    item = BeeTextItem('foo bar')
    item.exit_edit_mode = MagicMock()
    view.scene.addItem(item)
    view.scene.edit_item = item
    view.scene.itemAt = MagicMock(return_value=item)
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
    )
    view.scene.mousePressEvent(event)
    event.accept.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    item.exit_edit_mode.assert_not_called()
    assert view.scene.active_mode is None


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
def test_mouse_press_event_when_left_click_over_diff_item_in_edit_mode(
        mouse_mock, view, item):
    txtitem = BeeTextItem('foo bar')
    txtitem.exit_edit_mode = MagicMock()
    view.scene.addItem(txtitem)
    view.scene.edit_item = txtitem
    view.scene.itemAt = MagicMock(return_value=item)
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
    )
    view.scene.mousePressEvent(event)
    event.accept.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    txtitem.exit_edit_mode.assert_called_once_with()
    assert view.scene.active_mode == view.scene.MOVE_MODE


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
def test_mouse_press_event_when_left_click_over_no_item_in_edit_mode(
        mouse_mock, view):
    item = BeeTextItem('foo bar')
    item.exit_edit_mode = MagicMock()
    view.scene.addItem(item)
    view.scene.edit_item = item
    view.scene.itemAt = MagicMock(return_value=None)
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
    )
    view.scene.mousePressEvent(event)
    event.accept.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    item.exit_edit_mode.assert_called_once_with()
    assert view.scene.active_mode == view.scene.RUBBERBAND_MODE


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
def test_mouse_press_event_when_left_click_over_item_in_crop_mode(
        mouse_mock, view, item):
    view.scene.addItem(item)
    view.scene.cancel_crop_mode = MagicMock()
    view.scene.crop_item = item
    view.scene.itemAt = MagicMock(return_value=item)
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
    )
    view.scene.mousePressEvent(event)
    event.accept.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    view.scene.cancel_crop_mode.assert_not_called()
    assert view.scene.active_mode is None


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
def test_mouse_press_event_when_left_click_over_diff_item_in_crop_mode(
        mouse_mock, view, item):
    view.scene.addItem(item)
    view.scene.cancel_crop_mode = MagicMock()
    view.scene.crop_item = item
    other_item = BeePixmapItem(QtGui.QImage())
    view.scene.itemAt = MagicMock(return_value=other_item)
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
    )
    view.scene.mousePressEvent(event)
    event.accept.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    view.scene.cancel_crop_mode.assert_called_once_with()
    assert view.scene.active_mode is view.scene.MOVE_MODE


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
def test_mouse_press_event_when_left_click_over_no_item_in_crop_mode(
        mouse_mock, view, item):
    view.scene.addItem(item)
    view.scene.cancel_crop_mode = MagicMock()
    view.scene.crop_item = item
    view.scene.itemAt = MagicMock(return_value=None)
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
    )
    view.scene.mousePressEvent(event)
    event.accept.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    view.scene.cancel_crop_mode.assert_called_once_with()
    assert view.scene.active_mode == view.scene.RUBBERBAND_MODE


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
def test_mouse_press_event_when_left_click_not_over_item(
        mouse_mock, view, item):
    view.scene.addItem(item)
    view.scene.itemAt = MagicMock(return_value=None)
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
        scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)),
    )
    view.scene.mousePressEvent(event)
    event.accept.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    assert view.scene.active_mode == view.scene.RUBBERBAND_MODE
    assert view.scene.event_start == QtCore.QPointF(10, 20)


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
def test_mouse_press_event_when_no_items(mouse_mock, view):
    view.scene.itemAt = MagicMock(return_value=None)
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
        scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)),
    )
    view.scene.mousePressEvent(event)
    event.accept.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    assert view.scene.active_mode is None
    mouse_mock.assert_called_once_with(event)


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseDoubleClickEvent')
def test_mouse_doubleclick_event_when_over_item(mouse_mock, view, item):
    event = MagicMock()
    view.scene.active_mode = view.scene.MOVE_MODE
    view.scene.addItem(item)
    item.setPos(30, 40)
    item.setSelected(True)
    view.scene.itemAt = MagicMock(return_value=item)
    view.fit_rect = MagicMock()

    with patch.object(item, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 100)):
        view.scene.mouseDoubleClickEvent(event)

    assert view.scene.active_mode is None
    view.fit_rect.assert_called_once_with(
        QtCore.QRectF(30, 40, 100, 100), toggle_item=item)
    mouse_mock.assert_not_called()


@patch('PyQt6.QtWidgets.QGraphicsScene.mousePressEvent')
@patch('PyQt6.QtWidgets.QGraphicsScene.mouseDoubleClickEvent')
def test_mouse_doubleclick_event_when_over_editable_item(
        double_mock, press_mock, view):
    item = BeeTextItem('foo bar')
    item.enter_edit_mode = MagicMock()
    event = MagicMock()
    view.scene.active_mode = view.scene.MOVE_MODE
    view.scene.addItem(item)
    item.setPos(30, 40)
    item.setSelected(True)
    view.scene.itemAt = MagicMock(return_value=item)
    view.fit_rect = MagicMock()

    with patch.object(item, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 100)):
        view.scene.mouseDoubleClickEvent(event)

    assert view.scene.active_mode is None
    item.enter_edit_mode.assert_called_once_with()
    double_mock.assert_not_called()
    press_mock.assert_called_once_with(event)


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseDoubleClickEvent')
def test_mouse_doubleclick_event_when_item_not_selected(
        mouse_mock, view, item):
    event = MagicMock()
    view.scene.active_mode = view.scene.MOVE_MODE
    view.scene.addItem(item)
    item.setPos(30, 40)
    item.setSelected(False)
    view.scene.itemAt = MagicMock(return_value=item)
    view.fit_rect = MagicMock()

    with patch.object(item, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 100)):
        view.scene.mouseDoubleClickEvent(event)

    assert view.scene.active_mode is None
    view.fit_rect.assert_called_once_with(
        QtCore.QRectF(30, 40, 100, 100), toggle_item=item)
    mouse_mock.assert_not_called()
    assert item.isSelected() is True


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseDoubleClickEvent')
def test_mouse_doubleclick_event_when_not_over_item(mouse_mock, view):
    event = MagicMock()
    view.fit_rect = MagicMock()
    view.scene.itemAt = MagicMock(return_value=None)
    view.scene.mouseDoubleClickEvent(event)
    view.fit_rect.assert_not_called()
    mouse_mock.assert_called_once_with(event)


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseMoveEvent')
def test_mouse_move_event_when_rubberband_new(
        mouse_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.scene.active_mode = view.scene.RUBBERBAND_MODE
    view.scene.addItem = MagicMock()
    view.scene.event_start = QtCore.QPointF(0, 0)
    view.scene.rubberband_item.bring_to_front = MagicMock()
    assert view.scene.rubberband_item.scene() is None
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)))

    view.scene.mouseMoveEvent(event)

    view.scene.addItem.assert_called_once_with(view.scene.rubberband_item)
    view.scene.rubberband_item.bring_to_front.assert_called_once()
    view.scene.rubberband_item.rect().topLeft().x() == 0
    view.scene.rubberband_item.rect().topLeft().y() == 0
    view.scene.rubberband_item.rect().bottomRight().x() == 10
    view.scene.rubberband_item.rect().bottomRight().y() == 20
    assert item.isSelected() is True
    mouse_mock.assert_called_once_with(event)


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseMoveEvent')
def test_mouse_move_event_when_rubberband_not_new(
        mouse_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.scene.active_mode = view.scene.RUBBERBAND_MODE
    view.scene.event_start = QtCore.QPointF(0, 0)
    view.scene.rubberband_item.bring_to_front = MagicMock()
    view.scene.addItem(view.scene.rubberband_item)
    view.scene.addItem = MagicMock()
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)))

    view.scene.mouseMoveEvent(event)

    view.scene.addItem.assert_not_called()
    view.scene.rubberband_item.bring_to_front.assert_not_called()
    view.scene.rubberband_item.rect().topLeft().x() == 0
    view.scene.rubberband_item.rect().topLeft().y() == 0
    view.scene.rubberband_item.rect().bottomRight().x() == 10
    view.scene.rubberband_item.rect().bottomRight().y() == 20
    assert item.isSelected() is True
    mouse_mock.assert_called_once_with(event)


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseMoveEvent')
def test_mouse_move_event_when_no_rubberband(mouse_mock, view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    view.scene.active_mode = None
    view.scene.event_start = QtCore.QPointF(0, 0)
    view.scene.rubberband_item.bring_to_front = MagicMock()
    view.scene.addItem = MagicMock()
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPointF(10, 20)))

    view.scene.mouseMoveEvent(event)

    view.scene.addItem.assert_not_called()
    view.scene.rubberband_item.bring_to_front.assert_not_called()
    view.scene.rubberband_item.rect().topLeft().x() == 0
    view.scene.rubberband_item.rect().topLeft().y() == 0
    view.scene.rubberband_item.rect().bottomRight().x() == 0
    view.scene.rubberband_item.rect().bottomRight().y() == 0
    assert item.isSelected() is False
    mouse_mock.assert_called_once_with(event)


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
def test_mouse_release_event_when_rubberband_active(mouse_mock, view):
    event = MagicMock()
    view.scene.active_mode = view.scene.RUBBERBAND_MODE
    view.scene.addItem(view.scene.rubberband_item)
    view.scene.removeItem = MagicMock()

    view.scene.mouseReleaseEvent(event)
    view.scene.removeItem.assert_called_once_with(view.scene.rubberband_item)
    view.scene.active_mode is None


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
def test_mouse_release_event_when_move_active(mouse_mock, view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPoint(10, 20)))
    view.scene.active_mode = view.scene.MOVE_MODE
    view.scene.event_start = QtCore.QPoint(0, 0)
    view.scene.undo_stack = MagicMock(push=MagicMock())

    view.scene.mouseReleaseEvent(event)
    view.scene.undo_stack.push.assert_called_once()
    args = view.scene.undo_stack.push.call_args_list[0][0]
    cmd = args[0]
    assert isinstance(cmd, commands.MoveItemsBy)
    assert cmd.items == [item]
    assert cmd.ignore_first_redo is True
    assert cmd.delta.x() == 10
    assert cmd.delta.y() == 20
    mouse_mock.assert_called_once_with(event)
    assert view.scene.active_mode is None


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
def test_mouse_release_event_when_move_not_active(mouse_mock, view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPoint(10, 20)))
    view.scene.active_mode = None
    view.scene.undo_stack = MagicMock(push=MagicMock())

    view.scene.mouseReleaseEvent(event)
    view.scene.undo_stack.push.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    assert view.scene.active_mode is None


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
def test_mouse_release_event_when_no_selection(mouse_mock, view, item):
    view.scene.addItem(item)
    item.setSelected(False)
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPoint(10, 20)))
    view.scene.active_mode = view.scene.MOVE_MODE
    view.scene.undo_stack = MagicMock(push=MagicMock())

    view.scene.mouseReleaseEvent(event)
    view.scene.undo_stack.push.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    assert view.scene.active_mode is None


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
def test_mouse_release_event_when_item_action_active(mouse_mock, view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPoint(10, 20)))
    item.active_mode = item.SCALE_MODE
    view.scene.active_mode = view.scene.MOVE_MODE
    view.scene.undo_stack = MagicMock(push=MagicMock())

    view.scene.mouseReleaseEvent(event)
    view.scene.undo_stack.push.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    assert view.scene.active_mode is None


@patch('PyQt6.QtWidgets.QGraphicsScene.mouseReleaseEvent')
def test_mouse_release_event_when_multiselect_action_active(mouse_mock, view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    event = MagicMock(scenePos=MagicMock(return_value=QtCore.QPoint(10, 20)))
    view.scene.active_mode = view.scene.MOVE_MODE
    view.scene.multi_select_item.active_mode = BeePixmapItem.SCALE_MODE
    view.scene.undo_stack = MagicMock(push=MagicMock())

    view.scene.mouseReleaseEvent(event)
    view.scene.undo_stack.push.assert_not_called()
    mouse_mock.assert_called_once_with(event)
    assert view.scene.active_mode is None


def test_selected_items(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    selected = view.scene.selectedItems()
    assert len(selected) == 3  # Multi select item!
    assert item1 in selected
    assert item2 in selected


def test_selected_items_user_only(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    selected = view.scene.selectedItems(user_only=True)
    assert len(selected) == 2  # No multi select item!
    assert item1 in selected
    assert item2 in selected


def test_items_by_tpe(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item2 = BeeTextItem('foo')
    view.scene.addItem(item2)
    assert list(view.scene.items_by_type('text')) == [item2]


def test_items_for_save(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item3 = QtWidgets.QGraphicsRectItem()
    view.scene.addItem(item3)

    items = list(view.scene.items_for_save())
    assert items == [item1, item2]


def test_clear_save_ids(view):
    item1 = BeePixmapItem(QtGui.QImage())
    item1.save_id = 5
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item3 = QtWidgets.QGraphicsRectItem()
    view.scene.addItem(item3)

    view.scene.clear_save_ids()
    assert item1.save_id is None
    assert item2.save_id is None
    assert hasattr(item3, 'save_id') is False


def test_on_view_scale_change(view, item):
    view.scene.addItem(item)
    item.setSelected(True)
    item.on_view_scale_change = MagicMock()
    view.scene.on_view_scale_change()
    item.on_view_scale_change.assert_called_once()


def test_items_bounding_rect_given_items(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.setPos(4, -6)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setPos(-33, 22)
    item3 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item3)
    item3.setSelected(True)
    item3.setPos(1000, 1000)

    with patch.object(item1, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 100)):
        with patch.object(item2, 'bounding_rect_unselected',
                          return_value=QtCore.QRectF(0, 0, 100, 100)):
            rect = view.scene.itemsBoundingRect(items=[item1, item2])

    assert rect.topLeft().x() == -33
    assert rect.topLeft().y() == -6
    assert rect.bottomRight().x() == 104
    assert rect.bottomRight().y() == 122


def test_items_bounding_rect_two_items_selection_only(view):
    item1 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item1)
    item1.setSelected(True)
    item1.setPos(4, -6)
    item2 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item2)
    item2.setSelected(True)
    item2.setPos(-33, 22)
    item3 = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item3)
    item3.setSelected(False)
    item3.setPos(1000, 1000)

    with patch.object(item1, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 100)):
        with patch.object(item2, 'bounding_rect_unselected',
                          return_value=QtCore.QRectF(0, 0, 100, 100)):
            rect = view.scene.itemsBoundingRect(selection_only=True)

    assert rect.topLeft().x() == -33
    assert rect.topLeft().y() == -6
    assert rect.bottomRight().x() == 104
    assert rect.bottomRight().y() == 122


def test_items_bounding_rect_rotated_item(view, item):
    view.scene.addItem(item)
    item.setRotation(-45)

    with patch.object(item, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 100, 100)):
        rect = view.scene.itemsBoundingRect()

    assert rect.topLeft().x() == 0
    assert rect.topLeft().y() == approx(-math.sqrt(2) * 50)
    assert rect.bottomRight().x() == approx(math.sqrt(2) * 100)
    assert rect.bottomRight().y() == approx(math.sqrt(2) * 50)


def test_items_bounding_rect_flipped_item(view):
    item = BeePixmapItem(QtGui.QImage())
    view.scene.addItem(item)
    item.do_flip()
    with patch.object(item, 'bounding_rect_unselected',
                      return_value=QtCore.QRectF(0, 0, 50, 100)):
        rect = view.scene.itemsBoundingRect()

    assert rect.topLeft().x() == -50
    assert rect.topLeft().y() == 0
    assert rect.bottomRight().x() == 0
    assert rect.bottomRight().y() == 100


def test_items_bounding_rect_when_no_items(view):
    rect = view.scene.itemsBoundingRect()
    assert rect == QtCore.QRectF(0, 0, 0, 0)


def test_get_selection_center(view):
    with patch('beeref.scene.BeeGraphicsScene.itemsBoundingRect',
               return_value=QtCore.QRectF(10, 20, 100, 60)):
        center = view.scene.get_selection_center()
        assert center == QtCore.QPointF(60, 50)


def test_on_selection_change_when_multi_selection_new(view):
    view.scene.has_multi_selection = MagicMock(return_value=True)
    view.scene.multi_select_item.fit_selection_area = MagicMock()
    view.scene.multi_select_item.bring_to_front = MagicMock()
    view.scene.itemsBoundingRect = MagicMock(
        return_value=QtCore.QRectF(0, 0, 100, 80))
    view.scene.addItem = MagicMock()

    view.scene.on_selection_change()

    m_item = view.scene.multi_select_item
    m_item.fit_selection_area.assert_called_once_with(
        QtCore.QRectF(0, 0, 100, 80))
    m_item.bring_to_front.assert_called_once()
    view.scene.addItem.assert_called_once_with(m_item)


def test_on_selection_change_when_multi_selection_existing(view):
    view.scene.addItem(view.scene.multi_select_item)
    view.scene.has_multi_selection = MagicMock(return_value=True)
    view.scene.multi_select_item.fit_selection_area = MagicMock()
    view.scene.multi_select_item.bring_to_front = MagicMock()
    view.scene.itemsBoundingRect = MagicMock(
        return_value=QtCore.QRectF(0, 0, 100, 80))
    view.scene.addItem = MagicMock()

    view.scene.on_selection_change()

    m_item = view.scene.multi_select_item
    m_item.fit_selection_area.assert_called_once_with(
        QtCore.QRectF(0, 0, 100, 80))
    m_item.bring_to_front.assert_not_called()
    view.scene.addItem.assert_not_called()


def test_on_selection_change_when_multi_selection_ended(view):
    view.scene.addItem(view.scene.multi_select_item)
    view.scene.has_multi_selection = MagicMock(return_value=False)
    view.scene.multi_select_item.fit_selection_area = MagicMock()
    view.scene.multi_select_item.bring_to_front = MagicMock()
    view.scene.itemsBoundingRect = MagicMock(
        return_value=QtCore.QRectF(0, 0, 100, 80))
    view.scene.removeItem = MagicMock()

    view.scene.on_selection_change()

    m_item = view.scene.multi_select_item
    m_item.fit_selection_area.assert_not_called()
    view.scene.removeItem.assert_called_once_with(m_item)


def test_on_change_when_multi_select_when_no_scale_no_rotate(view):
    view.scene.addItem(view.scene.multi_select_item)
    view.scene.multi_select_item.fit_selection_area = MagicMock()
    view.scene.multi_select_item.active_mode = None
    view.scene.on_change(None)
    view.scene.multi_select_item.fit_selection_area.assert_called_once()


def test_on_change_when_multi_select_when_scale_active(view):
    view.scene.addItem(view.scene.multi_select_item)
    view.scene.multi_select_item.fit_selection_area = MagicMock()
    view.scene.multi_select_item.active_mode = BeePixmapItem.SCALE_MODE
    view.scene.on_change(None)
    view.scene.multi_select_item.fit_selection_area.assert_not_called()


def test_on_change_when_multi_select_when_rotate_active(view):
    view.scene.addItem(view.scene.multi_select_item)
    view.scene.multi_select_item.fit_selection_area = MagicMock()
    view.scene.multi_select_item.active_mode = BeePixmapItem.ROTATE_MODE
    view.scene.on_change(None)
    view.scene.multi_select_item.fit_selection_area.assert_not_called()


def test_on_change_when_no_multi_select(view):
    view.scene.multi_select_item.fit_selection_area = MagicMock()
    view.scene.multi_select_item.active_mode = BeePixmapItem.SCALE_MODE
    view.scene.on_change(None)
    view.scene.multi_select_item.fit_selection_area.assert_not_called()


def test_add_queued_items_unselected(view):
    data = {'type': 'text', 'z': 0.33, 'data': {'text': 'foo'}}
    view.scene.add_item_later(data, selected=False)
    view.scene.add_queued_items()
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.isSelected() is False
    assert view.scene.max_z == 0.33
    assert item.toPlainText() == 'foo'


def test_add_queued_items_selected(view):
    view.scene.max_z = 0.6
    data = {'type': 'text', 'z': 0.33, 'data': {'text': 'foo'}}
    view.scene.add_item_later(data, selected=True)
    view.scene.add_queued_items()
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.isSelected() is True
    assert item.zValue() > 0.6


def test_add_queued_items_when_no_items(view):
    view.scene.add_queued_items()
    assert view.scene.items() == []


def test_add_queued_items_ignores_unknown_type(view):
    data = {'type': 'foo', 'z': 0.33, 'data': {'bar': 'baz'}}
    view.scene.add_item_later(data, selected=False)
    view.scene.add_queued_items()
    assert len(view.scene.items()) == 1
    item = view.scene.items()[0]
    assert item.toPlainText() == 'Item of unknown type: foo'
