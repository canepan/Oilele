import attr
import os
import sys
from oilele.lib.parse_args import LoggingArgumentParser as ArgumentParser
from PIL import Image
from zipfile import ZipFile

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
from pdf2image import convert_from_path, pdfinfo_from_path


def parse_args(argv: list):
    parser = ArgumentParser()
    parser.add_argument('filein')
    return parser.parse_args(argv)


@attr.s
class ComicDisplay(object):
    screen: pygame.Surface = attr.ib()
    images: list = attr.ib()
    curr_index: int = attr.ib(default=0)
    visible: bool = attr.ib(default=False)
    rotate: int = attr.ib(converter=int, default=0)
    ratio: float = attr.ib(default=1.0)
    file_name: str = attr.ib(default='')

    @property
    def curr_image(self):
        return self.images[self.curr_index]

    def next(self):
        self.curr_index += 1
        if self.visible:
            self.show()
        return self.curr_image

    def prev(self):
        self.curr_index -= 1
        if self.visible:
            self.show()
        return self.curr_image

    def show(self, image_changed=True):
        self.visible = True
        if image_changed:
            image = self.curr_image
            surf = pygame.image.fromstring(image.tobytes(), image.size, image.mode).convert()
            self.ratio = image.height / image.width
            if self.rotate:
                surf = pygame.transform.rotate(surf, self.rotate)
            pygame.display.set_caption(f'{self.curr_index}/{len(self.images)} - {self.file_name}')
            self.surf = surf
        else:
            surf = self.surf
        new_size = self.screen.get_size()
        new_size = (self.ratio * new_size[1], new_size[1])
        surf = pygame.transform.smoothscale(surf, new_size)
        self.screen.blit(surf, surf.get_rect())
        pygame.display.flip()


def is_next_event(pyg_event) -> bool:
    return getattr(pyg_event, 'key', getattr(pyg_event, 'button', None)) in (pygame.K_RIGHT, 1)


def is_prev_event(pyg_event) -> bool:
    return getattr(pyg_event, 'key', getattr(pyg_event, 'button', None)) in (pygame.K_LEFT, 3)


def is_quit_event(pyg_event) -> bool:
    return pyg_event.type == pygame.QUIT or getattr(pyg_event, 'key', None) == pygame.K_q


def images_from_archive(file_name: str) -> list:
    images_list = list()
    with ZipFile(file_name, 'r') as archive_file:
        for image_name in sorted(archive_file.namelist()):
            images_list.append(Image.open(archive_file.open(image_name, 'r')))
    return images_list


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    cfg = parse_args(argv)

    pygame.display.init()
    # print(pygame.display.get_desktop_sizes())
    # screen = pygame.display.set_mode((800, 600), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    pygame.display.set_caption(f'Loading {cfg.filein}...')
    try:
        pdf_info = pdfinfo_from_path(cfg.filein)
        cfg.log.info(f'pdf_info: {pdf_info}')
        images = ComicDisplay(screen, convert_from_path(cfg.filein), rotate=pdf_info.get('Page rot'), file_name=cfg.filein)
    except Exception:
        images = ComicDisplay(screen, images_from_archive(cfg.filein), file_name=cfg.filein)

    images.show()
    looping = True
    while looping:
        for pyg_event in pygame.event.get():
            if is_quit_event(pyg_event):
                print(pyg_event)
                looping = False
            elif pyg_event.type == pygame.MOUSEBUTTONDOWN or pyg_event.type == pygame.KEYDOWN:
                # print(pyg_event)
                if is_next_event(pyg_event):
                    images.next()
                elif is_prev_event(pyg_event):
                    images.prev()
            elif pyg_event.type == pygame.VIDEORESIZE:
                print('VIDEORESIZE')
                # images.show(image_changed=False)
            elif pyg_event.type == pygame.WINDOWSIZECHANGED:
                print('WINDOWSIZECHANGED')
                images.show(image_changed=False)
            elif pyg_event.type != pygame.MOUSEMOTION:
                print(pyg_event)

    pygame.quit()


if __name__ == '__main__':
    main()
