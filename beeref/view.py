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

from beeref import commands
from beeref import fileio
from beeref.gui import BeeProgressDialog, WelcomeOverlay
from beeref.items import BeePixmapItem
from beeref.scene import BeeGraphicsScene

logger = logging.getLogger('BeeRef')


class BeeGraphicsView(QtWidgets.QGraphicsView):

    def __init__(self, app, parent=None, filename=None):
        super().__init__(parent)
        self.app = app
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(60, 60, 60)))

        self.undo_stack = QtGui.QUndoStack(self)
        self.undo_stack.setUndoLimit(10)
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

        # TBD: fix zoom anchor - why does this not work?
        # self.setTransformationAnchor(
        #     QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.pan_active = False
        self.scene.changed.connect(self.on_scene_changed)
        self.scene.selectionChanged.connect(self.on_selection_changed)

        self.setScene(self.scene)

        # Context menu and actions
        self.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)
        self.context_menu = QtWidgets.QMenu(self)
        self.build_actions()

        self.welcome_overlay = WelcomeOverlay(self)

        # Load file given via command line
        if filename:
            self.open_from_file(filename)

    def on_scene_changed(self, region):
        if not self.scene.items():
            logger.info('No items in scene')
            self.welcome_overlay.show()
        else:
            self.welcome_overlay.hide()
        self.recalc_scene_rect()

    def build_actions(self):

        self.actions_active_when_selection = []
        self.actions_active_when_can_undo = []
        self.actions_active_when_can_redo = []

        def add_to_menu(menu, actions):
            for action in actions:
                qaction = QtGui.QAction(action['text'], self)
                if 'shortcuts' in action:
                    qaction.setShortcuts(action['shortcuts'])
                qaction.triggered.connect(action['callback'])
                self.addAction(qaction)
                menu.addAction(qaction)
                if 'group' in action:
                    action['group'].append(qaction)
                qaction.setEnabled(action.get('enabled', True))

        # File menu
        actions = [
            {
                'text': '&Open',
                'shortcuts': ['Ctrl+O'],
                'callback': self.on_action_open,
            },
            {
                'text': '&Save',
                'shortcuts': ['Ctrl+S'],
                'callback': self.on_action_save,
            },
            {
                'text': 'Save &As...',
                'shortcuts': ['Ctrl+Shift+S'],
                'callback': self.on_action_save_as,
            },
            {
                'text': '&Quit...',
                'shortcuts': ['Ctrl+Q'],
                'callback': self.on_action_quit,
            },
        ]
        add_to_menu(self.context_menu.addMenu('&File'), actions)

        # Main menu
        actions = [
            {
                'text': '&Insert Images...',
                'shortcuts': ['Ctrl+I'],
                'callback': self.on_action_insert_images,
            },

        ]
        add_to_menu(self.context_menu, actions)

        # Edit menu
        actions = [
            {
                'text': '&Undo',
                'shortcuts': ['Ctrl+Z'],
                'callback': self.on_action_undo,
                'group': self.actions_active_when_can_undo,
                'enabled': False,
            },
            {
                'text': '&Redo',
                'shortcuts': ['Ctrl+Shift+Z'],
                'callback': self.on_action_redo,
                'group': self.actions_active_when_can_redo,
                'enabled': False,
            },
            {
                'text': '&Paste',
                'shortcuts': ['Ctrl+V'],
                'callback': self.on_action_paste,
            },
            {
                'text': '&Delete',
                'shortcuts': ['Del'],
                'callback': self.on_action_delete_items,
                'group': self.actions_active_when_selection,
                'enabled': False,
            },
        ]
        add_to_menu(self.context_menu.addMenu('&Edit'), actions)

        items_menu = self.context_menu.addMenu('&Items')
        actions = [
            {
                'text': '&Height',
                'shortcuts': ['Shift+H'],
                'callback': self.on_action_normalize_height,
                'group': self.actions_active_when_selection,
                'enabled': False,
            },
            {
                'text': '&Width',
                'shortcuts': ['Shift+W'],
                'callback': self.on_action_normalize_width,
                'group': self.actions_active_when_selection,
                'enabled': False,
            },
            {
                'text': '&Size',
                'shortcuts': ['Shift+S'],
                'callback': self.on_action_normalize_size,
                'group': self.actions_active_when_selection,
                'enabled': False,
            },
        ]
        add_to_menu(items_menu.addMenu('&Normalize'), actions)

    def on_can_redo_changed(self, can_redo):
        for action in self.actions_active_when_can_redo:
            action.setEnabled(can_redo)

    def on_can_undo_changed(self, can_undo):
        for action in self.actions_active_when_can_undo:
            action.setEnabled(can_undo)

    def on_context_menu(self, point):
        self.context_menu.exec(self.mapToGlobal(point))

    def get_supported_image_formats(self, cls):
        formats = map(lambda f: f'*.{f.data().decode()}',
                      cls.supportedImageFormats())
        return ' '.join(formats)

    def get_view_center(self):
        return QtCore.QPoint(self.size().width() / 2,
                             self.size().height() / 2)

    def on_action_undo(self):
        logger.debug('Undo: %s' % self.undo_stack.undoText())
        self.undo_stack.undo()

    def on_action_redo(self):
        logger.debug('Redo: %s' % self.undo_stack.redoText())
        self.undo_stack.redo()

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

    def open_from_file(self, filename):
        logger.info(f'Opening file {filename}')
        self.scene.clear()
        self.undo_stack.clear()
        try:
            progress = BeeProgressDialog(
                'Loading %s' % filename,
                parent=self)
            fileio.load(filename, self.scene, progress)
            self.filename = filename
        except fileio.BeeFileIOError:
            QtWidgets.QMessageBox.warning(
                self,
                'Problem loading file',
                ('<p>Problem loading file %s</p>'
                 '<p>Not accessible or not a proper bee file</p>') % filename)

    def on_action_open(self):
        filename, f = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='Open file',
            filter='BeeRef File (*.bee)')
        if filename:
            self.open_from_file(filename)
            self.filename = filename

    def on_action_save_as(self):
        filename, f = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption='Save file',
            filter='BeeRef File (*.bee)')
        if filename:
            if not filename.endswith('.bee'):
                filename = f'{filename}.bee'
            try:
                progress = BeeProgressDialog(
                    'Saving %s' % filename,
                    parent=self)
                fileio.save(filename, self.scene, create_new=True,
                            progress=progress)
                self.filename = filename
            except fileio.BeeFileIOError:
                QtWidgets.QMessageBox.warning(
                    self,
                    'Problem saving file',
                    ('<p>Problem saving file %s</p>'
                     '<p>File/directory not accessible</p>') % filename)

    def on_action_save(self):
        if not self.filename:
            self.on_action_save_as()
        else:
            progress = BeeProgressDialog(
                'Saving %s' % self.filename,
                parent=self)
            fileio.save(self.filename, self.scene, create_new=False,
                        progress=progress)

    def on_action_quit(self):
        logger.info('User quit. Exiting...')
        self.app.quit()

    def on_action_insert_images(self):
        formats = self.get_supported_image_formats(QtGui.QImageReader)
        filenames, f = QtWidgets.QFileDialog.getOpenFileNames(
            parent=self,
            caption='Select one ore more images to open',
            filter=f'Images ({formats})')

        pos = self.mapToScene(self.get_view_center())
        errors = []
        items = []

        progress = BeeProgressDialog(
            'Loading images...', len(filenames), parent=self)

        for i, filename in enumerate(filenames):
            logger.info(f'Loading image from file {filename}')
            img = QtGui.QImage(filename)
            progress.setValue(i)
            if progress.wasCanceled():
                break
            if img.isNull():
                errors.append(filename)
                continue
            item = BeePixmapItem(img, filename)
            item.set_pos_center(pos.x(), pos.y())
            items.append(item)
            pos.setX(pos.x() + 50)
            pos.setY(pos.y() + 50)

        self.undo_stack.push(commands.InsertItems(self.scene, items))

        if errors:
            errornames = [
                f'<li>{fn}</li>' for fn in errors]
            errornames = '<ul>%s</ul>' % '\n'.join(errornames)
            msg = ('{errors} image(s) out of {total} '
                   'could not be opened:'.format(
                       errors=len(errors), total=len(filenames)))
            QtWidgets.QMessageBox.warning(
                self,
                'Problem loading images',
                msg + errornames)

    def on_action_paste(self):
        logger.info('Pasting from clipboard...')
        clipboard = QtWidgets.QApplication.clipboard()
        img = clipboard.image()
        if img.isNull():
            logger.info('No image data in clipboard')
        else:
            self.scene.clearSelection()
            item = BeePixmapItem(img)
            pos = self.mapToScene(self.mapFromGlobal(self.cursor().pos()))
            item.set_pos_center(pos.x(), pos.y())
            self.undo_stack.push(commands.InsertItems(self.scene, [item]))

    def on_selection_changed(self):
        logger.debug('Currently selected items: %s',
                     len(self.scene.selectedItems()))
        for action in self.actions_active_when_selection:
            action.setEnabled(self.scene.has_selection())
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
        self.recalc_scene_rect()
        self.scene.update_selection()

    def get_scale(self):
        return self.transform().m11()

    def wheelEvent(self, event):
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
