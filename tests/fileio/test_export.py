import os
import stat
from unittest.mock import patch, ANY, MagicMock
import pytest

from PyQt6 import QtGui, QtCore

from beeref import constants
from beeref.items import BeePixmapItem, BeeTextItem
from beeref.fileio.errors import BeeFileIOError
from beeref.fileio.export import (
    exporter_registry,
    SceneToPixmapExporter,
    SceneToSVGExporter,
)


@pytest.mark.parametrize('key,expected',
                         [('png', SceneToPixmapExporter),
                          ('jpg', SceneToPixmapExporter),
                          ('svg', SceneToSVGExporter)])
def test_registry(key, expected):
    exporter_registry[key] == expected


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


def test_scene_to_svg_exporter_get_user_input(view):
    item1 = BeePixmapItem(
        QtGui.QImage(100, 100, QtGui.QImage.Format.Format_RGB32))
    item1.setPos(QtCore.QPointF(0, 0))
    view.scene.addItem(item1)

    item2 = BeePixmapItem(
        QtGui.QImage(100, 100, QtGui.QImage.Format.Format_RGB32))
    item1.setPos(QtCore.QPointF(200, 0))
    view.scene.addItem(item2)

    assert view.scene.sceneRect().size().toSize() == QtCore.QSize(300, 100)
    exporter = SceneToSVGExporter(view.scene)
    value = exporter.get_user_input(None)
    assert value is True
    assert exporter.size == QtCore.QSize(318, 118)


def test_scene_to_svg_exporter_render_pixmap_items(view):
    item1 = BeePixmapItem(
        QtGui.QImage(100, 110, QtGui.QImage.Format.Format_RGB32))
    item1.setPos(QtCore.QPointF(20, 30))
    view.scene.addItem(item1)

    item2 = BeePixmapItem(
        QtGui.QImage(70, 77, QtGui.QImage.Format.Format_RGB32))
    item2.setPos(QtCore.QPointF(50, 50))
    item2.setZValue(-1)
    view.scene.addItem(item2)

    exporter = SceneToSVGExporter(view.scene)
    exporter.size = QtCore.QSize(200, 400)
    exporter.margin = 5
    svg = exporter.render_to_svg()

    assert svg.tag == 'svg'
    assert svg.get('width') == '200'
    assert svg.get('height') == '400'
    assert svg.get('xmlns') == 'http://www.w3.org/2000/svg'
    assert svg.get('xmlns:xlink') == 'http://www.w3.org/1999/xlink'
    assert len(svg) == 2

    element = svg[0]  # item2
    assert element.tag == 'image'
    assert element.get('xlink:href').startswith('data:image/png;base64,iVBOR')
    assert element.get('width') == '70.0'
    assert element.get('height') == '77.0'
    assert element.get('image-rendering') == 'optimizeQuality'
    assert element.get('transform') == 'rotate(0.0 35.0 25.0)'
    assert element.get('x') == '35.0'
    assert element.get('y') == '25.0'
    assert element.get('opacity') == '1.0'

    element = svg[1]  # item1
    assert element.tag == 'image'
    assert element.get('width') == '100.0'
    assert element.get('height') == '110.0'
    assert element.get('image-rendering') == 'optimizeQuality'
    assert element.get('transform') == 'rotate(0.0 5.0 5.0)'
    assert element.get('x') == '5.0'
    assert element.get('y') == '5.0'
    assert element.get('opacity') == '1.0'


def test_scene_to_svg_exporter_render_pixmap_with_crop(view):
    item = BeePixmapItem(
        QtGui.QImage(100, 110, QtGui.QImage.Format.Format_RGB32))
    item.setPos(QtCore.QPointF(20, 30))
    item.crop = QtCore.QRectF(20, 25, 30, 33)
    view.scene.addItem(item)
    exporter = SceneToSVGExporter(view.scene)
    exporter.size = QtCore.QSize(200, 400)
    exporter.margin = 5
    svg = exporter.render_to_svg()

    assert len(svg) == 1

    element = svg[0]
    assert element.tag == 'image'
    assert element.get('width') == '30.0'
    assert element.get('height') == '33.0'
    assert element.get('transform') == 'rotate(0.0 -15.0 -20.0)'
    assert element.get('x') == '5.0'
    assert element.get('y') == '5.0'


def test_scene_to_svg_exporter_render_pixmap_with_rotation(view):
    item = BeePixmapItem(
        QtGui.QImage(100, 110, QtGui.QImage.Format.Format_RGB32))
    item.setPos(QtCore.QPointF(20, 30))
    item.setRotation(90)
    view.scene.addItem(item)
    exporter = SceneToSVGExporter(view.scene)
    exporter.size = QtCore.QSize(200, 400)
    exporter.margin = 5
    svg = exporter.render_to_svg()

    assert len(svg) == 1

    element = svg[0]
    assert element.tag == 'image'
    assert element.get('transform') == 'rotate(90.0 115.0 5.0)'
    assert element.get('x') == '115.0'
    assert element.get('y') == '5.0'


def test_scene_to_svg_exporter_render_pixmap_with_opacity(view):
    item = BeePixmapItem(
        QtGui.QImage(100, 110, QtGui.QImage.Format.Format_RGB32))
    item.setPos(QtCore.QPointF(20, 30))
    item.setOpacity(0.75)
    view.scene.addItem(item)
    exporter = SceneToSVGExporter(view.scene)
    exporter.size = QtCore.QSize(200, 400)
    exporter.margin = 5
    svg = exporter.render_to_svg()

    assert len(svg) == 1

    element = svg[0]
    assert element.tag == 'image'
    assert element.get('opacity') == '0.75'


