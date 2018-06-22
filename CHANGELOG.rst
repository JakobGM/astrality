=========
Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog
<http://keepachangelog.com/en/1.0.0/>`_ and this project adheres to `Semantic
Versioning <http://semver.org/spec/v2.0.0.html>`_.

[UNRELEASED]
============

Changed
-------

- Astrality no longer reverts to using the example configuration when
  ``ASTRALITY_CONFIG_HOME/astrality.yml`` does not exist.
  Default values are are used instead, and a warning is logged.
  Use ``--create-example-config`` to get create the example configuration
  instead.
- GitHub modules are now cloned to
  ``$XDG_DATA_HOME/astrality/repositories/github`` instead of
  ``$ASTRALITY_CONFIG_HOME/<modules_directory>``.

[1.0.3] - 2018-06-17
====================

Changed
-------

- Astrality is now marked as "production/stable" on PyPI.

Fixed
-----

- Fixed bug which caused ``$ASTRALITY_LOGGING_LEVEL`` and
  ``astrality -l <logging_level>`` to be ignored.
- Astrality now catches errors caused by starting the file system watcher.
  It logs the error and continues on without watching the error in such a case.

[1.0.2] - 2018-05-25
====================

Fixed
-----

- Fixed lint errors in documentation which caused incorrect rendering on PyPI.

[1.0.1] - 2018-05-24
====================

Fixed
-----

- Added missing dependency ``python-dateutil`` to ``setup.py``.

[1.0.0] - 2018-05-24
====================

Added
-----

- New ``symlink`` action type.
- New ``copy`` action type.
- New ``stow`` action type. This action allows you to either compile+symlink
  or compile+copy, bisecting a directory based on filename regular expression
  matching.
- You can now compile all templates recursively within a directory. Just set
  ``content`` to a directory path. ``target`` must be a directory as well, and
  the relative file hierarchy is preserved.
- You can now specify which filenames are considered templates when compiling
  directories recursively.
- Template target filenames can now be renamed by specifying a regular
  expression capture group.
- Non-template files can now be either symlinked, copied, or ignored.
- The run action now supports ``timeout`` option, in order to set
  ``run_timeout`` on command-by-command basis.
- ``compile`` actions now support an optional ``permissions`` field for
  setting the permissions of the compiled template. It allows setting octal
  values such as ``'755'``, and uses the UNIX ``chmod`` API.
- Module requirements can now specify required programs and environment
  variables by using the dictionary keys ``installed`` and ``env``
  respectively.
- You can now set ``requires`` timeout on a case-by-case basis.
- Add new ``--module`` CLI flag for running specific modules.
- ``on_startup`` blocks can now optionally be implicitly defined at the root
  indentation level in the module.
- You can now run astrality with ``--dry-run`` in order to check which actions
  that will be executed.
- Modules can now depend on other modules with the ``module`` requires keyword.
- Modules can now place action in a ``setup`` block, only to be executed once.
- You can now execute ``astrality --reset-setup module_name`` in order to
  clear executed module setup actions.
- Files created by ``compile``, ``copy``, ``stow``, and ``symlink`` actions
  are now persisted and cleaned up when executing
  ``astrality --cleanup MODULE``. Files that are overwritten by Astrality
  are backed up and restored on clean up.

Changed
-------

- ``astrality.yml`` has now been split into three separate files:
  ``astrality.yml`` for global configuration options, ``modules.yml``
  for global modules, and ``context.yml`` for global context.
- Directory module config file ``config.yml`` has been renamed and
  split into ``modules.yml`` and ``context.yml``. See point above.
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

- ``recompile_modified_templates`` has been renamed to
  ``reprocess_modified_files``, as this option now also includes copied files.

- Astrality will now only recompile templates that have already been compiled
  when ``reprocess_modified_files`` is set to ``true``.

- The ``template`` compile action keyword has now been replaced with
  ``content``. This keyword makes more sense when we add support for compiling
  all templates within a directory. It also stays consistent with the new action
  types that have been added.

  *Old syntax*

  .. code-block:: yaml

      compile:
          - template: path/to/template

  *New syntax:*

  .. code-block:: yaml

      compile:
          - content: path/to/template

- The module list items within the module ``requires`` option is now
  a dictionary, where shell commands are specified under the ``shell`` keyword.
  This allows other requirement types (see Added section).

  *Old syntax*

  .. code-block:: yaml

      requires:
          - './shell/script.sh'

  *New syntax:*

  .. code-block:: yaml

      requires:
          - shell: './shell/script'

- Astrality now automatically quits if there is no reason for it to continue
  running.
- When no compilation target is specified for a compile action, Astrality
  now creates a deterministic file within
  ``$XDG_DATA_HOME/astrality/compilations`` to be used as the compilation
  target. This behaves better than temporary files when programs expect
  files to still be present after Astrality restarts.
- Astrality is now more conservative when killing duplicate Astrality processes
  by using a *pidfile* instead of ``pgrep -f astrality``.


Fixed
-----

- If a ``import_context`` action imported specified ``from_section`` but not
  ``to_section``, the section was not imported at all. This is now fixed by
  setting ``to_section`` to the same as ``from_section``.

- Template path placeholders are now normalized, which makes it possible to
  refer to the same template path in different ways, using symlinks and ``..``
  paths.

- Module option ``requires_timeout`` is now respected.
- Astrality no longer kills processes containing "astrality" in their command
  line invocation.
