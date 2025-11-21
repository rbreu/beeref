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

from functools import partial
from typing import Optional
import logging
import os
import os.path

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref.actions import ActionsMixin, actions
from beeref import commands
from beeref.assets import BeeAssets
from beeref.config import CommandlineArgs, BeeSettings, KeyboardSettings
from beeref import constants
from beeref import fileio
from beeref.fileio.errors import IMG_LOADING_ERROR_MSG
from beeref.fileio.export import exporter_registry, ImagesToDirectoryExporter
from beeref import widgets
from beeref.widgets.text_floating_menu import TextFloatingMenu
from beeref.widgets.image_floating_menu import ImageFloatingMenu
from beeref.widgets.gif_floating_menu import GifFloatingMenu
from beeref.widgets.draw_floating_menu import DrawFloatingMenu
from beeref.items import BeePixmapItem, BeeTextItem, BeeDrawItem
from beeref.gif_item import BeeGifItem
from beeref.main_controls import MainControlsMixin
from beeref.scene import BeeGraphicsScene
from beeref.utils import get_file_extension_from_format, qcolor_to_hex


commandline_args = CommandlineArgs()
logger = logging.getLogger(__name__)


class BeeGraphicsView(MainControlsMixin,
                      QtWidgets.QGraphicsView,
                      ActionsMixin):

    PAN_MODE = 1
    ZOOM_MODE = 2
    SAMPLE_COLOR_MODE = 3
    DRAW_MODE = 4

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.parent = parent
        self.settings = BeeSettings()
        self.keyboard_settings = KeyboardSettings()
        self.welcome_overlay = widgets.welcome_overlay.WelcomeOverlay(self)

        self.image_floating_menu: Optional[ImageFloatingMenu] = None
        self.text_floating_menu: Optional[TextFloatingMenu] = None
        self.gif_floating_menu: Optional[GifFloatingMenu] = None
        self.draw_floating_menu: Optional[DrawFloatingMenu] = None
        
        # Initialize drawing mode
        self.drawing_mode = False
        self.current_draw_item = None
        self.drawing_path = None
        self.drawing_points = []  # For line smoothing

        self.setBackgroundBrush(
            QtGui.QBrush(QtGui.QColor(*constants.COLORS['Scene:Canvas'])))
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        self.undo_stack = QtGui.QUndoStack(self)
        self.undo_stack.setUndoLimit(100)
        self.undo_stack.canRedoChanged.connect(self.on_can_redo_changed)
        self.undo_stack.canUndoChanged.connect(self.on_can_undo_changed)
        self.undo_stack.cleanChanged.connect(self.on_undo_clean_changed)

        self.filename = None
        self.previous_transform = None
        self.active_mode = None

        self.scene = BeeGraphicsScene(self.undo_stack)
        self.scene.changed.connect(self.on_scene_changed)
        self.scene.selectionChanged.connect(self.on_selection_changed)
        self.scene.cursor_changed.connect(self.on_cursor_changed)
        self.scene.cursor_cleared.connect(self.on_cursor_cleared)
        self.setScene(self.scene)

        # Context menu and actions
        self.build_menu_and_actions()
        self.control_target = self
        self.init_main_controls(main_window=parent)

        if parent is not None:
            self._init_floating_menus(parent)

        # Load files given via command line
        if commandline_args.filenames:
            fn = commandline_args.filenames[0]
            if os.path.splitext(fn)[1] == '.bee':
                self.open_from_file(fn)
            else:
                self.do_insert_images(commandline_args.filenames)

        self.update_window_title()

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value
        self.update_window_title()
        if value:
            self.settings.update_recent_files(value)
            self.update_menu_and_actions()

    def cancel_active_modes(self):
        self.scene.cancel_active_modes()
        self.cancel_sample_color_mode()
        self.cancel_drawing_mode()
        self.active_mode = None

    def cancel_sample_color_mode(self):
        logger.debug('Cancel sample color mode')
        self.active_mode = None
        self.viewport().unsetCursor()
        if hasattr(self, 'sample_color_widget'):
            self.sample_color_widget.hide()
            del self.sample_color_widget
        if self.scene.has_multi_selection():
            self.scene.multi_select_item.bring_to_front()

    def cancel_drawing_mode(self):
        """Cancels drawing mode."""
        if self.drawing_mode:
            logger.debug('Cancel drawing mode')
            self.drawing_mode = False
            if self.current_draw_item and self.drawing_path:
                # If item is empty, remove it
                if self.drawing_path.elementCount() <= 1:
                    self.scene.removeItem(self.current_draw_item)
            self.current_draw_item = None
            self.drawing_path = None
            self.viewport().unsetCursor()
            # Hide drawing menu
            if self.draw_floating_menu:
                self.draw_floating_menu.hide_menu()

    def update_window_title(self):
        clean = self.undo_stack.isClean()
        if clean and not self.filename:
            title = constants.APPNAME
        else:
            name = os.path.basename(self.filename or '[Untitled]')
            clean = '' if clean else '*'
            title = f'{name}{clean} - {constants.APPNAME}'
        self.parent.setWindowTitle(title)

    def _init_floating_menus(self, parent: QtWidgets.QWidget) -> None:
        self.image_floating_menu = ImageFloatingMenu(parent, self)
        self.text_floating_menu = TextFloatingMenu(parent, self)
        self.gif_floating_menu = GifFloatingMenu(parent, self)
        self.draw_floating_menu = DrawFloatingMenu(parent, self)

    def _floating_menus(self):
        return [
            menu
            for menu in (self.image_floating_menu, self.text_floating_menu, 
                        self.gif_floating_menu, self.draw_floating_menu)
            if menu is not None
        ]

    def _hide_all_floating_menus(self) -> None:
        for menu in self._floating_menus():
            menu.hide_menu()

    def _update_floating_menus_on_selection(self) -> None:
        if not self._floating_menus():
            return

        if self.scene.has_single_selection():
            item = self.scene.selectedItems(user_only=True)[0]
            if isinstance(item, BeeTextItem) and self.text_floating_menu:
                self._hide_other_menus(self.text_floating_menu)
                self.text_floating_menu.show_for_item(item)
            elif isinstance(item, BeeGifItem) and self.gif_floating_menu:
                self._hide_other_menus(self.gif_floating_menu)
                self.gif_floating_menu.show_for_item(item)
            elif isinstance(item, BeeDrawItem) and self.draw_floating_menu:
                self._hide_other_menus(self.draw_floating_menu)
                self.draw_floating_menu.show_for_item(item)
            elif getattr(item, 'is_image', False) and self.image_floating_menu:
                self._hide_other_menus(self.image_floating_menu)
                self.image_floating_menu.show_for_item(item)
            else:
                self._hide_all_floating_menus()
        else:
            self._hide_all_floating_menus()

    def _hide_other_menus(self, current_menu):
        """Hides all menus except current one."""
        for menu in self._floating_menus():
            if menu != current_menu:
                menu.hide_menu()

    def update_floating_menus_position(self) -> None:
        for menu in self._floating_menus():
            menu.update_position()

    def _refresh_visible_floating_menu(self) -> None:
        if not self.scene.has_single_selection():
            return
        item = self.scene.selectedItems(user_only=True)[0]
        if (isinstance(item, BeeTextItem)
                and self.text_floating_menu
                and self.text_floating_menu.isVisible()):
            self.text_floating_menu.show_for_item(item)
        elif (isinstance(item, BeeGifItem)
              and self.gif_floating_menu
              and self.gif_floating_menu.isVisible()):
            self.gif_floating_menu.show_for_item(item)
        elif (isinstance(item, BeeDrawItem)
              and self.draw_floating_menu
              and self.draw_floating_menu.isVisible()):
            self.draw_floating_menu.show_for_item(item)
        elif (getattr(item, 'is_image', False)
              and self.image_floating_menu
              and self.image_floating_menu.isVisible()):
            self.image_floating_menu.show_for_item(item)

    def on_scene_changed(self, region):
        if not self.scene.items():
            logger.debug('No items in scene')
            self.setTransform(QtGui.QTransform())
            self.welcome_overlay.setFocus()
            self.clearFocus()
            self.welcome_overlay.show()
            self.actiongroup_set_enabled('active_when_items_in_scene', False)
            self._hide_all_floating_menus()
        else:
            self.setFocus()
            self.welcome_overlay.clearFocus()
            self.welcome_overlay.hide()
            self.actiongroup_set_enabled('active_when_items_in_scene', True)
        self.recalc_scene_rect()

    def on_can_redo_changed(self, can_redo):
        self.actiongroup_set_enabled('active_when_can_redo', can_redo)

    def on_can_undo_changed(self, can_undo):
        self.actiongroup_set_enabled('active_when_can_undo', can_undo)

    def on_undo_clean_changed(self, clean):
        self.update_window_title()

    def on_context_menu(self, point):
        self.context_menu.exec(self.mapToGlobal(point))

    def get_supported_image_formats(self, cls):
        formats = []

        for f in cls.supportedImageFormats():
            string = f'*.{f.data().decode()}'
            formats.extend((string, string.upper()))
        return ' '.join(formats)

    def get_view_center(self):
        return QtCore.QPoint(round(self.size().width() / 2),
                             round(self.size().height() / 2))

    def clear_scene(self):
        logging.debug('Clearing scene...')
        self.cancel_active_modes()
        self.scene.clear()
        self.undo_stack.clear()
        self.filename = None
        self.setTransform(QtGui.QTransform())

    def reset_previous_transform(self, toggle_item=None):
        if (self.previous_transform
                and self.previous_transform['toggle_item'] != toggle_item):
            self.previous_transform = None

    def fit_rect(self, rect, toggle_item=None):
        if toggle_item and self.previous_transform:
            logger.debug('Fit view: Reset to previous')
            self.setTransform(self.previous_transform['transform'])
            self.centerOn(self.previous_transform['center'])
            self.previous_transform = None
            return
        if toggle_item:
            self.previous_transform = {
                'toggle_item': toggle_item,
                'transform': QtGui.QTransform(self.transform()),
                'center': self.mapToScene(self.get_view_center()),
            }
        else:
            self.previous_transform = None

        logger.debug(f'Fit view: {rect}')
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self.recalc_scene_rect()
        # It seems to be more reliable when we fit a second time
        # Sometimes a changing scene rect can mess up the fitting
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        logger.trace('Fit view done')

    def get_confirmation_unsaved_changes(self, msg):
        confirm = self.settings.valueOrDefault('Save/confirm_close_unsaved')
        if confirm and not self.undo_stack.isClean():
            answer = QtWidgets.QMessageBox.question(
                self,
                'Discard unsaved changes?',
                msg,
                QtWidgets.QMessageBox.StandardButton.Yes |
                QtWidgets.QMessageBox.StandardButton.Cancel)
            return answer == QtWidgets.QMessageBox.StandardButton.Yes

        return True

    def on_action_new_scene(self):
        confirm = self.get_confirmation_unsaved_changes(
            'There are unsaved changes. '
            'Are you sure you want to open a new scene?')
        if confirm:
            self.clear_scene()

    def on_action_fit_scene(self):
        self.fit_rect(self.scene.itemsBoundingRect())

    def on_action_fit_selection(self):
        self.fit_rect(self.scene.itemsBoundingRect(selection_only=True))

    def on_action_fullscreen(self, checked):
        if checked:
            self.parent.showFullScreen()
        else:
            self.parent.showNormal()

    def on_action_always_on_top(self, checked):
        self.parent.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint, on=checked)
        self.parent.destroy()
        self.parent.create()
        self.parent.show()

    def on_action_show_scrollbars(self, checked):
        if checked:
            self.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def on_action_show_menubar(self, checked):
        if checked:
            self.parent.setMenuBar(self.create_menubar())
        else:
            self.parent.setMenuBar(None)

    def on_action_show_titlebar(self, checked):
        self.parent.setWindowFlag(
            Qt.WindowType.FramelessWindowHint, on=not checked)
        self.parent.destroy()
        self.parent.create()
        self.parent.show()

    def on_action_move_window(self):
        if self.welcome_overlay.isHidden():
            self.on_action_movewin_mode()
        else:
            self.welcome_overlay.on_action_movewin_mode()

    def on_action_undo(self):
        logger.debug('Undo: %s' % self.undo_stack.undoText())
        self.cancel_active_modes()
        self.undo_stack.undo()

    def on_action_redo(self):
        logger.debug('Redo: %s' % self.undo_stack.redoText())
        self.cancel_active_modes()
        self.undo_stack.redo()

    def on_action_select_all(self):
        self.scene.select_all_items()

    def on_action_deselect_all(self):
        self.scene.deselect_all_items()

    def on_action_delete_items(self):
        logger.debug('Deleting items...')
        self.cancel_active_modes()
        self.undo_stack.push(
            commands.DeleteItems(
                self.scene, self.scene.selectedItems(user_only=True)))

    def on_action_cut(self):
        logger.debug('Cutting items...')
        self.on_action_copy()
        self.undo_stack.push(
            commands.DeleteItems(
                self.scene, self.scene.selectedItems(user_only=True)))

    def on_action_raise_to_top(self):
        self.scene.raise_to_top()

    def on_action_lower_to_bottom(self):
        self.scene.lower_to_bottom()

    def on_action_normalize_height(self):
        self.scene.normalize_height()

    def on_action_normalize_width(self):
        self.scene.normalize_width()

    def on_action_normalize_size(self):
        self.scene.normalize_size()

    def on_action_arrange_horizontal(self):
        self.scene.arrange()

    def on_action_arrange_vertical(self):
        self.scene.arrange(vertical=True)

    def on_action_arrange_optimal(self):
        self.scene.arrange_optimal()

    def on_action_arrange_square(self):
        self.scene.arrange_square()

    def on_action_change_opacity(self):
        images = list(filter(
            lambda item: item.is_image,
            self.scene.selectedItems(user_only=True)))
        widgets.ChangeOpacityDialog(self, images, self.undo_stack)

    def on_action_grayscale(self, checked):
        images = list(filter(
            lambda item: item.is_image,
            self.scene.selectedItems(user_only=True)))
        if images:
            self.undo_stack.push(
                commands.ToggleGrayscale(images, checked))

    def on_action_crop(self):
        self.scene.crop_items()

    def on_action_flip_horizontally(self):
        self.scene.flip_items(vertical=False)

    def on_action_flip_vertically(self):
        self.scene.flip_items(vertical=True)

    def on_action_reset_scale(self):
        self.cancel_active_modes()
        self.undo_stack.push(commands.ResetScale(
            self.scene.selectedItems(user_only=True)))

    def on_action_reset_rotation(self):
        self.cancel_active_modes()
        self.undo_stack.push(commands.ResetRotation(
            self.scene.selectedItems(user_only=True)))

    def on_action_reset_flip(self):
        self.cancel_active_modes()
        self.undo_stack.push(commands.ResetFlip(
            self.scene.selectedItems(user_only=True)))

    def on_action_reset_crop(self):
        self.cancel_active_modes()
        self.undo_stack.push(commands.ResetCrop(
            self.scene.selectedItems(user_only=True)))

    def on_action_reset_transforms(self):
        self.cancel_active_modes()
        self.undo_stack.push(commands.ResetTransforms(
            self.scene.selectedItems(user_only=True)))

    def on_action_show_color_gamut(self):
        widgets.color_gamut.GamutDialog(self, self.scene.selectedItems()[0])

    # ------------------------------------------------------------------
    # Text helpers used by floating menus
    def _selected_text_items(self):
        return [
            item for item in self.scene.selectedItems(user_only=True)
            if isinstance(item, BeeTextItem)
        ]

    def change_selected_text_color(self):
        items = self._selected_text_items()
        if not items:
            return
        initial = items[0].defaultTextColor()
        dialog = widgets.color_picker.ColorPickerDialog(self, initial)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        color = dialog.selectedColor()
        for item in items:
            item.setDefaultTextColor(color)
            item.update()
        self._refresh_visible_floating_menu()

    def change_selected_text_background(self):
        items = self._selected_text_items()
        if not items:
            return
        initial = getattr(items[0], 'background_color', QtGui.QColor(0, 0, 0, 0))
        dialog = widgets.color_picker.ColorPickerDialog(self, initial)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        bg_color = dialog.selectedColor()
        
        # Calculate text color based on background color
        text_color = self._calculate_text_color_from_background(bg_color)
        
        for item in items:
            if hasattr(item, 'set_background_color'):
                item.set_background_color(bg_color)
            # Automatically change text color
            item.setDefaultTextColor(text_color)
            item.update()
        self._refresh_visible_floating_menu()
    
    def cancel_drawing_mode(self):
        """Cancels drawing mode."""
        if self.drawing_mode:
            logger.debug('Cancel drawing mode')
            self.drawing_mode = False
            if self.current_draw_item and self.drawing_path:
                # If item is empty, remove it
                if self.drawing_path.elementCount() <= 1:
                    self.scene.removeItem(self.current_draw_item)
            self.current_draw_item = None
            self.drawing_path = None
            self.drawing_points = []
            self.viewport().unsetCursor()

    def enter_drawing_mode(self):
        """Activates drawing mode."""
        logger.debug('Entering drawing mode')
        self.cancel_active_modes()
        self.drawing_mode = True
        assets = BeeAssets()
        self.viewport().setCursor(assets.cursor_draw_line)
        self.current_draw_item = None
        self.drawing_path = None
        self.drawing_points = []

    def _start_drawing(self, pos: QtCore.QPointF):
        """Starts drawing at specified position."""
        if not self.drawing_mode:
            return
        
        # Create new drawing item on first click
        if not self.current_draw_item:
            self.current_draw_item = BeeDrawItem()
            self.drawing_path = QtGui.QPainterPath()
            # Add item to scene
            self.undo_stack.push(commands.InsertItems(self.scene, [self.current_draw_item], pos))
        
        # Start new path
        self.drawing_path = QtGui.QPainterPath()
        self.drawing_points = []  # Reset points for smoothing
        local_pos = self.current_draw_item.mapFromScene(pos)
        self.drawing_path.moveTo(local_pos)
        self.drawing_points.append(local_pos)  # Save first point
        self.current_draw_item.setPath(self.drawing_path)

    def _continue_drawing(self, pos: QtCore.QPointF):
        """Continues drawing to specified position with improved smoothing."""
        if (not self.drawing_mode or not self.current_draw_item 
            or not self.drawing_path):
            return
            
        local_pos = self.current_draw_item.mapFromScene(pos)
        self.drawing_points.append(local_pos)
        
        # Apply improved smoothing through cubic Bezier curves
        if len(self.drawing_points) >= 2:
            if len(self.drawing_points) == 2:
                # For first two points, just draw a line
                self.drawing_path.lineTo(local_pos)
            elif len(self.drawing_points) == 3:
                # For three points, use quadratic curve
                p0 = self.drawing_points[0]
                p1 = self.drawing_points[1]
                p2 = self.drawing_points[2]
                
                # Control point is middle between p1 and p2
                cp_x = (p1.x() + p2.x()) / 2.0
                cp_y = (p1.y() + p2.y()) / 2.0
                
                self.drawing_path.quadTo(
                    QtCore.QPointF(cp_x, cp_y),
                    p2
                )
            else:
                # For four or more points, use improved smoothing algorithm
                # Use averaging of multiple points for smoother curves
                p1 = self.drawing_points[-2]  # Previous point
                p2 = self.drawing_points[-1]  # Current point
                
                # Calculate velocity (movement vector) based on several previous points
                if len(self.drawing_points) >= 4:
                    # Use vector averaging for smoother movement
                    p0 = self.drawing_points[-3]
                    p_prev = self.drawing_points[-4] if len(self.drawing_points) >= 5 else p0
                    
                    # Movement vector 1 (from p_prev to p0)
                    v1_x = p0.x() - p_prev.x()
                    v1_y = p0.y() - p_prev.y()
                    
                    # Movement vector 2 (from p0 to p1)
                    v2_x = p1.x() - p0.x()
                    v2_y = p1.y() - p0.y()
                    
                    # Movement vector 3 (from p1 to p2)
                    v3_x = p2.x() - p1.x()
                    v3_y = p2.y() - p1.y()
                    
                    # Average vectors for smoothness
                    avg_v1_x = (v1_x + v2_x) / 2.0
                    avg_v1_y = (v1_y + v2_y) / 2.0
                    avg_v2_x = (v2_x + v3_x) / 2.0
                    avg_v2_y = (v2_y + v3_y) / 2.0
                    
                    # Control points calculated considering movement direction
                    # Smoothing factor (can be adjusted from 0.3 to 0.7)
                    smooth_factor = 0.5
                    
                    cp1_x = p1.x() - avg_v1_x * smooth_factor
                    cp1_y = p1.y() - avg_v1_y * smooth_factor
                    cp2_x = p1.x() + avg_v2_x * smooth_factor
                    cp2_y = p1.y() + avg_v2_y * smooth_factor
                else:
                    # For fewer points, use simple algorithm
                    p0 = self.drawing_points[-3]
                    
                    # Control points closer to p1 for smoother transition
                    cp1_x = p0.x() + (p1.x() - p0.x()) * 0.7
                    cp1_y = p0.y() + (p1.y() - p0.y()) * 0.7
                    cp2_x = p1.x() + (p2.x() - p1.x()) * 0.3
                    cp2_y = p1.y() + (p2.y() - p1.y()) * 0.3
                
                # Use cubic Bezier curve for smooth transition
                self.drawing_path.cubicTo(
                    QtCore.QPointF(cp1_x, cp1_y),  # Control point 1
                    QtCore.QPointF(cp2_x, cp2_y),  # Control point 2
                    p2  # End point
                )
        
        self.current_draw_item.setPath(self.drawing_path)

    def _finish_drawing(self, pos: QtCore.QPointF):
        """Finishes drawing and applies path simplification."""
        if (not self.drawing_mode or not self.current_draw_item 
            or not self.drawing_path):
            return
            
        # Finish path
        self._continue_drawing(pos)
        
        # If path is too short, remove item
        if self.drawing_path.elementCount() <= 1:
            self.scene.removeItem(self.current_draw_item)
            self.current_draw_item = None
            self.drawing_path = None
            self.drawing_points = []
            return
        
        # Apply path simplification to remove unnecessary points
        if len(self.drawing_points) > 2:
            # Adaptive epsilon: use smaller value for complex curves
            adaptive_epsilon = self._calculate_adaptive_epsilon(self.drawing_points)
            simplified_points = self._simplify_path(self.drawing_points, epsilon=adaptive_epsilon)
            if len(simplified_points) >= 2:
                # Recreate path from simplified points with smart smoothing
                simplified_path = self._create_smooth_path(simplified_points)
                self.current_draw_item.setPath(simplified_path)
        
        # Clear current item, but drawing mode remains active
        # for next stroke (like in PureRef)
        self.current_draw_item = None
        self.drawing_path = None
        self.drawing_points = []

    def _simplify_path(self, points, epsilon=2.0):
        """Simplifies path by removing unnecessary points using Ramer-Douglas-Peucker algorithm.
        
        Args:
            points: List of QPointF points
            epsilon: Maximum distance from point to line (in pixels)
        
        Returns:
            Simplified list of points
        """
        if len(points) <= 2:
            return points
        
        # Find point with maximum distance from line between first and last point
        max_dist = 0
        max_index = 0
        start = points[0]
        end = points[-1]
        
        # Calculate segment length
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        segment_length_sq = dx * dx + dy * dy
        
        for i in range(1, len(points) - 1):
            p = points[i]
            # Distance from point to line
            if segment_length_sq > 0:
                # Vector from start to p
                vx = p.x() - start.x()
                vy = p.y() - start.y()
                # Projection onto segment
                t = max(0, min(1, (vx * dx + vy * dy) / segment_length_sq))
                # Closest point on segment
                proj_x = start.x() + t * dx
                proj_y = start.y() + t * dy
                # Distance from point to projection
                dist_sq = (p.x() - proj_x) ** 2 + (p.y() - proj_y) ** 2
                dist = (dist_sq) ** 0.5
            else:
                # If segment has zero length, use distance to start
                dist = ((p.x() - start.x()) ** 2 + (p.y() - start.y()) ** 2) ** 0.5
            
            if dist > max_dist:
                max_dist = dist
                max_index = i
        
        # If maximum distance is greater than epsilon, recursively simplify
        if max_dist > epsilon:
            # Recursively simplify left and right parts
            left = self._simplify_path(points[:max_index + 1], epsilon)
            right = self._simplify_path(points[max_index:], epsilon)
            
            # Combine results (remove duplicate in middle)
            return left[:-1] + right
        else:
            # All points between start and end can be removed
            return [start, end]

    def _calculate_adaptive_epsilon(self, points):
        """Calculates adaptive epsilon based on curve complexity.
        
        For complex curves with sharp turns, uses smaller epsilon
        to preserve more details.
        """
        if len(points) < 3:
            return 2.0
        
        # Calculate average turn angle (using approximation without math)
        total_angle_change = 0.0
        angle_count = 0
        
        for i in range(1, len(points) - 1):
            p0 = points[i - 1]
            p1 = points[i]
            p2 = points[i + 1]
            
            # Vectors
            v1_x = p1.x() - p0.x()
            v1_y = p1.y() - p0.y()
            v2_x = p2.x() - p1.x()
            v2_y = p2.y() - p1.y()
            
            # Vector lengths
            len1_sq = v1_x * v1_x + v1_y * v1_y
            len2_sq = v2_x * v2_x + v2_y * v2_y
            
            if len1_sq > 0.01 and len2_sq > 0.01:  # Avoid division by zero
                len1 = len1_sq ** 0.5
                len2 = len2_sq ** 0.5
                
                # Normalize vectors
                v1_x /= len1
                v1_y /= len1
                v2_x /= len2
                v2_y /= len2
                
                # Angle between vectors via dot product
                # Use approximation: for small angles cos(angle) ≈ 1 - angle²/2
                dot = v1_x * v2_x + v1_y * v2_y
                dot = max(-1.0, min(1.0, dot))  # Clamp for safety
                
                # Approximate angle calculation without math.acos
                # For small angles: angle ≈ sqrt(2 * (1 - dot))
                # For larger angles use more accurate approximation
                if dot > 0.9:
                    # Small angle, use approximation
                    angle_sq = 2.0 * (1.0 - dot)
                    angle = angle_sq ** 0.5
                else:
                    # Larger angle, use more accurate approximation
                    # acos(x) ≈ π/2 - x for x close to 0, but we need different approximation
                    # Use polynomial approximation
                    angle = 1.5708 - dot * (1.5708 - 0.2146 * dot * dot)
                    if angle < 0:
                        angle = -angle
                
                total_angle_change += angle
                angle_count += 1
        
        if angle_count > 0:
            avg_angle = total_angle_change / angle_count
            # For sharp turns (large angles) decrease epsilon
            # For smooth curves increase epsilon
            if avg_angle > 0.5:  # Sharp turns (>28 degrees)
                return 1.0
            elif avg_angle > 0.3:  # Medium turns
                return 1.5
            else:  # Smooth curves
                return 2.5
        
        return 2.0

    def _create_smooth_path(self, points):
        """Creates smooth path from points considering turn angles for complex curves."""
        path = QtGui.QPainterPath()
        path.moveTo(points[0])
        
        if len(points) == 2:
            path.lineTo(points[1])
        elif len(points) == 3:
            # Quadratic curve for three points
            p0, p1, p2 = points
            cp_x = (p1.x() + p2.x()) / 2.0
            cp_y = (p1.y() + p2.y()) / 2.0
            path.quadTo(QtCore.QPointF(cp_x, cp_y), p2)
        else:
            # For complex curves use adaptive approach
            for i in range(len(points) - 1):
                p0 = points[i]
                p1 = points[i + 1]
                
                # Determine previous and next points for context
                p_prev = points[i - 1] if i > 0 else p0
                p_next = points[i + 2] if i + 2 < len(points) else p1
                
                # Calculate turn angles (approximately)
                angle_before = self._calculate_angle_approx(p_prev, p0, p1)
                angle_after = self._calculate_angle_approx(p0, p1, p_next)
                
                # For sharp turns use simpler curves
                # For smooth sections - more complex Bezier curves
                if angle_before > 0.5 or angle_after > 0.5:  # Sharp turn
                    # For sharp turns use quadratic curve
                    if i == 0:
                        path.lineTo(p1)
                    else:
                        # Small quadratic curve for smoothness
                        mid_x = (p0.x() + p1.x()) / 2.0
                        mid_y = (p0.y() + p1.y()) / 2.0
                        path.quadTo(QtCore.QPointF(mid_x, mid_y), p1)
                else:
                    # Smooth section - use cubic Bezier curve
                    # Adaptive control points based on movement direction
                    if i == 0:
                        # First segment
                        v1_x = p1.x() - p0.x()
                        v1_y = p1.y() - p0.y()
                        v2_x = p_next.x() - p1.x() if i + 2 < len(points) else v1_x
                        v2_y = p_next.y() - p1.y() if i + 2 < len(points) else v1_y
                        
                        # Control points considering direction
                        tension = 0.3  # Curve tension
                        cp1_x = p0.x() + v1_x * tension
                        cp1_y = p0.y() + v1_y * tension
                        cp2_x = p1.x() - v2_x * tension
                        cp2_y = p1.y() - v2_y * tension
                        
                        path.cubicTo(
                            QtCore.QPointF(cp1_x, cp1_y),
                            QtCore.QPointF(cp2_x, cp2_y),
                            p1
                        )
                    elif i == len(points) - 2:
                        # Last segment
                        v1_x = p0.x() - p_prev.x()
                        v1_y = p0.y() - p_prev.y()
                        v2_x = p1.x() - p0.x()
                        v2_y = p1.y() - p0.y()
                        
                        tension = 0.3
                        cp1_x = p0.x() + v1_x * tension
                        cp1_y = p0.y() + v1_y * tension
                        cp2_x = p1.x() - v2_x * tension
                        cp2_y = p1.y() - v2_y * tension
                        
                        path.cubicTo(
                            QtCore.QPointF(cp1_x, cp1_y),
                            QtCore.QPointF(cp2_x, cp2_y),
                            p1
                        )
                    else:
                        # Middle segments - use Catmull-Rom splines
                        # Convert to Bezier curves
                        cp1_x, cp1_y, cp2_x, cp2_y = self._catmull_rom_to_bezier(
                            p_prev, p0, p1, p_next
                        )
                        path.cubicTo(
                            QtCore.QPointF(cp1_x, cp1_y),
                            QtCore.QPointF(cp2_x, cp2_y),
                            p1
                        )
        
        return path

    def _calculate_angle_approx(self, p0, p1, p2):
        """Calculates approximate turn angle at point p1 (in radians) without math."""
        v1_x = p1.x() - p0.x()
        v1_y = p1.y() - p0.y()
        v2_x = p2.x() - p1.x()
        v2_y = p2.y() - p1.y()
        
        len1_sq = v1_x * v1_x + v1_y * v1_y
        len2_sq = v2_x * v2_x + v2_y * v2_y
        
        if len1_sq < 0.01 or len2_sq < 0.01:
            return 0.0
        
        len1 = len1_sq ** 0.5
        len2 = len2_sq ** 0.5
        
        # Normalize
        v1_x /= len1
        v1_y /= len1
        v2_x /= len2
        v2_y /= len2
        
        # Angle via dot product (approximately)
        dot = v1_x * v2_x + v1_y * v2_y
        dot = max(-1.0, min(1.0, dot))
        
        # Approximate angle calculation without math.acos
        if dot > 0.9:
            # Small angle: use approximation sqrt(2 * (1 - dot))
            angle_sq = 2.0 * (1.0 - dot)
            return angle_sq ** 0.5
        else:
            # Polynomial approximation for acos
            # acos(x) ≈ π/2 - x - x³/6 for x close to 0
            # Use more accurate approximation
            angle = 1.5708 - dot * (1.5708 - 0.2146 * dot * dot)
            return abs(angle)

    def _catmull_rom_to_bezier(self, p0, p1, p2, p3, tension=0.5):
        """Converts Catmull-Rom spline points to Bezier control points.
        
        Args:
            p0, p1, p2, p3: Four points for Catmull-Rom spline
            tension: Curve tension (0.0 = very smooth, 1.0 = sharper)
        
        Returns:
            (cp1_x, cp1_y, cp2_x, cp2_y) - control points for cubicTo
        """
        # Catmull-Rom spline passes through p1 and p2
        # Control points calculated based on neighboring points
        cp1_x = p1.x() + (p2.x() - p0.x()) * tension / 6.0
        cp1_y = p1.y() + (p2.y() - p0.y()) * tension / 6.0
        cp2_x = p2.x() - (p3.x() - p1.x()) * tension / 6.0
        cp2_y = p2.y() - (p3.y() - p1.y()) * tension / 6.0
        
        return cp1_x, cp1_y, cp2_x, cp2_y

    def _calculate_text_color_from_background(self, bg_color: QtGui.QColor) -> QtGui.QColor:
        """Calculates text color based on background color.
        
        Rules:
        - If background is black (brightness < 30) - white text
        - If background is white (brightness > 230) - black text
        - Otherwise - text two shades darker than background
        """
        # Get RGB components (0-255)
        r, g, b = bg_color.red(), bg_color.green(), bg_color.blue()
        
        # Calculate brightness using formula: 0.299*R + 0.587*G + 0.114*B
        brightness = 0.299 * r + 0.587 * g + 0.114 * b
        
        if brightness < 30:
            # Very dark background - white text
            return QtGui.QColor(255, 255, 255)
        elif brightness > 230:
            # Very light background - black text
            return QtGui.QColor(0, 0, 0)
        else:
            # Medium brightness - make text two shades darker
            # Decrease each component by 40 units (two shades)
            new_r = max(0, r - 40)
            new_g = max(0, g - 40)
            new_b = max(0, b - 40)
            return QtGui.QColor(new_r, new_g, new_b)

    def change_selected_text_size(self, size: int):
        if size <= 0 or size > 1000:  # Reasonable upper limit
            return
        items = self._selected_text_items()
        for item in items:
            font = item.font()
            font.setPointSize(size)
            item.setFont(font)
        self._refresh_visible_floating_menu()

    def change_selected_text_font(self, family: str):
        items = self._selected_text_items()
        for item in items:
            new_font = item.font()
            new_font.setFamily(family)
            item.setFont(new_font)
        self._refresh_visible_floating_menu()

    def toggle_selected_text_bold(self):
        items = self._selected_text_items()
        if not items:
            return
        first_font = items[0].font()
        is_bold = first_font.weight() >= QtGui.QFont.Weight.Bold
        target_weight = (QtGui.QFont.Weight.Normal
                         if is_bold else QtGui.QFont.Weight.Bold)
        for item in items:
            font = item.font()
            font.setWeight(target_weight)
            item.setFont(font)
        self._refresh_visible_floating_menu()

    def toggle_selected_text_italic(self):
        items = self._selected_text_items()
        if not items:
            return
        is_italic = items[0].font().italic()
        for item in items:
            font = item.font()
            font.setItalic(not is_italic)
            item.setFont(font)
        self._refresh_visible_floating_menu()

    def toggle_selected_text_underline(self):
        items = self._selected_text_items()
        if not items:
            return
        is_underline = items[0].font().underline()
        for item in items:
            font = item.font()
            font.setUnderline(not is_underline)
            item.setFont(font)
        self._refresh_visible_floating_menu()

    def toggle_selected_text_strikethrough(self):
        items = self._selected_text_items()
        if not items:
            return
        is_strikethrough = items[0].font().strikeOut()
        for item in items:
            font = item.font()
            font.setStrikeOut(not is_strikethrough)
            item.setFont(font)
        self._refresh_visible_floating_menu()

    def reset_selected_text_format(self):
        """Reset text formatting to default values."""
        from beeref import constants
        items = self._selected_text_items()
        if not items:
            return
        default_color = QtGui.QColor(*constants.COLORS['Scene:Text'])
        default_font = QtGui.QFont()
        for item in items:
            # Reset text color
            item.setDefaultTextColor(default_color)
            # Reset background color if attribute exists
            if hasattr(item, 'set_background_color'):
                item.set_background_color(QtGui.QColor(0, 0, 0, 0))
            # Reset font to default
            item.setFont(default_font)
            item.update()
        self._refresh_visible_floating_menu()

    def on_action_sample_color(self):
        self.cancel_active_modes()
        logger.debug('Entering sample color mode')
        self.viewport().setCursor(Qt.CursorShape.CrossCursor)
        self.active_mode = self.SAMPLE_COLOR_MODE

        if self.scene.has_multi_selection():
            # We don't want to sample the multi select item, so
            # temporarily send it to the back:
            self.scene.multi_select_item.lower_behind_selection()

        pos = self.mapFromGlobal(self.cursor().pos())
        self.sample_color_widget = widgets.SampleColorWidget(
            self,
            pos,
            self.scene.sample_color_at(self.mapToScene(pos)))

    def on_items_loaded(self, value):
        logger.debug('On items loaded: add queued items')
        self.scene.add_queued_items()

    def on_loading_finished(self, filename, errors):
        if errors:
            QtWidgets.QMessageBox.warning(
                self,
                'Problem loading file',
                ('<p>Problem loading file %s</p>'
                 '<p>Not accessible or not a proper bee file</p>') % filename)
        else:
            self.filename = filename
            self.scene.add_queued_items()
            self.on_action_fit_scene()

    def on_action_open_recent_file(self, filename):
        confirm = self.get_confirmation_unsaved_changes(
            'There are unsaved changes. '
            'Are you sure you want to open a new scene?')
        if confirm:
            self.open_from_file(filename)

    def open_from_file(self, filename):
        logger.info(f'Opening file {filename}')
        self.clear_scene()
        self.worker = fileio.ThreadedIO(
            fileio.load_bee, filename, self.scene)
        self.worker.progress.connect(self.on_items_loaded)
        self.worker.finished.connect(self.on_loading_finished)
        self.progress = widgets.BeeProgressDialog(
            f'Loading {filename}',
            worker=self.worker,
            parent=self)
        self.worker.start()

    def on_action_open(self):
        confirm = self.get_confirmation_unsaved_changes(
            'There are unsaved changes. '
            'Are you sure you want to open a new scene?')
        if not confirm:
            return

        self.cancel_active_modes()
        filename, f = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='Open file',
            filter=f'{constants.APPNAME} File (*.bee)')
        if filename:
            filename = os.path.normpath(filename)
            self.open_from_file(filename)
            self.filename = filename

    def on_saving_finished(self, filename, errors):
        if errors:
            QtWidgets.QMessageBox.warning(
                self,
                'Problem saving file',
                ('<p>Problem saving file %s</p>'
                 '<p>File/directory not accessible</p>') % filename)
        else:
            self.filename = filename
            self.undo_stack.setClean()

    def do_save(self, filename, create_new):
        if not fileio.is_bee_file(filename):
            filename = f'{filename}.bee'
        self.worker = fileio.ThreadedIO(
            fileio.save_bee, filename, self.scene, create_new=create_new)
        self.worker.finished.connect(self.on_saving_finished)
        self.progress = widgets.BeeProgressDialog(
            f'Saving {filename}',
            worker=self.worker,
            parent=self)
        self.worker.start()

    def on_action_save_as(self):
        self.cancel_active_modes()
        directory = os.path.dirname(self.filename) if self.filename else None
        filename, f = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption='Save file',
            directory=directory,
            filter=f'{constants.APPNAME} File (*.bee)')
        if filename:
            self.do_save(filename, create_new=True)

    def on_action_save(self):
        self.cancel_active_modes()
        if not self.filename:
            self.on_action_save_as()
        else:
            self.do_save(self.filename, create_new=False)

    def on_action_export_scene(self):
        directory = os.path.dirname(self.filename) if self.filename else None
        filename, formatstr = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption='Export Scene to Image',
            directory=directory,
            filter=';;'.join(('Image Files (*.png *.jpg *.jpeg *.svg)',
                              'PNG (*.png)',
                              'JPEG (*.jpg *.jpeg)',
                              'SVG (*.svg)')))

        if not filename:
            return

        name, ext = os.path.splitext(filename)
        if not ext:
            ext = get_file_extension_from_format(formatstr)
            filename = f'{filename}.{ext}'
        logger.debug(f'Got export filename {filename}')

        exporter_cls = exporter_registry[ext]
        exporter = exporter_cls(self.scene)
        if not exporter.get_user_input(self):
            return

        self.worker = fileio.ThreadedIO(exporter.export, filename)
        self.worker.finished.connect(self.on_export_finished)
        self.progress = widgets.BeeProgressDialog(
            f'Exporting {filename}',
            worker=self.worker,
            parent=self)
        self.worker.start()

    def on_export_finished(self, filename, errors):
        if errors:
            err_msg = '</br>'.join(str(errors))
            QtWidgets.QMessageBox.warning(
                self,
                'Problem writing file',
                f'<p>Problem writing file {filename}</p><p>{err_msg}</p>')

    def on_action_export_images(self):
        directory = os.path.dirname(self.filename) if self.filename else None
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption='Export Images',
            directory=directory)

        if not directory:
            return

        logger.debug(f'Got export directory {directory}')
        self.exporter = ImagesToDirectoryExporter(self.scene, directory)
        self.worker = fileio.ThreadedIO(self.exporter.export)
        self.worker.user_input_required.connect(
            self.on_export_images_file_exists)
        self.worker.finished.connect(self.on_export_finished)
        self.progress = widgets.BeeProgressDialog(
            f'Exporting to {directory}',
            worker=self.worker,
            parent=self)
        self.worker.start()

    def on_export_images_file_exists(self, filename):
        dlg = widgets.ExportImagesFileExistsDialog(self, filename)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.exporter.handle_existing = dlg.get_answer()
            directory = self.exporter.dirname
            self.progress = widgets.BeeProgressDialog(
                f'Exporting to {directory}',
                worker=self.worker,
                parent=self)
            self.worker.start()

    def on_action_quit(self):
        confirm = self.get_confirmation_unsaved_changes(
            'There are unsaved changes. Are you sure you want to quit?')
        if confirm:
            logger.info('User quit. Exiting...')
            self.app.quit()

    def on_action_settings(self):
        widgets.settings.SettingsDialog(self)

    def on_action_keyboard_settings(self):
        widgets.controls.ControlsDialog(self)

    def on_action_help(self):
        widgets.HelpDialog(self)

    def on_action_about(self):
        QtWidgets.QMessageBox.about(
            self,
            f'About {constants.APPNAME}',
            (f'<h2>{constants.APPNAME} {constants.VERSION}</h2>'
             f'<p>{constants.APPNAME_FULL}</p>'
             f'<p>{constants.COPYRIGHT}</p>'
             f'<p><a href="{constants.WEBSITE}">'
             f'Visit the {constants.APPNAME} website</a></p>'))

    def on_action_debuglog(self):
        widgets.DebugLogDialog(self)

    def on_insert_images_finished(self, new_scene, filename, errors):
        """Callback for when loading of images is finished.

        :param new_scene: True if the scene was empty before, else False
        :param filename: Not used, for compatibility only
        :param errors: List of filenames that couldn't be loaded
        """

        logger.debug('Insert images finished')
        if errors:
            errornames = [
                f'<li>{fn}</li>' for fn in errors]
            errornames = '<ul>%s</ul>' % '\n'.join(errornames)
            num = len(errors)
            msg = f'{num} image(s) could not be opened.<br/>'
            QtWidgets.QMessageBox.warning(
                self,
                'Problem loading images',
                msg + IMG_LOADING_ERROR_MSG + errornames)
        self.scene.add_queued_items()
        self.scene.arrange_default()
        self.undo_stack.endMacro()
        if new_scene:
            self.on_action_fit_scene()

    def do_insert_images(self, filenames, pos=None):
        if not pos:
            pos = self.get_view_center()
        self.scene.deselect_all_items()
        self.undo_stack.beginMacro('Insert Images')
        self.worker = fileio.ThreadedIO(
            fileio.load_images,
            filenames,
            self.mapToScene(pos),
            self.scene)
        self.worker.progress.connect(self.on_items_loaded)
        self.worker.finished.connect(
            partial(self.on_insert_images_finished,
                    not self.scene.items()))
        self.progress = widgets.BeeProgressDialog(
            'Loading images',
            worker=self.worker,
            parent=self)
        self.worker.start()

    def on_action_insert_images(self):
        self.cancel_active_modes()
        formats = self.get_supported_image_formats(QtGui.QImageReader)
        logger.debug(f'Supported image types for reading: {formats}')
        filenames, f = QtWidgets.QFileDialog.getOpenFileNames(
            parent=self,
            caption='Select one or more images to open',
            filter=f'Images ({formats})')
        self.do_insert_images(filenames)

    def on_action_insert_text(self):
        self.cancel_active_modes()
        item = BeeTextItem()
        pos = self.mapToScene(self.mapFromGlobal(self.cursor().pos()))
        item.setScale(1 / self.get_scale())
        self.undo_stack.push(commands.InsertItems(self.scene, [item], pos))

    def on_action_insert_draw(self):
        """Activates drawing mode via context menu."""
        self.cancel_active_modes()
        self.scene.clearSelection()
        self.enter_drawing_mode()

    def on_action_copy(self):
        logger.debug('Copying to clipboard...')
        self.cancel_active_modes()
        clipboard = QtWidgets.QApplication.clipboard()
        items = self.scene.selectedItems(user_only=True)

        # At the moment, we can only copy one image to the global
        # clipboard. (Later, we might create an image of the whole
        # selection for external copying.)
        if items:
            items[0].copy_to_clipboard(clipboard)

        # However, we can copy all items to the internal clipboard:
        self.scene.copy_selection_to_internal_clipboard()

        # We set a marker for ourselves in the global clipboard so
        # that we know to look up the internal clipboard when pasting:
        clipboard.mimeData().setData(
            'beeref/items', QtCore.QByteArray.number(len(items)))

    def on_action_paste(self):
        self.cancel_active_modes()
        logger.debug('Pasting from clipboard...')
        clipboard = QtWidgets.QApplication.clipboard()
        pos = self.mapToScene(self.mapFromGlobal(self.cursor().pos()))

        # See if we need to look up the internal clipboard:
        data = clipboard.mimeData().data('beeref/items')
        logger.debug(f'Custom data in clipboard: {data}')
        if data and self.scene.internal_clipboard:
            # Checking that internal clipboard exists since the user
            # may have opened a new scene since copying.
            self.scene.paste_from_internal_clipboard(pos)
            return

        img = clipboard.image()
        if not img.isNull():
            item = BeePixmapItem(img)
            self.undo_stack.push(commands.InsertItems(self.scene, [item], pos))
            if len(self.scene.items()) == 1:
                # This is the first image in the scene
                self.on_action_fit_scene()
            return
        text = clipboard.text()
        if text:
            item = BeeTextItem(text)
            item.setScale(1 / self.get_scale())
            self.undo_stack.push(commands.InsertItems(self.scene, [item], pos))
            return

        msg = 'No image data or text in clipboard or image too big'
        logger.info(msg)
        widgets.BeeNotification(self, msg)

    def on_action_open_settings_dir(self):
        dirname = os.path.dirname(self.settings.fileName())
        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl.fromLocalFile(dirname))

    def on_selection_changed(self):
        # Check that scene still exists and hasn't been deleted
        if not hasattr(self, 'scene') or not self.scene:
            return
        
        try:
            # Check that scene object is still valid
            _ = self.scene.selectedItems()
        except RuntimeError:
            # Scene was deleted, ignore
            logger.debug('Scene was deleted, ignoring selection change')
            return
        
        try:
            logger.debug('Currently selected items: %s',
                         len(self.scene.selectedItems(user_only=True)))
            self.actiongroup_set_enabled('active_when_selection',
                                         self.scene.has_selection())
            self.actiongroup_set_enabled('active_when_single_image',
                                         self.scene.has_single_image_selection())

            if self.scene.has_selection():
                item = self.scene.selectedItems(user_only=True)[0]
                grayscale = getattr(item, 'grayscale', False)
                actions.actions['grayscale'].qaction.setChecked(grayscale)
            self.viewport().repaint()
            self._update_floating_menus_on_selection()
        except (RuntimeError, AttributeError):
            # Scene was deleted or object unavailable, ignore
            logger.debug('Scene was deleted or unavailable, ignoring selection change')
            return

    def on_cursor_changed(self, cursor):
        if self.active_mode is None:
            self.viewport().setCursor(cursor)

    def on_cursor_cleared(self):
        if self.active_mode is None:
            self.viewport().unsetCursor()

    def recalc_scene_rect(self):
        """Resize the scene rectangle so that it is always one view width
        wider than all items' bounding box at each side and one view
        width higher on top and bottom. This gives the impression of
        an infinite canvas."""

        if self.previous_transform:
            return
        logger.trace('Recalculating scene rectangle...')
        try:
            topleft = self.mapFromScene(
                self.scene.itemsBoundingRect().topLeft())
            topleft = self.mapToScene(QtCore.QPoint(
                topleft.x() - self.size().width(),
                topleft.y() - self.size().height()))
            bottomright = self.mapFromScene(
                self.scene.itemsBoundingRect().bottomRight())
            bottomright = self.mapToScene(QtCore.QPoint(
                bottomright.x() + self.size().width(),
                bottomright.y() + self.size().height()))
            self.setSceneRect(QtCore.QRectF(topleft, bottomright))
        except OverflowError:
            logger.info('Maximum scene size reached')
        logger.trace('Done recalculating scene rectangle')

    def get_zoom_size(self, func):
        """Calculates the size of all items' bounding box in the view's
        coordinates.

        This helps ensure that we never zoom out too much (scene
        becomes so tiny that items become invisible) or zoom in too
        much (causing overflow errors).

        :param func: Function which takes the width and height as
            arguments and turns it into a number, for ex. ``min`` or ``max``.
        """

        topleft = self.mapFromScene(
            self.scene.itemsBoundingRect().topLeft())
        bottomright = self.mapFromScene(
            self.scene.itemsBoundingRect().bottomRight())
        return func(bottomright.x() - topleft.x(),
                    bottomright.y() - topleft.y())

    def scale(self, *args, **kwargs):
        super().scale(*args, **kwargs)
        self.scene.on_view_scale_change()
        self.recalc_scene_rect()

    def get_scale(self):
        return self.transform().m11()

    def pan(self, delta):
        if not self.scene.items():
            logger.debug('No items in scene; ignore pan')
            return

        hscroll = self.horizontalScrollBar()
        hscroll.setValue(int(hscroll.value() + delta.x()))
        vscroll = self.verticalScrollBar()
        vscroll.setValue(int(vscroll.value() + delta.y()))

    def zoom(self, delta, anchor):
        if not self.scene.items():
            logger.debug('No items in scene; ignore zoom')
            return

        # We calculate where the anchor is before and after the zoom
        # and then move the view accordingly to keep the anchor fixed
        # We can't use QGraphicsView's AnchorUnderMouse since it
        # uses the current cursor position while we need the initial mouse
        # press position for zooming with Ctrl + Middle Drag
        anchor = QtCore.QPoint(round(anchor.x()),
                               round(anchor.y()))
        ref_point = self.mapToScene(anchor)
        if delta == 0:
            return
        factor = 1 + abs(delta / 1000)
        if delta > 0:
            if self.get_zoom_size(max) < 10000000:
                self.scale(factor, factor)
            else:
                logger.debug('Maximum zoom size reached')
                return
        else:
            if self.get_zoom_size(min) > 50:
                self.scale(1/factor, 1/factor)
            else:
                logger.debug('Minimum zoom size reached')
                return

        self.pan(self.mapFromScene(ref_point) - anchor)
        self.reset_previous_transform()

    def wheelEvent(self, event):
        action, inverted\
            = self.keyboard_settings.mousewheel_action_for_event(event)

        delta = event.angleDelta().y()
        if inverted:
            delta = delta * -1

        if action == 'zoom':
            self.zoom(delta, event.position())
            event.accept()
            return
        if action == 'pan_horizontal':
            self.pan(QtCore.QPointF(0, 0.5 * delta))
            event.accept()
            return
        if action == 'pan_vertical':
            self.pan(QtCore.QPointF(0.5 * delta, 0))
            event.accept()
            return

    def mousePressEvent(self, event):
        # Handle drawing
        if self.drawing_mode and event.button() == QtCore.Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.position().toPoint())
            self._start_drawing(pos)
            event.accept()
            return
        
        if self.mousePressEventMainControls(event):
            return

        if self.active_mode == self.SAMPLE_COLOR_MODE:
            if (event.button() == Qt.MouseButton.LeftButton):
                color = self.scene.sample_color_at(
                    self.mapToScene(event.pos()))
                if color:
                    name = qcolor_to_hex(color)
                    clipboard = QtWidgets.QApplication.clipboard()
                    clipboard.setText(name)
                    self.scene.internal_clipboard = []
                    msg = f'Copied color to clipboard: {name}'
                    logger.debug(msg)
                    widgets.BeeNotification(self, msg)
                else:
                    logger.debug('No color found')
            self.cancel_sample_color_mode()
            event.accept()
            return

        action, inverted = self.keyboard_settings.mouse_action_for_event(event)

        if action == 'zoom':
            self.active_mode = self.ZOOM_MODE
            self.event_start = event.position()
            self.event_anchor = event.position()
            self.event_inverted = inverted
            event.accept()
            return

        if action == 'pan':
            logger.trace('Begin pan')
            self.active_mode = self.PAN_MODE
            self.event_start = event.position()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            # ClosedHandCursor and OpenHandCursor don't work, but I
            # don't know if that's only on my system or a general
            # problem. It works with other cursors.
            event.accept()
            return

        if self.mousePressEventMainControls(event):
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Handle drawing
        if self.drawing_mode and self.current_draw_item:
            if event.buttons() & QtCore.Qt.MouseButton.LeftButton:
                pos = self.mapToScene(event.position().toPoint())
                self._continue_drawing(pos)
                event.accept()
                return
        
        if self.active_mode == self.PAN_MODE:
            self.reset_previous_transform()
            pos = event.position()
            self.pan(self.event_start - pos)
            self.event_start = pos
            event.accept()
            return

        if self.active_mode == self.ZOOM_MODE:
            self.reset_previous_transform()
            pos = event.position()
            delta = (self.event_start - pos).y()
            if self.event_inverted:
                delta *= -1
            self.event_start = pos
            self.zoom(delta * 20, self.event_anchor)
            event.accept()
            return

        if self.active_mode == self.SAMPLE_COLOR_MODE:
            self.sample_color_widget.update(
                event.position(),
                self.scene.sample_color_at(self.mapToScene(event.pos())))
            event.accept()
            return

        if self.mouseMoveEventMainControls(event):
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # Handle drawing
        if self.drawing_mode and event.button() == QtCore.Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.position().toPoint())
            self._finish_drawing(pos)
            event.accept()
            return
        
        if self.active_mode == self.PAN_MODE:
            logger.trace('End pan')
            self.viewport().unsetCursor()
            self.active_mode = None
            event.accept()
            return
        if self.active_mode == self.ZOOM_MODE:
            self.active_mode = None
            event.accept()
            return
        if self.mouseReleaseEventMainControls(event):
            return
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.recalc_scene_rect()
        self.welcome_overlay.resize(self.size())
        self.update_floating_menus_position()

    def keyPressEvent(self, event):
        # Handle Escape to exit drawing mode (priority)
        if event.key() == Qt.Key.Key_Escape:
            if self.drawing_mode:
                self.cancel_drawing_mode()
                event.accept()
                return
        
        # Handle Backspace/Delete for deleting items BEFORE other handlers
        # This ensures it works even if QAction is disabled
        if (event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete)
                and event.modifiers() == Qt.KeyboardModifier.NoModifier):
            selected = self.scene.selectedItems(user_only=True)
            if selected and not self.scene.edit_item:
                self.on_action_delete_items()
                event.accept()
                return
        
        if self.keyPressEventMainControls(event):
            return
        if self.active_mode == self.SAMPLE_COLOR_MODE:
            self.cancel_sample_color_mode()
            event.accept()
            return
        super().keyPressEvent(event)
