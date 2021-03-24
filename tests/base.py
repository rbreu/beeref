from unittest import TestCase

from PyQt6 import QtWidgets


class BeeTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication([])

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()
        del cls.app
