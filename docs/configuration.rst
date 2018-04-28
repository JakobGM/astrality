.. _configuration:

=============
Configuration
=============

.. _config_directory:

The Astrality configuration directory
=====================================
The configuration directory for astrality is determined in the following way:

* If ``$ASTRALITY_CONFIG_HOME`` is set, use that path as the configuration
  directory, else...
* If ``$XDG_CONFIG_HOME`` is set, use ``$XDG_CONFIG_HOME/astrality``,
  otherwise...
* Use ``~/.config/astrality``.

The resulting directory path can be displayed by running:

.. code-block:: console

    $ astrality --help
    usage: Astrality ...
    ...
    The location of Astralitys configuration directory is:
    "/home/jakobgm/.dotfiles/config/astrality".
    ...

This directory path will be referred to as ``$ASTRALITY_CONFIG_HOME`` in the
rest of the documentation.

.. _configuration_files:

The Astrality configuration files
=================================

There are three configuration files of importance in ``$ASTRALITY_CONFIG_HOME``:

``astrality.yml``
    Global configuration options for Astrality.

``modules.yml``
    Here you define modules you want to use.

``context.yml``
    Context values used for placeholder substitution in compiled templates.

If ``$ASTRALITY_CONFIG_HOME/astrality.yml`` does not exist, an
`example configuration directory
<https://github.com/JakobGM/astrality/blob/master/astrality/config>`_
will be used instead.

You can also copy over this example configuration directory as a starting point
for your configuration by running:

.. code-block:: console

    $ astrality --create-example-config
    Copying over example config directory to "/home/example_username/.config/astrality".

You should now edit ``$ASTRALITY_CONFIG_HOME/astrality.yml`` to fit your needs.

The configuration file syntax
=============================

Astrality's configuration files uses the ``YAML`` format.
The syntax should be relatively self-explanatory when looking at the `example
configuration
<https://github.com/JakobGM/astrality/blob/master/astrality/config>`_.
If you still want a basic overview, take a look at the `Ansible YAML syntax
documentation
<https://github.com/JakobGM/astrality/blob/master/astrality/config>`_ for
a quick primer.

Command substitution in configuration files
-------------------------------------------

Astrality's configuration files are themselves templates that are compiled
and interpreted at startup. Using templating features in astrality configuration
files is usually unnecessary.

But sometimes it is useful to insert the result of a shell command within a
configuration file, such as "context.yml". You can use `command substitutions
<http://wiki.bash-hackers.org/syntax/expansion/cmdsubst>`_ in order to achieve
this:

.. _command_substitution:

* **Command substitution**:
    ``{{ 'some_shell_command' | shell }}`` is replaced with the standard output
    resulting from running ``some_shell_command`` in a ``bash`` shell.

    You can set a timeout and/or fallback value for command substitutions. See
    the :ref:`documentation <shell_filter>` for the shell filter.

.. note::
    Shell commands in ``astrality.yml`` are run from
    ``$ASTRALITY_CONFIG_HOME``. If you need to refer to paths outside this
    directory, you can use absolute paths, e.g. ``{{ 'cat
    ~/.home_directory_file' | shell }}``.

.. _configuration_options:

Astrality configuration options
===============================

Global Astrality configuration options are specified in ``astrality.yml``
within a dictionary named ``astrality``, i.e.:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/astrality.yml
    astrality:
        hot_reload_config: true
        startup_delay: 10

**Avalable configuration options**:

``hot_reload_config:``
    *Default:* ``false``

    If enabled, Astrality will watch for modifications to ``astrality.yml``,
    ``modules.yml``, and ``context.yml``.

    When one of these are modified, Astrality will perform all :ref:`exit
    actions <module_events_on_exit>` in the old configuration, and then all
    :ref:`startup actions <module_events_on_startup>` from the new
    configuration.

    Ironically requires restart if enabled.

    *Useful for quick feedback when editing your configuration.*

``startup_delay:``
    *Default:* ``0``

    Delay Astrality on startup, given in seconds.

    *Useful when you depend on other startup scripts before Astrality startup,
    such as reordering displays.*


Where to go from here
=====================

What you should read of the documentation from here on depends on what you
intend to solve by using Astrality. The most central concepts are:

* :doc:`templating` explains how to write configuration file templates.
* :doc:`modules` specify which templates to compile, when to compile them, and
  which commands to run after they have been compiled.
* :doc:`event_listeners` define types of events which modules can listen to and
  change their behaviour accordingly.

These concepts are relatively interdependent, and each documentation section
assumes knowledge of concepts explained in earlier sections. If this is the
first time you are reading this documentation, you should probably just
continue reading the documentation in chronological order.
