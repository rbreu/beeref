import httpretty

from PyQt6 import QtCore

from beeref.fileio.image import load_image


def test_load_image_loads_from_filename(view, imgfilename3x3):
    img, filename = load_image(imgfilename3x3)
    assert img.isNull() is False
    assert filename == imgfilename3x3


def test_load_image_loads_from_nonexisting_filename(view, imgfilename3x3):
    img, filename = load_image('foo.png')
    assert img.isNull() is True
    assert filename == 'foo.png'


def test_load_image_loads_from_existing_local_url(view, imgfilename3x3):
    url = QtCore.QUrl.fromLocalFile(imgfilename3x3)
    img, filename = load_image(url)
    assert img.isNull() is False
    assert filename == imgfilename3x3


@httpretty.activate
def test_load_image_loads_from_existing_web_url(view, imgdata3x3):
    url = 'http://example.com/foo.png'
    httpretty.register_uri(
        httpretty.GET,
        url,
        body=imgdata3x3,
    )
    img, filename = load_image(QtCore.QUrl(url))
    assert img.isNull() is False
    assert filename == url


@httpretty.activate
def test_load_image_loads_from_web_url_errors(view, imgfilename3x3):
    url = 'http://example.com/foo.png'
    httpretty.register_uri(
        httpretty.GET,
        url,
        status=500,
    )
    img, filename = load_image(QtCore.QUrl(url))
    assert img.isNull() is True
    assert filename == url
