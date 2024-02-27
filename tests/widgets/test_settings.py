from unittest.mock import patch, MagicMock

from PyQt6 import QtWidgets, QtCore, QtGui

from beeref.actions.actions import Action, ActionList
from beeref.widgets.settings import (
    ArrangeGapWidget,
    ImageStorageFormatWidget,
    KeyboardSettingsDialog,
    KeyboardShortcutsDelegate,
    KeyboardShortcutsEditor,
    KeyboardShortcutsModel,
    KeyboardShortcutsProxy,
    SettingsDialog,
)


def test_image_storage_format_sets_title_when_not_edited(settings, view):
    widget = ImageStorageFormatWidget()
    assert widget.title() == 'Image Storage Format:'


def test_image_storage_format_sets_title_when_edited(settings, view):
    settings.setValue('Items/image_storage_format', 'jpg')
    widget = ImageStorageFormatWidget()
    assert widget.title() == 'Image Storage Format: ✎'


def test_image_storage_format_selects_radiobox(settings, view):
    settings.setValue('Items/image_storage_format', 'jpg')
    widget = ImageStorageFormatWidget()
    assert widget.buttons['best'].isChecked() is False
    assert widget.buttons['png'].isChecked() is False
    assert widget.buttons['jpg'].isChecked() is True


def test_image_storage_format_saves_change(settings, view):
    settings.setValue('Items/image_storage_format', 'best')
    widget = ImageStorageFormatWidget()
    widget.buttons['jpg'].setChecked(True)
    assert widget.buttons['best'].isChecked() is False
    assert widget.buttons['png'].isChecked() is False
    assert widget.buttons['jpg'].isChecked() is True
    assert settings.valueOrDefault('Items/image_storage_format') == 'jpg'
    assert widget.title() == 'Image Storage Format: ✎'


def test_image_storage_format_on_restore_defaults(settings, view):
    widget = ImageStorageFormatWidget()
    widget.buttons['jpg'].setChecked(True)
    settings.setValue('Items/image_storage_format', 'best')
    widget.on_restore_defaults()
    assert widget.buttons['best'].isChecked() is True
    assert widget.buttons['png'].isChecked() is False
    assert widget.buttons['jpg'].isChecked() is False
    assert widget.title() == 'Image Storage Format:'


def test_arrange_gap_initialises_input_from_settings(settings, view):
    settings.setValue('Items/arrange_gap', 6)
    widget = ArrangeGapWidget()
    assert widget.input.value() == 6


def test_arrange_gap_sets_title_when_not_edited(settings, view):
    widget = ArrangeGapWidget()
    assert widget.title() == 'Arrange Gap:'


def test_arrange_gap_sets_title_when_edited(settings, view):
    settings.setValue('Items/arrange_gap', 6)
    widget = ArrangeGapWidget()
    assert widget.title() == 'Arrange Gap: ✎'


def test_arrange_gap_saves_change(settings, view):
    settings.setValue('Items/arrange_gap', 6)
    widget = ArrangeGapWidget()
    widget.input.setValue(8)
    assert settings.valueOrDefault('Items/arrange_gap') == 8
    assert widget.title() == 'Arrange Gap: ✎'


def test_arrange_gap_on_restore_defaults(settings, view):
    widget = ArrangeGapWidget()
    widget.input.setValue(7)
    settings.setValue('Items/arrange_gap', 0)
    widget.on_restore_defaults()
    assert widget.input.value() == 0
    assert widget.title() == 'Arrange Gap:'


@patch('PyQt6.QtWidgets.QMessageBox.question',
       return_value=QtWidgets.QMessageBox.StandardButton.Yes)
def test_settings_dialog_on_restore_defaults(msg_mock, settings, view):
    dialog = SettingsDialog(view)
    settings.setValue('Items/image_storage_format', 'jpg')
    settings.setValue('Items/arrange_gap', 10)
    dialog.on_restore_defaults()
    msg_mock.assert_called_once()
    assert settings.valueOrDefault('Items/image_storage_format') == 'best'
    assert settings.valueOrDefault('Items/arrange_gap') == 0


def test_keyboard_shortcuts_editor_no_conflicts(view):
    a1 = Action({'id': 'foo', 'shortcuts': ['Ctrl+F']})
    a2 = Action({'id': 'bar', 'shortcuts': ['Ctrl+B']})
    with patch('beeref.widgets.settings.actions', ActionList([a1, a2])):
        editor = KeyboardShortcutsEditor(
            view,
            index=MagicMock(
                column=MagicMock(return_value=2),
                row=MagicMock(return_value=0)))
        editor.setKeySequence('Ctrl+A')
        editor.on_editing_finished()
        assert editor.keySequence().toString() == 'Ctrl+A'
        assert editor.remove_from_other is None


