import os
import stat
from unittest.mock import MagicMock
import pytest

from PyQt6 import QtGui

from beeref.items import BeePixmapItem
from beeref.fileio.errors import BeeFileIOError
from beeref.fileio.export import ImagesToDirectoryExporter


def test_images_to_directory_exporter_export_writes_images(
        view, tmpdir, imgdata3x3, imgfilename3x3,):
    item1 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    item2.save_id = 3
    view.scene.addItem(item2)
    exporter = ImagesToDirectoryExporter(view.scene, tmpdir)
    exporter.export()

    with open(os.path.join(tmpdir, '0003.png'), 'rb') as f:
        assert f.read().startswith(b'\x89PNG')
    with open(os.path.join(tmpdir, '0004.png'), 'rb') as f:
        assert f.read().startswith(b'\x89PNG')


def test_images_to_directory_exporter_export_file_exists_no_user_input(
        view, tmpdir, imgdata3x3, imgfilename3x3,):
    item1 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item2)

    with open(os.path.join(tmpdir, '0002.png'), 'w') as f:
        assert f.write('foo')

    exporter = ImagesToDirectoryExporter(view.scene, tmpdir)
    exporter.export()

    with open(os.path.join(tmpdir, '0001.png'), 'rb') as f:
        assert f.read().startswith(b'\x89PNG')
    with open(os.path.join(tmpdir, '0002.png'), 'r') as f:
        assert f.read() == 'foo'

    assert exporter.start_from == 1


def test_images_to_directory_exporter_export_file_exists_skip(
        view, tmpdir, imgdata3x3, imgfilename3x3,):
    item1 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item2)
    item3 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item3)

    with open(os.path.join(tmpdir, '0002.png'), 'w') as f:
        assert f.write('foo')
    with open(os.path.join(tmpdir, '0003.png'), 'w') as f:
        assert f.write('bar')

    exporter = ImagesToDirectoryExporter(view.scene, tmpdir)
    exporter.handle_existing = 'skip'
    exporter.export()

    with open(os.path.join(tmpdir, '0001.png'), 'rb') as f:
        assert f.read().startswith(b'\x89PNG')
    with open(os.path.join(tmpdir, '0002.png'), 'r') as f:
        assert f.read() == 'foo'
    with open(os.path.join(tmpdir, '0003.png'), 'r') as f:
        assert f.read() == 'bar'

    assert exporter.start_from == 2
    assert exporter.handle_existing is None


def test_images_to_directory_exporter_export_file_exists_skip_all(
        view, tmpdir, imgdata3x3, imgfilename3x3,):
    item1 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item2)
    item3 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item3)

    with open(os.path.join(tmpdir, '0002.png'), 'w') as f:
        assert f.write('foo')
    with open(os.path.join(tmpdir, '0003.png'), 'w') as f:
        assert f.write('bar')

    exporter = ImagesToDirectoryExporter(view.scene, tmpdir)
    exporter.handle_existing = 'skip_all'
    exporter.export()

    with open(os.path.join(tmpdir, '0001.png'), 'rb') as f:
        assert f.read().startswith(b'\x89PNG')
    with open(os.path.join(tmpdir, '0002.png'), 'r') as f:
        assert f.read() == 'foo'
    with open(os.path.join(tmpdir, '0003.png'), 'r') as f:
        assert f.read() == 'bar'

    assert exporter.handle_existing == 'skip_all'


def test_images_to_directory_exporter_export_file_exists_overwrite(
        view, tmpdir, imgdata3x3, imgfilename3x3,):
    item1 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item2)
    item3 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item3)

    with open(os.path.join(tmpdir, '0002.png'), 'w') as f:
        assert f.write('foo')
    with open(os.path.join(tmpdir, '0003.png'), 'w') as f:
        assert f.write('bar')

    exporter = ImagesToDirectoryExporter(view.scene, tmpdir)
    exporter.handle_existing = 'overwrite'
    exporter.export()

    with open(os.path.join(tmpdir, '0001.png'), 'rb') as f:
        assert f.read().startswith(b'\x89PNG')
    with open(os.path.join(tmpdir, '0002.png'), 'rb') as f:
        assert f.read().startswith(b'\x89PNG')
    with open(os.path.join(tmpdir, '0003.png'), 'r') as f:
        assert f.read() == 'bar'

    assert exporter.start_from == 2
    assert exporter.handle_existing is None


