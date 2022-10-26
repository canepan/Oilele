import curses
import subprocess
import tempfile

import attr

from .comic_screen import ComicScreen


@attr.s
class ComicScreenChafa(ComicScreen):
    def __attrs_post_init__(self):
        self._curr_image = None

    def show(self, image, image_index: int):
        with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
            image.save(image_file.name)
            self._log.debug(f'Saved {image_file.name}')
            subprocess.run(
                ['chafa', '-f', 'sixels', image_file.name]
            )
        self._log.info(f'{image_index + 1}/{self.images_count} - {self.file_name}')

    def main_loop_base(self, mgr):
        mgr.show()
        looping = True
        while looping:
            key_event = input()
            if key_event == 'q':
                looping = False
            elif key_event in ('n', 'd', ''):
                mgr.next()
            elif key_event in ('p', 'a'):
                mgr.prev()
            else:
                self._log.info(key_event)

    def main_loop(self, mgr):
        try:
            curses.wrapper(self._manage_keys, mgr)
        except Exception as e:
            self._log.debug(f'Unable to use curses: {e}')
            self.main_loop_base(mgr)

    def _manage_keys(self, stdscr, mgr):
        mgr.show()
        looping = True
        while looping:
            key_event = stdscr.getkey()
            if key_event == 'q':
                looping = False
            elif key_event in ('n', 'd', 'KEY_RIGHT'):
                mgr.next()
            elif key_event in ('p', 'a', 'KEY_LEFT'):
                mgr.prev()
            elif key_event == 'KEY_RESIZE':
                self._log.debug('WINDOWSIZECHANGED')
                mgr.show(image_changed=False)
            else:
                self._log.info(key_event)
