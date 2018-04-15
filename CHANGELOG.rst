=========
Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog
<http://keepachangelog.com/en/1.0.0/>`_ and this project adheres to `Semantic
Versioning <http://semver.org/spec/v2.0.0.html>`_.

[Unreleased]
============

Added
-----

- The run action now supports ``timeout`` option, in order to set
  ``run_timeout`` on command-by-command basis.
- ``compile`` actions now support an optional ``permissions`` field for
  setting the permissions of the compiled template. It allows setting octal
  values such as ``'755'``, and uses the UNIX ``chmod`` API.

Changed
-------

- The ``run`` module action is now a dictionary instead of a string. This
  enables us to support additional future options, such as ``timeout``. Now you
  specify the shell command to be run as a string value keyed to ``shell``.

  *Old syntax:*

  .. code-block:: yaml

      run:
          - command1
          - command2

  *New syntax:*

  .. code-block:: yaml

      run:
          - shell: command1
          - shell: command2

- The ``trigger`` module action is now a dictionary instead of a string. Now
  you specify the block to be triggered as a string value keyed to ``block``.
  ``on_modified`` blocks need to supply an additional ``path`` key indicating
  which file modification block to trigger.

  *Old syntax*

  .. code-block:: yaml

      trigger:
          - on_startup
          - on_modified:path/to/file

  *New syntax:*

  .. code-block:: yaml

      trigger:
          - block: on_startup
          - block: on_modified
            path: path/to/file

- Template metadata is now copied to compilation targets, including permission
  bits. Thanks to @sshashank124 for the implementation!

- The ``trigger`` action now follows recursive ``trigger`` actions. Beware of
  circular trigger chains!

- Astrality will now only recompile templates that have already been compiled
  when ``recompile_modified_templates`` is set to ``true``.

- The ``template`` compile action keyword has now been replaced with
  ``source``. This keyword makes more sense when we add support for compiling
  all templates within a directory.

  *Old syntax*

  .. code-block:: yaml

      compile:
          - template: path/to/template

  *New syntax:*

  .. code-block:: yaml

      compile:
          - source: path/to/template


Fixed
-----

- If a ``import_context`` action imported specified ``from_section`` but not
  ``to_section``, the section was not imported at all. This is now fixed by
  setting ``to_section`` to the same as ``from_section``.

- Template path placeholders are now normalized, which makes it possible to
  refer to the same template path in different ways, using symlinks and ``..``
  paths.
