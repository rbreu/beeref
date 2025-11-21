"""Floating menu shown when a single text item is selected."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6 import QtCore, QtGui, QtWidgets

from beeref.assets import BeeAssets
from beeref.widgets.floating_menu import FloatingMenu

if TYPE_CHECKING:
    from beeref.view import BeeGraphicsView
    from beeref.items import BeeTextItem


class TextFloatingMenu(FloatingMenu):
    """Contextual floating toolbar for text items."""

    FONT_SIZES = [8, 10, 12, 14, 16, 18, 24, 32, 48]

    def __init__(self, parent: QtWidgets.QWidget, view: "BeeGraphicsView"):
        super().__init__(parent, view)

        # Load icons
        assets = BeeAssets()
        icons_path = assets.PATH.joinpath('icons')
        text_color_icon = QtGui.QIcon(str(icons_path.joinpath('format-color-text.svg')))
        palette_icon = QtGui.QIcon(str(icons_path.joinpath('palette.svg')))
        bold_icon = QtGui.QIcon(str(icons_path.joinpath('format-bold.svg')))
        italic_icon = QtGui.QIcon(str(icons_path.joinpath('format-italic.svg')))
        underline_icon = QtGui.QIcon(str(icons_path.joinpath('format-underline.svg')))
        strikethrough_icon = QtGui.QIcon(str(icons_path.joinpath('format-strikethrough.svg')))
        reset_icon = QtGui.QIcon(str(icons_path.joinpath('clear.svg')))
        fonts_icon = QtGui.QIcon(str(icons_path.joinpath('fonts.svg')))

        self.text_color_btn = self.add_button(
            "",
            icon=text_color_icon,
            callback=self._on_text_color_clicked,
        )
        self.background_btn = self.add_button(
            "",
            icon=palette_icon,
            callback=self._on_background_clicked,
        )
        self.add_separator()

        self.bold_btn = self.add_button(
            "",
            icon=bold_icon,
            callback=self._on_bold_clicked,
            checkable=True,
        )
        self.italic_btn = self.add_button(
            "",
            icon=italic_icon,
            callback=self._on_italic_clicked,
            checkable=True,
        )
        self.underline_btn = self.add_button(
            "",
            icon=underline_icon,
            callback=self._on_underline_clicked,
            checkable=True,
        )
        self.strikethrough_btn = self.add_button(
            "",
            icon=strikethrough_icon,
            callback=self._on_strikethrough_clicked,
            checkable=True,
        )
        self.add_separator()

        self.size_combo = QtWidgets.QComboBox(self)
        self.size_combo.setObjectName("FloatingMenuFontSize")
        self.size_combo.setMinimumWidth(40)
        for size in self.FONT_SIZES:
            self.size_combo.addItem(str(size), size)
        self.size_combo.currentIndexChanged.connect(self._on_size_changed)
        self.add_widget(self.size_combo)

        self.font_combo = QtWidgets.QComboBox(self)
        self.font_combo.setObjectName("FloatingMenuFontFamily")
        self.font_combo.setMinimumWidth(40)
        self.font_combo.setIconSize(QtCore.QSize(32, 32))
        self.font_combo.setEditable(False)
        self.font_combo.setInsertPolicy(
            QtWidgets.QComboBox.InsertPolicy.NoInsert)
        families = QtGui.QFontDatabase.families()
        self.font_combo.addItems(families)
        # Add icon to all font items
        for i in range(self.font_combo.count()):
            self.font_combo.setItemIcon(i, fonts_icon)
        self.font_combo.currentTextChanged.connect(self._on_font_changed)
        self.add_widget(self.font_combo)

        self.add_separator()

        self.add_button(
            "",
            icon=reset_icon,
            callback=self.view.reset_selected_text_format,
        )

    # ------------------------------------------------------------------
    def show_for_item(self, item: "BeeTextItem") -> None:
        font = item.font()
        self._update_font_controls(font)
        self._update_colors(item)
        super().show_for_item(item)

    # UI updates -------------------------------------------------------
    def _update_font_controls(self, font: QtGui.QFont) -> None:
        self.bold_btn.setChecked(font.weight() >= QtGui.QFont.Weight.Bold)
        self.italic_btn.setChecked(font.italic())
        self.underline_btn.setChecked(font.underline())
        self.strikethrough_btn.setChecked(font.strikeOut())

        size = font.pointSize()
        if size == -1:
            size = int(font.pointSizeF())

        try:
            index = self.FONT_SIZES.index(size)
        except ValueError:
            index = -1
        self.size_combo.blockSignals(True)
        if index >= 0:
            self.size_combo.setCurrentIndex(index)
        else:
            self.size_combo.setCurrentText(str(size))
        self.size_combo.blockSignals(False)

        self.font_combo.blockSignals(True)
        family = font.family()
        index = self.font_combo.findText(family)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
        self.font_combo.blockSignals(False)

    def _update_colors(self, item: "BeeTextItem") -> None:
        text_color = item.defaultTextColor()
        self.text_color_btn.setProperty(
            "active", "true" if text_color else "false")
        self.text_color_btn.style().unpolish(self.text_color_btn)
        self.text_color_btn.style().polish(self.text_color_btn)

        bg_color = getattr(item, "background_color", None)
        self.background_btn.setProperty(
            "active", "true" if bg_color and bg_color.alpha() > 0 else "false")
        self.background_btn.style().unpolish(self.background_btn)
        self.background_btn.style().polish(self.background_btn)

    # Slots ------------------------------------------------------------
    def _on_text_color_clicked(self) -> None:
        self.view.change_selected_text_color()

    def _on_background_clicked(self) -> None:
        self.view.change_selected_text_background()

    def _on_bold_clicked(self) -> None:
        self.view.toggle_selected_text_bold()

    def _on_italic_clicked(self) -> None:
        self.view.toggle_selected_text_italic()

    def _on_underline_clicked(self) -> None:
        self.view.toggle_selected_text_underline()

    def _on_strikethrough_clicked(self) -> None:
        self.view.toggle_selected_text_strikethrough()

    def _on_size_changed(self, index: int) -> None:
        size = self.size_combo.currentData()
        if size is None:
            try:
                size = int(self.size_combo.currentText())
            except ValueError:
                return
        self.view.change_selected_text_size(size)

    def _on_font_changed(self, family: str) -> None:
        if not family:
            return
        self.view.change_selected_text_font(family)
