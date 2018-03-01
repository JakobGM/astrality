.. _configuration:

=============
Configuration
=============

.. _config_directory:

The Astrality configuration directory
=====================================
The configuration directory for astrality is determined in the following way:

* If ``$ASTRALITY_CONFIG_HOME`` is set, use that path as the configuration directory, else...
* If ``$XDG_CONFIG_HOME`` is set, use ``$XDG_CONFIG_HOME/astrality``, otherwise...
* Use ``~/.config/astrality``.

The resulting directory path can be displayed by running:

.. code-block:: console

    $ astrality --help
    usage: Astrality ...
    ...
    The location of Astralitys configuration directory is:
    "/home/jakobgm/.dotfiles/config/astrality".
    ...

This directory path will be referred to as ``$ASTRALITY_CONFIG_HOME`` in the rest of the documentation.

The Astrality configuration file
================================

The configuration file for astrality should be named ``astrality.yml`` and placed at the root of the Astrality configuration directory. If ``$ASTRALITY_CONFIG_HOME/astrality.yml`` does not exist, an `example configuration directory <https://github.com/JakobGM/astrality/blob/master/astrality/config>`_ will be used instead.

You can also copy over this example configuration directory as a starting point for your configuration by running:

.. code-block:: console

    $ astrality --create-example-config
    Copying over example config directory to "/home/example_username/.config/astrality".

You should now edit ``$ASTRALITY_CONFIG_HOME/astrality.yml`` to fit your needs.

The configuration file syntax
=============================

``astrality.yml`` uses the ``YAML`` format. The syntax should be relatively self-explanatory when looking at the `example configuration <https://github.com/JakobGM/astrality/blob/master/astrality/config/astrality.yml>`_. If you still want a basic overview, take a look at the `Ansible YAML syntax documentation <https://github.com/JakobGM/astrality/blob/master/astrality/config>`_ for a quick primer.

Value interpolation in the configuration file
---------------------------------------------

``astrality.yml`` is in itself a template which is compiled at Astrality startup. This allows you to use environment variable `parameter expansions <http://wiki.bash-hackers.org/syntax/pe?s[]=environment&s[]=variable#simple_usage>`_ and `command substitutions <http://wiki.bash-hackers.org/syntax/expansion/cmdsubst>`_ in your configuration. The syntax is as follows:


.. _parameter_expansion:

* **Parameter expansion**:
    ``{{ env.ENVIRONMENT_VARIABLE }}`` is replaced with the value of the environment variable, i.e. the result of ``echo $ENVIRONMENT_VARIABLE``.

    If the value of an environment variable contains other environment variables, then those environment variables will also be expanded.
    Say you have defined the following environment variables:

    .. code-block:: bash

        export VAR1 = run $var2
        export VAR2 = command

    Then the occurrence of ``{{ env.VAR1 }}`` in ``astrality.yml`` will be replaced with ``run command`` and **not** ``run $VAR2``.
    If you want the ability to turn off this "recursive expansion" feature, `open an issue <https://github.com/JakobGM/astrality/issues>`_, and I will add configuration option for it.

    .. caution::
        Only ``{{ env.NAME }}`` variables are expanded. ``$NAME`` will be left in place, to allow runtime expansions of environment variables when modules define shell commands to be run.

.. _command_substitution:

* **Command substitution**:
    ``{{ 'some_shell_command' | shell }}`` is replaced with the standard output resulting from running ``some_shell_command`` in a ``bash`` shell.

    You can set a timeout and/or fallback value for command substitutions. See the :ref:`documentation <shell_filter>` for the shell filter.

    .. note::
        Shell commands in ``astrality.yml`` are run from ``$ASTRALITY_CONFIG_HOME``. If you need to refer to paths outside this directory, you can use absolute paths, e.g. ``{{ 'cat ~/.home_directory_file' | shell }}``.

.. note::

    Interpolations in ``astrality.yml`` occur on Astrality startup, and will not reflect changes to environment variables and shell commands after startup.


.. _configuration_options:

Astrality configuration options
===============================

Global Astrality configuration options are specified in ``astrality.yml`` within a dictionary named ``config/astrality``, i.e.:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/astrality.yml

    config/astrality:
        option1: value1
        option2: value2
        ...

**Avalable configuration options**:

``hot_reload_config:``
    *Default:* ``false``

    If enabled, Astrality will watch for modifications to ``astrality.yml``.

    When ``astrality.yml`` is modified, Astrality will perform all :ref:`exit actions <module_events_on_exit>` in the old configuration, and then all :ref:`startup actions <module_events_on_startup>` from the new configuration.

    Ironically requires restart if enabled.

    *Useful for quick feedback when editing your configuration.*

``startup_delay:``
    *Default:* ``0``

    Delay Astrality on startup, given in seconds.

    *Useful when you depend on other startup scripts before Astrality startup,
    such as reordering displays.*


Where to go from here
=====================

What you should read of the documentation from here on depends on what you intend to solve by using Astrality. The most central concepts are:

* :doc:`templating` explains how to write configuration file templates.
* :doc:`modules` specify which templates to compile, when to compile them, and which commands to run after they have been compiled.
* :doc:`event_listeners` define types of events which modules can listen to and change their behaviour accordingly.

These concepts are relatively interdependent, and each documentation section assumes knowledge of concepts explained in earlier sections. If this is the first time you are reading this documentation, you should probably just continue reading the documentation in chronological order.
