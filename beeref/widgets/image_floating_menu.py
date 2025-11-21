"""Floating menu shown when a single image item is selected."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6 import QtGui, QtWidgets

from beeref.assets import BeeAssets
from beeref.widgets.floating_menu import FloatingMenu

if TYPE_CHECKING:  # pragma: no cover
    from beeref.view import BeeGraphicsView
    from beeref.items import BeePixmapItem


class ImageFloatingMenu(FloatingMenu):
    """Contextual floating toolbar for image items."""

    def __init__(self, parent: QtWidgets.QWidget, view: "BeeGraphicsView"):
        super().__init__(parent, view)

        # Load icons
        assets = BeeAssets()
        icons_path = assets.PATH.joinpath('icons')
        opacity_icon = QtGui.QIcon(str(icons_path.joinpath('opacity.svg')))
        grayscale_icon = QtGui.QIcon(str(icons_path.joinpath('grayscale.svg')))
        gamut_icon = QtGui.QIcon(str(icons_path.joinpath('gamut.svg')))
        flip_h_icon = QtGui.QIcon(str(icons_path.joinpath('flip_h.svg')))
        flip_v_icon = QtGui.QIcon(str(icons_path.joinpath('flip_v.svg')))
        crop_icon = QtGui.QIcon(str(icons_path.joinpath('crop.svg')))

        self.opacity_btn = self.add_button(
            "",
            icon=opacity_icon,
            callback=self.view.on_action_change_opacity,
        )
        self.opacity_btn.setToolTip("Opacity")
       

        self.grayscale_btn = self.add_button(
            "",
            icon=grayscale_icon,
            callback=self.view.on_action_grayscale,
            checkable=True,
        )
        self.grayscale_btn.setToolTip("Grayscale")
        gamut_btn = self.add_button(
            "",
            icon=gamut_icon,
            callback=self.view.on_action_show_color_gamut,
        )
        gamut_btn.setToolTip("Color Gamut")
        self.add_separator()

        crop_btn = self.add_button(
            "",
            icon=crop_icon,
            callback=self.view.on_action_crop,
        )
        crop_btn.setToolTip("Crop")
        self.add_separator()

        flip_h_btn = self.add_button(
            "",
            icon=flip_h_icon,
            callback=self.view.on_action_flip_horizontally,
        )
        flip_h_btn.setToolTip("Flip H")
        flip_v_btn = self.add_button(
            "",
            icon=flip_v_icon,
            callback=self.view.on_action_flip_vertically,
        )
        flip_v_btn.setToolTip("Flip V")
       
    def show_for_item(self, item: "BeePixmapItem") -> None:
        self.grayscale_btn.setChecked(getattr(item, "grayscale", False))
        super().show_for_item(item)
