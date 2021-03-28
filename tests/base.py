import os.path
from unittest import TestCase

from PyQt6 import QtWidgets


root = os.path.dirname(__file__)
imgfilename3x3 = os.path.join(root, 'assets', 'test3x3.png')
with open(imgfilename3x3, 'rb') as f:
    imgdata3x3 = f.read()


class BeeTestCase(TestCase):

    imgfilename3x3 = imgfilename3x3
    imgdata3x3 = imgdata3x3

    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication([])

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()
        del cls.app
