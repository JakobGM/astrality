.. _modules:

=======
Modules
=======

What are modules?
=================

Tasks to be performed by Astrality are grouped into so-called ``modules``.
These modules are used to define:

:ref:`actions`
    Tasks to be performed when :ref:`events <events>` occur, for example :ref:`compiling a template <compile_action>`.

:doc:`event_listeners`
    Event listeners can listen to predefined :ref:`events <event_listener_events>`.

.. _modules_how_to_define:

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
The default value of ``enabled`` is ``true``, so you do not have to specify it.


.. _module_requires:

Module dependencies
-------------------

You can specify conditionals that must be satisfied in order to consider a module enabled.
It can be useful if a module requires certain dependencies in order to work correctly

This is done by setting the module option ``requires`` equal to a shell command, or a list of shell commands,
*all* of which must be successfully executed (i.e. return a ``0`` exit code) in order to enable the module.

For example, if your module depends on the ``docker`` and ``docker-machine`` shell commands being available, you can check if they are available with the POSIX command ``command -v``:

.. code-block:: yaml

    module/docker:
        requires:
            - command -v docker
            - command -v docker-machine

If ``docker`` *or* ``docker-machine`` is not in your shell ``PATH``, this module will be disabled.

If one of the shell commands use more than 1 second to return, it will be considered failed. You can change the default time out by setting the :ref:`requires_timeout <configuration_options_requires_timeout>` configuration option.

.. hint::
    ``requires`` can be useful if you want to use Astrality to manage your `dotfiles <https://medium.com/@webprolific/getting-started-with-dotfiles-43c3602fd789>`_. You can use module dependencies in order to only compile configuration templates to their respective directories if the dependent application is available on the system. This way, Astrality becomes a "conditional symlinker" for your dotfiles.


.. _events:

Events
======

When you want to assign :ref:`tasks <actions>` for Astrality to perform, you have to define *when* to perform them. This is done by defining those ``actions`` in one of four available ``event`` blocks.

    .. _module_events_on_startup:

    ``on_startup``:
        Tasks to be performed when Astrality first starts up.
        Useful for compiling templates that don't need to change after they have been compiled.

    .. _module_events_on_exit:

    ``on_exit``:
        Tasks to be performed when you kill the Astrality process.
        Useful for cleaning up any unwanted clutter.

    .. _module_events_on_event:

    ``on_event``:
        Tasks to be performed when the specified module ``event listener`` detects a new ``event``.
        Useful for dynamic behaviour, periodic tasks, and templates that should change during runtime.
        The ``on_event`` block will never be triggered when no module event listener is defined.
        More on event listeners follows in :ref:`the next section <event_listeners>`.

    ``on_modified``:
        Tasks to be performed when specific files are modified on disk.
        You specify a set of tasks to performed on a *per-file-basis*.
        Useful for quick feedback when editing template files.

        .. caution::
            Only files within ``$ASTRALITY_CONFIG_HOME/**/*`` are observed for modifications.
            Also, :ref:`context imports <context_import_action>` are currently not supported in ``on_modified`` event blocks.

            If any of this is a use case for you, please open an `issue <https://github.com/jakobgm/astrality/issues>`_!

Example of module event blocks:

.. code-block:: yaml

    module/module_name:
        templates:
            some_template:
                source: 'templates/some.template'

        on_startup:
            ...startup actions...

        on_event:
            ...event actions...

        on_exit:
            ...shutdow actions...

        on_modified:
            some_template_path:
                ...some_template_path modified actions...

.. note::
    On Astrality startup, the ``on_startup`` event will be triggered, but **not** ``on_event``. The ``on_event`` event will only be triggered when the ``event listener`` detects a new ``event`` *after* Astrality startup.

.. _actions:

Actions
=======

