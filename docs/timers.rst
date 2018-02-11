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

What are modules used for?
==========================

Timers provide you with the tools needed for *dynamic* module behaviour. Sometimes you want a module to :ref:`execute <run_action>` different shell commands, and/or :ref:`compile <compile_action>` templates with :ref:`different context values <context_import_action>`, depending on exactly *when* those :ref:`actions <actions>` are performed.


.. _timer_how_to_define:

How to set a module timer
=========================

Module timers are defined within the :ref:`module block <modules_how_to_define>` it is supposed to provide functionality for. The syntax is as follows:

.. code-block:: yaml

    module/some_dynamic_module:
        timer:
            type: type_of_timer

            option1: whatever
            option2: something
            ...

Most timers provide you with additional options in order to tweak their behaviour. These are specified at the same indentation level as the timer type.

.. _timer_periods:

Periods
=======

Module timers keep track of some type of ``period`` and trigger the ``period_change`` :ref:`event <events>` whenever it enters a new period. You can refer to the current period in your module configuration (in ``astrality.yaml``) with the ``{period}`` placeholder.


An example using periods
------------------------

Let us explore the use of ``periods`` with an example: we want to use a different desktop wallpaper for each day of the week.

The ``weekday`` timer type keeps track of the following periods: ``monday``, ``tuesday``, ``wednesday``, ``thursday``, ``friday``, ``saturday``, and ``sunday``.

After having found seven fitting wallpapers, we name them according to the weekday we want to use them, and place them in ``$ASTRALITY_CONFIG_HOME/modules/weekday_wallpaper/``:

.. code-block:: console

    $ ls -l $ASTRALITY_CONFIG_HOME/modules/weekday_wallpaper

    monday.jpeg
    tuesday.jpg
    wednesday.png
    thursday.tiff
    friday.gif
    saturday.jpeg
    sunday.jpeg

Now we need to create a module with a ``weekday`` timer:

.. code-block:: yaml

    module/weekday_wallpaper:
        timer:
            type: weekday


We also need a way of setting the desktop wallpaper from the shell. Here we are going to use the `feh <https://wiki.archlinux.org/index.php/feh>`_ shell utility. Alternatively, on MacOS, we can use `this script <https://apple.stackexchange.com/a/150336>`_. After having installed ``feh``, we can use it to set the appropriate wallpaper on Astrality startup:

.. code-block:: yaml

    module/weekday_wallpaper:
        timer:
            type: weekday

        on_startup:
            run:
                - feh --bg-fill modules/weekday_wallpaper/{period}.*

Now Astrality will set the appropriate wallpaper on startup. We still have a small bug in our module. If you do not restart Astrality the next day, yesterday's wallpaper will still be in use. We can fix this by changing the wallpaper every time the weekday *changes* by listening for the ``period_change`` :ref:`event <events>`.

.. code-block:: yaml

    module/weekday_wallpaper:
        timer:
            type: weekday

        on_startup:
            run:
                - feh --bg-fill modules/weekday_wallpaper/{period}.*

        on_period_change:
            run:
                - feh --bg-fill modules/weekday_wallpaper/{period}.*


Timer types
===========

Here is a list of all available Astrality module timers and their configuration options. If what you need is not available, feel free to `open an issue <https://github.com/JakobGM/astrality/issues>`_ with a timer request!


.. _timer_types_solar:

Solar
-----

Description
    Keeps track of the sun's position in the sky at a given location.

Specifier
    ``type: solar``

Periods
    ``sunrise``, ``morning``, ``afternoon``, ``sunset``, ``night``

.. csv-table:: Configuration options
   :header: "Option", "Default", "Description"
   :widths: 6, 5, 30

   "latitude", 0, "Latitude coordinate point of your location."
   "longitude", 0, "Longitude coordinate point of your location."
   "elevation", 0, "Height above sea level at your location."

These coordinates can be obtained from `this website <https://www.latlong.net/>`_.

**Example configuration**

.. code-block:: yaml

    module/solar_module:
        timer:
            type: solar
            latitude: 63.446827
            longitude: 10.421906
            elevation: 0

Weekday
-------

Description
    Keeps track of the weekdays.

Specifier
    ``type: weekday``

Periods
    ``monday``, ``tuesday``, ``wednesday``, ``thursday``, ``friday``, ``saturday``, ``sunday``

*No configuration options are available for the weekday timer*.

**Example configuration**

.. code-block:: yaml

    module/weekday_module:
        timer:
            type: weekday


Periodic
--------

Description
    Keeps track of constant length time intervals.

Specifier
    ``type: periodic``

Periods
    ``0``, ``1``, ``2``, ``3``, and so on...

.. csv-table:: Configuration options
   :header: "Option", "Default", "Description"
   :widths: 6, 5, 30

   "seconds", 0, "Number of seconds between each period."
   "minutes", 0, "Number of minutes between each period."
   "hours", 0, "Number of hours between each period."
   "days", 0, "Number of days between each period."

If the configured time interval is of zero length, Astrality uses ``hours: 1`` instead.

**Example configuration**

.. code-block:: yaml

    module/periodic_module:
        timer:
            type: periodic
            hours: 8


Static
------

Description
    A timer which never changes its period. This is the default timer for modules.

Specifier
    ``type: static``

Periods
    ``static``

*No configuration options are available for the static timer*.

**Example configuration**

.. code-block:: yaml

    module/static_module:
        ...
