from unittest.mock import patch

from PyQt6 import QtWidgets

from beeref.widgets.settings import (
    ArrangeGapWidget,
    ImageStorageFormatWidget,
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
