import signal
import time

import attr
import inky

try:
    import RPi.GPIO as GPIO
# GPIO reports a RuntimeError if imported on a non raspberry PI host
except RuntimeError as e:
    raise ImportError(f'Unable to import GPIO: {e}')
from PIL import Image

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

    # "handle_button" will be called every time a button is pressed
    # It receives one argument: the associated input pin.
    def handle_button(self, pin: int):
        label = self.LABELS[self.BUTTONS.index(pin)]
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
            self._log.info(f'{label} ({pin}) pressed - stopping')
            self.looping = False
        else:
            self._log.info(f'{label} ({pin}) pressed')
        signal.raise_signal(signal.SIGUSR1)

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
        self._log.debug(f'source image size={image.size} mode={image.mode} rotation={rotation}')
        if rotation:
            image = image.rotate(rotation, expand=True)
        image.thumbnail(self.inky.resolution)
        box = [round(i / 2) for i in (inky_image.size[0] - image.size[0], inky_image.size[1] - image.size[1])]
        inky_image.paste(image, box=box)
        self._log.debug(f'Resized image: {image.size} -> {inky_image.size}, paste box={box}')
        try:
            self._log.debug('calling inky.set_image()')
            self.inky.set_image(inky_image, saturation=0.5)
            self._log.debug('set_image() ok; calling inky.show() (this can take tens of seconds)')
            self.inky.show()
            self._log.debug('inky.show() completed')
        except Exception as e:
            self._log.exception(f'Inky rendering failed at set_image/show: {e}')
            raise
        self._log.info(f"{title} - {time.monotonic() - start:.1f}s")

    def main_loop_base(self):
        self._log.debug('main_loop_base: initial show()')
        self.mgr.show()
        self.looping = True
        while self.looping:
            received_signal = signal.sigwait((signal.SIGUSR1,))
            self._log.debug(f'{received_signal=}')

    def main_loop(self, mgr):
        self.mgr = mgr
        GPIO.setmode(GPIO.BCM)  # Set up RPi.GPIO with the "BCM" numbering scheme

        # Buttons connect to ground when pressed, so we should set them up
        # with a "PULL UP", which weakly pulls the input signal to 3.3V.
        GPIO.setup(self.BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self._log.debug('GPIO.setup() done')

        # Loop through out buttons and attach the "handle_button" function to each
        # We're watching the "FALLING" edge (transition from 3.3V to Ground) and
        # picking a generous bouncetime of 250ms to smooth out button presses.
        for pin in self.BUTTONS:
            try:
                GPIO.add_event_detect(pin, GPIO.FALLING, self.handle_button, bouncetime=250)
                self._log.debug(f'edge detection added for pin {pin}')
            except Exception as e:
                self._log.exception(f'add_event_detect failed for pin {pin}: {e}')

        self._log.debug('entering main_loop_base')
        self.main_loop_base()
