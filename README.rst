.. image:: https://img.shields.io/github/v/tag/canepan/Oilele?style=plastic
   :alt: GitHub tag (latest by date)
   :target: `GitHub link`_

.. image:: https://img.shields.io/badge/python-3.7+-blue.svg
   :target: `GitHub link`_

.. .. _PyPI link: https://pypi.org/project/Oilala
.. _GitHub link: https://github.com/canepan/Oilele

.. image:: https://github.com/canepan/Oilele/workflows/tests/badge.svg
   :target: https://github.com/canepan/Oilele/actions?query=workflow%3A%22tests%22
   :alt: tests

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code style: Black

.. .. image:: https://readthedocs.org/projects/skeleton/badge/?version=latest
..    :target: https://skeleton.readthedocs.io/en/latest/?badge=latest

.. .. image:: https://img.shields.io/badge/Oilele-2022-informational
..    :target: https://blog.jaraco.com/skeleton


===================
Oilele comic viewer
===================
The project aims to build a Python comic viewer (PDF, CBZ, CBR supported) with multiple output options.

PDF reading is available through poppler_

As of today, the output can be sent to:

* anything pygame_ supports (i.e.: SDL/OpenGL)
* terminal (via Chafa_)
* `Inky paper LCD`_ (on RaspberryPI)

.. _poppler: https://poppler.freedesktop.org/
.. _Chafa: https://hpjansson.org/chafa/
.. _Inky paper LCD: https://github.com/pimoroni/inky
.. _pygame: https://www.pygame.org


Install
=======

The command `pip install Oilele` should work, with the following options:

[inky]
  to enable Raspberry GPIO Inky output
[rar]
  to be able to open `cbr` archives (requires librar on the O.S.)

To install with all dependencies::

  pip install Oilele[rar,inky]

Dependencies can usually installed by your favorite package manager:

Debian based
 `apt install poppler chafa`
Mac
  `brew install poppler chafa`

Usage
=====

Run with (can replace `oilala` with `faccela_vedé` or `faccela_toccá`)::

  oilala <filename>
  (opens <filename> via pygame)
  oilala -A <filename> -v
  (opens <filename> with Chafa, verbose output)
  oilala -I <filename> -p 32
  (opens <filename> at page 32 on Inky impressions)

Notes and dependencies
======================

The `-A` option (`--ascii`) is only available if you have Chafa_ installed (minimum 1.2 which has the `-f` option).
Alternatives to pdf2image (which depends on poppler) being considered:

* PyMuPDF_, it includes support for CBZ and some epub formats. Depends on the MuPDF_ library
* pikepdf_, depends on the QPDF_ CLI

.. _PyMuPDF: https://github.com/pymupdf/PyMuPDF
.. _MuPDF: https://mupdf.com/
.. _pikepdf: https://github.com/pikepdf/pikepdf
.. _QPDF: https://github.com/qpdf/qpdf


Please report any problem via the GitHub `issues` feature, with possible solutions, or even pull requests if appropriate.