def test_keyboard_shortcuts_editor_reenter_existing_shortcut(view):
    a1 = Action({'id': 'foo', 'shortcuts': ['Ctrl+F']})
    a2 = Action({'id': 'bar', 'shortcuts': ['Ctrl+B']})
    with patch('beeref.widgets.settings.actions', ActionList([a1, a2])):
        editor = KeyboardShortcutsEditor(
            view,
            index=MagicMock(
                column=MagicMock(return_value=2),
                row=MagicMock(return_value=0)))
        editor.setKeySequence('Ctrl+F')
        editor.on_editing_finished()
        assert editor.keySequence().toString() == 'Ctrl+F'
        assert editor.remove_from_other is None


@patch('PyQt6.QtWidgets.QMessageBox.question',
       return_value=QtWidgets.QMessageBox.StandardButton.No)
def test_keyboard_shortcuts_editor_conflicts_choose_to_cancel(
        question_mock, view):
    a1 = Action({'id': 'foo', 'text': 'Foo', 'shortcuts': ['Ctrl+F']})
    a2 = Action({'id': 'bar', 'text': 'Bar', 'shortcuts': ['Ctrl+B']})
    with patch('beeref.widgets.settings.actions', ActionList([a1, a2])):
        editor = KeyboardShortcutsEditor(
            view,
            index=MagicMock(
                column=MagicMock(return_value=2),
                row=MagicMock(return_value=0)))
        editor.setKeySequence('Ctrl+B')
        editor.on_editing_finished()
        assert editor.keySequence().toString() == 'Ctrl+F'
        assert editor.remove_from_other is None


@patch('PyQt6.QtWidgets.QMessageBox.question',
       return_value=QtWidgets.QMessageBox.StandardButton.Yes)
def test_keyboard_shortcuts_editor_conflicts_choose_to_confirm(
        question_mock, view):
    a1 = Action({'id': 'foo', 'text': 'Foo', 'shortcuts': ['Ctrl+F']})
    a2 = Action({'id': 'bar', 'text': 'Bar', 'shortcuts': ['Ctrl+B']})
    with patch('beeref.widgets.settings.actions', ActionList([a1, a2])):
        editor = KeyboardShortcutsEditor(
            view,
            index=MagicMock(
                column=MagicMock(return_value=2),
                row=MagicMock(return_value=0)))
        editor.setKeySequence('Ctrl+B')
        editor.on_editing_finished()
        assert editor.keySequence().toString() == 'Ctrl+B'
        assert editor.remove_from_other == a2


@patch('PyQt6.QtWidgets.QMessageBox.question',
       return_value=QtWidgets.QMessageBox.StandardButton.No)
def test_keyboard_shortcuts_editor_conflicts_choose_to_cancel_when_no_shortcut(
        question_mock, view):
    a1 = Action({'id': 'foo', 'text': 'Foo'})
    a2 = Action({'id': 'bar', 'text': 'Bar', 'shortcuts': ['Ctrl+B']})
    with patch('beeref.widgets.settings.actions', ActionList([a1, a2])):
        editor = KeyboardShortcutsEditor(
            view,
            index=MagicMock(
                column=MagicMock(return_value=2),
                row=MagicMock(return_value=0)))
        editor.setKeySequence('Ctrl+B')
        editor.on_editing_finished()
        assert editor.keySequence().toString() == ''
        assert a2.get_shortcuts() == ['Ctrl+B']


def test_keyboard_shortcuts_delegate_setmodeldata(view):
    a1 = Action({'id': 'foo', 'text': 'Foo'})
    a2 = Action({'id': 'bar', 'text': 'Bar', 'shortcuts': ['Ctrl+B']})
    with patch('beeref.widgets.settings.actions', ActionList([a1, a2])):
        model = KeyboardShortcutsModel()
        delegate = KeyboardShortcutsDelegate()
        editor = delegate.createEditor(view, None, index=model.index(0, 2))
        editor.setKeySequence('Ctrl+F')
        delegate.setModelData(
            editor, model, index=model.index(0, 2))
        assert a1.get_shortcuts() == ['Ctrl+F']


