import logging

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt


logger = logging.getLogger('BeeRef')


class WelcomeOverlay(QtWidgets.QWidget):

    txt = """<p>Paste or drop images here.</p>
             <p>Right-click for more options.</p>"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label = QtWidgets.QLabel(self)
        label.setText(self.txt)
        label.setAlignment(Qt.Alignment.AlignVCenter | Qt.Alignment.AlignCenter)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)
