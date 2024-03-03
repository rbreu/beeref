from unittest.mock import patch, MagicMock

from PyQt6.QtCore import Qt

from beeref.config.controls import (
    KeyboardSettings,
    MouseConfig,
    MouseWheelConfig,
)


def test_mousewheelconfig_eq():
    action1 = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=[], invertible=False)
    action2 = MouseWheelConfig(
        id='foo', group='foobar', text='Baz', modifiers=[], invertible=False)
    assert action1 == action2


def test_mousewheelconfig_str():
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=[], invertible=False)
    assert str(action) == 'foo'


def test_mousewheelconfig_kb_settings():
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=[], invertible=False)
    assert isinstance(action.kb_settings, KeyboardSettings)


def test_mousewheelconfig_get_modifiers(kbsettings):
    kbsettings.set_list('MouseWheel', 'foo_modifiers', ['Ctrl', 'Shift'])
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=[], invertible=False)
    assert action.get_modifiers() == ['Ctrl', 'Shift']


def test_mousewheelconfig_get_modifiers_default(kbsettings):
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=['Shift'],
        invertible=False)
    assert action.get_modifiers() == ['Shift']


def test_mousewheelconfig_set_modifiers(kbsettings):
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=[], invertible=False)
    action.set_modifiers(['Shift'])
    assert kbsettings.get_list('MouseWheel', 'foo_modifiers') == ['Shift']


def test_mousewheelconfig_set_modifiers_default(kbsettings):
    kbsettings.set_list('MouseWheel', 'foo_modifiers', ['Alt', 'Ctrl'])
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo',
        modifiers=['Shift'], invertible=False)
    action.set_modifiers(['Shift'])
    assert kbsettings.value('MouseWheel/foo_modifiers') is None


def test_mousewheelconfig_get_inverted(kbsettings):
    kbsettings.set_value('MouseWheel', 'foo_inverted', True)
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=[], invertible=True)
    assert action.get_inverted() is True


def test_mousewheelconfig_get_inverted_default():
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=[], invertible=True)
    assert action.get_inverted() is False


def test_mousewheelconfig_set_inverted(kbsettings):
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=[], invertible=True)
    action.set_inverted(True)
    assert kbsettings.get_value('MouseWheel', 'foo_inverted') is True


def test_mousewheelconfig_set_inverted_default(kbsettings):
    kbsettings.set_value('MouseWheel', 'foo_inverted', True)
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=[], invertible=True)
    action.set_inverted(False)
    assert kbsettings.value('MouseWheel/foo_inverted') is None


def test_mousewheelconfig_modifiers_to_qt_multiple():
    assert MouseWheelConfig.modifiers_to_qt(['Shift', 'Ctrl']) == (
        Qt.KeyboardModifier.ShiftModifier
        | Qt.KeyboardModifier.ControlModifier)


def test_mousewheelconfig_modifiers_to_single():
    assert MouseWheelConfig.modifiers_to_qt(['Alt']) ==\
        Qt.KeyboardModifier.AltModifier


def test_mousewheelconfig_controls_changed_not_changed():
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=['Shift'],
        invertible=True)
    assert action.controls_changed() is False


def test_mousewheelconfig_controls_changed_modifiers_changed():
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=['Shift'],
        invertible=True)
    action.set_modifiers(['Alt'])
    assert action.controls_changed() is True


def test_mousewheelconfig_controls_changed_inverted_changed():
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=['Shift'],
        invertible=True)
    action.set_inverted(True)
    assert action.controls_changed() is True


def test_mousewheelconfig_controls_is_configured_true():
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=['No Modifiers'],
        invertible=True)
    assert action.is_configured() is True


def test_mousewheelconfig_controls_is_configured_false():
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=[], invertible=True)
    assert action.is_configured() is False


def test_mousewheelconfig_controls_remove_controls():
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=['Shift'],
        invertible=True)
    action.set_inverted(True)
    action.remove_controls()
    assert action.get_modifiers() == []
    assert action.get_inverted() is False