def test_keyboard_shortcuts_model_columncount():
    model = KeyboardShortcutsModel()
    model.columnCount(None) == 4


@patch('beeref.widgets.settings.actions',
       ActionList([
           Action({'id': 'foo', 'text': 'Foo', 'shortcuts': ['Ctrl+F']}),
           Action({'id': 'bar', 'text': 'Bar', 'shortcuts': ['Ctrl+B']})
       ]))
def test_keyboard_shortcuts_model_rowcount():
    model = KeyboardShortcutsModel()
    model.rowCount(None) == 2


def test_keyboard_shortcuts_model_data_gets_text():
    action = Action({'id': 'foo', 'text': '&Foo', 'shortcuts': ['Ctrl+F']})
    action.menu_path = ['&Bar', 'Ba&z']
    with patch('beeref.widgets.settings.actions', ActionList([action])):
        model = KeyboardShortcutsModel()
        value = model.data(
            index=MagicMock(
                column=MagicMock(return_value=0),
                row=MagicMock(return_value=0)),
            role=QtCore.Qt.ItemDataRole.DisplayRole)
        assert value == 'Bar: Baz: Foo'


def test_keyboard_shortcuts_model_data_gets_changed_when_not_changed():
    action = Action({'id': 'foo', 'text': 'Foo', 'shortcuts': ['Ctrl+F']})
    with patch('beeref.widgets.settings.actions', ActionList([action])):
        model = KeyboardShortcutsModel()
        value = model.data(
            index=MagicMock(
                column=MagicMock(return_value=1),
                row=MagicMock(return_value=0)),
            role=QtCore.Qt.ItemDataRole.DisplayRole)
        assert value is None


def test_keyboard_shortcuts_model_data_gets_changed_when_changed(kbsettings):
    action = Action({'id': 'foo', 'text': 'Foo', 'shortcuts': ['Ctrl+F']})
    with patch('beeref.widgets.settings.actions', ActionList([action])):
        action.set_shortcuts(['Ctrl+B'])
        model = KeyboardShortcutsModel()
        value = model.data(
            index=MagicMock(
                column=MagicMock(return_value=1),
                row=MagicMock(return_value=0)),
            role=QtCore.Qt.ItemDataRole.DisplayRole)
        assert value == '✎'


def test_keyboard_shortcuts_model_data_gets_shortcut():
    action = Action({'id': 'foo', 'text': 'Foo', 'shortcuts': ['Ctrl+F']})
    with patch('beeref.widgets.settings.actions', ActionList([action])):
        model = KeyboardShortcutsModel()
        value = model.data(
            index=MagicMock(
                column=MagicMock(return_value=2),
                row=MagicMock(return_value=0)),
            role=QtCore.Qt.ItemDataRole.DisplayRole)
        assert value == 'Ctrl+F'


def test_keyboard_shortcuts_model_data_tooltip_changed_when_not_changed():
    action = Action({'id': 'foo', 'text': 'Foo', 'shortcuts': ['Ctrl+F']})
    with patch('beeref.widgets.settings.actions', ActionList([action])):
        model = KeyboardShortcutsModel()
        value = model.data(
            index=MagicMock(
                column=MagicMock(return_value=1),
                row=MagicMock(return_value=0)),
            role=QtCore.Qt.ItemDataRole.ToolTipRole)
        assert value is None


def test_keyboard_shortcuts_model_data_tooltip_changed_when_changed():
    action = Action({'id': 'foo', 'text': 'Foo', 'shortcuts': ['Ctrl+F']})
    action.set_shortcuts(['Ctrl+B'])
    with patch('beeref.widgets.settings.actions', ActionList([action])):
        model = KeyboardShortcutsModel()
        value = model.data(
            index=MagicMock(
                column=MagicMock(return_value=1),
                row=MagicMock(return_value=0)),
            role=QtCore.Qt.ItemDataRole.ToolTipRole)
        assert value == 'Changed from default'


def test_keyboard_shortcuts_model_data_tooltip_shortcut_when_not_changed():
    action = Action({'id': 'foo', 'text': 'Foo', 'shortcuts': ['Ctrl+F']})
    with patch('beeref.widgets.settings.actions', ActionList([action])):
        model = KeyboardShortcutsModel()
        value = model.data(
            index=MagicMock(
                column=MagicMock(return_value=2),
                row=MagicMock(return_value=0)),
            role=QtCore.Qt.ItemDataRole.ToolTipRole)
        assert value is None


