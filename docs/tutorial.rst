.. _examples:

========
Tutorial
========

.. _examples_dotfiles:

Managing dotfiles with templates
================================

It is relatively common to organize all configuration files in a "dotfiles"
repository. How you structure such a repository comes down to personal
preference. We would like to use the templating capabilities of Astrality
without making any changes to our existing dotfiles hierarchy. This is
relatively easy!

Let us start by managing the files located in ``$XDG_CONFIG_HOME``, where most
configuration files reside. The default value of this environment variable is
"~/.config". We will create an Astrality module which automatically detects
files named "template.whatever", and compile it to "whatever". This way you can
easily write new templates without having to add new configuration in order to
compile them.

.. code-block:: yaml

    # ~/.config/astrality/modules.yml

    dotfiles:
        compile:
            content: $XDG_CONFIG_HOME
            target: $XDG_CONFIG_HOME
            include: 'template\.(.+)'

Let us go through the module configuration step-by-step:

- We use the ``compile`` action type, as we are only interested in compiling
  templates at the moment.
- We set both the content and target to be ``$XDG_CONFIG_HOME``, compiling any
  template to the same directory as the template.
- We only want to compile template filenames which matches the regular
  expression ``template\.(.+)``.
- The regex capture group in ``template\.(.+)`` specifies that everything
  appearing after "template." should be used as the *compiled* target filename.

We can now compile all such templates within *$XDG_CONFIG_HOME* by running
``astrality`` from the shell. Before doing so, it is recommended to run
``astrality --dry-run`` to see which actions that will be performed.

But we would like to *automatically* recompile
templates when we modify them or create new ones. You can achieve this by
enabling ``reprocess_modified_files`` in ``astrality.yml``:

.. code-block:: yaml

    # ~/.config/astrality/astrality.yml

    config/modules:
        reprocess_modified_files: true

Astrality will automatically recompile any modified templates as long as it
runs as a background process.

Let us continue by managing a more complicated dotfiles repository. Most people
create a separate repository containing *all* their configuration files, not
only ``$XDG_CONFIG_HOME``. The repository is then cloned to something like
``~/.dotfiles``, the contents of which is symlinked or copied to separate
locations, ``$HOME``, ``$XDG_CONFIG_HOME``, ``$/etc`` on so on. You can do all
of this with Astrality.


For demonstration purposes, let us assume that the templates within
"~/.dotfiles/home" should be compiled to "~", and "~/.dotfiles/etc" to "/etc",
while non-templates should be symlinked instead. This combination of
:ref:`symlink <symlink_action>` and :ref:`compile <compile_action>` actions can
be done with the :ref:`stow <stow_action>` action.

Move ``modules.yml`` and ``astrality.yml`` to the root of your dotfiles
repository. Set ``export ASTRALITY_CONFIG_HOME=~/.dotfiles``. Finally, modify
the dotfiles module accordingly:

.. code-block:: yaml

    # ~/.dotfiles/modules.yml

    dotfiles:
        stow:
            - content: home
                target: ~
                templates: 'template\.(.+)'
                non_templates: symlink

            - content: etc
                target: /etc
                templates: 'template\.(.+)'
                non_templates: symlink

``templates: 'template\.(.+)'`` and ``non_templates: symlink`` are actually the
default options for the stow action, so we could have skipped specifying them
altogether. Alternatively, you can specify ``non_templates: copy``.

You can now start to write all your configuration files as templates instead,
using placeholders for secret API keys or configuration values that change
between machines, and much much more.

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

Now we need to create a module with a ``weekday`` event listener in ``modules.yml``:

.. code-block:: yaml

    weekday_wallpaper:
        event_listener:
            type: weekday


We also need a way of setting the desktop wallpaper from the shell. Here we are going to use the `feh <https://wiki.archlinux.org/index.php/feh>`_ shell utility. Alternatively, on MacOS, we can use `this script <https://apple.stackexchange.com/a/150336>`_. After having installed ``feh``, we can use it to set the appropriate wallpaper on Astrality startup:

.. code-block:: yaml

    weekday_wallpaper:
        event_listener:
            type: weekday

        on_startup:
            run:
                - shell: feh --bg-fill modules/weekday_wallpaper/{event}.*

Now Astrality will set the appropriate wallpaper on startup. We still have a small bug in our module. If you do not restart Astrality the next day, yesterday's wallpaper will still be in use. We can fix this by changing the wallpaper every time the weekday *changes* by listening for the weekday event.

.. code-block:: yaml

    weekday_wallpaper:
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

    weekday_wallpaper:
        event_listener:
            type: weekday

        on_startup:
            run:
                - shell: feh --bg-fill modules/weekday_wallpaper/{event}.*

        on_event:
            trigger: 
                - block: on_startup
