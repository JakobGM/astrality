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

Astrality allows you symlink/copy/compile files and templates from directories
according to a central configuration file.  Tasks to be performed are grouped
into modules which can be conditionally enabled, based on installed programs,
OS, environment variables, and so on.

You can also write configuration files as `Jinja2 templates
<http://jinja.pocoo.org/docs/2.10/templates/>`_. Placeholders will be replaced
with pre-defined context values.  Astrality builds upon this by allowing you to
dynamically manipulate the context store, changing configuration files based on
the current OS, the time of day, and much more.

When dotfiles are modified, Astrality will automatically
re-(symlink|copy|compile) those files.

Astrality modules can be fetched from GitHub, making configuration sharing
easy.  The use of template placeholders make such sharing portable on cross of
different systems and user preferences.

Take a look at `the tutorial
<http://astrality.readthedocs.io/en/latest/tutorial.html>`_ for managing a
dotfile repository, or see the `full documentation
<https://astrality.readthedocs.io>`_ for all available functionality.
Feel free to drop by our `Gitter room <https://gitter.im/astrality/Lobby>`_ when
getting started.

**Here is gif demonstrating how Astrality is used to**:

#) Automatically change the desktop wallpaper based on the sun's position in the sky.
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2FJakobGM%2Fastrality.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2FJakobGM%2Fastrality?ref=badge_shield)

#) Dynamically change the font size, and implicitly the bar height, of `polybar <https://github.com/jaagr/polybar>`_.
#) Simultaneously change the color scheme of `alacritty <https://github.com/jwilm/alacritty>`_, `kitty <https://github.com/kovidgoyal/kitty>`_, and polybar at the same time.

.. image:: https://user-images.githubusercontent.com/10655778/36535609-934488ec-17ca-11e8-860e-4af5e1464997.gif

Getting started
===============

Prerequisites
-------------
Astrality requires `python 3.6 <https://www.python.org/downloads/>`_ or
greater. Check your version by running ``python --version``.

Installation
------------

``astrality-git`` is published on the `AUR <https://aur.archlinux.org/>`_ for
ArchLinux users. Otherwise, you can install Astrality using ``pip``:

Create a new `virtualenv <https://virtualenv.pypa.io/en/stable/>`_ for python
3.6 (or use your system python 3.6 if you prefer). Install Astrality from `pypi
<https://pypi.org/project/astrality/>`_ like so:

.. code-block:: console

    $ python3.6 -m pip install astrality

You should now be able to start `astrality` from your command line, but first, let us create an example configuration:

.. code-block:: console

    $ astrality --create-example-config

And now start `astrality`:

.. code-block:: console

    $ astrality

If you have ``feh`` installed, your desktop wallpaper should now be changed according to the sun's position in the sky at `Null Island <https://en.wikipedia.org/wiki/Null_Island>`_. Since you probably don't live there, you should now configure Astrality.

Use cases
=========

* Create a single source of truth for configuration options. Change your preferred font type or color scheme, and see that change be applied across several different graphical applications.
* Receive rapid feedback when editing configuration files by specifying commands to run when specific configuration files are modified.
* Conditionally copy (or compile) configuration files to specific paths. For example, only copy `neovim's <https://neovim.io/>`_ configuration if it is available on the system.
* Configure dynamic behaviour for applications that do not support it. For example, set your desktop wallpaper based on the sun's position in the sky at your location.
* Couple configurations across your applications. When you change your desktop wallpaper, automatically change the font type and color of your `conky modules <https://github.com/brndnmtthws/conky>`_.
* Insert environment variables, by writing ``{{ env.USER }}``, and command substitutions, by writing ``{{ 'xrandr | grep -cw connected' | shell }}``), into configuration files that do not natively support them.
* Modularize your desktop configuration, allowing you to switch between different combinations of applications and/or configurations by only editing one line. With Astrality you can, for example, quickly switch between `different <https://github.com/jaagr/polybar>`_ `status <https://github.com/LemonBoy/bar>`_ `bars <https://i3wm.org/i3bar/>`_ with little effort.
* Share ``modules`` with others who can effortlessly try out your configuration, and easily switch back to their old configuration if they wish, making experimentation frictionless.
* And much more...  An `example configuration <http://astrality.readthedocs.io/en/latest/example_configuration.html>`_ with several examples is included.

The configuration format uses the flexible `YAML <http://docs.ansible.com/ansible/latest/YAMLSyntax.html#yaml-basics>`_ format, and the template language uses the `Jinja2 syntax <http://jinja.pocoo.org/docs/2.10/>`_, which is easy to get started with, but allows complex templating for those who need it.

It is relatively easy to create ``modules`` to your own liking. Pull requests with new example modules are welcome.

Configuration and further documentation
---------------------------------------

I recommend taking a look at the `full documentation <https://astrality.readthedocs.io/>`_ of Astrality hosted at `Read the Docs <https://readthedocs.org>`_.


## License
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2FJakobGM%2Fastrality.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2FJakobGM%2Fastrality?ref=badge_large)