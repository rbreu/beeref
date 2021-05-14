import httpretty

from PyQt6 import QtCore

from beeref.fileio.image import load_image
from ..base import BeeTestCase


class LoadImageTestCase(BeeTestCase):

    def test_loads_from_filename(self):
        img, filename = load_image(self.imgfilename3x3)
        assert img.isNull() is False
        assert filename == self.imgfilename3x3

    def test_loads_from_nonexisting_filename(self):
        img, filename = load_image('foo.png')
        assert img.isNull() is True
        assert filename == 'foo.png'

    def test_loads_from_existing_local_url(self):
        url = QtCore.QUrl.fromLocalFile(self.imgfilename3x3)
        img, filename = load_image(url)
        assert img.isNull() is False
        assert filename == self.imgfilename3x3

    @httpretty.activate
    def test_loads_from_existing_web_url(self):
        url = 'http://example.com/foo.png'
        httpretty.register_uri(
            httpretty.GET,
            url,
            body=self.imgdata3x3,
        )
        img, filename = load_image(QtCore.QUrl(url))
        assert img.isNull() is False
        assert filename == url

    @httpretty.activate
    def test_loads_from_web_url_errors(self):
        url = 'http://example.com/foo.png'
        httpretty.register_uri(
            httpretty.GET,
            url,
            status=500,
        )
        img, filename = load_image(QtCore.QUrl(url))
        assert img.isNull() is True
        assert filename == url
