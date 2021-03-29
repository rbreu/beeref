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

from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt


logger = logging.getLogger('BeeRef')


class WelcomeOverlay(QtWidgets.QWidget):
    """Some basic info to be displayed when the scene is empty."""

    txt = """<p>Paste or drop images here.</p>
             <p>Right-click for more options.</p>"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label = QtWidgets.QLabel(self)
        label.setStyleSheet("QLabel { color: #cccccc; }")
        label.setText(self.txt)
        label.setAlignment(Qt.Alignment.AlignVCenter
                           | Qt.Alignment.AlignCenter)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)


class BeeProgressDialog(QtWidgets.QProgressDialog):

    def __init__(self, label, maximum=100, parent=None):
        super().__init__(label, 'Cancel', 0, maximum, parent=parent)
        self.setMinimumDuration(2)
        self.setWindowModality(Qt.WindowModality.WindowModal)

    def setValue(self, value):
        super().setValue(value + 1)
