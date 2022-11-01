import curses
import subprocess
import tempfile

import attr

from .comic_screen import ComicScreen


@attr.s
class ComicScreenChafa(ComicScreen):
    output_format: str = attr.ib(default='sixels')

    def __attrs_post_init__(self):
        self._curr_image = None
        self.stdscr = None

    def show(self, image, image_index: int):
        title = f'{image_index + 1}/{self.images_count} - {self.file_name}'
        screen_size = self.stdscr.getmaxyx()
        with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
            image.save(image_file.name)
            self._log.debug(f'Saved {image_file.name}')
            self._log.info(title)
            subprocess.run(
                ['chafa', '-f', self.output_format, '--size', f'{screen_size[1]}x{screen_size[0] - 2}', image_file.name]
            )

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
        self.stdscr = stdscr
        curses.curs_set(0)
        looping = True
        # make sure the first image is shown
        curses.ungetch(curses.KEY_RESIZE)
        while looping:
            key_event = stdscr.getkey()
            if key_event in ('q',):
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
