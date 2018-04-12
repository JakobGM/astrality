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

- Template metadata is now copied to compilation targets, including permission
  bits. Thanks to @sshashank124 for the implementation!

Fixed
-----

- If a ``import_context`` action imported specified ``from_section`` but not
  ``to_section``, the section was not imported at all. This is now fixed by
  setting ``to_section`` to the same as ``from_section``.