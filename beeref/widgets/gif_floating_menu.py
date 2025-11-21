"""Floating menu shown when a single GIF item is selected."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from PyQt6 import QtCore, QtGui, QtWidgets

from beeref.assets import BeeAssets
from beeref.widgets.floating_menu import FloatingMenu

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover
    from beeref.view import BeeGraphicsView
    from beeref.gif_item import BeeGifItem
    from beeref.widgets.gif_frames_menu import GifFramesMenu


class GifFloatingMenu(FloatingMenu):
    """Contextual floating toolbar for GIF items."""

    SPEED_VALUES = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]

    def __init__(self, parent: QtWidgets.QWidget, view: "BeeGraphicsView"):
        super().__init__(parent, view)
        
        self._init_frames_menu(parent, view)
        self._init_icons()
        self._init_speed_combobox()
        self._init_control_buttons()

    def _init_frames_menu(
        self, 
        parent: QtWidgets.QWidget, 
        view: "BeeGraphicsView"
    ) -> None:
        """Initializes frames menu."""
        self.frames_menu: Optional["GifFramesMenu"] = None
        try:
            from beeref.widgets.gif_frames_menu import GifFramesMenu
            self.frames_menu = GifFramesMenu(parent, view, self)
        except ImportError as e:
            logger.warning(f'Failed to import frames menu: {e}')
        except Exception as e:
            logger.warning(f'Failed to initialize frames menu: {e}')

    def _init_icons(self) -> None:
        """Loads icons for control buttons."""
        assets = BeeAssets()
        icons_path = assets.PATH.joinpath('icons')
        
        self.prev_frame_icon = QtGui.QIcon(
            str(icons_path.joinpath('prev-frame.svg')))
        self.play_icon = QtGui.QIcon(str(icons_path.joinpath('play.svg')))
        self.pause_icon = QtGui.QIcon(str(icons_path.joinpath('pause.svg')))
        self.next_frame_icon = QtGui.QIcon(
            str(icons_path.joinpath('next-frame.svg')))
        self.frames_icon = QtGui.QIcon(str(icons_path.joinpath('frames.svg')))

    def _init_speed_combobox(self) -> None:
        """Initializes combobox for playback speed selection."""
        self.speed_combo = QtWidgets.QComboBox(self)
        self.speed_combo.setObjectName("FloatingMenuGifSpeed")
        self.speed_combo.setMinimumWidth(40)
        self.speed_combo.setIconSize(QtCore.QSize(32, 32))
        
        for speed in self.SPEED_VALUES:
            label = self._format_speed_label(speed)
            self.speed_combo.addItem(label, speed)
        
        # Set default value (1.0x)
        default_index = self.SPEED_VALUES.index(1.0)
        self.speed_combo.setCurrentIndex(default_index)
        self.speed_combo.currentIndexChanged.connect(self._on_speed_changed)
        self.speed_combo.setToolTip("Playback speed")
        self.add_widget(self.speed_combo)

    def _format_speed_label(self, speed: float) -> str:
        """Formats speed value for display in combobox."""
        if speed < 1.0:
            return f"{speed:.2f}x"
        else:
            speed_str = f"{speed:.2f}".rstrip('0').rstrip('.')
            return f"{speed_str}x"

    def _init_control_buttons(self) -> None:
        """Initializes playback control buttons."""
        self.prev_frame_btn = self.add_button(
            "",
            icon=self.prev_frame_icon,
            callback=self.on_previous_frame,
        )
        self.prev_frame_btn.setToolTip("Previous frame")

        self.play_pause_btn = self.add_button(
            "",
            icon=self.play_icon,
            callback=self.on_toggle_play_pause,
        )
        self.play_pause_btn.setToolTip("Play/Pause")

        self.next_frame_btn = self.add_button(
            "",
            icon=self.next_frame_icon,
            callback=self.on_next_frame,
        )
        self.next_frame_btn.setToolTip("Next frame")

        self.frames_btn = self.add_button(
            "",
            icon=self.frames_icon,
            callback=self.on_toggle_frames_menu,
        )
        self.frames_btn.setToolTip("Show frames timeline")

    def show_for_item(self, item: "BeeGifItem") -> None:
        """Shows menu for specified GIF item."""
        super().show_for_item(item)
        self.update_play_pause_button()
        self.update_speed_combo()
        self._hide_frames_menu()

    def _hide_frames_menu(self) -> None:
        """Hides frames menu if it's open."""
        if self.frames_menu:
            self.frames_menu.hide_menu()

    def update_speed_combo(self) -> None:
        """Updates speed value in combobox."""
        if not self._has_gif_item():
            return
        
        current_speed = self.current_item.get_speed()
        closest_speed = min(
            self.SPEED_VALUES, 
            key=lambda x: abs(x - current_speed)
        )
        index = self.SPEED_VALUES.index(closest_speed)
        
        self.speed_combo.blockSignals(True)
        self.speed_combo.setCurrentIndex(index)
        self.speed_combo.blockSignals(False)

    def _on_speed_changed(self, index: int) -> None:
        """Handler for playback speed change."""
        if not self._has_gif_item():
            return
        
        speed = self.speed_combo.currentData()
        if speed is not None:
            self.current_item.set_speed(speed)

    def update_play_pause_button(self) -> None:
        """Updates Play/Pause button icon."""
        if not self._has_gif_item():
            return
        
        if self.current_item.is_playing:
            self.play_pause_btn.setIcon(self.pause_icon)
            self.play_pause_btn.setToolTip("Pause")
        else:
            self.play_pause_btn.setIcon(self.play_icon)
            self.play_pause_btn.setToolTip("Play")

    def on_toggle_play_pause(self) -> None:
        """Toggles GIF play/pause."""
        if not self._has_gif_item():
            return
        
        # Defer execution so button can process event
        def do_toggle():
            self.current_item.toggle_animation()
            self.update_play_pause_button()
        
        QtCore.QTimer.singleShot(0, do_toggle)

    def on_previous_frame(self) -> None:
        """Goes to previous frame."""
        if not self._has_gif_item():
            return
        
        # Defer execution so button can process event
        def do_previous():
            self.current_item.previous_frame()
            self.update_play_pause_button()
            self._update_frames_menu_if_visible()
        
        QtCore.QTimer.singleShot(0, do_previous)

    def on_next_frame(self) -> None:
        """Goes to next frame."""
        if not self._has_gif_item():
            return
        
        # Defer execution so button can process event
        def do_next():
            self.current_item.next_frame()
            self.update_play_pause_button()
            self._update_frames_menu_if_visible()
        
        QtCore.QTimer.singleShot(0, do_next)

    def on_toggle_frames_menu(self) -> None:
        """Toggles frames menu visibility."""
        if not self._has_gif_item() or not self.frames_menu:
            return
        
        self.frames_menu.toggle_menu(self.current_item)

    def hide_menu(self) -> None:
        """Hides menu and frames menu."""
        self._hide_frames_menu()
        super().hide_menu()

    def update_position(self) -> None:
        """Updates position of menu and frames menu."""
        super().update_position()
        
        if self.frames_menu and self.frames_menu.isVisible():
            self.frames_menu.update_position()

    def _has_gif_item(self) -> bool:
        """Checks if current item is a GIF item."""
        return (self.current_item is not None and 
                hasattr(self.current_item, 'is_playing'))

    def _update_frames_menu_if_visible(self) -> None:
        """Updates frames menu if it's visible."""
        if self.frames_menu and self.frames_menu.isVisible():
            self.frames_menu.load_frames(self.current_item)