def test_mousewheelconfig_conflicts_with_true():
    action1 = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=['Shift'],
        invertible=True)
    action2 = MouseWheelConfig(
        id='bar', group='foobar', text='Bar', modifiers=['Shift'],
        invertible=True)
    assert action1.conflicts_with(action2) is True


def test_mousewheelconfig_conflicts_with_false():
    action1 = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=['Shift'],
        invertible=True)
    action2 = MouseWheelConfig(
        id='bar', group='foobar', text='Bar', modifiers=['Shift', 'Ctrl'],
        invertible=True)
    assert action1.conflicts_with(action2) is False


def test_mousewheelconfig_conflicts_false_when_both_not_configured():
    action1 = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=[],
        invertible=True)
    action2 = MouseWheelConfig(
        id='bar', group='foobar', text='Bar', modifiers=[],
        invertible=True)
    assert action1.conflicts_with(action2) is False


def test_mousewheelconfig_matches_event_true():
    event = MagicMock(
        modifiers=MagicMock(return_value=Qt.KeyboardModifier.AltModifier))
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=['Alt'],
        invertible=True)
    assert action.matches_event(event) is True


def test_mousewheelconfig_matches_event_false():
    event = MagicMock(
        modifiers=MagicMock(return_value=Qt.KeyboardModifier.AltModifier))
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=['Ctrl'],
        invertible=True)
    assert action.matches_event(event) is False


def test_mousewheelconfig_matches_event_false_when_not_configured():
    event = MagicMock(
        modifiers=MagicMock(return_value=Qt.KeyboardModifier.AltModifier))
    action = MouseWheelConfig(
        id='foo', group='foobar', text='Foo', modifiers=[],
        invertible=True)
    assert action.matches_event(event) is False


def test_mouseconfig_get_button(kbsettings):
    kbsettings.set_value('Mouse', 'foo_button', 'Left')
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Middle', modifiers=[],
        invertible=False)
    assert action.get_button() == 'Left'


def test_mouseconfig_get_button_default():
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Left', modifiers=[],
        invertible=False)
    assert action.get_button() == 'Left'


def test_mouseconfig_set_button(kbsettings):
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Left', modifiers=[],
        invertible=False)
    action.set_button('Middle')
    assert kbsettings.get_value('Mouse', 'foo_button') == 'Middle'


def test_mouseconfig_set_button_default(kbsettings):
    kbsettings.set_value('Mouse', 'foo_button', 'Middle')
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Middle', modifiers=[],
        invertible=False)
    action.set_button('Middle')
    assert kbsettings.value('Mouse/foo_button') is None


def test_mouseconfig_conflicts_with_true():
    action1 = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Left',
        modifiers=['Shift'], invertible=True)
    action2 = MouseConfig(
        id='bar', group='foobar', text='Bar', button='Left',
        modifiers=['Shift'], invertible=True)
    assert action1.conflicts_with(action2) is True


def test_mouseconfig_conflicts_with_false_when_diff_buttons():
    action1 = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Left',
        modifiers=['Shift'], invertible=True)
    action2 = MouseConfig(
        id='bar', group='foobar', text='Bar', button='Middle',
        modifiers=['Shift'], invertible=True)
    assert action1.conflicts_with(action2) is False


def test_mouseconfig_conflicts_with_false_when_diff_modifiers():
    action1 = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Middle',
        modifiers=['Shift'], invertible=True)
    action2 = MouseConfig(
        id='bar', group='foobar', text='Bar', button='Middle',
        modifiers=['Shift', 'Ctrl'], invertible=True)
    assert action1.conflicts_with(action2) is False


def test_mouseconfig_conflicts_false_when_both_not_configured():
    action1 = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Not Configured',
        modifiers=[], invertible=True)
    action2 = MouseConfig(
        id='bar', group='foobar', text='Bar', button='Not Configured',
        modifiers=[], invertible=True)
    assert action1.conflicts_with(action2) is False


def test_mouseconfig_is_configured_false():
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Middle',
        modifiers=[], invertible=True)
    action.set_button('Not Configured')
    assert action.conflicts_with(action) is False


