import attr
import pygame
import PIL

from .comic_screen import ComicScreen


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


@attr.s
class ComicScreenPygame(ComicScreen):
    def __attrs_post_init__(self):
        self._curr_image = None
        self._curr_pyg_image = None
        pygame.display.init()
        self.screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)  # | pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption(f'Loading {self.file_name}...')

    def show(self, image: PIL.Image.Image, image_index: int):
        if image != self._curr_image:
            self._curr_image = image
            pygame.display.set_caption(f'{image_index + 1}/{self.images_count} - {self.file_name}')
            image = image.convert('RGBA')
            self._curr_scr_image = image
        else:
            image = self._curr_scr_image
        self._log.debug(f'Thumbnail for: {image}')
        image.thumbnail(self.screen.get_size())
        self._log.debug(f'New size: {image.size} (screen: {self.screen.get_size()})')
        surf = pygame.image.fromstring(image.tobytes(), image.size, image.mode).convert()
        self._log.debug(f'Surface: {surf}')
        self.screen.blit(surf, surf.get_rect())
        pygame.display.flip()

    def main_loop(self, mgr):
        mgr.show()
        looping = True
        while looping:
            for pyg_event in pygame.event.get():
                if is_quit_event(pyg_event):
                    self._log.debug(pyg_event)
                    looping = False
                elif is_next_event(pyg_event):
                    mgr.next()
                elif is_prev_event(pyg_event):
                    mgr.prev()
                elif pygame.vernum.major == 1 and pyg_event.type == pygame.VIDEORESIZE:
                    self._log.debug('VIDEORESIZE')
                    self._log.debug(pyg_event)
                    self.screen = pygame.display.set_mode(pyg_event.dict['size'], pygame.RESIZABLE)
                    mgr.show(image_changed=True)
                elif pygame.vernum.major > 1 and pyg_event.type == pygame.WINDOWSIZECHANGED:
                    self._log.debug('WINDOWSIZECHANGED')
                    mgr.show(image_changed=False)
                elif pyg_event.type != pygame.MOUSEMOTION:
                    self._log.debug(pyg_event)
        pygame.quit()
