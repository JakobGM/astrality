=======
Modules
=======

How to add new wallpaper theme
==============================

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

