import os.path
import tempfile
from unittest import mock, TestCase

from PyQt6 import QtWidgets

from beeref.config import BeeSettings


root = os.path.dirname(__file__)
imgfilename3x3 = os.path.join(root, 'assets', 'test3x3.png')
with open(imgfilename3x3, 'rb') as f:
    imgdata3x3 = f.read()


class BeeTestCase(TestCase):

    imgfilename3x3 = imgfilename3x3
    imgdata3x3 = imgdata3x3

    @classmethod
    def setUpClass(cls):
        cls._settings_dir = tempfile.TemporaryDirectory()
        settings_dir_patcher = mock.patch(
            'beeref.config.BeeSettings.get_settings_dir',
            return_value=cls._settings_dir.name)
        cls._settings_dir_mock = settings_dir_patcher.start()
        inst = QtWidgets.QApplication.instance()
        cls.app = inst if inst else QtWidgets.QApplication([])

    @classmethod
    def tearDownClass(cls):
        cls._settings_dir_mock.stop()
        cls._settings_dir.cleanup()

    def tearDown(self):
        BeeSettings().clear()

    def queue2list(self, queue):
        qlist = []
        while not queue.empty():
            qlist.append(queue.get())
        return qlist