def test_keyboard_shortcuts_model_data_tooltip_shortcut_not_changed_not_set():
    action = Action({'id': 'foo', 'text': 'Foo'})
    with patch('beeref.widgets.settings.actions', ActionList([action])):
        model = KeyboardShortcutsModel()
        value = model.data(
            index=MagicMock(
                column=MagicMock(return_value=3),
                row=MagicMock(return_value=0)),
            role=QtCore.Qt.ItemDataRole.ToolTipRole)
        assert value is None


def test_keyboard_shortcuts_model_data_tooltip_shortcut_when_changed():
    action = Action({'id': 'foo', 'text': 'Foo', 'shortcuts': ['Ctrl+F']})
    with patch('beeref.widgets.settings.actions', ActionList([action])):
        action.set_shortcuts(['Ctrl+B'])
        model = KeyboardShortcutsModel()
        value = model.data(
            index=MagicMock(
                column=MagicMock(return_value=2),
                row=MagicMock(return_value=0)),
            role=QtCore.Qt.ItemDataRole.ToolTipRole)
        assert value == 'Default: Ctrl+F'


def test_keyboard_shortcuts_model_data_tooltip_shortcut_changed_from_none():
    action = Action({'id': 'foo', 'text': 'Foo'})
    with patch('beeref.widgets.settings.actions', ActionList([action])):
        action.set_shortcuts(['Ctrl+B'])
        model = KeyboardShortcutsModel()
        value = model.data(
            index=MagicMock(
                column=MagicMock(return_value=2),
                row=MagicMock(return_value=0)),
            role=QtCore.Qt.ItemDataRole.ToolTipRole)
        assert value == 'Default: -'


def test_keyboard_shortcuts_model_setdata_saves():
    action = Action({'id': 'foo', 'shortcuts': ['Ctrl+F']})
    with patch('beeref.widgets.settings.actions', ActionList([action])):
        model = KeyboardShortcutsModel()
        model.setData(
            index=MagicMock(
                column=MagicMock(return_value=2),
                row=MagicMock(return_value=0)),
            value=QtGui.QKeySequence('Ctrl+B'),
            role=None)
        assert action.get_shortcuts() == ['Ctrl+B']


def test_keyboard_shortcuts_model_setdata_saves_second_shortcut():
    action = Action({'id': 'foo', 'shortcuts': ['Ctrl+F']})
    with patch('beeref.widgets.settings.actions', ActionList([action])):
        model = KeyboardShortcutsModel()
        model.setData(
            index=MagicMock(
                column=MagicMock(return_value=3),
                row=MagicMock(return_value=0)),
            value=QtGui.QKeySequence('Ctrl+B'),
            role=None)
        assert action.get_shortcuts() == ['Ctrl+F', 'Ctrl+B']


def test_keyboard_shortcuts_model_setdata_saves_second_shortcut_no_first():
    action = Action({'id': 'foo'})
    with patch('beeref.widgets.settings.actions', ActionList([action])):
        model = KeyboardShortcutsModel()
        model.setData(
            index=MagicMock(
                column=MagicMock(return_value=3),
                row=MagicMock(return_value=0)),
            value=QtGui.QKeySequence('Ctrl+B'),
            role=None)
        assert action.get_shortcuts() == ['Ctrl+B']


def test_keyboard_shortcuts_model_setdata_removes_duplicate():
    action = Action({'id': 'foo', 'shortcuts': ['Ctrl+B']})
    with patch('beeref.widgets.settings.actions', ActionList([action])):
        model = KeyboardShortcutsModel()
        model.setData(
            index=MagicMock(
                column=MagicMock(return_value=3),
                row=MagicMock(return_value=0)),
            value=QtGui.QKeySequence('Ctrl+B'),
            role=None)
        assert action.get_shortcuts() == ['Ctrl+B']


def test_keyboard_shortcuts_model_setdata_remove_from_other():
    a1 = Action({'id': 'foo', 'shortcuts': ['Ctrl+F']})
    a2 = Action({'id': 'bar', 'shortcuts': ['Ctrl+B']})
    with patch('beeref.widgets.settings.actions', ActionList([a1, a2])):
        model = KeyboardShortcutsModel()
        model.setData(
            index=MagicMock(
                column=MagicMock(return_value=2),
                row=MagicMock(return_value=0)),
            value=QtGui.QKeySequence('Ctrl+B'),
            role=None,
            remove_from_other=a2)
        assert a1.get_shortcuts() == ['Ctrl+B']
        assert a2.get_shortcuts() == []


