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
import os
import os.path

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref import constants
from beeref import fileio
from beeref.assets import BeeAssets
from beeref.config import BeeSettings
from beeref.main_controls import MainControlsMixin


logger = logging.getLogger(__name__)


class RecentFilesModel(QtCore.QAbstractListModel):
    """An entry in the 'Recent Files' list."""

    def __init__(self, files):
        super().__init__()
        self.files = files

    def rowCount(self, parent):
        return len(self.files)

    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return os.path.basename(self.files[index.row()])
        if role == QtCore.Qt.ItemDataRole.FontRole:
            font = QtGui.QFont()
            font.setUnderline(True)
            return font


class RecentFilesView(QtWidgets.QListView):

    def __init__(self, parent, view, files=None):
        super().__init__(parent)
        self.view = view
        self.files = files or []
        self.clicked.connect(self.on_clicked)
        self.setModel(RecentFilesModel(self.files))
        self.setMouseTracking(True)

    def on_clicked(self, index):
        self.view.open_from_file(self.files[index.row()])

    def update_files(self, files):
        self.files = files or []
        self.setModel(RecentFilesModel(self.files))
        self.updateGeometry()

    def sizeHint(self):
        size = QtCore.QSize()
        if not self.files:
            return size
        height = sum(
            (self.sizeHintForRow(i) + 2) for i in range(len(self.files)))
        width = max(self.sizeHintForColumn(i) for i in range(len(self.files)))
        size.setHeight(height)
        size.setWidth(width + 2)
        return size

    def mouseMoveEvent(self, event):
        index = self.indexAt(
            QtCore.QPoint(int(event.position().x()),
                          int(event.position().y())))
        if index.isValid():
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        super().mouseMoveEvent(event)


class WelcomeOverlay(MainControlsMixin, QtWidgets.QWidget):
    """Some basic info to be displayed when the scene is empty."""

    def __init__(self, parent):
        super().__init__(parent)
        self.control_target = parent
        self.setAutoFillBackground(True)
        self.init_main_controls(main_window=parent.parent)

        # Icon
        icon_path = BeeAssets.PATH.joinpath('icons','drag-and-drop.svg')
        icon_pixmap = QtGui.QPixmap(str(icon_path))
        self.icon_label = QtWidgets.QLabel(self)
        self.icon_label.setPixmap(icon_pixmap)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet(constants.get_welcome_overlay_icon_style())

        # Help text
        self.label = QtWidgets.QLabel('<p>Paste or drop images here.</p>', self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter
                                | Qt.AlignmentFlag.AlignCenter)

        # Right-click text
        self.right_click_label = QtWidgets.QLabel('<p>Right-click for more options.</p>', self)
        self.right_click_label.setAlignment(Qt.AlignmentFlag.AlignVCenter
                                          | Qt.AlignmentFlag.AlignCenter)

        # Browse button
        self.browse_button = QtWidgets.QPushButton('Browse', self)
        self.browse_button.setStyleSheet(constants.get_standard_button_style())
        self.browse_button.clicked.connect(self.on_browse_clicked)

        # Recent files
        self.files_view = RecentFilesView(self, parent)
        self.files_widget = QtWidgets.QWidget(self)
        files_layout = QtWidgets.QVBoxLayout()
        files_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.recent_files_label = QtWidgets.QLabel('<h3>Recent Files</h3>', self)
        self.recent_files_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        files_layout.addWidget(self.recent_files_label)
        files_layout.addWidget(self.files_view)
        self.files_widget.setLayout(files_layout)
        self.files_widget.hide()

        # Center content widget
        center_widget = QtWidgets.QWidget(self)
        center_layout = QtWidgets.QVBoxLayout()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addStretch()
        center_layout.addWidget(self.icon_label)
        center_layout.addWidget(self.label)
        center_layout.addWidget(self.right_click_label)
        center_layout.addWidget(self.browse_button)
        center_layout.setAlignment(self.browse_button, Qt.AlignmentFlag.AlignHCenter)
        center_layout.addWidget(self.files_widget)
        center_layout.addStretch()
        center_widget.setLayout(center_layout)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addStretch()
        self.layout.addWidget(center_widget)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def show(self):
        files = BeeSettings().get_recent_files(existing_only=True)
        self.files_view.update_files(files)
        self.files_widget.setVisible(bool(files))
        super().show()

    def disable_mouse_events(self):
        self.icon_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.right_click_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.browse_button.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.files_view.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.files_widget.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def enable_mouse_events(self):
        self.icon_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            on=False)
        self.label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            on=False)
        self.right_click_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            on=False)
        self.browse_button.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            on=False)
        self.files_view.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            on=False)
        self.files_widget.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            on=False)

    def mousePressEvent(self, event):
        if self.mousePressEventMainControls(event):
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.mouseMoveEventMainControls(event):
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.mouseReleaseEventMainControls(event):
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if self.keyPressEventMainControls(event):
            return
        super().keyPressEvent(event)

    def on_browse_clicked(self):
        """Open file dialog to select .bee files or images."""
        if not hasattr(self.control_target, 'get_supported_image_formats'):
            return
        
        # Get supported image formats
        formats = self.control_target.get_supported_image_formats(QtGui.QImageReader)
        
        # Create filter string for file dialog
        # First option: All supported files (bee + images)
        all_formats = f'*.bee {formats}'
        filter_str = ';;'.join((
            f'All Supported Files ({all_formats})',
            f'{constants.APPNAME} File (*.bee)',
            f'Images ({formats})',
            'All Files (*)'
        ))
        
        # Open file dialog allowing multiple selection
        filenames, selected_filter = QtWidgets.QFileDialog.getOpenFileNames(
            parent=self,
            caption='Open file or images',
            filter=filter_str)
        
        if not filenames:
            return
        
        # Check if any selected file is a .bee file
        bee_files = [f for f in filenames if fileio.is_bee_file(f)]
        image_files = [f for f in filenames if not fileio.is_bee_file(f)]
        
        # If we have .bee files, open the first one (clear scene first)
        if bee_files:
            if hasattr(self.control_target, 'get_confirmation_unsaved_changes'):
                confirm = self.control_target.get_confirmation_unsaved_changes(
                    'There are unsaved changes. '
                    'Are you sure you want to open a new scene?')
                if not confirm:
                    return
            
            if hasattr(self.control_target, 'open_from_file'):
                filename = os.path.normpath(bee_files[0])
                self.control_target.open_from_file(filename)
                self.control_target.filename = filename
                # If there are also image files, add them after opening .bee
                if image_files and hasattr(self.control_target, 'do_insert_images'):
                    self.control_target.do_insert_images(image_files)
            return
        
        # If only images, insert them
        if image_files and hasattr(self.control_target, 'do_insert_images'):
            self.control_target.do_insert_images(image_files)
