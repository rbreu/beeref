import os.path
import pytest
from unittest.mock import MagicMock, patch

from PyQt6 import QtGui, QtWidgets


def pytest_configure(config):
    # Ignore logging configuration for BeeRef during test runs. This
    # avoids logging to the regular log file and spamming test output
    # with debug messages.
    #
    # This needs to be done before the application code is even loaded since
    # logging configuration happens on module level
    import logging.config
    logging.config.dictConfig = MagicMock


@pytest.fixture(autouse=True)
def commandline_args():
    config_patcher = patch('beeref.view.commandline_args')
    config_mock = config_patcher.start()
    config_mock.filename = None
    yield config_mock
    config_patcher.stop()


@pytest.fixture(autouse=True)
def settings(tmpdir):
    from beeref.config import BeeSettings
    dir_patcher = patch('beeref.config.BeeSettings.get_settings_dir',
                        return_value=tmpdir.dirname)
    dir_patcher.start()
    settings = BeeSettings()
    yield settings
    settings.clear()
    dir_patcher.stop()


@pytest.fixture
def main_window(qtbot):
    from beeref.__main__ import BeeRefMainWindow
    app = QtWidgets.QApplication.instance()
    main = BeeRefMainWindow(app)
    qtbot.addWidget(main)
    yield main


@pytest.fixture
def view(main_window):
    yield main_window.view


@pytest.fixture
def imgfilename3x3():
    root = os.path.dirname(__file__)
    yield os.path.join(root, 'assets', 'test3x3.png')


@pytest.fixture
def imgdata3x3(imgfilename3x3):
    with open(imgfilename3x3, 'rb') as f:
        imgdata3x3 = f.read()
    yield imgdata3x3


@pytest.fixture
def tmpfile(tmpdir):
    yield os.path.join(tmpdir, 'test')


@pytest.fixture
def item():
    from beeref.items import BeePixmapItem
    yield BeePixmapItem(QtGui.QImage())