def test_images_to_directory_exporter_export_file_exists_overwrite_all(
        view, tmpdir, imgdata3x3, imgfilename3x3,):
    item1 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item1)
    item2 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item2)
    item3 = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item3)

    with open(os.path.join(tmpdir, '0002.png'), 'w') as f:
        assert f.write('foo')
    with open(os.path.join(tmpdir, '0003.png'), 'w') as f:
        assert f.write('bar')

    exporter = ImagesToDirectoryExporter(view.scene, tmpdir)
    exporter.handle_existing = 'overwrite_all'
    exporter.export()

    with open(os.path.join(tmpdir, '0001.png'), 'rb') as f:
        assert f.read().startswith(b'\x89PNG')
    with open(os.path.join(tmpdir, '0002.png'), 'rb') as f:
        assert f.read().startswith(b'\x89PNG')
    with open(os.path.join(tmpdir, '0003.png'), 'rb') as f:
        assert f.read().startswith(b'\x89PNG')

    assert exporter.handle_existing == 'overwrite_all'


def test_images_to_directory_exporter_export_with_worker(
        view, tmpdir, imgdata3x3, imgfilename3x3,):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    worker = MagicMock(canceled=False)
    exporter = ImagesToDirectoryExporter(view.scene, tmpdir)
    exporter.export(worker)

    with open(os.path.join(tmpdir, '0001.png'), 'rb') as f:
        assert f.read().startswith(b'\x89PNG')

    worker.begin_processing.emit.assert_called_once_with(1)
    worker.progress.emit.assert_called_with(0)
    worker.finished.emit.assert_called_once_with(tmpdir, [])


def test_images_to_directory_exporter_export_with_worker_when_canceled(
        view, tmpdir, imgdata3x3, imgfilename3x3,):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)
    worker = MagicMock(canceled=True)
    exporter = ImagesToDirectoryExporter(view.scene, tmpdir)
    exporter.export(worker)

    assert os.path.exists(os.path.join(tmpdir, '0001.png')) is False

    worker.begin_processing.emit.assert_called_once_with(1)
    worker.progress.emit.assert_called_once_with(0)
    worker.finished.emit.assert_called_once_with(tmpdir, [])


def test_images_to_directory_exporter_export_with_worker_when_file_exists(
        view, tmpdir, imgdata3x3, imgfilename3x3,):
    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)

    with open(os.path.join(tmpdir, '0001.png'), 'w') as f:
        assert f.write('foo')

    worker = MagicMock(canceled=False)
    exporter = ImagesToDirectoryExporter(view.scene, tmpdir)
    exporter.export(worker)

    imgfilename = os.path.join(tmpdir, '0001.png')
    with open(imgfilename, 'r') as f:
        assert f.read() == 'foo'

    worker.begin_processing.emit.assert_called_once_with(1)
    worker.progress.emit.assert_called_with(0)
    worker.user_input_required.emit.assert_called_once_with(imgfilename)


def test_images_to_directory_exporter_export_when_dir_not_writeable(
        view, tmpdir, imgdata3x3, imgfilename3x3,):

    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)

    os.chmod(tmpdir, stat.S_IREAD)
    exporter = ImagesToDirectoryExporter(view.scene, tmpdir)

    with pytest.raises(BeeFileIOError) as e:
        exporter.export()
        assert e.filename == tmpdir


def test_images_to_directory_exporter_export_when_dir_not_writeable_w_worker(
        view, tmpdir, imgdata3x3, imgfilename3x3,):

    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)

    os.chmod(tmpdir, stat.S_IREAD)
    exporter = ImagesToDirectoryExporter(view.scene, tmpdir)
    worker = MagicMock(canceled=False)

    exporter.export(worker)
    worker.begin_processing.emit.assert_called_once_with(1)
    worker.finished.emit.assert_called_once()
    args = worker.finished.emit.call_args.args
    assert args[0] == tmpdir
    assert len(args[1]) == 1


def test_images_to_directory_exporter_export_when_img_not_writeable(
        view, tmpdir, imgdata3x3, imgfilename3x3,):

    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)

    imgfilename = os.path.join(tmpdir, '0001.png')
    with open(imgfilename, 'w') as f:
        assert f.write('foo')
    os.chmod(imgfilename, stat.S_IREAD)

    exporter = ImagesToDirectoryExporter(view.scene, tmpdir)
    exporter.handle_existing = 'overwrite_all'

    with pytest.raises(BeeFileIOError) as e:
        exporter.export()
        assert e.filename == tmpdir


def test_images_to_directory_exporter_export_when_img_not_writeable_w_worker(
        view, tmpdir, imgdata3x3, imgfilename3x3,):

    item = BeePixmapItem(QtGui.QImage(imgfilename3x3))
    view.scene.addItem(item)

    imgfilename = os.path.join(tmpdir, '0001.png')
    with open(imgfilename, 'w') as f:
        assert f.write('foo')
    os.chmod(imgfilename, stat.S_IREAD)

    exporter = ImagesToDirectoryExporter(view.scene, tmpdir)
    exporter.handle_existing = 'overwrite_all'
    worker = MagicMock(canceled=False)

    exporter.export(worker)
    worker.begin_processing.emit.assert_called_once_with(1)
    worker.finished.emit.assert_called_once()
    args = worker.finished.emit.call_args.args
    assert args[0] == imgfilename
    assert len(args[1]) == 1
