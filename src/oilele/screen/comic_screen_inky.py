import threading
import time
from pathlib import Path

import attr
import inky
from gpiozero import Button
from PIL import Image, ImageDraw, ImageFont

from .comic_screen import ComicScreen


@attr.s
class ComicScreenInky(ComicScreen):
    force_rotation: int = attr.ib(default=None)
    BUTTONS = [5, 6, 16, 24]  # Gpio pins for each button (from top to bottom)
    LABELS = ['A', 'B', 'C', 'D']  # These correspond to buttons A, B, C and D respectively

    def __attrs_post_init__(self):
        self._curr_image = None

        try:
            self.inky = inky.auto(verbose=True)
            if tuple(self.inky.resolution) == (1600, 1200):
                self.BUTTONS = [5, 6, 25, 24]
        except Exception as e:
            self._log.debug(f'Exception detecting Inky device: {e}. Using Inky7Colour')
            self.inky = inky.Inky7Colour()

        self._log.debug(
            f'Inky device: {type(self.inky).__module__}.{type(self.inky).__name__} '
            f'resolution={self.inky.resolution} colour={getattr(self.inky, "colour", "?")} '
            f'buttons={self.BUTTONS}'
        )
        self.inky_ratio = self._ratio(self.inky.resolution)

    # "handle_button" is called every time a button is pressed, with its label.
    def handle_button(self, label: str):
        if label == 'A':
            self.mgr.next()
        elif label == 'B':
            self.mgr.prev()
        elif label == 'C':
            rotation = 0
            if self.force_rotation is not None:
                rotation = self.force_rotation
            self.force_rotation = (rotation + 90) % 360
            self.mgr.show()
        elif label == 'D':
            self._log.info(f'{label} pressed - stopping')
            self._stop.set()
        else:
            self._log.info(f'{label} pressed')

    def _ratio(self, size: tuple) -> float:
        """This is to ensure we use the same ratio during calculations"""
        return size[0] / size[1]

    def _required_rotation(self, image):
        if self.force_rotation is not None:
            return self.force_rotation
        image_ratio = self._ratio(image.size)
        if (self.inky_ratio > 1 and image_ratio < 1) or (self.inky_ratio < 1 and image_ratio > 1):
            # by default, rotate 90 degrees counter-clockwise
            return 270
        return 0

    def show(self, image, image_index: int):
        title = f'{image_index + 1}/{self.images_count} - {self.file_name}'
        start = time.monotonic()

        inky_image = Image.new('RGBA', self.inky.resolution, (0, 0, 0, 0))
        rotation = self._required_rotation(image)
        if rotation:
            image = image.rotate(rotation, expand=True)
        image.thumbnail(self.inky.resolution)
        box = [round(i / 2) for i in (inky_image.size[0] - image.size[0], inky_image.size[1] - image.size[1])]
        inky_image.paste(image, box=box)
        self._log.debug(f'Resized image: {image.size} -> {inky_image.size} (rotation={rotation})')
        try:
            self.inky.set_image(inky_image, saturation=0.5)
            self.inky.show()
        except Exception as e:
            self._log.exception(f'Inky rendering failed: {e}')
            raise
        self._log.info(f"{title} - {time.monotonic() - start:.1f}s")

    def main_loop_base(self):
        self.mgr.show()
        self._stop.wait()  # block the main thread until a button (D) asks to stop

    def main_loop(self, mgr):
        self.mgr = mgr
        self._stop = threading.Event()
        # Buttons connect to ground when pressed -> pull_up=True. gpiozero uses
        # lgpio/gpiod under the hood, so it works on kernel >=6.6 and doesn't
        # choke on the board's old-style revision code (unlike RPi.GPIO).
        self._buttons = []
        for pin, label in zip(self.BUTTONS, self.LABELS):
            try:
                button = Button(pin, pull_up=True)
                # keep a reference so gpiozero doesn't garbage-collect the pin
                button.when_pressed = lambda lbl=label: self.handle_button(lbl)
                self._buttons.append(button)
                self._log.debug(f'button {label} attached to GPIO{pin}')
            except Exception as e:
                self._log.exception(f'failed to attach button {label} (GPIO{pin}): {e}')
        self.main_loop_base()

    def _render_menu(self, options, index, title):
        """Draw the option list (with the current row marked) to the panel.

        Note: a full e-ink refresh is slow (tens of seconds), so each up/down
        move repaints the whole panel — usable for a short list, not snappy.
        """
        width, height = self.inky.resolution
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', max(18, height // 30))
        except OSError:
            font = ImageFont.load_default()
        line_h = getattr(font, 'size', 16) + 12
        draw.text((20, 10), f'{title}  (A/B move, C open, D cancel)', fill=(0, 0, 0), font=font)
        # window the visible rows around the current selection
        rows = max(1, (height - 3 * line_h) // line_h)
        start = max(0, min(index - rows // 2, len(options) - rows))
        top = 10 + 2 * line_h
        for offset, option in enumerate(options[start:start + rows]):
            i = start + offset
            marker = '> ' if i == index else '   '
            draw.text((20, top + offset * line_h), f'{marker}{Path(option).name}', fill=(0, 0, 0), font=font)
        self.inky.set_image(image)
        self.inky.show()

    def select(self, options, title='Choose a file'):
        if not options:
            return None
        self._sel_index = 0
        self._sel_result = None
        done = threading.Event()

        def on_press(label):
            if label == 'A':
                self._sel_index = (self._sel_index - 1) % len(options)
                self._render_menu(options, self._sel_index, title)
            elif label == 'B':
                self._sel_index = (self._sel_index + 1) % len(options)
                self._render_menu(options, self._sel_index, title)
            elif label == 'C':
                self._sel_result = options[self._sel_index]
                done.set()
            elif label == 'D':
                self._sel_result = None
                done.set()

        self._render_menu(options, self._sel_index, title)
        buttons = []
        for pin, label in zip(self.BUTTONS, self.LABELS):
            button = Button(pin, pull_up=True)
            button.when_pressed = lambda lbl=label: on_press(lbl)
            buttons.append(button)
        try:
            done.wait()
        finally:
            for button in buttons:
                button.close()
        return self._sel_result
