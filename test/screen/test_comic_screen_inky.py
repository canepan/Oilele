import logging
from unittest.mock import patch

import pytest

# comic_screen_inky imports RPi.GPIO/inky at module load; on non-Pi hosts that
# import fails, so skip this module there instead of erroring at collection.
comic_screen_inky = pytest.importorskip(
    "oilele.screen.comic_screen_inky",
    reason="needs RPi.GPIO/inky (Raspberry Pi only)",
)
ComicScreenInky = comic_screen_inky.ComicScreenInky


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


def test_inky(mock_gpio, mock_inky):
    inky = ComicScreenInky(images_count=3, file_name="test.cbz", log=logging.getLogger(__name__))
