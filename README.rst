.. _readme:

.. |pypi_version| image:: https://badge.fury.io/py/astrality.svg
    :target: https://badge.fury.io/py/astrality
    :alt: PyPI package

.. |travis-ci| image:: https://travis-ci.org/JakobGM/astrality.svg?branch=master
    :target: https://travis-ci.org/JakobGM/astrality
    :alt: Travis-CI

.. |coveralls| image:: https://coveralls.io/repos/github/JakobGM/astrality/badge.svg?branch=master
    :target: https://coveralls.io/github/JakobGM/astrality?branch=master
    :alt: Coveralls

.. |rtfd| image:: https://readthedocs.org/projects/astrality/badge/?version=latest
    :target: http://astrality.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |logo| image:: https://github.com/JakobGM/astrality/raw/master/docs/images/astrality_logo.png
    :alt: Astrality logo

.. |gitter| image:: https://badges.gitter.im/JakobGM/astrality.png
    :target: https://gitter.im/astrality/Lobby

==============================================================================================================
|logo| Astrality - A Dynamic Configuration File Manager |pypi_version| |travis-ci| |rtfd| |coveralls| |gitter|
==============================================================================================================

    TL;DR: Automatically deploy dotfiles. Grouped into modules with dynamic behaviour.

What does it do?
================

Astrality is a flexible tool for managing configuration files, inspired by `GNU
Stow`_ and Ansible_.

Let's begin with a list of some of Astrality's key features:

* Manage and deploy configuration files according to a central YAML config
  file.
* Group related configuration into *modules*.
* Conditionally enable modules based on environment variables, OS, installed
  programs and shell commands.
* Copy and/or symlink files.
* Execute shell commands.
* Compile `Jinja2 templates`_
  templates to target destinations.
* Dynamically manipulate context values used during jinja2 compilation.
* Automatically re-deploy dotfiles when source content is modified.
* Subscribe to pre-defined events, such as local daylight, and execute actions
  accordingly.
* Fetch modules from GitHub.
* Restore files created and/or overwritten by modules.

Take a look at the `tutorial`_ for managing a dotfile repository, or see the
`full documentation`_ for all available functionality.  Feel free to drop by
our `Gitter room`_ when getting started.

**Here is gif demonstrating how Astrality is used to**:

#) Automatically change the desktop wallpaper based on the sun's position in
   the sky.
#) Dynamically change the font size, and implicitly the bar height, of
   `polybar`_.
#) Simultaneously change the color scheme of `alacritty`_, `kitty`_, and
   polybar at the same time.

.. image:: https://user-images.githubusercontent.com/10655778/36535609-934488ec-17ca-11e8-860e-4af5e1464997.gif

Getting started
===============

Prerequisites
-------------
Astrality requires `python 3.6`_ or greater. Check your version by running
``python --version``.

Installation
------------

``astrality-git`` is published on the `AUR`_ for ArchLinux users. Otherwise,
you can install Astrality using ``pip``:

Create a new virtualenv_ for python 3.6 (or use your system python 3.6 if you
prefer). Install Astrality from PyPI_ like so:

.. code-block:: console

    $ python3.6 -m pip install astrality

You should now be able to start `astrality` from your command line, but first,
let us create an example configuration:

.. code-block:: console

    $ astrality --create-example-config

Take a look at the generated example configuration at ``~/.config/astrality``.
Now start `astrality`:

.. code-block:: console

    $ astrality


Configuration and further documentation
---------------------------------------

I recommend taking a look at the `full documentation`_ of Astrality hosted at
`Read the Docs`_.


.. _full documentation: https://astrality.readthedocs.io/
.. _Read the Docs: https://readthedocs.org
.. _virtualenv: https://virtualenv.pypa.io/en/stable/
.. _PyPI: https://pypi.org/project/astrality/
.. _Python 3.6: https://www.python.org/downloads/
.. _alacritty: https://github.com/jwilm/alacritty
.. _kitty: https://github.com/kovidgoyal/kitty
.. _polybar: https://github.com/jaagr/polybar
.. _Gitter room: https://gitter.im/astrality/Lobby
.. _tutorial: http://astrality.readthedocs.io/en/latest/tutorial.html
.. _AUR: https://aur.archlinux.org/
.. _GNU Stow: https://www.gnu.org/software/stow/
.. _Ansible: https://www.ansible.com/
.. _Jinja2 templates: http://jinja.pocoo.org/docs/2.10/templates/
