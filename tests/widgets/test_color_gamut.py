from unittest.mock import MagicMock

from PyQt6 import QtGui

from beeref.items import BeePixmapItem
from beeref.widgets.color_gamut import (
    GamutDialog,
    GamutPainterThread,
    GamutWidget,
)


def test_gamut_painter_thread_generates_image(view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    dialog = GamutDialog(view, item)
    dialog.threshold_input.setValue(0)
    widget = GamutWidget(dialog, item)
    worker = GamutPainterThread(widget, item)
    mock = MagicMock()
    worker.finished.connect(mock)
    worker.run()

    mock.assert_called_once()
    image = mock.call_args[0][0]
    assert image.size().width() == 500
    assert image.size().height() == 500
    assert image.allGray() is False


def test_gamut_painter_thread_generates_image_below_threshold(
        view, imgfilename3x3):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    dialog = GamutDialog(view, item)
    dialog.threshold_input.setValue(20)
    widget = GamutWidget(dialog, item)
    worker = GamutPainterThread(widget, item)
    mock = MagicMock()
    worker.finished.connect(mock)
    worker.run()

    mock.assert_called_once()
    image = mock.call_args[0][0]
    assert image.size().width() == 500
    assert image.size().height() == 500
    assert image.allGray() is True


def test_gamut_widget_generates_image(view, imgfilename3x3, qtbot):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    dialog = GamutDialog(view, item)
    dialog.threshold_input.setValue(0)
    widget = GamutWidget(dialog, item)
    assert widget.image is None
    widget.show()
    qtbot.waitUntil(lambda: widget.image is not None)
    assert widget.image.size().width() == 500
    assert widget.image.size().height() == 500
    assert widget.image.allGray() is False
