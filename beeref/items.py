import base64
import logging

from PyQt6 import QtCore, QtGui, QtWidgets

from beeref.selection import SelectionItem


logger = logging.getLogger('BeeRef')


class BeePixmapItem(QtWidgets.QGraphicsPixmapItem):

    def __init__(self, image, filename=None):
        super().__init__(QtGui.QPixmap.fromImage(image))
        logger.debug(f'Initialized image "{filename}" with dimensions: '
                     f'{self.width} x {self.height} at index {self.zValue()}')

        self.filename = filename
        self.scale_factor = 1
        self.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsMovable
            | QtWidgets.QGraphicsItem.GraphicsItemFlags.ItemIsSelectable)

    def setScale(self, factor):
        self.scale_factor = factor
        logger.debug(f'Setting scale for image "{self.filename}" to {factor}')
        super().setScale(factor)

    def set_pos_center(self, x, y):
        """Sets the position using the item's center as the origin point."""

        self.setPos(x - self.width * self.scale_factor / 2,
                    y - self.height * self.scale_factor / 2)

    @property
    def width(self):
        return self.pixmap().size().width()

    @property
    def height(self):
        return self.pixmap().size().height()

    def pixmap_to_str(self):
        barray = QtCore.QByteArray()
        buffer = QtCore.QBuffer(barray)
        buffer.open(QtCore.QIODevice.OpenMode.WriteOnly)
        img = self.pixmap().toImage()
        img.save(buffer, 'PNG')
        data = base64.b64encode(barray.data())
        return data.decode('ascii')

    @classmethod
    def qimage_from_str(self, data):
        img = QtGui.QImage()
        img.loadFromData(base64.b64decode(data))
        return img

    def to_bee_json(self):
        return {
            'cls': self.__class__.__name__,
            'scale': self.scale_factor,
            'pixmap': self.pixmap_to_str(),
            'pos': [self.pos().x(), self.pos().y()],
            'z': self.zValue(),
            'filename': self.filename,
        }

    @classmethod
    def from_bee_json(cls, obj):
        img = cls.qimage_from_str(obj['pixmap'])
        item = cls(img, filename=obj.get('filename'))
        if 'scale' in obj:
            item.setScale(obj['scale'])
        if 'pos' in obj:
            item.setPos(*obj['pos'])
        if 'z' in obj:
            item.setZValue(obj['z'])

        return item

    def create_selection(self):
        SelectionItem(self)

    def clear_selection(self):
        for child in self.childItems():
            logger.debug('Removing child item...')
            self.scene().removeItem(child)
            logger.debug('Child item removed')

    def itemChange(self, change, value):
        ret = super().itemChange(change, value)

        if change == self.GraphicsItemChange.ItemSelectedChange:
            if value:
                logger.debug('Item selected')
                self.create_selection()
            else:
                logger.debug('Item deselected')
                self.clear_selection()

        return ret

    def mousePressEvent(self, event):
        print('????')

    def sceneEvent(self, event):
        print('********', event)
        return super().sceneEvent(event)
