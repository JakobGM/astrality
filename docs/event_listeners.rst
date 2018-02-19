.. _event_listeners:

===============
Event listeners
===============

What are event listeners?
=========================

``Event listeners`` provide you with the ability to keep track of certain events, and change module behaviour accordingly. A short summation of event listeners:

    #. Event listeners are specified on a *per-module-basis*.
    #. There are different ``types`` of event listeners.
    #. Event listeners determine exactly *when* the :ref:`actions <actions>` you specify within a module's :ref:`on_event <module_events_on_event>` :ref:`event block <events>` are executed.
    #. Event listeners are optional, you can write valid modules without specifying one. Actions specified within the ``on_event`` action block will never be executed when no module event listener is specified.
    #. Event listeners provide the module with the ``{event}`` placeholder. It is replaced by the current ``event`` at runtime. The replacement value is specific for that specific event listener's type, and dynamically changes according to rules set by the event listener.

What are modules used for?
==========================

Event listeners provide you with the tools needed for *dynamic* module behaviour. Sometimes you want a module to :ref:`execute <run_action>` different shell commands, and/or :ref:`compile <compile_action>` templates with :ref:`different context values <context_import_action>`, depending on exactly *when* those :ref:`actions <actions>` are performed.


.. _event_listener_how_to_define:

How to set a module event listener
==================================

Module event listeners are defined within the :ref:`module block <modules_how_to_define>` it is supposed to provide functionality for. The syntax is as follows:

.. code-block:: yaml

    module/some_dynamic_module:
        event_listener:
            type: type_of_event_listener

            option1: whatever
            option2: something
            ...

Most event listeners provide you with additional options in order to tweak their behaviour. These are specified at the same indentation level as the event listener type.

.. _event_listener_events:

Events
======

Module event listeners keep track of some type of ``event`` and trigger the ``event`` :ref:`event <events>` whenever it enters a new event. You can refer to the current event in your module configuration (in ``astrality.yaml``) with the ``{event}`` placeholder.

.. caution::

    When you use placeholders, you must take care that the placeholder is not interpreted as a YAML *dictionary* instead of a *string*. The following will not work as intended:

    .. code-block:: yaml

        some_option: {event}

    This is interpreted as the dictionary ``{'event': None}``. In this case you must mark the option explicitly as a string:

    .. code-block:: yaml

        some_option: '{event}'

    Using quotes is not necessary when the placeholder is part of a greater string. This works:


    .. code-block:: yaml

        some_option: echo {event}

An example using events
------------------------

Let us explore the use of ``events`` with an example: we want to use a different desktop wallpaper for each day of the week.

The ``weekday`` event listener type keeps track of the following events: ``monday``, ``tuesday``, ``wednesday``, ``thursday``, ``friday``, ``saturday``, and ``sunday``.

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

Now we need to create a module with a ``weekday`` event listener:

.. code-block:: yaml

    module/weekday_wallpaper:
        event_listener:
            type: weekday


We also need a way of setting the desktop wallpaper from the shell. Here we are going to use the `feh <https://wiki.archlinux.org/index.php/feh>`_ shell utility. Alternatively, on MacOS, we can use `this script <https://apple.stackexchange.com/a/150336>`_. After having installed ``feh``, we can use it to set the appropriate wallpaper on Astrality startup:

.. code-block:: yaml

    module/weekday_wallpaper:
        event_listener:
            type: weekday

        on_startup:
            run:
                - feh --bg-fill modules/weekday_wallpaper/{event}.*

Now Astrality will set the appropriate wallpaper on startup. We still have a small bug in our module. If you do not restart Astrality the next day, yesterday's wallpaper will still be in use. We can fix this by changing the wallpaper every time the weekday *changes* by listening for the ``event`` :ref:`event <events>`.

.. code-block:: yaml

    module/weekday_wallpaper:
        event_listener:
            type: weekday

        on_startup:
            run:
                - feh --bg-fill modules/weekday_wallpaper/{event}.*

        on_event:
            run:
                - feh --bg-fill modules/weekday_wallpaper/{event}.*

Or, alternatively, we can just :ref:`trigger <trigger_action>` startup event when the event changes:

.. code-block:: yaml

    module/weekday_wallpaper:
        event_listener:
            type: weekday

        on_startup:
            run:
                - feh --bg-fill modules/weekday_wallpaper/{event}.*

        on_event:
            trigger: on_startup


Event listener types
===========

Here is a list of all available Astrality module event listeners and their configuration options. If what you need is not available, feel free to `open an issue <https://github.com/JakobGM/astrality/issues>`_ with a event listener request!


.. _event_listener_types_solar:

Solar
-----

Description
    Keeps track of the sun's position in the sky at a given location.

Specifier
    ``type: solar``

Events
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
        event_listener:
            type: solar
            latitude: 63.446827
            longitude: 10.421906
            elevation: 0


.. _event_listener_types_static:

Static
------

Description
    An event listener which never changes its event. This is the default event listener for modules.

Specifier
    ``type: static``

Events
    ``static``

*No configuration options are available for the static event listener*.

**Example configuration**

.. code-block:: yaml

    module/static_module:
        ...


.. _event_listener_types_time_of_day:

Time of day
-----------

Description
    Keeps track of a specific time interval for each day of the week. Useful for tracking when you are at work.

Specifier
    ``type: time_of_day``

Events
    ``on``, ``off``

.. csv-table:: Configuration options
   :header: "Option", "Default", "Description"
   :widths: 6, 5, 30

   "monday", "``'09:00-17:00'``", "The time of day that is considered 'on'."
   "tuesday", "``'09:00-17:00'``", "The time of day that is considered 'on'."
   "wednesday", "``'09:00-17:00'``", "The time of day that is considered 'on'."
   "thursday", "``'09:00-17:00'``", "The time of day that is considered 'on'."
   "friday", "``'09:00-17:00'``", "The time of day that is considered 'on'."
   "saturday", "``''``", "The time of day that is considered 'on'."
   "sunday", "``''``", "The time of day that is considered 'on'."


**Example configuration**

.. code-block:: yaml

    module/european_tue_to_sat_work_week:
        event_listener:
            type: time_of_day
            monday: ''
            tuesday: '08:00-16:00'
            wednesday: '08:00-16:00'
            thursday: '08:00-16:00'
            friday: '08:00-16:00'
            saturday: '08:00-16:00'


Weekday
-------

Description
    Keeps track of the weekdays.

Specifier
    ``type: weekday``

Events
    ``monday``, ``tuesday``, ``wednesday``, ``thursday``, ``friday``, ``saturday``, ``sunday``

*No configuration options are available for the weekday event listener*.

**Example configuration**

.. code-block:: yaml

    module/weekday_module:
        event_listener:
            type: weekday


.. _event_listener_types_periodic:

Periodic
--------

Description
    Keeps track of constant length time intervals.

Specifier
    ``type: periodic``

Events
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
        event_listener:
            type: periodic
            hours: 8