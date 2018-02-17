.. _modules:

=======
Modules
=======

What are modules?
=================

Tasks to be performed by Astrality are grouped into so-called ``modules``.
These modules are used to define:

:ref:`module_templates`
    Configuration file templates that are available for compilation.

:doc:`timers`
    Timers can trigger events when certain predefined :ref:`periods <timer_periods>` occur.

:ref:`actions`
    Tasks to be performed when :ref:`events` occur.

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


.. _module_templates:

Templates
=========

Modules define which templates that are *available* for compilation.
Templates are defined on a per-module-basis, using the ``templates`` keyword.

Each *key* in the ``templates`` dictionary becomes a ``shortname`` for that specific template, used to refer to that template in other parts of your Astrality configuration. More on that later in the :ref:`actions` section of this page.

Each template item has the following available attributes:

    ``source``
        Path to the template.
    ``target``: *[Optional]*
        Path which specifies where to put the *compiled* template.

        You can skip this option if you do not care where the compiled template is placed, and what it is named.
        You can still use the compiled result by writing ``{shortname}`` in the rest of your module. This placeholder will be replaced with the absolute path of the compiled template. You can for instance refer to the file in :ref:`a shell command <run_action>`.

        .. warning::
            When you do not provide Astrality with a ``target`` path for a template, Astrality will create a *temporary* file as the target for compilation. This file will be automatically deleted when you quit Astrality.

An example of module templates syntax:

.. code-block:: yaml

    module/module_name:
        templates:
            template_A:
                source: templates/A.conf
            template_B:
                source: /absolute/path/B.conf
                target: ${XDG_CONFIG_HOME}/B/config

.. note::
    All relative file paths are interpreted relative to the :ref:`config directory<config_directory>` of Astrality.

.. caution::
    Defining a ``templates`` section in a module will make those templates *available* for compilation. It will **not** automatically compile them. That must be additionaly specified as an action. See the :ref:`compilation action <compile_action>` documentation.

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

    .. _module_events_on_period_change:

    ``on_period_change``:
        Tasks to be performed when the specified module ``timer`` detects a new ``period``.
        Useful for dynamic behaviour, periodic tasks, and templates that should change during runtime.
        This event will never be triggered when no module timer is defined.
        More on timers follows in :ref:`the next section <timers>`.

    ``on_modified``:
        Tasks to be performed when specific templates are modified on disk.
        You specify a set of tasks to performed on a *per-template-basis*.
        Useful for quick feedback when editing template files.

        .. caution::
            Only templates within ``$ASTRALITY_CONFIG_HOME/**/*`` are observed for modifications.
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

        on_period_change:
            ...period change actions...

        on_exit:
            ...shutdow actions...

        on_modified:
            some_template:
                ...some_template modified actions...

.. note::
    On Astrality startup, the ``on_startup`` event will be triggered, but **not** ``on_period_change``. The ``on_period_change`` event will only be triggered when the ``timer`` defined ``period`` changes *after* Astrality startup.

.. _actions:

Actions
=======

Actions are tasks for Astrality to perform, and are placed within :ref:`event blocks <events>` in order to specify *when* to perform them. There are four available ``action`` types:

    :ref:`import_context <context_import_action>`:
        Import a ``context`` section from a YAML formatted file. ``context`` variables are used as replacement values for placeholders in your :ref:`templates <module_templates>`. See :ref:`context <context>` for more information.

    :ref:`compile <compile_action>`:
        Compile a specific :ref:`template <module_templates>` to its target destination.

    :ref:`run <run_action>`:
        Execute a shell command, possibly referring to any compiled template and/or the current :ref:`period <timer_periods>` defined by the :ref:`module timer <timers>`.

    :ref:`trigger <trigger_action>`:
        Perform *all* actions specified within another :ref:`event block <events>`. With other words, this action *appends* all the actions within another event block to the actions already specified in the event block. Useful for not having to repeat yourself when you want the same actions to be performed during different events.


