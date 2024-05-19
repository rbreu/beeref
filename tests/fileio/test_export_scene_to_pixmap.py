import os
import stat
from unittest.mock import patch, ANY, MagicMock
import pytest

from PyQt6 import QtGui, QtCore

from beeref import constants
from beeref.items import BeePixmapItem
from beeref.fileio.errors import BeeFileIOError
from beeref.fileio.export import SceneToPixmapExporter


@patch('beeref.widgets.SceneToPixmapExporterDialog.exec', return_value=True)
@patch('beeref.widgets.SceneToPixmapExporterDialog.value',
       return_value=QtCore.QSize(100, 200))
def test_scene_to_pixmap_exporter_get_user_input(value_mock, exec_mock, view):
    exporter = SceneToPixmapExporter(view.scene)
    value = exporter.get_user_input(None)
    assert value is True
    assert exporter.size == QtCore.QSize(100, 200)


@patch('beeref.widgets.SceneToPixmapExporterDialog.exec', return_value=False)
@patch('beeref.widgets.SceneToPixmapExporterDialog.value')
def test_scene_to_pixmap_exporter_get_user_input_when_canceled(
        value_mock, exec_mock, view):
    exporter = SceneToPixmapExporter(view.scene)
    value = exporter.get_user_input(None)
    assert value is False


def test_scene_to_pixmap_exporter_default_size_and_margin(view):
    item1 = BeePixmapItem(
        QtGui.QImage(100, 100, QtGui.QImage.Format.Format_RGB32))
    item1.setPos(QtCore.QPointF(0, 0))
    view.scene.addItem(item1)

    item2 = BeePixmapItem(
        QtGui.QImage(100, 100, QtGui.QImage.Format.Format_RGB32))
    item1.setPos(QtCore.QPointF(200, 0))
    view.scene.addItem(item2)

    exporter = SceneToPixmapExporter(view.scene)
    assert view.scene.sceneRect().size().toSize() == QtCore.QSize(300, 100)
    assert (exporter.margin - 9) < 0.000001
    assert exporter.default_size == QtCore.QSize(318, 118)


def test_scene_to_pixmap_exporter_default_size_and_margin_when_selection(view):
    item1 = BeePixmapItem(
        QtGui.QImage(100, 100, QtGui.QImage.Format.Format_RGB32))
    item1.setPos(QtCore.QPointF(0, 0))
    view.scene.addItem(item1)

    item2 = BeePixmapItem(
        QtGui.QImage(100, 100, QtGui.QImage.Format.Format_RGB32))
    item1.setPos(QtCore.QPointF(200, 0))
    view.scene.addItem(item2)
    item2.setSelected(True)

    exporter = SceneToPixmapExporter(view.scene)
    assert view.scene.sceneRect().size().toSize() == QtCore.QSize(300, 100)
    assert (exporter.margin - 9) < 0.000001
    assert exporter.default_size == QtCore.QSize(318, 118)


@patch('beeref.scene.BeeGraphicsScene.render')
def test_scene_to_pixmap_exporter_render_sets_margins(render_mock, view):
    item = BeePixmapItem(
        QtGui.QImage(1000, 1200, QtGui.QImage.Format.Format_RGB32))
    view.scene.addItem(item)
    exporter = SceneToPixmapExporter(view.scene)
    assert exporter.margin == 36
    assert exporter.default_size == QtCore.QSize(1072, 1272)

    exporter.size = QtCore.QSize(536, 636)
    exporter.render_to_image()

    render_mock.assert_called_once_with(
        ANY,
        source=QtCore.QRectF(0, 0, 1000, 1200),
        target=QtCore.QRectF(18, 18, 500, 600))