def test_keyboard_shortcuts_model_headerdata():
    model = KeyboardShortcutsModel()
    header = model.headerData(
        0,
        QtCore.Qt.Orientation.Horizontal,
        QtCore.Qt.ItemDataRole.DisplayRole)
    assert header == 'Action'


def test_flags_first_column():
    model = KeyboardShortcutsModel()
    flags = model.flags(model.index(0, 0))
    assert flags == (QtCore.Qt.ItemFlag.ItemIsEnabled
                     | QtCore.Qt.ItemFlag.ItemNeverHasChildren)


def test_flags_shortcut_column():
    model = KeyboardShortcutsModel()
    flags = model.flags(model.index(0, 2))
    assert flags == (QtCore.Qt.ItemFlag.ItemIsEnabled
                     | QtCore.Qt.ItemFlag.ItemNeverHasChildren
                     | QtCore.Qt.ItemFlag.ItemIsEditable)


@patch('beeref.widgets.settings.actions',
       ActionList([Action({'id': 'bar', 'text': 'Bar'}),
                   Action({'id': 'foo', 'text': 'Foo'}),
                   Action({'id': 'baz', 'text': 'Baz'})]))
def test_keyboard_shortcuts_proxy_data_unfiltered():
    proxy = KeyboardShortcutsProxy()
    assert proxy.data(
        proxy.index(0, 0), QtCore.Qt.ItemDataRole.DisplayRole) == 'Bar'
    assert proxy.data(
        proxy.index(1, 0), QtCore.Qt.ItemDataRole.DisplayRole) == 'Foo'
    assert proxy.data(
        proxy.index(2, 0), QtCore.Qt.ItemDataRole.DisplayRole) == 'Baz'


@patch('beeref.widgets.settings.actions',
       ActionList([Action({'id': 'bar', 'text': 'Bar'}),
                   Action({'id': 'foo', 'text': 'Foo'}),
                   Action({'id': 'baz', 'text': 'Baz'})]))
def test_keyboard_shortcuts_proxy_data_filtered():
    proxy = KeyboardShortcutsProxy()
    proxy.setFilterFixedString('b')
    assert proxy.data(
        proxy.index(0, 0), QtCore.Qt.ItemDataRole.DisplayRole) == 'Bar'
    assert proxy.data(
        proxy.index(1, 0), QtCore.Qt.ItemDataRole.DisplayRole) == 'Baz'


def test_keyboard_shortcuts_proxy_setdata_saves_correct_filtered_index():
    a1 = Action({'id': 'bar', 'text': 'Bar'})
    a2 = Action({'id': 'foo', 'text': 'Foo'})
    a3 = Action({'id': 'baz', 'text': 'Baz'})

    with patch('beeref.widgets.settings.actions', ActionList([a1, a2, a3])):
        proxy = KeyboardShortcutsProxy()
        proxy.setFilterFixedString('b')
        proxy.setData(
            index=proxy.index(1, 2),
            value=QtGui.QKeySequence('Ctrl+B'),
            role=None)
        assert a1.get_shortcuts() == []
        assert a2.get_shortcuts() == []
        assert a3.get_shortcuts() == ['Ctrl+B']


def test_keyboard_shortcuts_proxy_setdata_remove_from_other():
    a1 = Action({'id': 'foo', 'shortcuts': ['Ctrl+F']})
    a2 = Action({'id': 'bar', 'shortcuts': ['Ctrl+B']})
    with patch('beeref.widgets.settings.actions', ActionList([a1, a2])):
        proxy = KeyboardShortcutsProxy()
        proxy.setData(
            index=proxy.index(0, 2),
            value=QtGui.QKeySequence('Ctrl+B'),
            role=None,
            remove_from_other=a2)
        assert a1.get_shortcuts() == ['Ctrl+B']
        assert a2.get_shortcuts() == []


@patch('PyQt6.QtWidgets.QMessageBox.question',
       return_value=QtWidgets.QMessageBox.StandardButton.Yes)
@patch('beeref.config.KeyboardSettings.restore_defaults')
def test_keyboard_settings_dialog_on_restore_defaults(
        restore_mock,  msg_mock, kbsettings, view):
    dialog = KeyboardSettingsDialog(view)
    dialog.on_restore_defaults()
    msg_mock.assert_called_once()
    restore_mock.assert_called()
