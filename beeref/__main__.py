#!/usr/bin/env python3

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
import signal
import sys

from PyQt6 import QtCore, QtGui, QtWidgets

from beeref.view import BeeGraphicsView


logger = logging.getLogger('BeeRef')


class BeeRefMainWindow(QtWidgets.QWidget):

    def __init__(self, app, filename=None):
        super().__init__()
        self.setWindowTitle('BeeRef')
        root = os.path.dirname(__file__)
        logo = os.path.join(root, 'assets', 'logo.png')
        logger.debug(f'Loading icon {logo}')
        self.setWindowIcon(QtGui.QIcon(logo))
        view = BeeGraphicsView(app, self, filename)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))
        layout.addWidget(view)
        self.setLayout(layout)
        self.resize(500, 300)
        self.show()


def safe_timer(timeout, func, *args, **kwargs):
    """Create a timer that is safe against garbage collection and
    overlapping calls.
    See: http://ralsina.me/weblog/posts/BB974.html
    """
    def timer_event():
        try:
            func(*args, **kwargs)
        finally:
            QtCore.QTimer.singleShot(timeout, timer_event)
    QtCore.QTimer.singleShot(timeout, timer_event)


def handle_sigint(signum, frame):
    logger.info('Received interrupt. Exiting...')
    QtWidgets.QApplication.quit()


def main():
    logger = logging.getLogger('BeeRef')
    logging.basicConfig(level=logging.DEBUG)
    app = QtWidgets.QApplication(sys.argv)

    filename = sys.argv[1] if len(sys.argv) > 1 else None
    bee = BeeRefMainWindow(app, filename)

    signal.signal(signal.SIGINT, handle_sigint)
    # Repeatedly run python-noop to give the interpreter time to
    # handel signals
    safe_timer(50, lambda: None)

    app.exec()


if __name__ == '__main__':
    main()
