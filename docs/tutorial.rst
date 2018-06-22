.. _examples:

========
Tutorial
========

.. _examples_templating:

Writing an application configuration template
=============================================

Motivation
----------

In order to use an application on a UNIX system, there are often several tasks
that need to be performed before doing so.

* Determine if the application should be installed on the system in the first
  place.
* Install the package.
* Place the default configuration file for the application in its appropriate
  location.
* Tweak configuration paramateres according to the host environment and
  personal preferences.
* Start any required background processes on startup.

Preferably you would want to do this work once, and easily deploy such
configurations across different systems.
Astrality enables you to manage such tasks in a reproducible and sharable way,
grouping those tasks together into a single configuration.

For the sake of example, we will use Astrality to manage the configuration of
polybar_, a status line application for Linux.
Hopefully, we will be able to demonstrate that the end result is
a configuration that is easy to tweak, re-deploy, and share with others.

The task
--------

In most cases, you will have an existing configuration to start from. In this
case it will be the `default configuration`_ shipped with polybar.
Here is a small extract of this default configuration file:

.. literalinclude:: examples/config1
   :language: dosini
   :caption: ~/.config/polybar/config
   :lines: 12-13,35-39,197-200

This extract contains the two types of configuration types one usually wants to
change:

* **Personal preference** - The three main fonts used in the status bar.
* **Host environment** - The wlan interface identifier.

Create a polybar module
-----------------------

We will create a Astrality module which is responsible for the management of
all things related polybar.

Modules can by defined in either ``~/.config/astrality/modules.yml`` or
``~/.config/astrality/modules/<module_group>/modules.yml``.
You can tweak these locations to your preferences by setting
:ref:`$ASTRALITY_CONFIG_HOME <configuration>` and/or by setting the
:ref:`modules_directory <modules_directory>` config option.
For now, we will create a ``statusbars`` module group in the latter default
location.

Let's start by creating a seperate directory for this module group:

.. code-block:: console

    $ mkdir -p ~/.config/astrality/modules/statusbars && cd $_

We will also move the default configuration file to this folder to keep
everything in one place.
This file will be used as a template for compilation so we will prefix the
filename with ``template.`` to make this clear:

.. code-block:: console

    $ mv ~/.config/polybar/config template.config

We will :ref:`define a module <modules_how_to_define>` named ``polybar`` which
:ref:`compiles <compile_action>` this template to the previous location:

.. literalinclude:: examples/modules1.yml
   :language: yaml
   :caption: ~/.config/astrality/modules/statusbars/modules.yml

You can also instruct Astrality to :ref:`copy <copy_action>` or :ref:`symlink
<symlink_action>`, optionally recursively. See the :ref:`actions documentation
<actions>` for more information.

We can now compile this template by running: ``astrality -m
statusbars::polybar``, or alternatively just ``astrality``, as all defined
modules are enabled by default. An optional ``--dry-run`` flag is supported
if you want to safely check which actions will be executed.

At this point this is nothing more than
a glorified copy script, but we can now start to insert Jinja2 templating
syntax into this file.

Writing the template with context placeholders
----------------------------------------------

We can start by defining some context values which we want to
insert into our template:

.. literalinclude:: examples/context1.yml
   :language: yaml
   :caption: ~/.config/astrality/modules/statusbars/context.yml

And now let's use *placeholders* in the template where these values should be
inserted:

.. literalinclude:: examples/config2
   :emphasize-lines: 4-6,10
   :language: dosini
   :caption: ~/.config/astrality/modules/statusbars/template.config
   :lines: 12-13,35-39,197-200

The compilation target will replace these placeholders with the placeholders
defined in ``context.yml``, and you can check the result by running ``astrality
-m statusbars::polybar`` again.

This extracts the configuration options which are of interest into a much more
succinct file, enabling us to tweak it easily.
The same placeholders can be used in other templates, which can make switching
between different status bars more consistent, for instance.
There are also other benefits related to *sharing* modules, which we will come
back to later.

.. hint::

    You may have noticed that we only defined *two* fonts in ``context.yml``,
    while using *three* fonts in the template, thinking that the use of ``{{
    statusbar.font.3 }}`` is undefined. But for numeric context keys, astrality
    will fall back to the greatest number available.
    
    With other words: ``statusbar.font.3 -> statusbar.font.2``.

    This allows us to specify an additional font in the future if we want to.

More information can be found in the :ref:`templating documentation
<templating>`.

Expanding the module
--------------------

Starting polybar
~~~~~~~~~~~~~~~~

Currently, Astrality only compiles the template and quits. We can do better!
First, we can instruct Astrality to start polybar after having compiled the
template:

.. literalinclude:: examples/modules2.yml
   :language: yaml
   :caption: ~/.config/astrality/modules/statusbars/modules.yml
   :emphasize-lines: 6-7

