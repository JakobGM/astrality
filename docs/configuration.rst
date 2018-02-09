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

The configuration file for astrality should be named ``astrality.yaml`` and placed at the root of the Astrality configuration directory. If ``$ASTRALITY_CONFIG_HOME/astrality.yaml`` does not exist, an `example configuration directory <https://github.com/JakobGM/astrality/blob/master/astrality/config>`_ will be used instead.

You can also copy over this example configuration directory as a starting point for your configuration by running:

.. code-block:: console

    $ astrality --create-example-config
    Copying over example config directory to "/home/example_username/.config/astrality".

You should now edit ``$ASTRALITY_CONFIG_HOME/astrality.yaml`` to fit your needs.

The configuration file syntax
=============================

``astrality.yaml`` uses the ``YAML`` format. The syntax should be relatively self-explanatory when looking at the `example configuration <https://github.com/JakobGM/astrality/blob/master/astrality/config/astrality.yaml>`_. If you still want a basic overview, take a look at the `Ansible YAML syntax documentation <https://github.com/JakobGM/astrality/blob/master/astrality/config>`_ for a quick primer.

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

    Then the occurrence of ``${VAR1}`` in ``astrality.yaml`` will be replaced with ``run command`` and **not** ``run $VAR2``.
    If you want the ability to turn off this "recursive expansion" feature, `open an issue <https://github.com/JakobGM/astrality/issues>`_, and I will add configuration option for it.
    
    .. caution::
        Only ``${NAME}`` blocks are expanded. ``$NAME`` will be left in place, to allow runtime expansions of environment variables when modules define shell commands to be run.

.. _command_substitution:

* **Command substitution**: 
    ``$( some_shell_command )`` is replaced with the standard output resulting from running ``some_shell_command`` in a ``bash`` shell.

.. note::

    Interpolations in ``astrality.yaml`` occur on Astrality startup, and will not reflect changes to environment variables and shell commands after startup.

Where to go from here
=====================

What you should read of the documentation from here on depends on what you intend to solve by using Astrality. The most central concepts are:

* :doc:`modules` define which templates to compile, when to compile them, and which commands to run after they have been compiled.
* :doc:`timers` define when modules should change their behaviour.
* :doc:`templating` explains how to write configuration file templates.

These concepts are relatively interdependent, and each documentation section assumes knowledge of concepts explained in earlier sections. If this is the first time you are reading this documentation, you should probably just continue reading the documentation in chronological order.
