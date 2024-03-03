from unittest.mock import patch, MagicMock

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import Qt

from beeref.config.controls import MouseWheelConfig
from beeref.widgets.controls.mousewheel import (
    MouseWheelDelegate,
    MouseWheelModifiersEditor,
    MouseWheelModel,
    MouseWheelProxy,
)
from beeref.utils import ActionList


def test_mousewheel_editor_inits_modifiers_when_not_configured(view):
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=[],
        invertible=True)
    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    assert len(editor.checkboxes) == 6
    for checkbox in editor.checkboxes.values():
        assert checkbox.isChecked() is False


def test_mousewheel_editor_inits_modifiers_when_configured(view):
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt', 'Ctrl'],
        invertible=True)
    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    assert len(editor.checkboxes) == 6
    for key, checkbox in editor.checkboxes.items():
        if key in ('Alt', 'Ctrl'):
            assert checkbox.isChecked() is True
        else:
            assert checkbox.isChecked() is False


def test_mousewheel_editor_set_modifiers_no_modifier(view):
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt', 'Ctrl'],
        invertible=True)
    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    editor.set_modifiers_no_modifier()
    for key, checkbox in editor.checkboxes.items():
        if key == 'No Modifier':
            assert checkbox.isChecked() is True
        else:
            assert checkbox.isChecked() is False


def test_mousewheel_editor_on_modifiers_changed_no_modifiers_checked(view):
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt', 'Ctrl'],
        invertible=True)
    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    editor.on_modifiers_changed('No Modifier', Qt.CheckState.Checked.value)
    for key, checkbox in editor.checkboxes.items():
        if key == 'No Modifier':
            assert checkbox.isChecked() is True
        else:
            assert checkbox.isChecked() is False


def test_mousewheel_editor_on_modifiers_changed_when_a_modifier_checked(view):
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['No Modifier'],
        invertible=True)
    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    editor.on_modifiers_changed('Alt', Qt.CheckState.Checked.value)
    for key, checkbox in editor.checkboxes.items():
        if key == 'No Modifier':
            assert checkbox.isChecked() is False


def test_mousewheel_editor_on_modifiers_changed_everything_unchecked(view):
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=[],
        invertible=True)
    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    editor.on_modifiers_changed('Alt', Qt.CheckState.Unchecked.value)
    for key, checkbox in editor.checkboxes.items():
        if key == 'No Modifier':
            assert checkbox.isChecked() is True
        else:
            assert checkbox.isChecked() is False


def test_mousewheel_editor_get_modifiers(view):
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=[],
        invertible=True)
    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    editor.checkboxes['Alt'].setChecked(True)
    editor.get_modifiers() == ['Alt']


def test_mousewheel_editor_get_modifiers_when_no_modifiers(view):
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=[],
        invertible=True)
    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    editor.ignore_on_changed = True
    editor.checkboxes['No Modifier'].setChecked(True)
    editor.checkboxes['Alt'].setChecked(True)
    editor.get_modifiers() == ['No Modifier']


def test_mousewheel_editor_get_modifiers_when_no_modifiers_cleaned_false(view):
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=[],
        invertible=True)
    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    editor.ignore_on_changed = True
    editor.checkboxes['Shift'].setChecked(True)
    editor.checkboxes['Alt'].setChecked(True)
    editor.ignore_on_changed = False

    assert editor.get_modifiers(cleaned=False) == ['Shift', 'Alt']


def test_mousewheel_editor_set_modifiers(view):
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=[],
        invertible=True)
    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    editor.set_modifiers(['Alt', 'Shift'])
    for key, checkbox in editor.checkboxes.items():
        if key in ['Alt', 'Shift']:
            assert checkbox.isChecked() is True
        else:
            assert checkbox.isChecked() is False


def test_mousewheel_editor_get_temp_action(view):
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)
    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    tmp = editor.get_temp_action()
    assert tmp.get_modifiers() == ['Alt']


def test_mousewheel_editor_reset_inputs(view):
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)
    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    editor.set_modifiers(['Ctrl'])
    editor.reset_inputs()
    assert editor.get_modifiers() == ['Alt']


