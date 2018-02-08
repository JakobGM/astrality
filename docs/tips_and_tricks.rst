.. _tips_and_tricks:

===============
Tips and Tricks
===============

Configuration of other applications
===================================

i3wm
----
You probably want to automatically start Astrality on startup. Here is an example for those who use the `i3 tiling window manager <https://github.com/i3/i3>`_.

Add the following line to ``$XDG_CONFIG_HOME/i3/config``:

.. code-block:: console

    exec --no-startup-id "astrality"

Compton
-------
If you are using the `compton <https://github.com/chjj/compton>`_ compositor, and want to use the conky ``modules`` included in the example configuration, you should disable any shadows and dims which could be applied to the conky desktop modules. Here is an example compton configuration which you should place at ``$XDG_CONFIG_HOME/compton/compton.conf``:

.. code-block:: lua

    inactive-dim = 0.1;
    shadow = true;
    shadow-exclude = [
        "! name~=''",
        "class_g = 'Conky'"
        ]
    mark-ovredir-focused = true;
