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

from PyQt6 import QtGui


class InsertImages(QtGui.QUndoCommand):

    def __init__(self, scene, items):
        super().__init__('Insert images')
        self.scene = scene
        self.items = items

    def redo(self):
        self.scene.clearSelection()
        for item in self.items:
            item.setSelected(True)
            self.scene.addItem(item)

    def undo(self):
        self.scene.clearSelection()
        for item in self.items:
            self.scene.removeItem(item)


class DeleteSelectedItems(QtGui.QUndoCommand):

    def __init__(self, scene):
        super().__init__('Delete images')
        self.scene = scene
        self.items = []

    def redo(self):
        for item in self.scene.selectedItems():
            self.items.append(item)
            self.scene.removeItem(item)

    def undo(self):
        self.scene.clearSelection()
        for item in self.items:
            item.setSelected(True)
            self.scene.addItem(item)
