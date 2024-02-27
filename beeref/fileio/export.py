# This file is part of BeeRef.
#
# BeeRef is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BeeRef is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BeeRef.  If not, see <https://www.gnu.org/licenses/>.

import base64
import logging
from xml.etree import ElementTree as ET

from PyQt6 import QtCore, QtGui

from .errors import BeeFileIOError
from beeref import constants, widgets
from beeref.config import BeeStyleSheet


logger = logging.getLogger(__name__)


class ExporterRegistry(dict):

    DEFAULT_TYPE = 0

    def __getitem__(self, key):
        key = key.removeprefix('.')
        exp = self.get(key, super().__getitem__(self.DEFAULT_TYPE))
        logger.debug(f'Exporter for type {key}: {exp}')
        return exp


exporter_registry = ExporterRegistry()


def register_exporter(cls):
    exporter_registry[cls.TYPE] = cls
    return cls


class ExporterBase:
    """For exporting the scene to a single image."""

    def __init__(self, scene):
        self.scene = scene
        self.scene.cancel_crop_mode()
        self.scene.deselect_all_items()
        # Selection outlines/handles will be rendered to the exported
        # image, so deselect first. (Alternatively, pass an attribute
        # to paint functions to not paint them?)
        rect = self.scene.itemsBoundingRect()
        logger.trace(f'Items bounding rect: {rect}')
        size = QtCore.QSize(int(rect.width()), int(rect.height()))
        logger.trace(f'Export size without margins: {size}')
        self.margin = max(size.width(), size.height()) * 0.03
        self.default_size = size.grownBy(
            QtCore.QMargins(*([int(self.margin)] * 4)))
        logger.debug(f'Default export margin: {self.margin}')
        logger.debug(f'Default export size with margins: {self.default_size}')


@register_exporter
class SceneToPixmapExporter(ExporterBase):

    TYPE = ExporterRegistry.DEFAULT_TYPE

    def get_user_input(self, parent):
        """Ask user for final export size."""

        dialog = widgets.SceneToPixmapExporterDialog(
            parent=parent,
            default_size=self.default_size,
        )
        if dialog.exec():
            size = dialog.value()
            logger.debug(f'Got export size {size}')
            self.size = size
            return True
        else:
            return False

    def render_to_image(self):
        logger.debug(f'Final export size: {self.size}')
        margin = self.margin * self.size.width() / self.default_size.width()
        logger.debug(f'Final export margin: {margin}')

        image = QtGui.QImage(self.size, QtGui.QImage.Format.Format_RGB32)
        color = BeeStyleSheet().get_color('QGraphicsView', 'background')
        if color:
            image.fill(color)
        painter = QtGui.QPainter(image)
        target_rect = QtCore.QRectF(
            margin,
            margin,
            self.size.width() - 2 * margin,
            self.size.height() - 2 * margin)
        logger.trace(f'Final export target_rect: {target_rect}')
        self.scene.render(painter,
                          source=self.scene.itemsBoundingRect(),
                          target=target_rect)
        painter.end()
        return image

    def export(self, filename, worker=None):
        logger.debug(f'Exporting scene to {filename}')
        if worker:
            worker.begin_processing.emit(1)

        image = self.render_to_image()

        if worker and worker.canceled:
            logger.debug('Export canceled')
            worker.finished.emit(filename, [])
            return

        if not image.save(filename, quality=90):
            msg = 'Error writing file'
            logger.debug(f'Export failed: {msg}')
            if worker:
                worker.finished.emit(filename, [msg])
                return
            else:
                raise BeeFileIOError(msg, filename=filename)

        logger.debug('Export finished')
        if worker:
            worker.progress.emit(1)
            worker.finished.emit(filename, [])


