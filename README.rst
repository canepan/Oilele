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

As of today, the output can be sent to:

* anything pygame_ supports (i.e.: SDL/OpenGL)
* terminal (via Chafa_)
* `Inky paper LCD`_ (on RaspberryPI)

.. _Chafa: https://hpjansson.org/chafa/
.. _Inky paper LCD: https://github.com/pimoroni/inky
.. _pygame: https://www.pygame.org


Install
=======

The usual `pip` should work, with the following options:

[inky]
  to enable Raspberry GPIO Inky output
[rar]
  to be able to open `cbr` archives (requires librar on the O.S.)

Usage
=====

Run with (can replace `oilala` with `faccela_vedé` or `faccela_toccá`):
::

  oilala <filename>
  (opens <filename> via pygame)
  oilala -A <filename> -v
  (opens <filename> with Chafa, verbose output)
  oilala -I <filename> -p 32
  (opens <filename> at page 32 on Inky impressions)

