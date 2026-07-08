from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_rpi_gpio():
    with patch("RPi.GPIO") as mock_obj:
        yield mock_obj
    print(f"{mock_obj} calls: {mock_obj.mock_calls}")


"""Make ``comic_screen_inky`` importable on non-Pi hosts (x86_64 / CI).

The screen module does a top-level ``import RPi.GPIO``. Where the real library
isn't installed (or raises on non-Pi), inject a stub into ``sys.modules`` so the
screen code can be imported and unit-tested for coverage. On a real Raspberry Pi
the genuine module is used; the tests patch ``GPIO`` regardless.
"""
import sys
from unittest import mock

try:
    import RPi.GPIO  # noqa: F401
except Exception:
    sys.modules["RPi"] = mock.MagicMock()
    sys.modules["RPi.GPIO"] = mock.MagicMock()
