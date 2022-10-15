import sys
from argparse import ArgumentParser

import attr
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
from pdf2image import convert_from_path


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

    def show(self):
        self.visible = True
        image = self.curr_image
        surf = pygame.transform.smoothscale(pygame.image.fromstring(image.tobytes(), image.size, image.mode).convert(), self.screen.get_size())
        self.screen.blit(surf, surf.get_rect())
        pygame.display.flip()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    cfg = parse_args(argv)

    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption(f'Loading {cfg.filein}...')
    images = ComicDisplay(screen, convert_from_path(cfg.filein))

    pygame.display.set_caption(cfg.filein)
    images.show()
    looping = True
    while looping:
        for pyg_event in pygame.event.get():
            if pyg_event.type == pygame.QUIT:
                looping = False
            elif pyg_event.type == pygame.MOUSEBUTTONDOWN:
                images.next()
            elif pyg_event.type != pygame.MOUSEMOTION:
                print(pyg_event)

    pygame.quit()


if __name__ == '__main__':
    main()
