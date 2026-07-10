import os
from abc import ABC, abstractmethod
from typing import List, Optional

import attr


@attr.s
class ComicScreen(ABC):
    images_count: int = attr.ib()
    file_name: str = attr.ib(converter=os.path.basename)
    _log = attr.ib()
    extra_options = []

    @abstractmethod
    def show(self, image, image_index: int):
        ...

    @abstractmethod
    def select(self, options: List[str], title: str = "Choose a file") -> Optional[str]:
        """Return the chosen option (e.g. a file path), or None to cancel."""
        ...
