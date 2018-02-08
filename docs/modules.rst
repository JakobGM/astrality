.. _modules:

=======
Modules
=======

What are modules?
=================

Tasks to be performed by Astrality are grouped into so-called ``modules``.
These modules are used to define:

:ref:`templates`
    Configuration file templates that are available for compilation.

:doc:`timers`
    Timers can trigger events when certain predefined :ref:`periods` occur.

:ref:`actions`
    Tasks to be performed when :ref:`events` occur.

How to define a module
======================

Modules are defined in ``astrality.yaml``.
They should be formated as *dictionaries* placed at the root indentation level, and **must** be named ``module/*``. 
Choose ``*`` to be whatever you want to name your module.
The simplest module, with no associated behaviour, is:

.. code-block:: yaml

    module/test_module:
        enabled: true

Astrality skips parsing any modules which contain the option :code:`enabled: false`.
The default value of ``enabled`` is ``true``.

.. _templates:

Templates
=========

Modules define which templates that are *available* for compilation.
Templates are defined on a per-module-basis, using the ``templates`` keyword.

Each *key* in the ``templates`` dictionary becomes a ``shortname`` for that specific template, used to refer to that template in other parts of your Astrality configuration. More on that later in the :ref:`actions` section of this page.

Each template item has the following available attributes:

    * ``source``: Path to the template.
    * ``target``: *[Optional]* Path which specifies where to put the *compiled* template. You can skip this option if you do not care where the compiled template is placed, and what it is named. You can still use the compiled result by referencing its ``shortname``, which will be explained :ref:`later <actions>`.

An example of module templates syntax:

.. code-block:: yaml

    module/module_name:
        templates:
            template_A:
                source: templates/A.conf
            template_B:
                source: /absolute/path/B.conf
                target: ${XDG_CONFIG_HOME}/B/config

.. note::
    All relative file paths are interpreted relative to the :ref:`config directory<config_directory>` of Astrality.

.. caution::
    Defining a ``templates`` section in a module will make those templates *available* for compilation. It will **not** automatically compile them. That must be additionaly specified as an action. See the :ref:`actions` section.

.. _events:

Events
======
TODO

.. _actions:

Actions
=======
TODO