@patch('beeref.widgets.controls.mousewheel.MouseWheelModifiersEditor.accept')
def test_mousewheel_editor_on_save_no_conflicts(accept_mock, view):
    a1 = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)
    a2 = MouseWheelConfig(
        id='bar1',
        group='bar',
        text='Bar',
        modifiers=['Ctrl'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([a1, a2])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    editor.set_modifiers(['Shift'])
    editor.on_save()
    assert editor.get_modifiers() == ['Shift']
    assert editor.remove_from_other is None
    accept_mock.assert_called_once_with()


@patch('beeref.widgets.controls.mousewheel.MouseWheelModifiersEditor.accept')
def test_mousewheel_editor_on_save_reenter_existing_shortcut(
        accept_mock, view):
    a1 = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)
    a2 = MouseWheelConfig(
        id='bar1',
        group='bar',
        text='Bar',
        modifiers=['Ctrl'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([a1, a2])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    editor.on_save()
    assert editor.get_modifiers() == ['Alt']
    assert editor.remove_from_other is None
    accept_mock.assert_called_once_with()


@patch('PyQt6.QtWidgets.QMessageBox.question',
       return_value=QtWidgets.QMessageBox.StandardButton.No)
@patch('beeref.widgets.controls.mousewheel.MouseWheelModifiersEditor.accept')
def test_mousewheel_editor_on_save_conflicts_cancel(
        accept_mock, msg_mock, view):
    a1 = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)
    a2 = MouseWheelConfig(
        id='bar1',
        group='bar',
        text='Bar',
        modifiers=['Ctrl'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([a1, a2])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    editor.set_modifiers(['Ctrl'])
    editor.on_save()
    assert editor.get_modifiers() == ['Alt']
    assert editor.remove_from_other is None
    accept_mock.assert_not_called()


@patch('PyQt6.QtWidgets.QMessageBox.question',
       return_value=QtWidgets.QMessageBox.StandardButton.Yes)
@patch('beeref.widgets.controls.mousewheel.MouseWheelModifiersEditor.accept')
def test_mousewheel_editor_on_save_conflicts_confirm(
        accept_mock, msg_mock, view):
    a1 = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)
    a2 = MouseWheelConfig(
        id='bar1',
        group='bar',
        text='Bar',
        modifiers=['Ctrl'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([a1, a2])):
        editor = MouseWheelModifiersEditor(
            view, index=MagicMock(row=MagicMock(return_value=0)))

    editor.set_modifiers(['Ctrl'])
    editor.on_save()
    assert editor.get_modifiers() == ['Ctrl']
    assert editor.remove_from_other == a2
    accept_mock.assert_called_once_with()


def test_mousewheel_delegate_create_editor(view):
    delegate = MouseWheelDelegate()
    model = MouseWheelModel()
    widget = delegate.createEditor(
        view, QtWidgets.QStyleOptionViewItem(), index=model.index(0, 3))
    assert isinstance(widget.editor, MouseWheelModifiersEditor)


def test_mousewheel_delegate_setmodeldata(view):
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)
    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        delegate = MouseWheelDelegate()
        model = MouseWheelModel()
        widget = delegate.createEditor(
            view, QtWidgets.QStyleOptionViewItem(), index=model.index(0, 2))
        widget.editor.set_modifiers(['Ctrl', 'Shift'])

    with patch.object(widget.editor, 'result',
                      return_value=QtWidgets.QDialog.DialogCode.Accepted):
        delegate.setModelData(widget, model, index=model.index(0, 2))
        assert action.get_modifiers() == ['Shift', 'Ctrl']


def test_mousewheel_model_columncount():
    model = MouseWheelModel()
    model.columnCount(None) == 3


def test_mousewheel_model_rowcount():
    a1 = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)
    a2 = MouseWheelConfig(
        id='bar1',
        group='bar',
        text='Bar',
        modifiers=['Ctrl'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([a1, a2])):
        model = MouseWheelModel()
        model.rowCount(None) == 2


def test_mousewheel_model_headerdata():
    model = MouseWheelModel()
    header = model.headerData(
        0,
        QtCore.Qt.Orientation.Horizontal,
        QtCore.Qt.ItemDataRole.DisplayRole)
    assert header == 'Action'


def test_flags_first_column():
    model = MouseWheelModel()
    flags = model.flags(model.index(0, 0))
    assert flags == (QtCore.Qt.ItemFlag.ItemIsEnabled
                     | QtCore.Qt.ItemFlag.ItemNeverHasChildren)


def test_flags_modifiers_column():
    model = MouseWheelModel()
    flags = model.flags(model.index(0, 2))
    assert flags == (QtCore.Qt.ItemFlag.ItemIsEnabled
                     | QtCore.Qt.ItemFlag.ItemNeverHasChildren
                     | QtCore.Qt.ItemFlag.ItemIsEditable)


def test_flags_inverted_column_when_invertible():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    flags = model.flags(model.index(0, 4))
    assert flags == (QtCore.Qt.ItemFlag.ItemIsEnabled
                     | QtCore.Qt.ItemFlag.ItemNeverHasChildren
                     | QtCore.Qt.ItemFlag.ItemIsEditable
                     | QtCore.Qt.ItemFlag.ItemIsUserCheckable)


def test_flags_inverted_column_when_not_invertible():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=False)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    flags = model.flags(model.index(0, 4))
    assert flags == (QtCore.Qt.ItemFlag.ItemIsEnabled
                     | QtCore.Qt.ItemFlag.ItemNeverHasChildren)


def test_mousewheel_model_data_gets_text():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=False)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=0),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.DisplayRole)
    assert value == 'Foo'


