import os
import shutil
import sys
import typing
from pathlib import Path

from oilele.lib.parse_args import LoggingArgumentParser as ArgumentParser

try:
    from unrar.rarfile import RarFile

    UNRAR_ENABLED = True
except (ImportError, LookupError) as e:
    UNRAR_ENABLED = False
    if '-v' in sys.argv or '--verbose' in sys.argv:
        print(e)
from zipfile import ZipFile

import attr
import pdf2image
from PIL import Image

from .screen.comic_screen import ComicScreen

SCREENS: typing.Dict[str, ComicScreen] = {}
try:
    from .screen.comic_screen_inky import ComicScreenInky

    INKY_ENABLED = True
    SCREENS['inky'] = ComicScreenInky  # type:ignore
except ImportError as e:
    INKY_ENABLED = False
    if '-v' in sys.argv or '--verbose' in sys.argv:
        print(e)

try:
    from .screen.comic_screen_kivy import ComicScreenKivy

    KIVY_ENABLED = True
    SCREENS['kivy'] = ComicScreenKivy  # type:ignore
except ImportError as e:
    KIVY_ENABLED = False
    if '-v' in sys.argv or '--verbose' in sys.argv:
        print(e)

if shutil.which('chafa'):
    from .screen.comic_screen_chafa import ComicScreenChafa

    CHAFA_ENABLED = True
    SCREENS['ascii'] = ComicScreenChafa  # type:ignore
else:
    CHAFA_ENABLED = False

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from .screen.comic_screen_pygame import ComicScreenPygame  # noqa: E402


def parse_args(argv: list):
    parser = ArgumentParser(app_name=__name__)
    parser.add_argument('filein')
    if SCREENS:
        parser.add_argument('--output-format', default=None)
        g = parser.add_mutually_exclusive_group()
    for k in SCREENS:
        g.add_argument(f'--{k}', f'-{k.replace("-", "")[0].upper()}', action='store_true')
    parser.add_argument('--page', '-p', default=1, type=int, help='Initial page')
    return parser.parse_args(argv)


@attr.s
class OilalaImages(object):
    # this will contain either PIL or pygame image objects, based on the input
    images: list = attr.ib()
    _log = attr.ib()
    file_name: str = attr.ib(default='', converter=os.path.basename)
    curr_index: int = attr.ib(default=0)
    rotate: int = attr.ib(converter=int, default=0)

    @property
    def curr_image(self):
        image = self.images[self.curr_index]
        if self.rotate:
            image = image.rotate(self.rotate, expand=True)
        return image

    def next(self):
        self.curr_index = (self.curr_index + 1) % len(self.images)
        return self.curr_image

    def prev(self):
        self.curr_index = (self.curr_index - 1) % len(self.images)
        return self.curr_image


@attr.s
class ComicManager(object):
    screen: ComicScreen = attr.ib()
    images: OilalaImages = attr.ib()
    log = attr.ib()
    start_page: int = attr.ib(default=1)
    visible: bool = attr.ib(default=False)

    def __attrs_post_init__(self):
        self.images.curr_index = self.start_page - 1

    @property
    def curr_image(self):
        return self.images.curr_image

    def next(self):
        self.images.next()
        if self.visible:
            self.show()

    def prev(self):
        self.images.prev()
        if self.visible:
            self.show()

    def show(self, image_changed=True):
        self.visible = True
        return self.screen.show(self.curr_image, self.images.curr_index)


def images_from_pdf(file_name: str, log) -> OilalaImages:
    pdf_info = pdf2image.pdfinfo_from_path(file_name)
    log.debug(f'pdf_info: {pdf_info}')
    rotate = pdf_info.get('Page rot')
    pdf_images = pdf2image.convert_from_path(file_name)
    # see https://stackoverflow.com/questions/67103934 for the mypy issue
    return OilalaImages(pdf_images, log=log, file_name=file_name, rotate=rotate)  # type: ignore


def images_from_rar_archive(file_name: str, log) -> OilalaImages:
    images_list = list()
    with RarFile(file_name, 'r') as archive_file:
        for image_name in sorted(n for n in archive_file.namelist() if not n.endswith('/')):
            try:
                log.debug(image_name)
                images_list.append(Image.open(archive_file.open(image_name, 'r')))
            except Exception as e:
                log.exception(e)
                log.error(f'Error while adding {image_name} as an image from {file_name}: {e}')
    # see https://stackoverflow.com/questions/67103934 for the mypy issue
    return OilalaImages(images_list, log=log, file_name=file_name)  # type: ignore


def images_from_zip_archive(file_name: str, log) -> OilalaImages:
    images_list = list()
    with ZipFile(file_name, 'r') as archive_file:
        for image_name in sorted(n for n in archive_file.namelist() if not n.endswith('/')):
            try:
                log.debug(image_name)
                images_list.append(Image.open(archive_file.open(image_name, 'r')))
            except Exception as e:
                log.exception(e)
                log.error(f'Error while adding {image_name} as an image from {file_name}: {e}')
    # see https://stackoverflow.com/questions/67103934 for the mypy issue
    return OilalaImages(images_list, log=log, file_name=file_name)  # type: ignore


def images_from_archive(file_name: str, log) -> OilalaImages:
    extractor_funcs = [images_from_pdf, images_from_zip_archive]
    if UNRAR_ENABLED:
        extractor_funcs.append(images_from_rar_archive)
    for extractor in extractor_funcs:
        try:
            images_list = extractor(file_name, log)
            return images_list
        except Exception as e:
            log.debug(f'Error while opening {file_name} via {extractor}: {e}')
    # see https://stackoverflow.com/questions/67103934 for the mypy issue
    return OilalaImages(list(), log, file_name=file_name)  # type: ignore


COMIC_EXTS = {'.pdf', '.cbz', '.cbr', '.zip', '.rar'}


def _comic_files(directory: str) -> list:
    return sorted(str(p) for p in Path(directory).rglob('*') if p.suffix.lower() in COMIC_EXTS)


def _make_screen(cfg, images_count: int, file_name: str):
    for k, m in SCREENS.items():
        if getattr(cfg, k, False):
            extra_args = {key: getattr(cfg, key) for key in m.extra_options if getattr(cfg, key, None) is not None}
            return m(images_count=images_count, file_name=file_name, log=cfg.log, **extra_args)
    return ComicScreenPygame(images_count=images_count, file_name=file_name, log=cfg.log)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    cfg = parse_args(argv)

    if os.path.isdir(cfg.filein):
        files = _comic_files(cfg.filein)
        if not files:
            cfg.log.error(f'No comic files found in {cfg.filein}')
            return 1
        # Build the screen first (no file yet), let it pick one, then load it.
        screen = _make_screen(cfg, images_count=0, file_name=cfg.filein)
        chosen = screen.select(files, title=cfg.filein)
        if not chosen:
            return 0
        images = images_from_archive(chosen, cfg.log)
        screen.images_count = len(images.images)
        screen.file_name = os.path.basename(chosen)
    else:
        images = images_from_archive(cfg.filein, cfg.log)
        screen = _make_screen(cfg, len(images.images), cfg.filein)

    if not images.images:
        cfg.log.error(f'No images found in {cfg.filein}')
        return 1

    mgr = ComicManager(screen, images, cfg.log, start_page=cfg.page)
    screen.main_loop(mgr)
    return 0


if __name__ == '__main__':
    main()
