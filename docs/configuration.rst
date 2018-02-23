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
Astrality makes two non-standard additions to the ``YAML`` syntax, so-called interpolations. Environment variable `parameter expansions <http://wiki.bash-hackers.org/syntax/pe?s[]=environment&s[]=variable#simple_usage>`_ and `command substitutions <http://wiki.bash-hackers.org/syntax/expansion/cmdsubst>`_. The syntax is as follows:


.. _parameter_expansion:

* **Parameter expansion**:
    ``${ENVIRONMENT_VARIABLE}`` is replaced with the value of the environment variable, i.e. the result of ``echo $ENVIRONMENT_VARIABLE``.

    If the value of an environment variable contains other environment variables, then those environment variables will also be expanded.
    Say you have defined the following environment variables:

    .. code-block:: bash

        export VAR1 = run $var2
        export VAR2 = command

    Then the occurrence of ``${VAR1}`` in ``astrality.yml`` will be replaced with ``run command`` and **not** ``run $VAR2``.
    If you want the ability to turn off this "recursive expansion" feature, `open an issue <https://github.com/JakobGM/astrality/issues>`_, and I will add configuration option for it.

    .. caution::
        Only ``${NAME}`` blocks are expanded. ``$NAME`` will be left in place, to allow runtime expansions of environment variables when modules define shell commands to be run.

.. _command_substitution:

* **Command substitution**:
    ``$( some_shell_command )`` is replaced with the standard output resulting from running ``some_shell_command`` in a ``bash`` shell.

    .. note::
        Shell commands are run from ``$ASTRALITY_CONFIG_HOME``. If you need to refer to paths outside this directory, you can use absolute paths, e.g. ``$( cat ~/.home_directory_file )``.

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

    *Useful for quick feedback when editing* :ref:`templates <templating>`.

``recompile_modified_templates:``
    *Defualt:* ``false``

    If enabled, Astrality will watch for modifications to all templates sources :ref:`specified <compile_action>` in ``astrality.yml``.
    If a template is modified, it will be recompiled to its specified target path(s).

    .. note::
        With this option enabled, any modified template will be recompiled as long
        as it is specified within a :ref:`compile action <compile_action>`, regardless of
        exactly *when* you intended the template to be compiled in the first place.

        For instance, if a template is configured to be compiled on Astrality exit,
        and not sooner, it will still be recompiled when it is modified, even though
        Astrality has not exited.

        You can have more fine-grained control over exactly *what* happens when
        a file is modified by using the ``on_modified`` :ref:`module event <events>`.
        This way you can run shell commands, import context values, and compile
        arbitrary templates when specific files are modified on disk.

    .. caution::
        At the moment, Astrality only watches for file changes recursively within
        ``$ASTRALITY_CONFIG_HOME``.

``startup_delay:``
    *Default:* ``0``

    Delay Astrality on startup, given in seconds.

    *Useful when you depend on other startup scripts before Astrality startup,
    such as reordering displays.*

``run_timeout``
    *Default:* ``0``

    Determines how long Astrality waits for :ref:`shell commands <run_action>` to exit successfully, given in seconds.

    *Useful when shell commands are dependent on earlier shell commands.*

.. _configuration_options_requires_timeout:

``requires_timeout``
    *Default:* ``1``

    Determines how long Astrality waits for :ref:`module requirements <module_requires>` to exit successfully, given in seconds. If the requirement times out, it will be considered failed.

    *Useful when requirements are costly to determine, but you still do not want them to time out.*

Where to go from here
=====================

What you should read of the documentation from here on depends on what you intend to solve by using Astrality. The most central concepts are:

* :doc:`templating` explains how to write configuration file templates.
* :doc:`modules` specify which templates to compile, when to compile them, and which commands to run after they have been compiled.
* :doc:`event_listeners` define types of events when modules should change their behaviour.

These concepts are relatively interdependent, and each documentation section assumes knowledge of concepts explained in earlier sections. If this is the first time you are reading this documentation, you should probably just continue reading the documentation in chronological order.