def test_mousewheel_model_data_gets_changed_when_not_changed():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=False)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=1),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.DisplayRole)
    assert value is None


def test_mousewheel_model_data_gets_changed_when_changed():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=False)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    action.set_modifiers(['Shift'])
    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=1),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.DisplayRole)
    assert value == '✎'


def test_mousewheel_model_data_gets_modifiers():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Ctrl', 'Alt'],
        invertible=False)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=2),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.DisplayRole)
    assert value == 'Ctrl + Alt'


def test_mousewheel_model_data_gets_inverted_when_invertible():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Ctrl', 'Alt'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=3),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.DisplayRole)
    assert value == 'No'


def test_mousewheel_model_data_gets_inverted_when_not_invertible():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Ctrl', 'Alt'],
        invertible=False)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=3),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.DisplayRole)
    assert value is None


def test_mousewheel_model_data_tooltip_changed_when_not_changed():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Ctrl', 'Alt'],
        invertible=False)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()
    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=1),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.ToolTipRole)
    assert value is None


def test_mousewheel_model_data_tooltip_changed_when_changed():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=False)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    action.set_modifiers(['Shift'])
    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=1),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.ToolTipRole)
    assert value == 'Changed from default'


def test_mousewheel_model_data_tooltip_modifiers_changed_from_not_configured():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=[],
        invertible=False)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    action.set_modifiers(['Shift'])
    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=2),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.ToolTipRole)
    assert value == 'Default: Not configured'


def test_mousewheel_model_data_tooltip_modifiers_when_changed():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Ctrl', 'Alt'],
        invertible=False)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    action.set_modifiers(['Shift'])
    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=2),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.ToolTipRole)
    assert value == 'Default: Ctrl + Alt'


def test_mousewheel_model_data_tooltip_inverted_when_changed_and_invertible():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    action.set_inverted(True)
    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=3),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.ToolTipRole)
    assert value == 'Default: No'


def test_mousewheel_model_data_tooltip_inverted_changed_and_not_invertible():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=False)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    action.set_modifiers(['Shift'])
    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=3),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.ToolTipRole)
    assert value is None


def test_mousewheel_model_data_checkstaterole_invertible_invertcol_inverted():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    action.set_inverted(True)
    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=3),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.CheckStateRole)
    assert value == Qt.CheckState.Checked


def test_mousewheel_model_data_checkstaterole_invertible_invcol_not_inverted():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=3),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.CheckStateRole)
    assert value == Qt.CheckState.Unchecked


def test_mousewheel_model_data_checkstaterole_other_column():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    value = model.data(
        index=MagicMock(
            column=MagicMock(return_value=2),
            row=MagicMock(return_value=0)),
        role=QtCore.Qt.ItemDataRole.CheckStateRole)
    assert value is None


