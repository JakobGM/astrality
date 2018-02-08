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
TODO

.. _events:

Events
======
TODO

.. _actions:

Actions
=======
TODO