Actions are tasks for Astrality to perform, and are placed within :ref:`event blocks <events>` in order to specify *when* to perform them. There are four available ``action`` types:

    :ref:`import_context <context_import_action>`:
        Import a ``context`` section from a YAML formatted file. ``context`` variables are used as replacement values for placeholders in your :ref:`templates <templating>`. See :ref:`context <context>` for more information.

    :ref:`compile <compile_action>`:
        Compile a specific template to a target path.

    :ref:`run <run_action>`:
        Execute a shell command, possibly referring to any compiled template and/or the last detected :ref:`event <event_listener_events>` defined by the :ref:`module event listener <event_listeners>`.

    :ref:`trigger <trigger_action>`:
        Perform *all* actions specified within another :ref:`event block <events>`. With other words, this action *appends* all the actions within another event block to the actions already specified in the event block. Useful for not having to repeat yourself when you want the same actions to be performed during different events.


.. _context_import_action:

Context imports
---------------

The simplest way to define :ref:`context values <context>` is to just define their values in ``astrality.yaml``.
Those context values are available for insertion into all your templates.

But you can also import context values from arbitrary YAML files. Among other use cases, this allows you to:

* Split context definitions into separate files in order to clean up your configuration. You can, for instance, create one dedicated context file for each of your modules.
* Combine context imports with :ref:`on_event <events>` blocks in order to dynamically change how templates compile. This allows quite complex behaviour.

Context imports are defined as a dictionary, or a list of dictionaries if you need several imports, under the ``import_context`` keyword in an :ref:`event block <events>` of a module.

This is best explained with an example. Let us create a color schemes file:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/contexts/color_schemes.yaml

    context/gruvbox_dark:
        background: 282828
        foreground: ebdbb2

Then let us import the gruvbox color scheme into the "colors" :ref:`context <context>` section:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/astrality.yaml

    module/color_scheme:
        on_startup:
            import_context:
                from_path: contexts/color_schemes.yaml
                from_section: gruvbox_dark
                to_section: colors

This is functionally equivalent to writing:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/astrality.yaml

    context/colors:
        background: 282828
        foreground: ebdbb2

.. hint::
    You may wonder why you would want to use this kind of redirection when definining context variables. The advantages are:

        * You can now use ``{{ colors.foreground }}`` in all your templates instead of ``{{ gruvbox_dark.foreground }}``. Since your templates do not know exactly *which* color scheme you are using, you can easily change it in the future by editing only one line in ``astrality.yaml``.

        * You can use ``import_context`` in a ``on_event`` event block in order to change your colorscheme based on the time of day. Perhaps you want to use "gruvbox light" during daylight, but change to "gruvbox dark" after dusk?

The available attributes for ``import_context`` are:

    ``from_path``:
        A YAML formatted file containing :ref:`context sections <context>`.

    ``from_section``: *[Optional]*
        Which context section to import from the file specified in ``from_path``.

        If none is specified, all sections defined in ``from_path`` will be
        imported.

    ``to_section``: *[Optional]*
        What you want to name the imported context section. If this attribute is omitted, Astrality will use the same name as ``from_section``.

        This option will only have an effect if ``from_section`` is specified.


.. _compile_action:

Compile templates
-----------------

Template compilations are defined as a dictionary, or a list of dictionaries, under the ``compile`` keyword in an :ref:`event block <events>` of a module.

Each template compilation action has the following available attributes:

    ``template``
        Path to the template.
    ``target``: *[Optional]*
        Path which specifies where to put the *compiled* template.

        You can skip this option if you do not care where the compiled template is placed, and what it is named.
        You can still use the compiled result by writing ``{template_path}`` in the rest of your module. This placeholder will be replaced with the absolute path of the compiled template. You can for instance refer to the file in :ref:`a shell command <run_action>`.

        .. warning::
            When you do not provide Astrality with a ``target`` path for a template, Astrality will create a *temporary* file as the target for compilation. This file will be automatically deleted when you quit Astrality.


Here is an example:

