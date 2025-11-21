"""Floating menu for drawing items."""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

from PyQt6 import QtCore, QtGui, QtWidgets

from beeref import constants
from beeref import widgets
from beeref.assets import BeeAssets
from beeref.widgets.floating_menu import FloatingMenu

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from beeref.view import BeeGraphicsView
    from beeref.items import BeeDrawItem


class UpwardComboBox(QtWidgets.QComboBox):
    """QComboBox that opens its dropdown menu upward."""
    
    def showPopup(self):
        """Override to show popup above the combobox."""
        super().showPopup()
        # Use QTimer to get popup after it's created
        QtCore.QTimer.singleShot(0, self._reposition_popup)
    
    def _reposition_popup(self):
        """Moves popup above the combobox."""
        # Find active popup widget
        popup = QtWidgets.QApplication.activePopupWidget()
        if not popup:
            # Alternative method - find through view
            view = self.view()
            if view:
                popup = view.parent()
                while popup and not isinstance(popup, QtWidgets.QFrame):
                    popup = popup.parent()
        
        if popup:
            # Get global position of combobox
            global_pos = self.mapToGlobal(QtCore.QPoint(0, 0))
            # Calculate new position above combobox
            popup_height = popup.height()
            new_y = global_pos.y() - popup_height
            popup.move(global_pos.x(), new_y)


class DrawFloatingMenu(FloatingMenu):
    """Floating menu for drawing tools."""

    def __init__(self, parent: QtWidgets.QWidget, view: "BeeGraphicsView"):
        super().__init__(parent, view)
        self.current_item: Optional["BeeDrawItem"] = None
        
        # Color selection button via colorpicker
        assets = BeeAssets()
        icons_path = assets.PATH.joinpath('icons')
        palette_icon = QtGui.QIcon(str(icons_path.joinpath('palette.svg')))
        
        self.color_btn = self.add_button(
            "",
            icon=palette_icon,
            callback=self._on_color_clicked,
        )
        self.color_btn.setToolTip("Color")
        
        # Combobox for line style selection
        self.add_separator()
        self.style_combo = self.add_style_combobox()
        
        # Pen width selector
        self.add_separator()
        self.width_slider = self.add_width_slider()
        
        # Close menu button (cancel drawing mode)
        self.add_separator()
        close_icon = QtGui.QIcon(str(icons_path.joinpath('close.svg')))
        self.close_button = self.add_button(
            "",
            icon=close_icon,
            callback=self._on_close_clicked
        )
        self.close_button.setToolTip("Close")

    def add_style_combobox(self):
        """Adds combobox for line style selection."""
        assets = BeeAssets()
        icons_path = assets.PATH.joinpath('icons')
        
        # Load icons for styles
        solid_icon = QtGui.QIcon(str(icons_path.joinpath('line-solid.svg')))
        dashed_icon = QtGui.QIcon(str(icons_path.joinpath('line-dashed.svg')))
        arrow_icon = QtGui.QIcon(str(icons_path.joinpath('line-arrow.svg')))
        arrow_left_icon = QtGui.QIcon(str(icons_path.joinpath('line-arrow-left.svg')))
        arrow_both_icon = QtGui.QIcon(str(icons_path.joinpath('line-arrow-both.svg')))
        
        combo = UpwardComboBox(self)
        combo.setObjectName("FloatingMenuLineStyle")
        combo.setMinimumWidth(40)
        combo.setIconSize(QtCore.QSize(32, 32))
        
        # Add items with icons
        combo.addItem(solid_icon, "", 'solid')
        combo.addItem(dashed_icon, "", 'dashed')
        combo.addItem(arrow_icon, "", 'arrow')
        combo.addItem(arrow_left_icon, "", '<-')
        combo.addItem(arrow_both_icon, "", '<->')
        # Set icons for items
        combo.setItemIcon(0, solid_icon)
        combo.setItemIcon(1, dashed_icon)
        combo.setItemIcon(2, arrow_icon)
        combo.setItemIcon(3, arrow_left_icon)
        combo.setItemIcon(4, arrow_both_icon)
        
        combo.setCurrentIndex(0)  # Default to solid
        combo.currentIndexChanged.connect(self._on_style_changed)
        combo.setToolTip("Line style")
        
        self.add_widget(combo)
        return combo

    def _on_color_clicked(self) -> None:
        """Opens color selection dialog."""
        if not self.current_item:
            return
        
        initial = self.current_item.pen_color
        dialog = widgets.color_picker.ColorPickerDialog(self, initial)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        color = dialog.selectedColor()
        self.set_pen_color(color)

    def _on_style_changed(self, index: int) -> None:
        """Handler for line style change."""
        if not self.current_item:
            return
        style = self.style_combo.itemData(index)
        if style:
            self.set_pen_style(style)

    def add_width_slider(self):
        """Adds slider for pen width selection."""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QtWidgets.QLabel("Width:")
        layout.addWidget(label)
        
        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        slider.setRange(1, 20)
        slider.setValue(8)
        slider.valueChanged.connect(self.set_pen_width)
        layout.addWidget(slider)
        
        self.add_widget(container)
        return slider

    def show_for_item(self, item: "BeeDrawItem") -> None:
        """Shows menu for selected drawing item."""
        self.current_item = item
        if item:
            self.width_slider.setValue(item.pen_width)
            # Set current style in combobox
            style_index = self.style_combo.findData(item.pen_style)
            if style_index >= 0:
                self.style_combo.blockSignals(True)
                self.style_combo.setCurrentIndex(style_index)
                self.style_combo.blockSignals(False)
        super().show_for_item(item)

    def set_pen_color(self, color: QtGui.QColor):
        """Sets pen color for selected item."""
        if self.current_item:
            self.current_item.set_pen_color(color)

    def set_pen_width(self, width: int):
        """Sets pen width for selected item."""
        if self.current_item:
            self.current_item.set_pen_width(width)

    def set_pen_style(self, style: str):
        """Sets line style for selected item."""
        if self.current_item:
            self.current_item.set_pen_style(style)

    def _on_close_clicked(self) -> None:
        """Closes menu and cancels drawing mode."""
        self.view.cancel_drawing_mode()
        self.hide_menu()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Handles key press events."""
        if event.key() == QtCore.Qt.Key.Key_Escape:
            # ESC closes menu and cancels drawing mode
            self.view.cancel_drawing_mode()
            self.hide_menu()
            event.accept()
            return
        super().keyPressEvent(event)

