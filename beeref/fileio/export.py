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
import pathlib
from xml.etree import ElementTree as ET

from PyQt6 import QtCore, QtGui

from .errors import BeeFileIOError
from beeref import constants, widgets
from beeref.items import BeePixmapItem


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

    def emit_begin_processing(self, worker, start):
        if worker:
            worker.begin_processing.emit(start)

    def emit_progress(self, worker, progress):
        if worker:
            worker.progress.emit(progress)

    def emit_finished(self, worker, filename, errors):
        filename = str(filename)
        if worker:
            worker.finished.emit(filename, errors)

    def emit_user_input_required(self, worker, msg):
        if worker:
            worker.user_input_required.emit(msg)

    def handle_export_error(self, filename, error, worker):
        filename = str(filename)
        logger.debug(f'Export failed: {error}')
        if worker:
            worker.finished.emit(filename, [str(error)])
            return
        else:
            e = error if isinstance(error, Exception) else None
            raise BeeFileIOError(msg=str(error), filename=filename) from e


class SceneExporterBase(ExporterBase):
    """For exporting the scene to a single image."""

    def __init__(self, scene):
        self.scene = scene
        self.scene.cancel_active_modes()
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
class SceneToPixmapExporter(SceneExporterBase):

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
        image.fill(QtGui.QColor(*constants.COLORS['Scene:Canvas']))
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
        self.emit_begin_processing(worker, 1)
        image = self.render_to_image()

        if worker and worker.canceled:
            logger.debug('Export canceled')
            self.emit_finished(worker, filename, [])
            return

        if not image.save(filename, quality=90):
            self.handle_export_error(filename, 'Error writing file', worker)
            return

        logger.debug('Export finished')
        self.emit_progress(worker, 1)
        self.emit_finished(worker, filename, [])


@register_exporter
class SceneToSVGExporter(SceneExporterBase):

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
            self.emit_progress(worker, i)
            if worker and worker.canceled:
                return

        return svg

    def export(self, filename, worker=None):
        logger.debug(f'Exporting scene to {filename}')
        self.emit_begin_processing(worker, len(self.scene.items()))
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
            self.handle_export_error(filename, e, worker)
            return

        logger.debug('Export finished')
        self.emit_finished(worker, filename, [])


class ImagesToDirectoryExporter(ExporterBase):
    """Export all images to a folder.

    Not registered in the registry as it is accessed via its own menu entry,
    not auto-detected by file extension.
    """

    def __init__(self, scene, dirname):
        self.scene = scene
        self.dirname = dirname
        self.items = list(self.scene.items_by_type(BeePixmapItem.TYPE))
        self.max_save_id = 0
        for item in self.items:
            if item.save_id:
                self.max_save_id = max(self.max_save_id, item.save_id)
        self.num_total = len(self.items)
        self.start_from = 0
        self.handle_existing = None

    def export(self, worker=None):
        logger.debug(f'Exporting images to {self.dirname}')
        logger.debug(f'Starting at {self.start_from}')

        self.emit_begin_processing(worker, self.num_total)
        self.emit_progress(worker, self.start_from)

        for i, item in enumerate(
                self.items[self.start_from:], start=self.start_from):
            if worker and worker.canceled:
                logger.debug('Export canceled')
                worker.finished.emit(self.dirname, [])
                return

            pixmap, imgformat = item.pixmap_to_bytes()

            if item.save_id:
                filename = item.get_filename_for_export(imgformat)
            else:
                self.max_save_id += 1
                save_id = self.max_save_id
                filename = item.get_filename_for_export(imgformat, save_id)

            try:
                path = pathlib.Path(self.dirname) / filename
                path_exists = path.exists()
            except OSError as e:
                self.handle_export_error(self.dirname, e, worker)
                return

            if path_exists:
                logger.debug(f'File already exists: {path}')
                if self.handle_existing is None:
                    self.start_from = i
                    self.emit_user_input_required(worker, str(path))
                    return
                else:
                    if self.handle_existing == 'skip':
                        self.handle_existing = None
                        logger.debug('Skipping file')
                        continue
                    elif self.handle_existing == 'skip_all':
                        logger.debug('Skipping file')
                        continue
                    elif self.handle_existing == 'overwrite':
                        self.handle_existing = None
                        logger.debug('Overwrite file')
                    elif self.handle_existing == 'overwrite_all':
                        logger.debug('Overwrite file')

            logger.debug(f'Writing file: {path}')
            try:
                path.write_bytes(pixmap)
            except OSError as e:
                self.handle_export_error(path, e, worker)
                return

            self.emit_progress(worker, i)

        self.emit_finished(worker, self.dirname, [])