.. code-block:: yaml

    module/desktop:
        on_startup:
            compile:
                - source: modules/desktop/polybar.template
                  target: ${XDG_CONFIG_HOME}/polybar/config
                - source: modules/desktop/conky_module.template

            run:
                - conky -c {modules/desktop/conky_module.template}
                - polybar bar

Notice that the shell command ``conky -c {modules/desktop/conky_module.template}`` is replaced with something like ``conky -c /path/to/compiled/template.temp``.

.. note::
    All relative file paths are interpreted relative to the :ref:`config directory<config_directory>` of Astrality.


.. _run_action:

Run shell commands
------------------

You can instruct Astrality to run an arbitrary number of shell commands when different :ref:`events <events>` occur.
Place each command as a list item under the ``run`` option of an :ref:`event block <events>`.

You can place the following placeholders within your shell commands:

    ``{event}``:
        The last event detected by the :ref:`module event listener <event_listeners>`.

    ``{template_path}``:
        Replaced with the absolute path of the *compiled* version of the template placed at the path ``template_path``.

Example:

.. code-block:: yaml

    module/weekday_module:
        event_listener:
            type: weekday

        on_startup:
            run: notify-send "You just started Astrality, and the day is {event}"

        on_event:
            run:
                - notify-send "It is now midnight, have a great {event}! I'm creating a notes document for this day."
                - touch ~/notes/notes_for_{event}.txt

        on_exit:
            run:
                - echo "Deleting today's notes!"
                - rm ~/notes/notes_for_{event}.txt


.. _trigger_action:

Trigger events
--------------

You can trigger another module :ref:`event <events>` by specifying the ``trigger`` action.

The ``trigger`` option accepts ``on_startup``, ``on_event``, ``on_exit``, and ``on_modified:file_path``, either as a single string, or a list with any combination of these.

An example of a module using ``trigger`` actions:

.. code-block:: yaml

    module/module_using_triggers:
        templates:
            event_listener:
                type: weekday

            on_startup:
                run: startup_command

                trigger:
                    - on_event
                    - on_modified:templates/templateA

            on_event:
                import_context:
                    - from_path: contexts/A.yaml
                      from_section: '{event}'
                      to_section: a_stuff

                trigger: on_modified:templates/templateA

            on_modified:
                templates/A.template:
                    compile:
                        template: templates/A.template

                    run: shell_command_dependent_on_templateA

This is equivalent to writing the following module:

.. code-block:: yaml

    module/module_using_triggers:
        templates:
            event_listener:
                type: weekday

            on_startup:
                import_context:
                    - from_path: contexts/A.yaml
                      from_section: '{event}'
                      to_section: a_stuff

                compile:
                    template: templates/templateA

                run:
                    - startup_command
                    - shell_command_dependent_on_templateA

            on_event:
                import_context:
                    from_path: contexts/A.yaml
                    from_section: '{event}'
                    to_section: a_stuff

                compile:
                    template: templateA

                run: shell_command_dependent_on_templateA

            on_modified:
                templates/templateA:
                    compile:
                        template: templates/templateA

                    run: shell_command_dependent_on_templateA


.. hint::
    You can use ``trigger: on_event`` in the ``on_startup`` block in order to consider the event detected on Astrality startup as a new ``event``.

    The ``trigger`` action can also help you reduce the degree of repetition in your configuration.

.. caution::
    Astrality does not invoke recursive trigger events at the moment.
    You have to specify them manually instead, as shown in the example above.



The execution order of module actions
-------------------------------------

The order of action execution is as follows:

    #. :ref:`context_import <context_import_action>` for each module.
    #. :ref:`compile <compile_action>` for each module.
    #. :ref:`run <run_action>` for each module.

Modules are iterated over from top to bottom such that they appear in ``astrality.yaml``.
This ensures the following invariants:

    * When you compile templates, all ``context`` imports have been performed, and are available for placeholder substitution.
    * When you run shell commands, all templates have been compiled, and are available for reference.
