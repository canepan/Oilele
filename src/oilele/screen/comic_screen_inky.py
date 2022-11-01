import signal
import tempfile

import attr
import inky
import RPi.GPIO as GPIO

from .comic_screen import ComicScreen


@attr.s
class ComicScreenInky(ComicScreen):
    BUTTONS = [5, 6, 16, 24]  # Gpio pins for each button (from top to bottom)
    LABELS = ['A', 'B', 'C', 'D']  # These correspond to buttons A, B, C and D respectively

    def __attrs_post_init__(self):
        self._curr_image = None

    # "handle_button" will be called every time a button is pressed
    # It receives one argument: the associated input pin.
    def handle_button(self, pin: int):
        label = self.LABELS[self.BUTTONS.index(pin)]
        if label == 'A':
            self.mgr.next()
        elif label == 'B':
            self.mgr.prev()
        elif label == 'D':
            self.looping = False
            signal.raise_signal(signal.SIGCONT)
        else:
            self._log.info(f'{label} ({pin}) pressed')

    def show(self, image, image_index: int):
        title = f'{image_index + 1}/{self.images_count} - {self.file_name}'
        self._log.info(title)

        image = image.resize(self.inky.resolution)
        with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
            image.save(image_file.name)
            self._log.debug(f'Saved {image_file.name}')
            self.inky.set_image(image, saturation=0.5)
            self.inky.show()

    def main_loop_base(self, mgr):
        mgr.show()
        self.looping = True
        while self.looping:
            signal.pause()
            received_signal = signal.sigwait((signal.SIGCONT, signal.SIGALRM, signal.SIGUSR1))
            self.log._debug(f'{received_signal=}')
            # key_event = input()
            # if key_event == 'q':
            #     self.looping = False
            # elif key_event in ('n', 'd', ''):
            #     mgr.next()
            # elif key_event in ('p', 'a'):
            #     mgr.prev()
            # else:
            #     self._log.info(key_event)

    def main_loop(self, mgr):
        self.mgr = mgr
        GPIO.setmode(GPIO.BCM)  # Set up RPi.GPIO with the "BCM" numbering scheme

        # Buttons connect to ground when pressed, so we should set them up
        # with a "PULL UP", which weakly pulls the input signal to 3.3V.
        GPIO.setup(self.BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        try:
            self.inky = inky.auto(verbose=True)
        except Exception as e:
            self._log.debug(f'Exception detecting Inky device: {e}. Using Inky7Colour')
            self.inky = inky.Inky7Colour()

        # Loop through out buttons and attach the "handle_button" function to each
        # We're watching the "FALLING" edge (transition from 3.3V to Ground) and
        # picking a generous bouncetime of 250ms to smooth out button presses.
        for pin in self.BUTTONS:
            GPIO.add_event_detect(pin, GPIO.FALLING, self.handle_button, bouncetime=250)

        self.main_loop_base(mgr)
