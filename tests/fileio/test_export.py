import pytest

from beeref.fileio.export import (
    exporter_registry,
    SceneToPixmapExporter,
    SceneToSVGExporter,
)


@pytest.mark.parametrize('key,expected',
                         [('png', SceneToPixmapExporter),
                          ('jpg', SceneToPixmapExporter),
                          ('svg', SceneToSVGExporter)])
def test_registry(key, expected):
    exporter_registry[key] == expected
