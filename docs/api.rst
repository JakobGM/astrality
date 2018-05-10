.. _API:

=================
API documentation
=================

This section contains documentation for the source code of Astrality, and is
intended for the developers of Astrality.

.. contents::
    :depth: 3

.. _API_structure_of_the_code_base:

The structure of the code base
==============================

Here we offer a quick overview of the most relevant python modules in the code base, loosely ordered according to their execution order.

``bin.astrality``:
    The CLI entry point of Astrality, using the standard library ``argparse`` module.

``astrality.astrality``:
    The main loop of Astrality, binding everything together. Calls out to the different submodules and handles interruption signals gracefully.

``astrality.config``:
    Compilation and pre-processing of the user configuration according to the heuristics explained in the documentation.

``astrality.github``:
    Retrieval of modules defined in GitHub repositories.

``astrality.module``:
    Execution of actions defined in modules.

    Each module in the user configuration is represented by a ``Module`` object.
    All ``Module``-objects are managed by a single ``ModuleManager`` object which iterates over them and executes their actions.

``astrality.requirements``:
    Module for checking if module requirements are satisfied.

``astrality.actions``:
    Module for executing actions such as "import_context", "compile", "run", and "trigger".

``astrality.event_listener``:
    Implements all the types of module event listeners as subclasses of ``EventListener``.

``astrality.context``:
    Defines a dictionary-like data structure which contains context values, passed off to Jinja2 template compilation.

``astrality.compiler``:
    Wrappers around the ``Jinja2`` library for compiling templates with specific context values.

``astrality.filewatcher``:
    Implements a file system watcher which dispatches to event handlers when files are modified on disk.

``astrality.utils``:
    Utility functions which are used all over the code base, most importantly a wrapper function for running shell commands.


Modules
=======

Astrality's modules are placed within the ``astrality`` mother-module. For
example, the ``actions`` module is importable from ``astrality.actions``.

Actions module
--------------

.. automodule:: astrality.actions
    :members:
    :undoc-members:
    :inherited-members:
    :show-inheritance:
