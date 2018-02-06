=============
Configuration
=============
The configuration directory for astrality is determined in the following way:

* If ``$ASTRALITY_CONFIG_HOME`` is set, use that folder as the configuration directory, else...
* If ``$XDG_CONFIG_HOME`` is set, use ``$XDG_CONFIG_HOME/astrality``, else...
* Use ``~/.config/astrality``, if it contains a ``astrality.yaml`` file, else...
* Use an example configuration.

The configuration file for astrality should be placed at the root of the astrality configuration directory and an example configuration can be found `here <https://github.com/JakobGM/astrality/blob/master/astrality.conf.example>`_.

Edit the configuration file in order to add your current location, given by your GPS coordinates (longitude, latitude, and elevation). These coordinates can be obtained from `this website <https://www.latlong.net/>`_.

Compton
-------
If you are using the `compton <https://github.com/chjj/compton>`_ compositor, you should disable any shadows and dims which could be applied to the conky wallpaper modules. Here is an example configuration from ``$XDG_CONFIG_HOME/compton/compton.conf``:

.. code-block:: lua

    inactive-dim = 0.1;
    shadow = true;
    shadow-exclude = [
        "! name~=''",
        "class_g = 'Conky'"
        ]
    mark-ovredir-focused = true;

How to add new wallpaper theme
------------------------------
Say you would want to create a new wallpaper theme called ``nature``. First create a new subdirectory in ``$XDG_CONFIG_HOME/astrality/wallpaper_themes`` named ``nature``:

.. code-block:: console

    mkdir -p $XDG_CONFIG_HOME/astrality/wallpaper_themes/nature

Then place pictures `supported by feh <http://search.cpan.org/~kryde/Image-Base-Imlib2-1/lib/Image/Base/Imlib2.pm#DESCRIPTION>`_ in the newly created directory. You **have** to use the following filenames::

    sunrise.*
    morning.*
    afternoon.*
    sunset.*
    night.*

Where the ``*`` suffixes can be any combination of file types supported by feh.

The images are not required to be different, in case if you do not have enough fitting wallpapers to choose from. You can use identical copies for some or all of the time periods, or even better, create a symbolic links. For example:

.. code-block:: console

    # Let sunrise be the same picture as sunset
    ln -s sunrise.jpg sunrise.jpg

Then you have to add the following line to the ``[Appearance]`` section of ``astrality.conf``:

Restart the astrality process in order to see the change of the wallpaper theme.

Pull requests containing new themes are very welcome!

