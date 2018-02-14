.. _readme:

.. |pypi_version| image:: https://badge.fury.io/py/astrality.svg
    :target: https://badge.fury.io/py/astrality

.. |travis-ci| image:: https://travis-ci.org/JakobGM/astrality.svg?branch=master
    :target: https://travis-ci.org/JakobGM/astrality

.. |coveralls| image:: https://coveralls.io/repos/github/JakobGM/astrality/badge.svg?branch=master
    :target: https://coveralls.io/github/JakobGM/astrality?branch=master

.. |rtfd| image:: https://readthedocs.org/projects/astrality/badge/?version=latest
    :target: http://astrality.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |logo| image:: https://github.com/JakobGM/astrality/raw/master/docs/astrality_logo.png

=====================================================================================================
|logo| Astrality - A Dynamic Configuration File Manager |pypi_version| |travis-ci| |rtfd| |coveralls|
=====================================================================================================

What Does It Do?
================

Astrality is a tool for managing configuration files and scheduling tasks related to those files.

You can create templates for your configuration files, and Astrality will replace placeholders within those templates with ``context`` values defined in a central configuration file. Furthermore, you can dynamically manipulate that ``context`` at predefined times and events.

**Possible use cases are:**

* Insert environment variables (e.g. ``$USER``) and command substitutions (e.g. ``$(xrandr | grep -cw connected)``) into configuration files that do not support them.
* Create a single source of truth for configuration options. Change your preferred font type or color scheme, and instantly see that change be applied across several different applications.
* Change your desktop wallpaper when your specific location (given by latitude and longitude) experiences dawn, noon, sunset, and dusk. It adapts to the length of day through the year. Make your `Conky modules <https://github.com/brndnmtthws/conky>`_ change font color accordingly.
* And much more...  An example configuration with several examples is included.

The configuration format uses the flexible `YAML <http://docs.ansible.com/ansible/latest/YAMLSyntax.html#yaml-basics>`_ format, and the template language uses the `Jinja2 syntax <http://jinja.pocoo.org/docs/2.10/>`_, which is easy to get started with, but allows complex templating for those who need it.

It is relatively easy to create ``modules`` to your own liking. Pull requests with new themes, conky modules, and improvements are very welcome.

Getting Started
===============

Prerequisites
-------------
Astrality requires `python 3.6 <https://www.python.org/downloads/>`_ or greater. The included configuration for Astrality also contains modules which utilize `conky <https://wiki.archlinux.org/index.php/Conky>`_ and `feh <https://wiki.archlinux.org/index.php/feh>`_. You can either disable these modules or install their dependencies. An example installation on ArchLinux would be:

.. code-block:: console

    sudo pacman -Syu conky feh python

The default configuration also uses the `Nerd Font <https://github.com/ryanoasis/nerd-fonts>`_ "FuraCode Nerd Font". Install it if you don't change the font in your configuration. On ArchLinux, it can be installed with the ``nerd-fonts-complete`` AUR package:

.. code-block:: console

    yaourt -S nerd-fonts-complete

Installation
------------

Create a new virtualenv for python 3.6 (or use your system python 3.6 if you prefer). Install Astrality from `pypi <https://pypi.org/project/astrality/>`_ like so:

.. code-block:: console

    pip3 install astrality

You should now be able to start `astrality` from your command line, but first, let's create an example configuration:

.. code-block:: console

    astrality --create-example-config

And now start `astrality`:

.. code-block:: console

    astrality

If you have ``feh`` installed, your desktop wallpaper should now be changed according to the sun's position in the sky at `Null Island <https://en.wikipedia.org/wiki/Null_Island>`_. Since you probably don't live there, you should now configure Astrality.

Configuration and Further Documentation
---------------------------------------

I recommend taking a look at the `full documentation <https://astrality.readthedocs.io/>`_ of Astrality hosted at `Read the Docs <https://readthedocs.org>`_.