@register_exporter
class SceneToSVGExporter(ExporterBase):

    TYPE = 'svg'

    def get_user_input(self, parent):
        self.size = self.default_size
        return True

    def _get_textstyles(self, item):
        fontstylemap = {
            QtGui.QFont.Style.StyleNormal: 'normal',
            QtGui.QFont.Style.StyleItalic: 'italic',
            QtGui.QFont.Style.StyleOblique: 'oblique',
        }

        font = item.font()
        fontsize = font.pointSize() * item.scale()
        families = ', '.join(font.families())
        fontstyle = fontstylemap[font.style()]

        return ('white-space:pre',
                f'font-size:{fontsize}pt',
                f'font-family:{families}',
                f'font-weight:{font.weight()}',
                f'font-stretch:{font.stretch()}',
                f'font-style:{fontstyle}')

    def render_to_svg(self, worker=None):
        svg = ET.Element(
            'svg',
            attrib={'width': str(self.size.width()),
                    'height': str(self.size.height()),
                    'xmlns': 'http://www.w3.org/2000/svg',
                    'xmlns:xlink': 'http://www.w3.org/1999/xlink',
                    })

        rect = self.scene.itemsBoundingRect()
        offset = rect.topLeft() - QtCore.QPointF(self.margin, self.margin)

        for i, item in enumerate(sorted(self.scene.items(),
                                        key=lambda x: x.zValue())):
            # z order in SVG specified via the order of elements in the tree
            pos = item.pos() - offset
            anchor = pos

            if item.TYPE == 'text':
                styles = self._get_textstyles(item)
                element = ET.Element(
                    'text',
                    attrib={'style': ';'.join(styles),
                            'dominant-baseline': 'hanging'})
                element.text = item.toPlainText()
            if item.TYPE == 'pixmap':
                width = item.width * item.scale()
                height = item.height * item.scale()
                pixmap, imgformat = item.pixmap_to_bytes(
                    apply_grayscale=True,
                    apply_crop=True)
                pixmap = base64.b64encode(pixmap).decode('ascii')
                element = ET.Element(
                    'image',
                    attrib={
                        'xlink:href':
                        f'data:image/{imgformat};base64,{pixmap}',
                        'width': str(width),
                        'height': str(height),
                        'image-rendering': ('crisp-edges' if item.scale() > 2
                                            else 'optimizeQuality')})
                pos = pos + item.crop.topLeft()

            transforms = []
            if item.flip() == -1:
                # The following is not recognised by Inkscape and not an
                # official standard:
                # element.set('transform-origin', f'{anchor.x()} {anchor.y()}')
                # Thus we need to fix the origin manually
                transforms.append(f'translate({anchor.x()} {anchor.y()})')
                transforms.append(f'scale({item.flip()} 1)')
                transforms.append(f'translate(-{anchor.x()} -{anchor.y()})')
            transforms.append(
                f'rotate({item.rotation()} {anchor.x()} {anchor.y()})')

            element.set('transform', ' '.join(transforms))
            element.set('x', str(pos.x()))
            element.set('y', str(pos.y()))
            element.set('opacity', str(item.opacity()))

            svg.append(element)
            if worker:
                worker.progress.emit(i)
                if worker.canceled:
                    return

        return svg

    def export(self, filename, worker=None):
        logger.debug(f'Exporting scene to {filename}')
        if worker:
            worker.begin_processing.emit(len(self.scene.items()))

        svg = self.render_to_svg(worker)

        if worker and worker.canceled:
            logger.debug('Export canceled')
            worker.finished.emit(filename, [])
            return

        tree = ET.ElementTree(svg)
        ET.indent(tree, space='  ')

        try:
            with open(filename, 'w') as f:
                tree.write(f, encoding='unicode', xml_declaration=True)
        except OSError as e:
            logger.debug(f'Export failed: {e}')
            if worker:
                worker.finished.emit(filename, [str(e)])
                return
            else:
                raise BeeFileIOError(msg=str(e), filename=filename) from e

        logger.debug('Export finished')
        if worker:
            worker.finished.emit(filename, [])
