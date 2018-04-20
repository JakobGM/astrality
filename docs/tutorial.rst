.. _examples:

========
Tutorial
========

.. _examples_weekday_wallpaper:

A module using events
=====================

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

Now we need to create a module with a ``weekday`` event listener in ``astrality.yml``:

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
                - shell: feh --bg-fill modules/weekday_wallpaper/{event}.*

Now Astrality will set the appropriate wallpaper on startup. We still have a small bug in our module. If you do not restart Astrality the next day, yesterday's wallpaper will still be in use. We can fix this by changing the wallpaper every time the weekday *changes* by listening for the weekday event.

.. code-block:: yaml

    module/weekday_wallpaper:
        event_listener:
            type: weekday

        on_startup:
            run:
                - shell: feh --bg-fill modules/weekday_wallpaper/{event}.*

        on_event:
            run:
                - shell: feh --bg-fill modules/weekday_wallpaper/{event}.*

Or, alternatively, we can just :ref:`trigger <trigger_action>` the ``on_startup`` action block when the event changes:

.. code-block:: yaml

    module/weekday_wallpaper:
        event_listener:
            type: weekday

        on_startup:
            run:
                - shell: feh --bg-fill modules/weekday_wallpaper/{event}.*

        on_event:
            trigger: 
                - block: on_startup