def test_mousewheel_model_setdate_saves_inverted():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    model.setData(
        index=MagicMock(
            column=MagicMock(return_value=3),
            row=MagicMock(return_value=0)),
        value=Qt.CheckState.Checked.value,
        role=None)
    assert action.get_inverted() is True


def test_mousewheel_model_setdata_saves_controls():
    action = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([action])):
        model = MouseWheelModel()

    model.setData(
        index=MagicMock(
            column=MagicMock(return_value=2),
            row=MagicMock(return_value=0)),
        value=['Ctrl'],
        role=None)

    assert action.get_modifiers() == ['Ctrl']


def test_mousewheel_model_setdata_saves_controls_and_removes_from_other():
    a1 = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)
    a2 = MouseWheelConfig(
        id='bar1',
        group='bar',
        text='Bar',
        modifiers=['Ctrl'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([a1, a2])):
        model = MouseWheelModel()

    model.setData(
        index=MagicMock(
            column=MagicMock(return_value=2),
            row=MagicMock(return_value=0)),
        value=['Ctrl'],
        role=None,
        remove_from_other=a2)

    assert a1.get_modifiers() == ['Ctrl']
    assert a2.get_modifiers() == []


def test_mousewheel_proxy_data_unfiltered():
    a1 = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)
    a2 = MouseWheelConfig(
        id='bar1',
        group='bar',
        text='Bar',
        modifiers=['Ctrl'],
        invertible=True)
    a3 = MouseWheelConfig(
        id='baz1',
        group='baz',
        text='Baz',
        modifiers=['Shift'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([a2, a1, a3])):
        proxy = MouseWheelProxy()

    assert proxy.data(
        proxy.index(0, 0), QtCore.Qt.ItemDataRole.DisplayRole) == 'Bar'
    assert proxy.data(
        proxy.index(1, 0), QtCore.Qt.ItemDataRole.DisplayRole) == 'Foo'
    assert proxy.data(
        proxy.index(2, 0), QtCore.Qt.ItemDataRole.DisplayRole) == 'Baz'


def test_mousewheel_proxy_data_filtered():
    a1 = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)
    a2 = MouseWheelConfig(
        id='bar1',
        group='bar',
        text='Bar',
        modifiers=['Ctrl'],
        invertible=True)
    a3 = MouseWheelConfig(
        id='baz1',
        group='baz',
        text='Baz',
        modifiers=['Shift'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([a2, a1, a3])):
        proxy = MouseWheelProxy()

    proxy.setFilterFixedString('b')
    assert proxy.data(
        proxy.index(0, 0), QtCore.Qt.ItemDataRole.DisplayRole) == 'Bar'
    assert proxy.data(
        proxy.index(1, 0), QtCore.Qt.ItemDataRole.DisplayRole) == 'Baz'


def test_mousewheel_proxy_setdata_saves_correct_filtered_index():
    a1 = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)
    a2 = MouseWheelConfig(
        id='bar1',
        group='bar',
        text='Bar',
        modifiers=['Ctrl'],
        invertible=True)
    a3 = MouseWheelConfig(
        id='baz1',
        group='baz',
        text='Baz',
        modifiers=['Shift'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([a2, a1, a3])):
        proxy = MouseWheelProxy()

    proxy.setFilterFixedString('b')
    proxy.setData(
        index=proxy.index(1, 3),
        value={'modifiers': ['Ctrl', 'Alt']},
        role=None)

    a3.get_modifiers() == ['Ctrl', 'Alt']


def test_mousewheel_proxy_setdata_remove_from_other():
    a1 = MouseWheelConfig(
        id='foo1',
        group='foo',
        text='Foo',
        modifiers=['Alt'],
        invertible=True)
    a2 = MouseWheelConfig(
        id='bar1',
        group='bar',
        text='Bar',
        modifiers=['Ctrl'],
        invertible=True)

    with patch('beeref.config.controls.KeyboardSettings.MOUSEWHEEL_ACTIONS',
               ActionList([a2, a1])):
        proxy = MouseWheelProxy()

    proxy.setData(
        index=proxy.index(0, 3),
        value={'modifiers': ['Ctrl', 'Alt']},
        role=None,
        remove_from_other=a2)

    a1.get_modifiers() == ['Ctrl', 'Alt']
    a2.get_modifiers() == []
