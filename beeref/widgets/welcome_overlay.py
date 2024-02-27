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
import os.path

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

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
        self.files = files
        self.model().files = files
        self.reset()

    def sizeHint(self):
        size = QtCore.QSize()
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

    txt = """<p>Paste or drop images here.</p>
             <p>Right-click for more options.</p>"""

    def __init__(self, parent):
        super().__init__(parent)
        self.control_target = parent
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.init_main_controls(main_window=parent.parent)

        # Recent files
        self.files_widget = QtWidgets.QWidget(self)
        files_layout = QtWidgets.QVBoxLayout()
        files_layout.addStretch(50)
        files_layout.addWidget(
            QtWidgets.QLabel('<h3>Recent Files</h3>', self))
        self.files_view = RecentFilesView(self, parent)
        files_layout.addWidget(self.files_view)
        files_layout.addStretch(50)
        self.files_widget.setLayout(files_layout)
        self.files_widget.hide()

        # Help text
        self.label = QtWidgets.QLabel(self.txt, self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter
                                | Qt.AlignmentFlag.AlignCenter)
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addStretch(50)
        self.layout.addWidget(self.label)
        self.layout.addStretch(50)
        self.setLayout(self.layout)

    def show(self):
        files = BeeSettings().get_recent_files(existing_only=True)
        self.files_view.update_files(files)
        if files and self.layout.indexOf(self.files_widget) < 0:
            self.layout.insertWidget(0, self.files_widget)
            self.files_widget.show()
        super().show()

    def disable_mouse_events(self):
        self.files_view.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def enable_mouse_events(self):
        self.files_view.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            on=False)
        self.label.setAttribute(
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
