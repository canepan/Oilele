import attr
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from oilele.lib.parse_args import LoggingArgumentParser as ArgumentParser
from zipfile import ZipFile

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pdf2image  # noqa: E402
import pygame  # noqa: E402


def parse_args(argv: list):
    parser = ArgumentParser()
    parser.add_argument('filein')
    parser.add_argument('--ascii', '-a', action='store_true')
    return parser.parse_args(argv)


@attr.s
class OilalaImages(object):
    # this will contain either image objects, or file names
    # (if the "screen" is based on an external command)
    images: list = attr.ib()
    _log = attr.ib()
    file_name: str = attr.ib(default='', converter=os.path.basename)
    rotate: int = attr.ib(converter=int, default=0)

    def __attrs_post_init__(self):
        self.curr_index = 0

    # @abstractmethod
    # def filename(self) -> str:
    #     ...

    # @abstractmethod
    # def native_object(self):
    #     ...

    @property
    def curr_image(self):
        return self.images[self.curr_index]

    def next(self):
        self.curr_index += 1
        return self.curr_image

    def prev(self):
        self.curr_index -= 1
        return self.curr_image


@attr.s
class ComicScreen(ABC):
    images_count: int = attr.ib()
    file_name: str = attr.ib()
    _log = attr.ib()

    @abstractmethod
    def show(self, image, image_index: int, rotate: int = 0):
        ...


@attr.s
class ComicScreenPygame(ComicScreen):
    def __attrs_post_init__(self):
        self._curr_image = None
        pygame.display.init()
        self.screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)  # | pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption(f'Loading {self.file_name}...')

    def show(self, image: pygame.surface.Surface, image_index: int, rotate: int = 0):
        if image != self._curr_image:
            surf = image
            self.ratio = surf.get_height() / surf.get_width()
            if rotate:
                surf = pygame.transform.rotate(surf, rotate)
            pygame.display.set_caption(f'{image_index + 1}/{self.images_count} - {self.file_name}')
            self._curr_image = surf
        else:
            surf = self._curr_image
        self._log.debug(f'Surface: {surf}')
        width, height = self.screen.get_size()
        new_size = (self.ratio * height, height)
        surf = pygame.transform.smoothscale(surf, new_size)
        self.screen.blit(surf, surf.get_rect())
        pygame.display.flip()


@attr.s
class ComicScreenChafa(ComicScreen):
    def __attrs_post_init__(self):
        self._curr_image = None

    def show(self, image: str, image_index: int, rotate: int = 0):
        self._log.info(f'{image_index}/{self.images_count} - {self.file_name}')
        subprocess.check_output(['chafa', '-f', 'sixels', image])


@attr.s
class ComicManager(object):
    screen: ComicScreen = attr.ib()
    images: OilalaImages = attr.ib()
    log = attr.ib()
    # curr_index: int = attr.ib(default=0)
    visible: bool = attr.ib(default=False)
    rotate: int = attr.ib(converter=int, default=0)
    # ratio: float = attr.ib(default=1.0)
    # file_name: str = attr.ib(default='', converter=os.path.basename)

    @property
    def curr_image(self):
        image = self.images.curr_image
        try:
            return pygame.image.fromstring(image.tobytes(), image.size, image.mode).convert()
        except Exception as e:
            self.log.debug(e)
            return image

    def next(self):
        self.images.next()
        if self.visible:
            self.show()
        # return self.curr_image

    def prev(self):
        self.images.prev()
        if self.visible:
            self.show()
        # return self.curr_image

    def show(self, image_changed=True):
        self.visible = True
        return self.screen.show(self.curr_image, self.images.curr_index, self.images.rotate)


@attr.s
class ComicManagerPil(ComicManager):
    @property
    def curr_image(self):
        image = self.images.curr_image
        self.log.debug(f'Image: {image}')
        return pygame.image.fromstring(image.tobytes(), image.size, image.mode).convert()


def is_mouse_or_key(pyg_event, mouse_button, key) -> bool:
    return (pyg_event.type == pygame.MOUSEBUTTONDOWN and pyg_event.button == mouse_button) or (
        pyg_event.type == pygame.KEYDOWN and pyg_event.key == key
    )


def is_next_event(pyg_event) -> bool:
    return is_mouse_or_key(pyg_event, 1, pygame.K_RIGHT)


def is_prev_event(pyg_event) -> bool:
    return is_mouse_or_key(pyg_event, 3, pygame.K_LEFT)


def is_quit_event(pyg_event) -> bool:
    return pyg_event.type == pygame.QUIT or getattr(pyg_event, 'key', None) == pygame.K_q


def images_from_archive(file_name: str, log) -> list:
    images_list = list()
    with ZipFile(file_name, 'r') as archive_file:
        for image_name in sorted(n for n in archive_file.namelist() if not n.endswith('/')):
            try:
                log.debug(image_name)
                images_list.append(pygame.image.load(archive_file.open(image_name, 'r')))
            # except PIL.UnidentifiedImageError as e:
            except Exception as e:
                log.exception(e)
                log.error(f'Error while adding {image_name} as an image from {file_name}: {e}')
    return images_list


def main_loop(mgr, log):
    looping = True
    while looping:
        for pyg_event in pygame.event.get():
            if is_quit_event(pyg_event):
                log.debug(pyg_event)
                looping = False
            elif is_next_event(pyg_event):
                mgr.next()
            elif is_prev_event(pyg_event):
                mgr.prev()
            elif pyg_event.type == pygame.VIDEORESIZE:
                log.debug('VIDEORESIZE')
            elif pyg_event.type == pygame.WINDOWSIZECHANGED:
                log.debug('WINDOWSIZECHANGED')
                mgr.show(image_changed=False)
            elif pyg_event.type != pygame.MOUSEMOTION:
                log.debug(pyg_event)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    cfg = parse_args(argv)

    try:
        pdf_info = pdf2image.pdfinfo_from_path(cfg.filein)
        cfg.log.info(f'pdf_info: {pdf_info}')
        rotate = pdf_info.get('Page rot')
        images = OilalaImages(pdf2image.convert_from_path(cfg.filein), log=cfg.log, file_name=cfg.filein, rotate=rotate)
    except pdf2image.exceptions.PDFPageCountError as e:
        cfg.log.debug(e)
        images = OilalaImages(images_from_archive(cfg.filein, cfg.log), cfg.log, file_name=cfg.filein)
    if cfg.ascii:
        screen = ComicScreenChafa(images_count=len(images.images), file_name=cfg.filein, log=cfg.log)
    else:
        screen = ComicScreenPygame(images_count=len(images.images), file_name=cfg.filein, log=cfg.log)
    mgr = ComicManager(screen, images, cfg.log)

    mgr.show()
    main_loop(mgr, cfg.log)

    pygame.quit()


if __name__ == '__main__':
    main()
