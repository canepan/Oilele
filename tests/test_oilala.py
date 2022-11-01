from unittest import mock
import pytest

from oilele.oilala import main


@pytest.fixture
def mock_pil_image(monkeypatch):
    mock_obj = mock.MagicMock(name='PIL.Image')
    monkeypatch.setattr('oilele.oilala.Image', mock_obj)
    yield mock_obj
    print(f'{mock_obj} calls: {mock_obj.mock_calls}')


@pytest.fixture
def mock_pdf2image(monkeypatch):
    mock_obj = mock.MagicMock(name='pdf2image')
    monkeypatch.setattr('oilele.oilala.pdf2image', mock_obj)
    yield mock_obj
    print(f'{mock_obj} calls: {mock_obj.mock_calls}')


@pytest.fixture
def mock_pygame(monkeypatch):
    mock_obj = mock.MagicMock(name='pygame')
    mock_obj.display.set_mode.return_value.get_size.return_value = (100, 150)
    mock_events = (
        mock.Mock(name='event1'),
        mock.Mock(name='event2'),
        mock.Mock(name='event3', type=mock_obj.QUIT),
    )
    mock_obj.event.get.return_value = mock_events
    mock_obj.vernum.major = 2
    monkeypatch.setattr('oilele.screen.comic_screen_pygame.pygame', mock_obj)
    yield mock_obj, mock_events
    print(f'{mock_obj} calls: {mock_obj.mock_calls}')
    for mock_event in mock_events:
        print(f'{mock_event} calls: {mock_event.mock_calls}')


@pytest.fixture
def mock_subprocess(monkeypatch):
    mock_obj = mock.MagicMock(name='subprocess')
    monkeypatch.setattr('oilele.screen.comic_screen_chafa.subprocess', mock_obj)
    yield mock_obj
    print(f'{mock_obj} calls: {mock_obj.mock_calls}')


@pytest.fixture
def mock_zipfile(monkeypatch):
    mock_obj = mock.MagicMock(name='ZipFile')
    filenames = ('dir1/', 'dir1/filename1', 'dir1/filename2')
    mock_obj.return_value.__enter__.return_value.namelist.return_value = filenames
    monkeypatch.setattr('oilele.oilala.ZipFile', mock_obj)
    yield mock_obj
    print(f'{mock_obj} calls: {mock_obj.mock_calls}')


@pytest.mark.parametrize('pygame_version', (1, 2))
def test_main(mock_pil_image, mock_pdf2image, mock_pygame, pygame_version):
    mock_pygame[0].vernum.major = pygame_version
    mock_pdf2image.pdfinfo_from_path.return_value = {'Page rot': '3'}
    images = [
        mock.Mock(name='pdf_image1'),
        mock.Mock(name='pdf_image2'),
        mock.Mock(name='pdf_image3'),
    ]
    mock_pdf2image.convert_from_path.return_value = images

    main(['test'])

    for m in mock_pdf2image.convert_from_path.return_value:
        print(f'{m} calls: {m.mock_calls}')

    mock_pdf2image.pdfinfo_from_path.assert_called_once_with('test')
    mock_pdf2image.convert_from_path.assert_called_once_with('test')
    mock_pygame[0].display.set_caption.assert_called_with('1/3 - test')
    image = images[0].rotate.return_value.convert.return_value
    mock_pygame[0].image.fromstring.assert_called_with(image.tobytes.return_value, image.size, image.mode)


def test_main_cbz(mock_pil_image, mock_pdf2image, mock_pygame, mock_zipfile):
    mock_pdf2image.exceptions.PDFPageCountError = Exception
    mock_pdf2image.pdfinfo_from_path.side_effect = mock_pdf2image.exceptions.PDFPageCountError
    main(['test'])
    mock_pygame[0].display.set_caption.assert_called_with('1/2 - test')