def test_mouseconfig_is_configured_true():
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Not Configured',
        modifiers=[], invertible=True)
    action.set_button('Left')
    assert action.conflicts_with(action) is True


def test_mouseconfig_controls_changed_false():
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Middle',
        modifiers=['Shift'], invertible=True)
    action.controls_changed() is False


def test_mouseconfig_controls_changed_true_when_button_changed():
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Middle',
        modifiers=['Shift'], invertible=True)
    action.set_button('Left')
    action.controls_changed() is True


def test_mouseconfig_controls_changed_true_when_modifiers_changed():
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Middle',
        modifiers=['Shift'], invertible=True)
    action.set_modifiers(['Shift', 'Ctrl'])
    action.controls_changed() is True


def test_mouseconfig_controls_changed_true_when_inverted_changed():
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Middle',
        modifiers=['Shift'], invertible=True)
    action.set_inverted(True)
    action.controls_changed() is True


def test_mouseconfig_remove_controls():
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Middle',
        modifiers=['Shift'], invertible=True)
    action.set_inverted(True)

    action.remove_controls()
    assert action.get_button() == 'Not Configured'
    assert action.get_modifiers() == []
    assert action.get_inverted() is False


def test_mouseconfig_matches_event_true():
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
        modifiers=MagicMock(return_value=Qt.KeyboardModifier.AltModifier))
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Left',
        modifiers=['Alt'], invertible=True)
    assert action.matches_event(event) is True


def test_mouseconfig_matches_event_false_when_diff_button():
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
        modifiers=MagicMock(return_value=Qt.KeyboardModifier.AltModifier))
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Middle',
        modifiers=['Alt'], invertible=True)
    assert action.matches_event(event) is False


def test_mouseconfig_matches_event_false_when_diff_modifiers():
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
        modifiers=MagicMock(return_value=Qt.KeyboardModifier.AltModifier))
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Left',
        modifiers=['Ctrl'], invertible=True)
    assert action.matches_event(event) is False


def test_mouseconfig_matches_event_false_when_not_configured():
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.LeftButton),
        modifiers=MagicMock(return_value=Qt.KeyboardModifier.AltModifier))
    action = MouseConfig(
        id='foo', group='foobar', text='Foo', button='Not Configured',
        modifiers=[], invertible=True)
    assert action.matches_event(event) is False


def test_keyboardsettings_set_value(kbsettings):
    kbsettings.set_value('mygroup', 'foo', 'bar')
    assert kbsettings.value('mygroup/foo', 'bar')


def test_keyboardsettings_set_value_default_value(kbsettings):
    kbsettings.setValue('mygroup/foo', 'bar')
    kbsettings.set_value('mygroup', 'foo', 'baz', 'baz')
    assert kbsettings.value('mygroup/foo') is None


def test_keyboardsettings_get_value_existing(kbsettings):
    kbsettings.set_value('mygroup', 'bar', 'foo')
    value = kbsettings.get_value('mygroup', 'bar', 'baz')
    assert value == 'foo'


def test_keyboardsettings_get_value_default(kbsettings):
    assert kbsettings.get_value('mygroup', 'bar', 'baz') == 'baz'


def test_keyboardsettings_set_list(kbsettings):
    kbsettings.set_list('mygroup', 'foo', ['Ctrl+F'])
    assert kbsettings.get_list('mygroup', 'foo') == ['Ctrl+F']


def test_keyboardsettings_set_list_multiple(kbsettings):
    kbsettings.set_list('mygroup', 'foo', ['Ctrl+F', 'Alt+O'])
    assert kbsettings.get_list('mygroup', 'foo') == ['Ctrl+F', 'Alt+O']


def test_keyboardsettings_set_list_default_value(kbsettings):
    kbsettings.setValue('mygroup/foo', 'Ctrl+F')
    kbsettings.set_list('mygroup', 'foo', 'Ctrl+B', 'Ctrl+B')
    assert kbsettings.value('mygroup/foo') is None


def test_keyboardsettings_get_list_existing(kbsettings):
    kbsettings.set_list('mygroup', 'bar', ['Ctrl+R'])
    shortcuts = kbsettings.get_list('mygroup', 'bar', ['Ctrl+B'])
    assert shortcuts == ['Ctrl+R']


