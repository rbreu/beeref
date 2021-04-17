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

import logging

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref.actions import ActionsMixin
from beeref import commands
from beeref.config import CommandlineArgs
from beeref import fileio
from beeref.gui import BeeProgressDialog, WelcomeOverlay
from beeref.items import BeePixmapItem
from beeref.scene import BeeGraphicsScene


commandline_args = CommandlineArgs()
logger = logging.getLogger('BeeRef')


class BeeGraphicsView(QtWidgets.QGraphicsView, ActionsMixin):

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(60, 60, 60)))
        self.setTransformationAnchor(
            QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.undo_stack = QtGui.QUndoStack(self)
        self.undo_stack.setUndoLimit(100)
        self.undo_stack.canRedoChanged.connect(self.on_can_redo_changed)
        self.undo_stack.canUndoChanged.connect(self.on_can_undo_changed)

        self.scene = BeeGraphicsScene(self.undo_stack)
        self.filename = None

        # TBD: make scrollbar configurable
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setAcceptDrops(True)

        self.previous_transform = None
        self.pan_active = False
        self.scene.changed.connect(self.on_scene_changed)
        self.scene.selectionChanged.connect(self.on_selection_changed)

        self.setScene(self.scene)

        # Context menu and actions
        self.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)
        self.context_menu = self.create_menu_and_actions()

        self.welcome_overlay = WelcomeOverlay(self)

        # Load file given via command line
        if commandline_args.filename:
            self.open_from_file(commandline_args.filename)

    def on_scene_changed(self, region):
        if not self.scene.items():
            logger.debug('No items in scene')
            self.setTransform(QtGui.QTransform())
            self.welcome_overlay.show()
        else:
            self.welcome_overlay.hide()
        self.recalc_scene_rect()

    def on_can_redo_changed(self, can_redo):
        self.actiongroup_set_enabled('active_when_can_redo', can_redo)

    def on_can_undo_changed(self, can_undo):
        self.actiongroup_set_enabled('active_when_can_undo', can_undo)

    def on_context_menu(self, point):
        self.context_menu.exec(self.mapToGlobal(point))

    def get_supported_image_formats(self, cls):
        formats = map(lambda f: f'*.{f.data().decode()}',
                      cls.supportedImageFormats())
        return ' '.join(formats)

    def get_view_center(self):
        return QtCore.QPoint(self.size().width() / 2,
                             self.size().height() / 2)

    def clear_scene(self):
        logging.debug('Clearing scene...')
        self.scene.clear()
        self.undo_stack.clear()
        self.filename = None
        self.setTransform(QtGui.QTransform())

    def reset_previous_transform(self, toggle_item=None):
        if (self.previous_transform
                and self.previous_transform['toggle_item'] != toggle_item):
            self.previous_transform = None

    def fit_rect(self, rect, toggle_item=None):
        if toggle_item and self.previous_transform:
            logger.debug('Fit view: Reset to previous')
            self.setTransform(self.previous_transform['transform'])
            self.centerOn(self.previous_transform['center'])
            self.previous_transform = None
            return
        if toggle_item:
            self.previous_transform = {
                'toggle_item': toggle_item,
                'transform': QtGui.QTransform(self.transform()),
                'center': self.mapToScene(self.get_view_center()),
            }
        else:
            self.previous_transform = None

        logger.debug(f'Fit view: {rect}')
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self.recalc_scene_rect()
        # It seems to be more reliable when we fit a second time
        # Sometimes a changing scene rect can mess up the fitting
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def on_action_fit_scene(self):
        self.fit_rect(self.scene.itemsBoundingRect())

    def on_action_fit_selection(self):
        self.fit_rect(self.scene.itemsBoundingRect(selection_only=True))

    def on_action_undo(self):
        logger.debug('Undo: %s' % self.undo_stack.undoText())
        self.undo_stack.undo()

    def on_action_redo(self):
        logger.debug('Redo: %s' % self.undo_stack.redoText())
        self.undo_stack.redo()

    def on_action_select_all(self):
        self.scene.set_selected_all_items(True)

    def on_action_deselect_all(self):
        self.scene.set_selected_all_items(False)

    def on_action_delete_items(self):
        logger.debug('Deleting items...')
        self.undo_stack.push(
            commands.DeleteItems(self.scene, self.scene.selectedItems()))

    def on_action_normalize_height(self):
        self.scene.normalize_height()

    def on_action_normalize_width(self):
        self.scene.normalize_width()

    def on_action_normalize_size(self):
        self.scene.normalize_size()

    def on_action_flip_horizontally(self):
        self.scene.flip_items(vertical=False)

    def on_action_flip_vertically(self):
        self.scene.flip_items(vertical=True)

    def on_action_reset_scale(self):
        self.undo_stack.push(commands.ResetScale(
            self.scene.selectedItems()))

    def on_action_reset_rotation(self):
        self.undo_stack.push(commands.ResetRotation(
            self.scene.selectedItems()))

    def on_action_reset_flip(self):
        self.undo_stack.push(commands.ResetFlip(
            self.scene.selectedItems()))

    def on_action_reset_transforms(self):
        self.undo_stack.push(commands.ResetTransforms(
            self.scene.selectedItems()))

    def on_items_loaded(self, value):
        self.scene.add_delayed_items()

    def on_loading_finished(self, filename, errors):
        if filename:
            self.filename = filename
        if errors:
            QtWidgets.QMessageBox.warning(
                self,
                'Problem loading file',
                ('<p>Problem loading file %s</p>'
                 '<p>Not accessible or not a proper bee file</p>') % filename)
        else:
            self.on_action_fit_scene()

    def open_from_file(self, filename):
        logger.info(f'Opening file {filename}')
        self.clear_scene()
        self.worker = fileio.ThreadedIO(
            fileio.load_bee, filename, self.scene)
        self.worker.progress.connect(self.on_items_loaded)
        self.worker.finished.connect(self.on_loading_finished)
        self.progress = BeeProgressDialog(
            'Loading %s' % filename,
            worker=self.worker,
            parent=self)
        self.worker.start()

    def on_action_open(self):
        filename, f = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='Open file',
            filter='BeeRef File (*.bee)')
        if filename:
            self.open_from_file(filename)
            self.filename = filename

    def on_saving_finished(self, filename, errors):
        if filename:
            self.filename = filename
        else:
            QtWidgets.QMessageBox.warning(
                self,
                'Problem saving file',
                ('<p>Problem saving file %s</p>'
                 '<p>File/directory not accessible</p>') % filename)

    def do_save(self, filename, create_new):
        if not filename.endswith('.bee'):
            filename = f'{filename}.bee'
        self.worker = fileio.ThreadedIO(
            fileio.save_bee, filename, self.scene, create_new=create_new)
        self.worker.finished.connect(self.on_saving_finished)
        self.progress = BeeProgressDialog(
            'Saving %s' % filename,
            worker=self.worker,
            parent=self)
        self.worker.start()

    def on_action_save_as(self):
        filename, f = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption='Save file',
            filter='BeeRef File (*.bee)')
        if filename:
            self.do_save(filename, create_new=True)

    def on_action_save(self):
        if not self.filename:
            self.on_action_save_as()
        else:
            self.do_save(self.filename, create_new=False)

    def on_action_quit(self):
        logger.info('User quit. Exiting...')
        self.app.quit()

    def on_insert_images_finished(self, filename, errors):
        if errors:
            errornames = [
                f'<li>{fn}</li>' for fn in errors]
            errornames = '<ul>%s</ul>' % '\n'.join(errornames)
            msg = ('{errors} image(s) out of {total} '
                   'could not be opened:'.format(
                       errors=len(errors), total=len(errors)))
            QtWidgets.QMessageBox.warning(
                self,
                'Problem loading images',
                msg + errornames)

    def on_action_insert_images(self):
        formats = self.get_supported_image_formats(QtGui.QImageReader)
        filenames, f = QtWidgets.QFileDialog.getOpenFileNames(
            parent=self,
            caption='Select one ore more images to open',
            filter=f'Images ({formats})')

        self.scene.clearSelection()
        self.worker = fileio.ThreadedIO(
            fileio.load_images,
            filenames,
            self.mapToScene(self.get_view_center()),
            self.scene)
        self.worker.progress.connect(self.on_items_loaded)
        self.worker.finished.connect(self.on_insert_images_finished)
        self.progress = BeeProgressDialog(
            'Loading images',
            worker=self.worker,
            parent=self)
        self.worker.start()

    def on_action_paste(self):
        logger.info('Pasting from clipboard...')
        clipboard = QtWidgets.QApplication.clipboard()
        img = clipboard.image()
        if img.isNull():
            logger.info('No image data in clipboard')
        else:
            item = BeePixmapItem(img)
            pos = self.mapToScene(self.mapFromGlobal(self.cursor().pos()))
            item.set_pos_center(pos)
            self.undo_stack.push(commands.InsertItems(self.scene, [item]))

    def on_selection_changed(self):
        logger.debug('Currently selected items: %s',
                     len(self.scene.selectedItems()))
        self.actiongroup_set_enabled('active_when_selection',
                                     self.scene.has_selection())
        self.viewport().repaint()

    def recalc_scene_rect(self):
        """Resize the scene rectangle so that it is always one view width
        wider than all items' bounding box at each side and one view
        width higher on top and bottom. This gives the impression of
        an infinite canvas."""

        logger.debug('Recalculating scene rectangle...')
        try:
            topleft = self.mapFromScene(
                self.scene.itemsBoundingRect().topLeft())
            topleft = self.mapToScene(QtCore.QPoint(
                topleft.x() - self.size().width(),
                topleft.y() - self.size().height()))
            bottomright = self.mapFromScene(
                self.scene.itemsBoundingRect().bottomRight())
            bottomright = self.mapToScene(QtCore.QPoint(
                bottomright.x() + self.size().width(),
                bottomright.y() + self.size().height()))
            self.setSceneRect(QtCore.QRectF(topleft, bottomright))
        except OverflowError:
            logger.info('Maximum scene size reached')

    def get_zoom_size(self, func):
        """Calculates the size of all items' bounding box in the view's
        coordinates.

        This helps ensure that we never zoom out too much (scene
        becomes so tiny that items become invisible) or zoom in too
        much (causing overflow errors).

        :param func: Function which takes the width and height as
        arguments and turns it into a number, for ex. ``min`` or ``max``.
        """

        topleft = self.mapFromScene(
            self.scene.itemsBoundingRect().topLeft())
        bottomright = self.mapFromScene(
            self.scene.itemsBoundingRect().bottomRight())
        return func(bottomright.x() - topleft.x(),
                    bottomright.y() - topleft.y())

    def scale(self, *args, **kwargs):
        super().scale(*args, **kwargs)
        self.scene.on_view_scale_change()
        self.recalc_scene_rect()

    def get_scale(self):
        return self.transform().m11()

    def wheelEvent(self, event):
        if not self.scene.items():
            logger.debug('No items in scene; ignore zoom')
            return
        factor = 1.2
        if event.angleDelta().y() > 0:
            if self.get_zoom_size(max) < 10000000:
                self.scale(factor, factor)
            else:
                logger.debug('Maximum zoom size reached')
        else:
            if self.get_zoom_size(min) > 50:
                self.scale(1/factor, 1/factor)
            else:
                logger.debug('Minimum zoom size reached')
        event.accept()

    def mouseMoveEvent(self, event):
        if self.pan_active:
            self.reset_previous_transform()
            point = event.position()
            hscroll = self.horizontalScrollBar()
            hscroll.setValue(hscroll.value() + self.pan_start.x() - point.x())
            vscroll = self.verticalScrollBar()
            vscroll.setValue(vscroll.value() + self.pan_start.y() - point.y())
            self.pan_start = point
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if (event.button() == Qt.MouseButtons.MiddleButton
            or (event.button() == Qt.MouseButtons.LeftButton
                and event.modifiers() == Qt.KeyboardModifiers.AltModifier)):
            if not self.scene.items():
                logger.debug('No items in scene; ignore pan')
                return

            self.pan_active = True
            self.pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.pan_active:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.pan_active = False
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.recalc_scene_rect()
        self.welcome_overlay.resize(self.size())

    def dragEnterEvent(self, event):
        logger.debug('Received drag enter event')

        # tbd: always empty???
        print(event.mimeData().formats())
        print(dir(event))
        if event.mimeData().hasImage():
            event.acceptProposedAction()
        else:
            logger.info('Attempted drop not an image')

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        logger.info('Handling file drop...')
        print(event.mimeData().formats())
        # tbd
