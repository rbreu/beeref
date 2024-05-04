import math
import os.path
from unittest.mock import patch

import httpretty
import pytest

import plum

from PyQt6 import QtCore, QtGui

from beeref.fileio.image import exif_rotated_image, load_image


def test_exif_rotated_image_without_path(qapp):
    img = exif_rotated_image()
    assert img.isNull() is True


def test_exif_rotated_image_not_a_file(qapp):
    img = exif_rotated_image('foo')
    assert img.isNull() is True


def test_exif_rotated_image_exif_unpack_error(qapp, imgfilename3x3):
    with patch('beeref.fileio.image.exif.Image',
               side_effect=plum.exceptions.UnpackError()):
        img = exif_rotated_image(imgfilename3x3)
        assert img.isNull() is False


def test_exif_rotated_image_exif_notimplementederror(qapp, imgfilename3x3):
    with patch('beeref.fileio.image.exif.Image.list_all',
               side_effect=NotImplementedError()):
        img = exif_rotated_image(imgfilename3x3)
        assert img.isNull() is False


@pytest.mark.parametrize('path,expected',
                         [('test3x3.png', 'test3x3.png'),
                          ('test3x3_orientation1.jpg', 'test3x3.jpg'),
                          ('test3x3_orientation2.jpg', 'test3x3.jpg'),
                          ('test3x3_orientation3.jpg', 'test3x3.jpg'),
                          ('test3x3_orientation4.jpg', 'test3x3.jpg'),
                          ('test3x3_orientation5.jpg', 'test3x3.jpg'),
                          ('test3x3_orientation6.jpg', 'test3x3.jpg'),
                          ('test3x3_orientation7.jpg', 'test3x3.jpg'),
                          ('test3x3_orientation8.jpg', 'test3x3.jpg')])
def test_exif_rotated_image(path, expected, qapp):
    def get_fname(p):
        root = os.path.dirname(__file__)
        return os.path.join(root, '..', 'assets', p)

    img = exif_rotated_image(get_fname(path))
    assert img.isNull() is False
    expected = QtGui.QImage(get_fname(expected))
    assert expected.isNull() is False

    # The JPEG format isn't pixel perfect, so we have to check whether
    # pixels are approximately the same:
    for x in range(3):
        for y in range(3):
            col_img = img.pixelColor(x, y).getRgb()
            col_expected = expected.pixelColor(x, y).getRgb()
            diff = [(col_img[i] - col_expected[i])**2 for i in range(4)]
            assert math.sqrt(sum(diff)) < 3


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
def test_load_image_loads_from_existing_web_url_non_ascii(view, imgdata3x3):
    url = 'http://example.com/föö.png'
    httpretty.register_uri(
        httpretty.GET,
        url,
        body=imgdata3x3,
    )
    img, filename = load_image(QtCore.QUrl(url))
    assert img.isNull() is False
    assert filename == 'http://example.com/f%C3%B6%C3%B6.png'


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


@httpretty.activate
def test_load_image_from_pinterest_finds_image(view, imgdata3x3):
    url = 'http://pinterest.com/a1b2c3/'
    img_url = 'http://pinterest.com/foo.png'
    httpretty.register_uri(
        httpretty.GET,
        url,
        body=f'<html><body><img src="{img_url}"/></body></html>',
    )
    httpretty.register_uri(
        httpretty.GET,
        img_url,
        body=imgdata3x3,
    )
    img, filename = load_image(QtCore.QUrl(url))
    assert img.isNull() is False
    assert filename == img_url


@httpretty.activate
def test_load_image_from_pinterest_when_already_image(view, imgdata3x3):
    img_url = 'http://pinterest.com/foo.png'
    httpretty.register_uri(
        httpretty.GET,
        img_url,
        body=imgdata3x3,
    )
    img, filename = load_image(QtCore.QUrl(img_url))
    assert img.isNull() is False
    assert filename == img_url


@httpretty.activate
def test_load_image_from_pinterest_when_img_url_not_found(view, imgdata3x3):
    url = 'http://pinterest.com/a1b2c3/'
    img_url = 'http://pinterest.com/foo.png'
    httpretty.register_uri(
        httpretty.GET,
        url,
        body='<html><body><p>no image here</p></body></html>',
    )
    httpretty.register_uri(
        httpretty.GET,
        img_url,
        body=imgdata3x3,
    )
    img, filename = load_image(QtCore.QUrl(url))
    assert img.isNull() is True


@httpretty.activate
def test_load_image_from_pinterest_when_url_errors(view, imgdata3x3):
    url = 'http://pinterest.com/a1b2c3/'
    httpretty.register_uri(
        httpretty.GET,
        url,
        status=500,
    )
    img, filename = load_image(QtCore.QUrl(url))
    assert img.isNull() is True
