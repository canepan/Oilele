import logging
from unittest.mock import patch

import pytest
from PIL import Image

# comic_screen_inky imports RPi.GPIO/inky at module load; on non-Pi hosts that
# import fails, so skip this module there instead of erroring at collection.
comic_screen_inky = pytest.importorskip(
    "oilele.screen.comic_screen_inky",
    reason="needs RPi.GPIO/inky (Raspberry Pi only)",
)
ComicScreenInky = comic_screen_inky.ComicScreenInky

DISPLAY_SIZE = (600, 448)  # a landscape Inky panel


@pytest.fixture
def mock_gpio():
    with patch("oilele.screen.comic_screen_inky.GPIO") as mock_obj:
        yield mock_obj
    print(f"{mock_obj} calls: {mock_obj.mock_calls}")


@pytest.fixture
def mock_inky():
    with patch("oilele.screen.comic_screen_inky.inky") as mock_obj:
        yield mock_obj
    print(f"{mock_obj} calls: {mock_obj.mock_calls}")


@pytest.fixture
def inky(mock_gpio, mock_inky):
    mock_inky.auto.return_value.resolution = DISPLAY_SIZE
    return ComicScreenInky(images_count=3, file_name="test.cbz", log=logging.getLogger(__name__))


def test_inky_uses_detected_device(inky, mock_inky):
    assert inky.inky is mock_inky.auto.return_value


@pytest.mark.parametrize("source_size", [(300, 450), (450, 300), DISPLAY_SIZE])
def test_show_composites_page_to_panel(inky, mock_inky, source_size):
    device = mock_inky.auto.return_value
    inky.show(Image.new("RGB", source_size), 0)
    # whatever the source orientation, the page is drawn and pushed to the panel
    device.set_image.assert_called_once()
    device.show.assert_called_once()
    assert device.set_image.call_args.args[0].size == DISPLAY_SIZE


def test_show_each_page_refreshes_the_display(inky, mock_inky):
    device = mock_inky.auto.return_value
    for index in range(3):
        inky.show(Image.new("RGB", (300, 450)), index)
    assert device.show.call_count == 3