def test_scene_to_pixmap_exporter_render_renders_scene(view):
    item_img = QtGui.QImage(1000, 1200, QtGui.QImage.Format.Format_RGB32)
    item_img.fill(QtGui.QColor(11, 22, 33))
    item = BeePixmapItem(item_img)
    view.scene.addItem(item)
    exporter = SceneToPixmapExporter(view.scene)
    assert exporter.margin == 36
    assert exporter.default_size == QtCore.QSize(1072, 1272)

    exporter.size = QtCore.QSize(536, 636)
    image = exporter.render_to_image()
    assert image.pixel(1, 1) == QtGui.QColor(*constants.COLORS['Scene:Canvas'])
    assert image.pixel(100, 100) == QtGui.QColor(11, 22, 33)


def test_scene_to_pixmap_exporter_export_writes_image(view, tmpdir):
    filename = os.path.join(tmpdir, 'foo.png')
    item_img = QtGui.QImage(1000, 1200, QtGui.QImage.Format.Format_RGB32)
    item = BeePixmapItem(item_img)
    view.scene.addItem(item)
    exporter = SceneToPixmapExporter(view.scene)
    exporter.size = QtCore.QSize(100, 120)
    exporter.export(filename)

    with open(filename, 'rb') as f:
        assert f.read().startswith(b'\x89PNG')


def test_scene_to_pixmap_exporter_export_with_worker(view, tmpdir):
    filename = os.path.join(tmpdir, 'foo.png')
    item_img = QtGui.QImage(1000, 1200, QtGui.QImage.Format.Format_RGB32)
    item = BeePixmapItem(item_img)
    view.scene.addItem(item)
    exporter = SceneToPixmapExporter(view.scene)
    exporter.size = QtCore.QSize(100, 120)
    worker = MagicMock(canceled=False)
    exporter.export(filename, worker)

    worker.begin_processing.emit.assert_called_once_with(1)
    worker.progress.emit.assert_called_once_with(1)
    worker.finished.emit.assert_called_once_with(filename, [])
    with open(filename, 'rb') as f:
        assert f.read().startswith(b'\x89PNG')


def test_scene_to_pixmap_exporter_export_with_worker_when_canceled(
        view, tmpdir):
    filename = os.path.join(tmpdir, 'foo.png')
    item_img = QtGui.QImage(1000, 1200, QtGui.QImage.Format.Format_RGB32)
    item = BeePixmapItem(item_img)
    view.scene.addItem(item)
    exporter = SceneToPixmapExporter(view.scene)
    exporter.size = QtCore.QSize(100, 120)
    worker = MagicMock(canceled=True)
    exporter.export(filename, worker)

    worker.begin_processing.emit.assert_called_once_with(1)
    worker.progress.emit.assert_not_called()
    worker.finished.emit.assert_called_once_with(filename, [])
    os.path.exists(filename) is False


def test_scene_to_pixmap_exporter_export_when_file_not_writeable(view, tmpdir):
    filename = os.path.join(tmpdir, 'foo.png')
    with open(filename, 'w') as f:
        f.write('foo')
    os.chmod(filename, stat.S_IREAD)
    item_img = QtGui.QImage(1000, 1200, QtGui.QImage.Format.Format_RGB32)
    item = BeePixmapItem(item_img)
    view.scene.addItem(item)
    exporter = SceneToPixmapExporter(view.scene)
    exporter.size = QtCore.QSize(100, 120)

    with pytest.raises(BeeFileIOError) as e:
        exporter.export(filename)
        assert e.filename == filename


def test_scene_to_pixmap_exporter_export_when_file_not_writeable_with_worker(
        view, tmpdir):
    filename = os.path.join(tmpdir, 'foo.png')
    with open(filename, 'w') as f:
        f.write('foo')
    os.chmod(filename, stat.S_IREAD)
    item_img = QtGui.QImage(1000, 1200, QtGui.QImage.Format.Format_RGB32)
    item = BeePixmapItem(item_img)
    view.scene.addItem(item)
    exporter = SceneToPixmapExporter(view.scene)
    exporter.size = QtCore.QSize(100, 120)
    worker = MagicMock(canceled=False)

    exporter.export(filename, worker=worker)
    worker.begin_processing.emit.assert_called_once_with(1)
    worker.progress.emit.assert_not_called()
    worker.finished.emit.assert_called_once_with(
        filename, ['Error writing file'])
