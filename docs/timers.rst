.. _timers:

======
Timers
======

What are timers?
================

``Timers`` provide you with the ability to keep track of certain events, and change module behaviour accordingly. A short summation of timers:

    #. Timers are specified on a *per-module-basis*.
    #. There are different ``types`` of timers.
    #. Timers determine exactly *when* the :ref:`actions <actions>` you specify within a module's :ref:`on_period_change <module_events_on_period_change>` :ref:`event block <events>` are executed.
    #. Timers are optional, you can write valid modules without specifying one. Actions specified within the ``on_period_change`` action block will never be executed when no module timer is specified.
    #. Timers provide the module with the ``{period}`` placeholder. It is replaced by the current ``period`` at runtime. The replacement value is specific for that specific timer's type, and dynamically changes according to rules set by the timer.

.. _timer_periods:

Periods
=======

TODO: Explain periods

Solar Timer
===========

Edit the configuration file in order to add your current location, given by your GPS coordinates (longitude, latitude, and elevation). These coordinates can be obtained from `this website <https://www.latlong.net/>`_.