def test_keyboardsettings_get_list_existing_empty_list(kbsettings):
    kbsettings.set_list('mygroup', 'bar', [])
    shortcuts = kbsettings.get_list('mygroup', 'bar', ['Ctrl+B'])
    assert shortcuts == []


def test_keyboardsettings_get_list_default(kbsettings):
    shortcuts = kbsettings.get_list('mygroup', 'bar', ['Ctrl+B'])
    assert shortcuts == ['Ctrl+B']


@patch('beeref.config.KeyboardSettings.setValue')
@patch('beeref.config.KeyboardSettings.remove')
def test_keyboardsettings_set_list_other_than_default_saves(
        remove_mock, set_mock, kbsettings):
    kbsettings.set_list('mygroup', 'bar', ['Ctrl+R'], ['Ctrl+Z'])
    set_mock.assert_called_once_with('mygroup/bar', 'Ctrl+R')
    remove_mock.assert_not_called()


@patch('beeref.config.KeyboardSettings.setValue')
@patch('beeref.config.KeyboardSettings.remove')
def test_keyboardsettings_set_list_with_than_default_doesnt_save(
        remove_mock, set_mock, kbsettings):
    kbsettings.set_list('mygroup', 'bar', ['Ctrl+R'], ['Ctrl+R'])
    set_mock.assert_not_called()
    remove_mock.assert_called_once_with('mygroup/bar')


@patch('PyQt6.QtGui.QAction.setShortcuts')
def test_keyboardsettings_restore_defaults_restores(shortcut_mock, kbsettings):
    kbsettings.setValue('Actions/bar', 'Ctrl+R')
    kbsettings.restore_defaults()
    assert kbsettings.contains('Actions/bar') is False


def test_keyboardsettings_mousewheel_action_for_event_finds(kbsettings):
    action = kbsettings.MOUSEWHEEL_ACTIONS['zoom1']
    action.set_modifiers(['Shift', 'Ctrl', 'Alt'])
    action.set_inverted(True)

    event = MagicMock(
        modifiers=MagicMock(
            return_value=(Qt.KeyboardModifier.AltModifier
                          | Qt.KeyboardModifier.ShiftModifier
                          | Qt.KeyboardModifier.ControlModifier)))

    group, inverted = kbsettings.mousewheel_action_for_event(event)
    assert group == 'zoom'
    assert inverted is True


def test_keyboardsettings_mousewheel_action_for_event_empty(kbsettings):
    event = MagicMock(
        modifiers=MagicMock(
            return_value=(Qt.KeyboardModifier.AltModifier
                          | Qt.KeyboardModifier.ShiftModifier
                          | Qt.KeyboardModifier.ControlModifier)))

    group, inverted = kbsettings.mousewheel_action_for_event(event)
    assert group is None
    assert inverted is None


def test_keyboardsettings_mouse_action_for_event_finds(kbsettings):
    action = kbsettings.MOUSE_ACTIONS['zoom1']
    action.set_button('Middle')
    action.set_modifiers(['Shift', 'Ctrl', 'Alt'])
    action.set_inverted(True)

    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.MiddleButton),
        modifiers=MagicMock(
            return_value=(Qt.KeyboardModifier.AltModifier
                          | Qt.KeyboardModifier.ShiftModifier
                          | Qt.KeyboardModifier.ControlModifier)))

    group, inverted = kbsettings.mouse_action_for_event(event)
    assert group == 'zoom'
    assert inverted is True


def test_keyboardsettings_mouse_action_for_event_empty(kbsettings):
    event = MagicMock(
        button=MagicMock(return_value=Qt.MouseButton.MiddleButton),
        modifiers=MagicMock(
            return_value=(Qt.KeyboardModifier.AltModifier
                          | Qt.KeyboardModifier.ShiftModifier
                          | Qt.KeyboardModifier.ControlModifier)))

    group, inverted = kbsettings.mouse_action_for_event(event)
    assert group is None
    assert inverted is None