def test_scene_to_svg_exporter_render_pixmap_with_flip(view):
    item = BeePixmapItem(
        QtGui.QImage(100, 110, QtGui.QImage.Format.Format_RGB32))
    item.setPos(QtCore.QPointF(20, 30))
    item.do_flip()
    view.scene.addItem(item)
    exporter = SceneToSVGExporter(view.scene)
    exporter.size = QtCore.QSize(200, 400)
    exporter.margin = 5
    svg = exporter.render_to_svg()

    assert len(svg) == 1

    element = svg[0]
    assert element.tag == 'image'
    assert element.get('transform') == (
        'translate(105.0 5.0) scale(-1.0 1)'
        ' translate(-105.0 -5.0) rotate(0.0 105.0 5.0)')
    assert element.get('x') == '105.0'
    assert element.get('y') == '5.0'


def test_scene_to_svg_exporter_render_text(view):
    item = BeeTextItem('foo')
    item.setPos(QtCore.QPointF(20, 30))
    view.scene.addItem(item)
    exporter = SceneToSVGExporter(view.scene)
    exporter.size = QtCore.QSize(200, 400)
    exporter.margin = 5
    svg = exporter.render_to_svg()

    assert len(svg) == 1

    element = svg[0]
    assert element.tag == 'text'
    assert element.text == 'foo'
    assert element.get('dominant-baseline') == 'hanging'
    assert 'font-family' in element.get('style')
    assert element.get('transform') == 'rotate(0.0 5.0 5.0)'
    assert element.get('x') == '5.0'
    assert element.get('y') == '5.0'


def test_scene_to_svg_exporter_export_when_file_not_writeable(view, tmpdir):
    filename = os.path.join(tmpdir, 'foo.svg')
    with open(filename, 'w') as f:
        f.write('foo')
    os.chmod(filename, stat.S_IREAD)
    item = BeeTextItem('foo')
    view.scene.addItem(item)
    exporter = SceneToSVGExporter(view.scene)
    exporter.size = QtCore.QSize(100, 120)

    with pytest.raises(BeeFileIOError) as e:
        exporter.export(filename)
        assert e.filename == filename


def test_scene_to_svg_exporter_render_with_worker(view):
    item = BeeTextItem('foo')
    item.setPos(QtCore.QPointF(20, 30))
    view.scene.addItem(item)
    exporter = SceneToSVGExporter(view.scene)
    exporter.size = QtCore.QSize(200, 400)
    exporter.margin = 5

    worker = MagicMock(canceled=False)
    svg = exporter.render_to_svg(worker=worker)
    assert len(svg) == 1
    worker.progress.emit.assert_called_once_with(0)


def test_scene_to_svg_exporter_render_with_worker_canceled(view):
    item = BeeTextItem('foo')
    item.setPos(QtCore.QPointF(20, 30))
    view.scene.addItem(item)
    exporter = SceneToSVGExporter(view.scene)
    exporter.size = QtCore.QSize(200, 400)
    exporter.margin = 5

    worker = MagicMock(canceled=True)
    svg = exporter.render_to_svg(worker=worker)
    assert svg is None


def test_scene_to_svg_exporter_export_writes_svg(view, tmpdir):
    filename = os.path.join(tmpdir, 'foo.svg')
    item = BeeTextItem('foo')
    view.scene.addItem(item)
    exporter = SceneToSVGExporter(view.scene)
    exporter.size = QtCore.QSize(100, 120)
    exporter.export(filename)

    with open(filename, 'rb') as f:
        assert f.read().startswith(b'<?xml')


def test_scene_to_svg_exporter_export_with_worker(view, tmpdir):
    filename = os.path.join(tmpdir, 'foo.svg')
    item = BeeTextItem('foo')
    view.scene.addItem(item)
    exporter = SceneToSVGExporter(view.scene)
    exporter.size = QtCore.QSize(100, 120)
    worker = MagicMock(canceled=False)
    exporter.export(filename, worker)

    worker.begin_processing.emit.assert_called_once_with(1)
    worker.progress.emit.assert_called_once_with(0)
    worker.finished.emit.assert_called_once_with(filename, [])
    with open(filename, 'rb') as f:
        assert f.read().startswith(b'<?xml')


def test_scene_to_svg_exporter_export_with_worker_canceled(view, tmpdir):
    filename = os.path.join(tmpdir, 'foo.svg')
    item = BeeTextItem('foo')
    view.scene.addItem(item)
    exporter = SceneToSVGExporter(view.scene)
    exporter.size = QtCore.QSize(100, 120)
    worker = MagicMock(canceled=True)
    exporter.export(filename, worker)

    worker.begin_processing.emit.assert_called_once_with(1)
    worker.progress.emit.assert_called_once_with(0)
    worker.finished.emit.assert_called_once_with(filename, [])
    os.path.exists(filename) is False


def test_scene_to_svg_exporter_export_when_file_not_writeable_with_worker(
        view, tmpdir):
    filename = os.path.join(tmpdir, 'foo.svg')
    with open(filename, 'w') as f:
        f.write('foo')
    os.chmod(filename, stat.S_IREAD)
    item = BeeTextItem('foo')
    view.scene.addItem(item)
    exporter = SceneToSVGExporter(view.scene)
    exporter.size = QtCore.QSize(100, 120)
    worker = MagicMock(canceled=False)

    exporter.export(filename, worker=worker)
    worker.begin_processing.emit.assert_called_once_with(1)
    worker.progress.emit.assert_called_once_with(0)
    worker.finished.emit.assert_called_once()
    args = worker.finished.emit.call_args.args
    assert args[0] == filename
    assert len(args[1]) == 1
