import os
from abc import ABC, abstractmethod

import attr


@attr.s
class ComicScreen(ABC):
    images_count: int = attr.ib()
    file_name: str = attr.ib(converter=os.path.basename)
    _log = attr.ib()

    @abstractmethod
    def show(self, image, image_index: int):
        ...
