"""Floating menu widgets shown for single item selections."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Callable

from PyQt6 import QtCore, QtGui, QtWidgets

from beeref import constants


if TYPE_CHECKING:  # pragma: no cover - type checking only
    from beeref.view import BeeGraphicsView


class FloatingMenu(QtWidgets.QWidget):
    """Base widget for floating menus pinned to the bottom centre."""

    BOTTOM_MARGIN = 8
    CORNER_RADIUS = 8

    def __init__(self, parent: QtWidgets.QWidget, view: "BeeGraphicsView"):
        # Create as independent window to prevent event blocking
        super().__init__(None)
        self.setObjectName("FloatingMenu")
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        # Make it a tool window that stays on top
        self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(QtCore.Qt.WindowType.Tool, True)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, True)
        # Store parent for positioning
        self._parent_widget = parent
        self.view = view
        self.current_item: Optional[QtWidgets.QGraphicsItem] = None
        
        # Cache for update_position optimization
        self._cached_position: Optional[QtCore.QPoint] = None
        self._cached_viewport_size: Optional[QtCore.QSize] = None
        self._cached_window_pos: Optional[QtCore.QPoint] = None

        # Timer for tracking main window movement
        self._position_timer = QtCore.QTimer(self)
        self._position_timer.timeout.connect(self._check_window_position)
        self._position_timer.setInterval(50)  # Check every 50ms

        # Main layout with uniform spacing
        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(8, 6, 8, 6)
        self._layout.setSpacing(6)
        self._layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(constants.get_floating_menu_style())

        self.hide()

    def _check_window_position(self) -> None:
        """Checks viewport position and updates menu position if needed."""
        if not self.isVisible():
            return
        
        view = self.view
        if view is None:
            return
        
        viewport = view.viewport()
        if viewport is None:
            return
        
        # Get viewport position in global coordinates
        view_rect = viewport.rect()
        current_viewport_pos = viewport.mapToGlobal(view_rect.topLeft())
        
        # If viewport position changed, update menu position
        if self._cached_window_pos is not None and self._cached_window_pos != current_viewport_pos:
            self.update_position()
        
        self._cached_window_pos = current_viewport_pos

    def _apply_rounded_mask(self) -> None:
        """
        Applies rounded mask to widget with antialiasing.
        Implementation based on approach from VK Teams article.
        """
        size = self.size()
        if size.width() == 0 or size.height() == 0:
            return
        
        # Use QBitmap with antialiasing for smoother rendering
        # Create image with increased resolution (as in article)
        scale_factor = 2
        scaled_size = QtCore.QSize(
            int(size.width() * scale_factor),
            int(size.height() * scale_factor)
        )
        
        # Create QPixmap for drawing with antialiasing
        pixmap = QtGui.QPixmap(scaled_size)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtCore.Qt.GlobalColor.black)  # Black for mask
        
        # Draw rounded rectangle at increased resolution
        scaled_rect = QtCore.QRectF(0, 0, scaled_size.width(), scaled_size.height())
        scaled_radius = self.CORNER_RADIUS * scale_factor
        painter.drawRoundedRect(scaled_rect, scaled_radius, scaled_radius)
        painter.end()
        
        # Scale back with smoothing
        pixmap = pixmap.scaled(
            size,
            QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation
        )
        
        # Convert to QBitmap for mask
        # In mask: opaque pixels = visible areas, transparent = invisible
        image = pixmap.toImage()
        # Create mask from opaque pixels
        bitmap = QtGui.QBitmap.fromImage(image.createAlphaMask())
        
        # Apply mask
        self.setMask(bitmap)

    def add_widget(self, widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
        widget.setParent(self)
        self._layout.addWidget(widget)
        return widget

    def add_button(
        self,
        text: str,
        icon: Optional[QtGui.QIcon] = None,
        callback: Optional[Callable[[], None]] = None,
        checkable: bool = False,
    ) -> QtWidgets.QPushButton:
        button = QtWidgets.QPushButton(text, self)
        button.setCheckable(checkable)
        if icon:
            button.setIcon(icon)
            button.setIconSize(QtCore.QSize(32, 32))
        button.setProperty("floatingButton", True)
        if callback:
            # Connect directly - button events are handled independently
            button.clicked.connect(callback)
        self._layout.addWidget(button)
        return button

    def add_separator(self) -> None:
        separator = QtWidgets.QFrame(self)
        separator.setObjectName("FloatingMenuSeparator")
        separator.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        separator.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        separator.setFixedWidth(1)
        self._layout.addWidget(separator)

    def show_for_item(self, item: QtWidgets.QGraphicsItem) -> None:
        self.current_item = item
        self.show_menu()

    def show_menu(self) -> None:
        self.adjustSize()
        self._apply_rounded_mask()
        self.show()
        self.raise_()
        # Reset cache when showing menu to ensure position update
        self._cached_position = None
        self._cached_viewport_size = None
        self._cached_window_pos = None
        self.update_position()
        # Start timer for tracking window movement
        self._position_timer.start()
        # Ensure menu is on top after positioning
        self.raise_()
        # Return focus to view so keyboard events are handled correctly
        # FloatingMenu should not intercept focus as it has NoFocus
        if self.view:
            self.view.setFocus()

    def hide_menu(self) -> None:
        self.current_item = None
        # Stop timer
        self._position_timer.stop()
        # Clear cache when hiding menu
        self._cached_position = None
        self._cached_viewport_size = None
        self._cached_window_pos = None
        self.hide()

    def update_position(self) -> None:
        if not self.isVisible():
            return

        parent = self._parent_widget
        view = self.view
        if parent is None or view is None:
            return

        viewport = view.viewport()
        if viewport is None:
            return

        view_rect = viewport.rect()
        viewport_size = view_rect.size()
        
        # Get current viewport position for change detection
        current_viewport_pos = viewport.mapToGlobal(view_rect.topLeft())
        
        # Check if viewport size and position changed
        if (self._cached_viewport_size is not None and 
            self._cached_viewport_size == viewport_size and
            self._cached_window_pos is not None and
            self._cached_window_pos == current_viewport_pos and
            self._cached_position is not None):
            # If viewport size and position haven't changed, check menu position
            current_pos = self.pos()
            if current_pos == self._cached_position:
                # Position hasn't changed, skip update
                return

        size = self.sizeHint()
        width = self.width() or size.width()
        height = self.height() or size.height()

        # Calculate position in global coordinates (independent window)
        top_left_global = viewport.mapToGlobal(view_rect.topLeft())
        bottom_left_global = viewport.mapToGlobal(view_rect.bottomLeft())
        bottom_right_global = viewport.mapToGlobal(view_rect.bottomRight())
        top_right_global = viewport.mapToGlobal(view_rect.topRight())

        # Get viewport bounds in global coordinates
        viewport_left = top_left_global.x()
        viewport_right = top_right_global.x()
        viewport_top = top_left_global.y()
        viewport_bottom = bottom_left_global.y()
        viewport_width = viewport_right - viewport_left

        # Calculate X position (center, but don't go beyond boundaries)
        x = viewport_left + max(0, (viewport_width - width) // 2)
        # Limit to prevent menu from going beyond left and right boundaries
        x = max(viewport_left, min(x, viewport_right - width))

        # Calculate Y position (bottom with margin)
        y = viewport_bottom - height - self.BOTTOM_MARGIN
        # Limit to prevent menu from going beyond top boundary
        # If menu doesn't fit at bottom, place it at top
        if y < viewport_top:
            y = viewport_top + self.BOTTOM_MARGIN
        # Also check that menu doesn't go beyond bottom boundary
        if y + height > viewport_bottom:
            y = viewport_bottom - height - self.BOTTOM_MARGIN
            # If still doesn't fit, place at top
            if y < viewport_top:
                y = viewport_top + self.BOTTOM_MARGIN

        new_position = QtCore.QPoint(x, y)
        
        # Update position only if it actually changed
        if self._cached_position != new_position:
            self.move(new_position)
            self._cached_position = new_position
            self._cached_viewport_size = viewport_size
            self._cached_window_pos = current_viewport_pos
            # Update mask after size/position change
            self._apply_rounded_mask()

    def parentWidget(self):
        """Override to return stored parent widget for compatibility."""
        return self._parent_widget

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Intercept mouse events to prevent them from reaching view."""
        # Accept event to prevent propagation
        event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """Intercept mouse events to prevent them from reaching view."""
        event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """Intercept mouse events to prevent them from reaching view."""
        event.accept()
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Updates mask when widget size changes."""
        super().resizeEvent(event)
        self._apply_rounded_mask()
