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

"""Class for animated GIF images."""

import logging
import os.path
from typing import Optional

from PyQt6 import QtCore, QtGui, QtWidgets

from beeref.config import BeeSettings
from beeref.items import BeeItemMixin, register_item


logger = logging.getLogger(__name__)


@register_item
class BeeGifItem(BeeItemMixin, QtWidgets.QGraphicsPixmapItem):
    """Class for animated GIF images."""

    TYPE = 'gif'

    def __init__(self, filename=None, **kwargs):
        super().__init__()
        self.save_id = None
        self.filename = filename
        self.is_image = True
        self.init_selectable()
        self.settings = BeeSettings()
        
        # GIF animation control
        self.movie = None
        self.is_playing = False
        self.current_frame = 0
        self.frame_count = 0
        self.speed = 1.0
        
        # Timer for automatic playback (using singleShot instead of regular timer)
        self._animation_timer_id = None
        
        # Frame cache
        self._frame_cache: dict[int, QtGui.QPixmap] = {}
        self._frame_delays: dict[int, int] = {}
        
        if filename:
            self.load_gif(filename)
        
        logger.debug(f'Initialized {self}')

    def load_gif(self, filename):
        """Loads GIF file and initializes animation."""
        if not filename or not os.path.exists(filename):
            logger.warning(f'GIF file not found: {filename}')
            return
        
        self.movie = QtGui.QMovie(filename)
        self.movie.setCacheMode(QtGui.QMovie.CacheMode.CacheAll)
        
        # Get frame count
        self.frame_count = self.movie.frameCount()
        logger.debug(f'Loaded GIF: {filename}, frames: {self.frame_count}')
        
        if self.frame_count > 0:
            # Load and cache all frames
            self._cache_all_frames()
            
            # Show first frame
            self._show_frame(0)
            
            # Start animation automatically by default
            if self.frame_count > 1:
                self.play_animation()

    def _cache_all_frames(self):
        """Caches all GIF frames and their delays."""
        if not self.movie:
            return
            
        current_frame = self.current_frame
        
        for frame_num in range(self.frame_count):
            if self.movie.jumpToFrame(frame_num):
                pixmap = self.movie.currentPixmap()
                if not pixmap.isNull():
                    self._frame_cache[frame_num] = pixmap
                    self._frame_delays[frame_num] = self.movie.nextFrameDelay()
        
        # Restore original frame
        if current_frame >= 0 and current_frame < self.frame_count:
            self.movie.jumpToFrame(current_frame)

    def _show_frame(self, frame_num: int):
        """Shows the specified frame."""
        if frame_num in self._frame_cache:
            self.current_frame = frame_num
            # Use setPixmap and update, but this should be fast with cached frames
            self.setPixmap(self._frame_cache[frame_num])
            self.update()

    def _on_animation_tick(self):
        """Animation timer tick handler."""
        if not self.is_playing or self.frame_count <= 1:
            return
            
        next_frame = (self.current_frame + 1) % self.frame_count
        
        # Defer frame update to give UI time to process events
        def show_next():
            if self.is_playing:  # Check again, as pause may have occurred
                self._show_frame(next_frame)
                # Set next timeout with speed consideration
                if next_frame in self._frame_delays:
                    delay = max(10, int(self._frame_delays[next_frame] / self.speed))
                    # Use singleShot instead of regular timer for better responsiveness
                    if self.is_playing:  # Check again before starting
                        QtCore.QTimer.singleShot(delay, self._on_animation_tick)
        
        QtCore.QTimer.singleShot(0, show_next)

    def toggle_animation(self):
        """Toggles animation play/pause."""
        if self.is_playing:
            self.pause_animation()
        else:
            self.play_animation()

    def play_animation(self):
        """Starts automatic animation playback."""
        if not self.movie or self.frame_count <= 1:
            return
        
        if not self.is_playing:
            self.is_playing = True
            
            # Start timer for next frame using singleShot
            next_frame = (self.current_frame + 1) % self.frame_count
            if next_frame in self._frame_delays:
                delay = max(10, int(self._frame_delays[next_frame] / self.speed))
                self._animation_timer_id = QtCore.QTimer.singleShot(delay, self._on_animation_tick)
            
            logger.debug(f'Started playing GIF: {self.filename}')

    def pause_animation(self):
        """Pauses animation playback."""
        if self.is_playing:
            self.is_playing = False
            # QTimer.singleShot doesn't return ID for cancellation, but we can simply
            # set is_playing = False flag, and _on_animation_tick will check it
            self._animation_timer_id = None
            logger.debug(f'Paused GIF: {self.filename}')

    def set_speed(self, speed):
        """Sets animation playback speed."""
        self.speed = speed
        
        # If animation is playing, restart timer with new speed
        if self.is_playing:
            self.pause_animation()
            self.play_animation()
        
        logger.debug(f'Set GIF speed to {speed}x: {self.filename}')

    def get_speed(self):
        """Returns current playback speed."""
        return self.speed

    def previous_frame(self):
        """Goes to previous frame."""
        if self.frame_count == 0:
            return
        
        # Stop automatic playback
        if self.is_playing:
            self.pause_animation()
        
        new_frame = (self.current_frame - 1) % self.frame_count
        self._show_frame(new_frame)

    def next_frame(self):
        """Goes to next frame."""
        if self.frame_count == 0:
            return
        
        # Stop automatic playback
        if self.is_playing:
            self.pause_animation()
        
        new_frame = (self.current_frame + 1) % self.frame_count
        self._show_frame(new_frame)

    def bounding_rect_unselected(self):
        """Returns item bounds without selection."""
        return QtWidgets.QGraphicsPixmapItem.boundingRect(self)

    def paint(self, painter, option, widget):
        """Paints GIF item with selection border."""
        if abs(painter.combinedTransform().m11()) < 2:
            # Smooth image rendering at low zoom
            painter.setRenderHint(painter.RenderHint.SmoothPixmapTransform)
        
        # Draw current frame
        pm = self.pixmap()
        if not pm.isNull():
            painter.drawPixmap(0, 0, pm)
        
        # Draw selection border and handles
        self.paint_selectable(painter, option, widget)

    def __str__(self):
        if self.movie:
            size = self.movie.scaledSize()
            return (f'GIF "{self.filename}" {size.width()} x {size.height()}, '
                    f'{self.frame_count} frames')
        return f'GIF "{self.filename}"'

    @classmethod
    def create_from_data(cls, **kwargs):
        item = kwargs.pop('item', None)
        data = kwargs.pop('data', {})
        filename = data.get('filename') or (item.filename if item else None)
        
        gif_item = cls(filename=filename)
        return gif_item

    def update_from_data(self, **kwargs):
        """Updates item from data."""
        super().update_from_data(**kwargs)

    def get_extra_save_data(self):
        """Returns additional data for saving."""
        return {
            'filename': self.filename,
            'opacity': self.opacity(),
            'current_frame': self.current_frame,
        }

    def gif_to_bytes(self):
        """Reads GIF file and returns its bytes."""
        if not self.filename or not os.path.exists(self.filename):
            return None
        try:
            with open(self.filename, 'rb') as f:
                return f.read()
        except IOError as e:
            logger.error(f'Error reading GIF file {self.filename}: {e}')
            return None

    def get_filename_for_export(self, imgformat='gif', save_id_default=None):
        """Returns filename for export."""
        save_id = self.save_id or save_id_default
        if save_id is None:
            raise ValueError("save_id must be provided for export")

        if self.filename:
            basename = os.path.splitext(os.path.basename(self.filename))[0]
            return f'{save_id:04}-{basename}.{imgformat}'
        else:
            return f'{save_id:04}.{imgformat}'

    def create_copy(self):
        """Creates a copy of the item."""
        item = BeeGifItem(self.filename)
        item.setPos(self.pos())
        item.setZValue(self.zValue())
        item.setScale(self.scale())
        item.setRotation(self.rotation())
        item.setOpacity(self.opacity())
        if self.flip() == -1:
            item.do_flip()
        
        # Copy animation state
        item.current_frame = self.current_frame
        item._show_frame(self.current_frame)
        
        return item

    def get_frame_pixmap(self, frame_number: int):
        """Gets pixmap of specified frame."""
        return self._frame_cache.get(frame_number)

    def get_frame_delay(self, frame_number: int):
        """Gets delay of specified frame in milliseconds."""
        return self._frame_delays.get(frame_number, 100)

    def copy_to_clipboard(self, clipboard):
        """Copies current frame to clipboard."""
        pixmap = self.pixmap()
        if not pixmap.isNull():
            clipboard.setPixmap(pixmap)