We can now compile the template *and* start polybar by running ``astrality -m
statusbars::polybar``.

When using the ``--config`` polybar flag, we do not actually care exactly *where*
the compiled template is saved, as long as we can provide the compilation path
to polybar. We can therefore skip specifying the ``target`` for the compilation
and instead use ``{template.config}`` in the shell command. This placeholder
will be replaced with the file path to the compiled template.

.. literalinclude:: examples/modules3.yml
   :language: yaml
   :caption: ~/.config/astrality/modules/statusbars/modules.yml
   :emphasize-lines: 5-6

This will reduce additional clutter on our filesystem and prevent overwriting
any existing files. This unique compilation target will make the module easier
to share with other, a topic which we will come back to soon.

We can also kill potentially existing polybar processes before starting the new
one:

.. literalinclude:: examples/modules4.yml
   :language: yaml
   :caption: ~/.config/astrality/modules/statusbars/modules.yml
   :emphasize-lines: 6

See :ref:`the run action <run_action>` for more information regarding the
execution of shell commands within Astrality.

Requirements
~~~~~~~~~~~~

By default, all modules defined in subdirectories of
``~/.config/astrality/modules`` will be enabled. See :ref:`enabled modules
documentation <modules_enabled_modules>` for how to gain more fine-grained
control.

We can add *additional* constrains for when we consider a module enabled. In
this case, we can require polybar to be installed on the system. If polybar is
*not* installed, Astrality will skip any further module action and log
a warning.

.. literalinclude:: examples/modules5.yml
   :language: yaml
   :caption: ~/.config/astrality/modules/statusbars/modules.yml
   :emphasize-lines: 2-3

You can also add requirements related to environmet variables, shell command
exit codes, and other astrality modules. Alternatively, you can define actions
within an ``on_setup`` block to install such dependencies once, and only once.
See :ref:`module dependencies <module_requires>` and :ref:`action blocks
<modules_action_blocks>` for more information.

Sharing your module
-------------------

Publish to GitHub
~~~~~~~~~~~~~~~~~

You can easily share an Astrality module by `publishing
<https://github.com/JakobGM/color-schemes.astrality>`_ the module directory to
GitHub_ as a repository. ``modules.yml`` and ``context.yml`` must be located
at the root level of the repository. An example module repository can be found
`here <https://github.com/JakobGM/color-schemes.astrality>`_.

Fetch module from GitHub
~~~~~~~~~~~~~~~~~~~~~~~~

Let us assume that your GitHub username is ``username`` and you published the
statusbars module directory as part of a repository named ``statusbars``.
Other people can now try your status bar configuration by running:

.. code-block:: console

    $ astrality -m github::username/statusbars::polybar

Astrality will automatically clone the repository and execute the module's
actions. They will be able to quickly judge if your specific configuration
is to their taste or not.

Overriding context values
~~~~~~~~~~~~~~~~~~~~~~~~~

The context values used in the polybar template was earlier defined in
``context.yml`` within the module directory. Any such context key can
be overwritten by defining the same key in the global context store
located at ``~/.config/astrality/context.yml``.

This allows anybody to specify *their* favorite font and correct WLAN
interface handle, while still using *your* polybar configuration.

It is this that makes Astrality modules much more sharable across
different preferences and host environments. The ``context.yml``
clearly stipulates which parameters which someone (including you)
probably want to change at some time.

If someone want specify their correct interfaces, while keeping
your specified font, they can define the following global context
items (all without taking a deep-dive into your configuration):

.. literalinclude:: examples/global_context1.yml
   :language: yaml
   :caption: ~/.config/astrality/context.yml
   :emphasize-lines: 4,7


Permanently add a GitHub module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the user decides to keep the module in use, they can add
``github::username/statusbars::polybar`` to the ``enabled_modules`` section in
``~/.config/astrality/astrality.yml``. It will be added to any existing modules
when executing ``astrality`` in the shell.

Clean up files created by a module
----------------------------------

You can easily clean up any files created by a module of any type, restoring
any overwritten files in the process. Use the ``--cleanup`` flag with the
same name you would use to enable the module. For example:

.. code-block:: console

    $ astrality --cleanup github::username/statusbars::polybar

If a module has overwritten a valuable file, you can use this option to restore
it. It also makes it easy to remove configuration files for applications you no
longer use! You can also try a new module with the ``--dry-run`` flag to safely
check which actions that will be executed.

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


.. _polybar: https://github.com/jaagr/polybar
.. _default configuration: https://github.com/jaagr/polybar/blob/73e4b4ac08ee7e746d327abf69e6242facbdc312/doc/config.cmake
.. _GitHub: https://github.com
