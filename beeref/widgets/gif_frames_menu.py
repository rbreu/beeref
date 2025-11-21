"""Floating menu showing GIF frames timeline."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from PyQt6 import QtCore, QtGui, QtWidgets

from beeref import constants

if TYPE_CHECKING:  # pragma: no cover
    from beeref.view import BeeGraphicsView
    from beeref.gif_item import BeeGifItem

logger = logging.getLogger(__name__)


class GifFrameThumbnail(QtWidgets.QWidget):
    """Widget for displaying a single GIF frame."""
    
    FRAME_SIZE = 96  # Thumbnail size
    
    def __init__(self, frame_number: int, pixmap: QtGui.QPixmap, 
                 delay_ms: int, frames_menu: "GifFramesMenu", parent=None):
        super().__init__(parent)
        self.frame_number = frame_number
        self.pixmap = pixmap
        self.delay_ms = delay_ms
        self.is_selected = False
        self.frames_menu = frames_menu  # Keep reference to frames menu
        
        self.setFixedSize(self.FRAME_SIZE + 8, self.FRAME_SIZE + 24)
        self.setToolTip(f"Frame: {frame_number}\nDelay: {delay_ms / 1000:.2f}s")
        self.drag_start_position = None
        self.is_dragging = False
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform)
        
        # Selection border
        if self.is_selected:
            pen = QtGui.QPen(QtGui.QColor(*constants.COLORS['Scene:Selection']))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.setBrush(QtGui.QBrush())
            painter.drawRect(2, 2, self.FRAME_SIZE + 4, self.FRAME_SIZE + 4)
        
        # Frame thumbnail
        scaled_pixmap = self.pixmap.scaled(
            self.FRAME_SIZE, self.FRAME_SIZE,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation
        )
        x = (self.width() - scaled_pixmap.width()) // 2
        y = 4
        painter.drawPixmap(x, y, scaled_pixmap)
        
        # Frame number
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        text_rect = QtCore.QRect(0, self.FRAME_SIZE + 8, self.width(), 16)
        painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignCenter, 
                        str(self.frame_number))
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Save drag start position
            self.drag_start_position = event.position().toPoint()
            self.is_dragging = False
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handles start of frame dragging."""
        if not (event.buttons() & QtCore.Qt.MouseButton.LeftButton):
            return
        
        if self.drag_start_position is None:
            return
        
        # Check if mouse moved enough to start drag
        if ((event.position().toPoint() - self.drag_start_position).manhattanLength() 
                < QtWidgets.QApplication.startDragDistance()):
            return
        
        # Mark that dragging has started
        self.is_dragging = True
        
        # Create QDrag object
        drag = QtGui.QDrag(self)
        mime_data = QtCore.QMimeData()
        
        # Convert pixmap to QImage for drag transfer
        image = self.pixmap.toImage()
        mime_data.setImageData(image)
        
        drag.setMimeData(mime_data)
        
        # Set visual representation during drag
        # Use original pixmap but scaled down for preview
        preview_pixmap = self.pixmap.scaled(
            128, 128,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation
        )
        drag.setPixmap(preview_pixmap)
        drag.setHotSpot(event.position().toPoint() - self.drag_start_position)
        
        # Start drag operation
        drag.exec(QtCore.Qt.DropAction.CopyAction)
        
        # Reset state after drag completion
        self.drag_start_position = None
        self.is_dragging = False
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handles frame click (if no dragging occurred)."""
        if (event.button() == QtCore.Qt.MouseButton.LeftButton 
                and not self.is_dragging 
                and self.drag_start_position is not None):
            # If no dragging occurred, select frame
            if self.frames_menu:
                self.frames_menu.select_frame(self.frame_number)
        
        self.drag_start_position = None
        self.is_dragging = False
        super().mouseReleaseEvent(event)


class GifFramesMenu(QtWidgets.QWidget):
    """Floating menu with GIF frames."""
    
    def __init__(self, parent: QtWidgets.QWidget, view: "BeeGraphicsView",
                 gif_menu: "GifFloatingMenu"):
        # Create as independent window to match gif_floating_menu
        super().__init__(None)
        self.setObjectName("GifFramesMenu")
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        # Make it a tool window that stays on top
        self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(QtCore.Qt.WindowType.Tool, True)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, True)
        # Store parent for compatibility
        self._parent_widget = parent
        self.view = view
        self.gif_menu = gif_menu
        self.current_item: Optional["BeeGifItem"] = None
        
        # Cache for update_position optimization
        self._cached_position: Optional[QtCore.QPoint] = None
        self._cached_viewport_size: Optional[QtCore.QSize] = None
        self._cached_gif_menu_pos: Optional[QtCore.QPoint] = None
        
        # Layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Scroll area for frames
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 4px;
                background-color: rgba(40, 40, 40, 240);
            }
            QScrollBar:horizontal {
                height: 8px;
                background: rgba(60, 60, 60, 200);
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(140, 140, 140, 200);
                border-radius: 4px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(180, 180, 180, 200);
            }
        """)
        
        # Container for frames
        self.frames_container = QtWidgets.QWidget()
        self.frames_layout = QtWidgets.QHBoxLayout(self.frames_container)
        self.frames_layout.setContentsMargins(4, 4, 4, 4)
        self.frames_layout.setSpacing(4)
        
        scroll_area.setWidget(self.frames_container)
        layout.addWidget(scroll_area)
        
        # Apply rounded style like other floating panels
        bg = constants.COLORS['Active:Window']
        border = constants.COLORS['Active:Base']
        bg_r, bg_g, bg_b = bg[:3]
        border_r, border_g, border_b = border[:3]
        self.setStyleSheet(f"""
            QWidget#GifFramesMenu {{
                background-color: rgba({bg_r}, {bg_g}, {bg_b}, 255);
                border-radius: 8px;
                border: 1px solid rgba({border_r}, {border_g}, {border_b}, 255);
            }}
        """)
        self.hide()
        
        self.frame_widgets = []
    
    def load_frames(self, item: "BeeGifItem"):
        """Loads all frames from GIF."""
        self.current_item = item
        self.frame_widgets.clear()
        
        # Clear old widgets
        while self.frames_layout.count():
            child = self.frames_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not item.movie or item.frame_count == 0:
            return
        
        # Save current frame
        current_frame = item.current_frame
        was_playing = item.is_playing
        if was_playing:
            item.pause_animation()
        
        # Load all frames
        for frame_num in range(item.frame_count):
            if item.movie.jumpToFrame(frame_num):
                pixmap = item.movie.currentPixmap()
                if not pixmap.isNull():
                    # Get frame delay (in milliseconds)
                    delay_ms = item.movie.nextFrameDelay()
                    if delay_ms <= 0:
                        delay_ms = 100  # Default value
                    
                    frame_widget = GifFrameThumbnail(
                        frame_num + 1, pixmap, delay_ms, self, self.frames_container)
                    frame_widget.is_selected = (frame_num == current_frame)
                    self.frames_layout.addWidget(frame_widget)
                    self.frame_widgets.append(frame_widget)
        
        # Restore current frame
        if item.movie.jumpToFrame(current_frame):
            item.current_frame = current_frame
            pixmap = item.movie.currentPixmap()
            if not pixmap.isNull():
                item.setPixmap(pixmap)
        
        if was_playing:
            item.play_animation()
        
        self.frames_container.adjustSize()
        self.adjustSize()
    
    def select_frame(self, frame_number: int):
        """Selects frame and displays it in item."""
        if not self.current_item or not self.current_item.movie:
            return
        
        frame_index = frame_number - 1  # Frame numbers start from 1
        
        # Update selection in widgets
        for i, widget in enumerate(self.frame_widgets):
            widget.is_selected = (i == frame_index)
            widget.update()
        
        # Go to selected frame in item
        was_playing = self.current_item.is_playing
        if was_playing:
            self.current_item.pause_animation()
        
        if self.current_item.movie.jumpToFrame(frame_index):
            self.current_item.current_frame = frame_index
            pixmap = self.current_item.movie.currentPixmap()
            if not pixmap.isNull():
                self.current_item.setPixmap(pixmap)
                self.current_item.update()
        
        if was_playing:
            self.current_item.play_animation()
    
    def show_menu(self):
        """Shows menu above main GIF menu."""
        if not self.current_item:
            return
        
        # Reset cache when showing menu to ensure position update
        self._cached_position = None
        self._cached_viewport_size = None
        self._cached_gif_menu_pos = None
        
        self.adjustSize()
        self.show()
        self.raise_()
        self.update_position()
        self.raise_()
        # Activate window to ensure it receives events
        self.activateWindow()
    
    def update_position(self):
        """Updates menu position above main GIF menu with optimization."""
        if not self.isVisible():
            return
        
        view = self.view
        if view is None:
            return
        
        viewport = view.viewport()
        if viewport is None:
            return
        
        view_rect = viewport.rect()
        viewport_size = view_rect.size()
        
        # Get GIF menu position in global coordinates (both are independent windows)
        gif_menu_pos = None
        if self.gif_menu.isVisible():
            gif_menu_pos = self.gif_menu.pos()  # Already in global coordinates
        
        # Check if viewport size or GIF menu position changed
        if (self._cached_viewport_size is not None and 
            self._cached_viewport_size == viewport_size and
            self._cached_gif_menu_pos == gif_menu_pos and
            self._cached_position is not None):
            # If nothing changed, check current position
            current_pos = self.pos()
            if current_pos == self._cached_position:
                # Position hasn't changed, skip update
                return
        
        # Calculate available width from viewport (in global coordinates)
        bottom_left_global = viewport.mapToGlobal(view_rect.bottomLeft())
        bottom_right_global = viewport.mapToGlobal(view_rect.bottomRight())
        available_width = bottom_right_global.x() - bottom_left_global.x()
        
        # Set full width only if it changed
        if self.width() != available_width:
            self.setFixedWidth(available_width)
        
        # Get natural content height
        self.adjustSize()
        height = self.height()
        
        # Position above main GIF menu with 8px offset
        if self.gif_menu.isVisible() and gif_menu_pos is not None:
            # Center frames menu above gif_menu
            gif_menu_width = self.gif_menu.width()
            frames_menu_width = self.width()
            # Center frames menu relative to gif_menu
            x = gif_menu_pos.x() + (gif_menu_width - frames_menu_width) // 2
            y = gif_menu_pos.y() - height - 8  # Above with 8px gap
        else:
            # If main menu is not visible, position relative to viewport bottom
            y = bottom_left_global.y() - height - 8
            x = bottom_left_global.x()
        
        # Check if it goes beyond screen bounds (top of screen)
        if y < 0:
            if self.gif_menu.isVisible() and gif_menu_pos is not None:
                # If doesn't fit above, position below gif_menu
                y = gif_menu_pos.y() + self.gif_menu.height() + 8
            else:
                y = 8
        
        new_position = QtCore.QPoint(x, y)
        
        # Update position only if it actually changed
        if self._cached_position != new_position:
            self.move(new_position)
            self._cached_position = new_position
            self._cached_viewport_size = viewport_size
            self._cached_gif_menu_pos = gif_menu_pos
    
    def parentWidget(self):
        """Override to return stored parent widget for compatibility."""
        return self._parent_widget
    
    def hide_menu(self):
        """Hides menu."""
        self.current_item = None
        # Clear cache when hiding menu
        self._cached_position = None
        self._cached_viewport_size = None
        self._cached_gif_menu_pos = None
        self.hide()
    
    def toggle_menu(self, item: "BeeGifItem"):
        """Toggles menu visibility."""
        if self.isVisible():
            self.hide_menu()
        else:
            self.load_frames(item)
            self.show_menu()