.. _context_import_action:

Context imports
---------------

Context imports are defined as a list of dictionaries under the ``import_context`` keyword in an :ref:`event block <events>` of a module.

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
                - from_path: contexts/color_schemes.yaml
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

        * You can use ``import_context`` in a ``on_period_change`` event block in order to change your colorscheme based on the time of day. Perhaps you want to use "gruvbox light" during daylight, but change to "gruvbox dark" after dusk?

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

In order to compile a configuration file template, you first need to :ref:`give it a shortname <module_templates>`.
After having done that, you can compile it in an :ref:`event block <events>`. Put the ``shortname`` of the template as a list item within the ``compile`` option.
Here is an example:

.. code-block:: yaml

    module/polybar:
        templates:
            polybar:
                source: templates/polybar
                target: ${XDG_CONFIG_HOME}/polybar/config

        on_startup:
            compile:
                - polybar

Compiling templates from another module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you need to compile a template from another module, you can refer to it by using the syntax ``module_name.template_shortname``. For instance:

.. code-block:: yaml

    module/A:
        templates:
            template_A:
                source: /what/ever

    module/B:
        on_period_change:
            compile:
                - A.template_A

.. _run_action:

Run shell commands
------------------

You can instruct Astrality to run an arbitrary number of shell commands when different :ref:`events <events>` occur.
Place each command as a list item under the ``run`` option of an :ref:`event block <events>`.

You can place the following placeholders within your shell commands:

    ``{period}``:
        The current period defined by the :ref:`module timer <timers>`.

    ``{template_shortname}``:
        The absolute path of the *compiled* template specified in the module option ``templates``.

Example:

.. code-block:: yaml

    module/weekday_module:
        timer:
            type: weekday

        on_startup:
            run:
                - notify-send "You just started Astrality, and the day is {period}"

        on_period_change:
            run:
                - notify-send "It is now midnight, have a great {period}! I'm creating a notes document for this day."
                - touch ~/notes/notes_for_{period}.txt

        on_exit:
            run:
                - echo "Deleting today's notes!"
                - rm ~/notes/notes_for_{period}.txt


.. _trigger_action:

Trigger events
--------------

You can trigger another module :ref:`event <events>` by specifying the ``trigger`` action.

The ``trigger`` option accepts ``on_startup``, ``on_period_change``, ``on_exit``, and ``on_modified.template_shortname``, either as a single string, or a list with any combination of these.

An example of a module using ``trigger`` actions:

.. code-block:: yaml

    module/module_using_triggers:
        templates:
            timer:
                type: weekday

            templateA:
                source: templates/A.template

            on_startup:
                run:
                    - startup_command
                trigger:
                    - on_period_change
                    - on_modified.templateA

            on_period_change:
                import_context:
                    - from_path: contexts/A.yaml
                      from_section: '{period}'
                      to_section: a_stuff
                trigger: on_modified.templateA

            on_modified:
                templateA:
                    compile:
                        - templateA
                    run:
                        - shell_command_dependent_on_templateA

This is equivalent to writing the following module:

.. code-block:: yaml

    module/module_using_triggers:
        templates:
            timer:
                type: weekday

            templateA:
                source: templates/A.template

            on_startup:
                import_context:
                    - from_path: contexts/A.yaml
                      from_section: '{period}'
                      to_section: a_stuff
                compile:
                    - templateA
                run:
                    - startup_command
                    - shell_command_dependent_on_templateA

            on_period_change:
                import_context:
                    - from_path: contexts/A.yaml
                      from_section: '{period}'
                      to_section: a_stuff
                compile:
                    - templateA
                run:
                    - shell_command_dependent_on_templateA

            on_modified:
                templateA:
                    compile:
                        - templateA
                    run:
                        - shell_command_dependent_on_templateA


.. hint::
    You can use ``trigger: on_period_change`` in order to consider Astrality startup as a ``period change`` event.

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
