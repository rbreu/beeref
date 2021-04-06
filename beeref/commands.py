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


class InsertItems(QtGui.QUndoCommand):

    def __init__(self, scene, items):
        super().__init__('Insert items')
        self.scene = scene
        self.items = items

    def redo(self):
        self.scene.clearSelection()
        for item in self.items:
            self.scene.addItem(item)
            item.setSelected(True)

    def undo(self):
        self.scene.clearSelection()
        for item in self.items:
            self.scene.removeItem(item)


class DeleteItems(QtGui.QUndoCommand):

    def __init__(self, scene, items):
        super().__init__('Delete items')
        self.scene = scene
        self.items = items

    def redo(self):
        for item in self.items:
            self.scene.removeItem(item)

    def undo(self):
        self.scene.clearSelection()
        for item in self.items:
            item.setSelected(True)
            self.scene.addItem(item)


class MoveItemsBy(QtGui.QUndoCommand):

    def __init__(self, items, delta, ignore_first_redo=False):
        super().__init__('Move items')
        self.items = items
        self.delta = delta
        self.ignore_first_redo = ignore_first_redo

    def redo(self):
        if self.ignore_first_redo:
            self.ignore_first_redo = False
            return
        for item in self.items:
            item.moveBy(self.delta.x(), self.delta.y())

    def undo(self):
        for item in self.items:
            item.moveBy(-self.delta.x(), -self.delta.y())


class ScaleItemsBy(QtGui.QUndoCommand):
    """Scale items by a given factor around the given anchor."""

    def __init__(self, items, factor, anchor, ignore_first_redo=False):
        super().__init__('Scale items')
        self.ignore_first_redo = ignore_first_redo
        self.items = items
        self.factor = factor
        self.anchor = anchor

    def redo(self):
        if self.ignore_first_redo:
            self.ignore_first_redo = False
            return
        for item in self.items:
            item.setScale(item.scale() * self.factor,
                          item.mapFromScene(self.anchor))

    def undo(self):
        for item in self.items:
            item.setScale(item.scale() / self.factor,
                          item.mapFromScene(self.anchor))


class RotateItemsBy(QtGui.QUndoCommand):
    """Rotate items by a given delta around the given anchor."""

    def __init__(self, items, delta, anchor, ignore_first_redo=False):
        super().__init__('Scale items')
        self.ignore_first_redo = ignore_first_redo
        self.items = items
        self.delta = delta
        self.anchor = anchor

    def redo(self):
        if self.ignore_first_redo:
            self.ignore_first_redo = False
            return
        for item in self.items:
            item.setRotation(item.rotation() + self.delta,
                             item.mapFromScene(self.anchor))

    def undo(self):
        for item in self.items:
            item.setRotation(item.rotation() - self.delta,
                             item.mapFromScene(self.anchor))


class NormalizeItems(QtGui.QUndoCommand):

    def __init__(self, items, scale_factors):
        super().__init__('Normalize items')
        self.items = items
        self.scale_factors = scale_factors

    def redo(self):
        self.old_scale_factors = []
        for item, factor in zip(self.items, self.scale_factors):
            self.old_scale_factors.append(item.scale())
            item.setScale(factor)

    def undo(self):
        for item, factor in zip(self.items, self.old_scale_factors):
            item.setScale(factor)
