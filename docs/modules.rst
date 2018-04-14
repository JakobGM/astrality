.. _modules:

=======
Modules
=======

What are modules?
=================

Tasks to be performed by Astrality are grouped into so-called ``modules``.
These modules are used to define:

:ref:`modules_action_blocks`:
    A grouping of :ref:`actions <actions>` which is supposed to be performed at a specific time, such as "on Astrality startup", "on Astrality exit", or "on event".

:ref:`actions`
    Tasks to be performed by Astrality, for example :ref:`compiling templates <compile_action>` or :ref:`running shell commands <run_action>`.

:doc:`event_listeners`
    Event listeners can listen to predefined :ref:`events <event_listener_events>` and trigger the "on event" action block of the module.

You can easily enable and disable modules, making your configuration more modular.

.. _modules_how_to_define:

How to define modules
=====================

There are two types of places where you can define your modules:

Directly in ``$ASTRALITY_CONFIG_HOME/astrality.yml``:
    Useful if you don't have too many modules, and you want to keep everything easily accessible in one file.

In a file named ``config.yml`` within a :ref:`modules directory <modules_directory>`:
    Useful if you have lots of modules, and want to separate them into separate directories with common responsibilities.

    See the :ref:`documentation <modules_external_modules>` for external modules for how to define modules this way.

    You can use templating features in ``config.yml``, since they are compiled at startup, after having parsed ``astrality.yml``.
    All context values defined in ``astrality.yml`` are therefore available in ``config.yml``, allowing configuration of module behaviour.

.. hint::
    A useful configuration structure is to define modules with "global responsibilities" in ``astrality.yml``, and group the remaining modules in seperate module directories by their categorical responsibilites (for example "terminals").

    Here "global responsibility" means having the responsibility to satisfy the dependecies of several other modules, such as defining context values used in several templates, creating directories, or installing common dependencies.

Module definition syntax
------------------------
Modules are formated as *dictionaries* placed at the root indentation level, and **must** be named ``module/*``.
Choose ``*`` to be whatever you want to name your module.
The simplest module, with no specific behaviour, is:

.. code-block:: yaml

    module/test_module:
        ... contents of module ...

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

If one of the shell commands use more than 1 second to return, it will be considered failed. You can change the default time out by setting the :ref:`requires_timeout <modules_config_requires_timeout>` configuration option.

.. hint::
    ``requires`` can be useful if you want to use Astrality to manage your `dotfiles <https://medium.com/@webprolific/getting-started-with-dotfiles-43c3602fd789>`_. You can use module dependencies in order to only compile configuration templates to their respective directories if the dependent application is available on the system. This way, Astrality becomes a "conditional symlinker" for your dotfiles.


.. _modules_action_blocks:

Action blocks
=============

When you want to assign :ref:`tasks <actions>` for Astrality to perform, you have to define *when* to perform them. This is done by defining those ``actions`` in one of four available ``action blocks``.

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

            If this is a use case for you, please open an `issue <https://github.com/jakobgm/astrality/issues>`_!

Demonstration of module action blocks:

.. code-block:: yaml

    module/module_name:
        on_startup:
            ...startup actions...

        on_event:
            ...event actions...

        on_exit:
            ...shutdow actions...

        on_modified:
            some/template/path:
                ...some/template/path modified actions...

.. note::
    On Astrality startup, the ``on_startup`` event will be triggered, but **not** ``on_event``. The ``on_event`` event will only be triggered when the ``event listener`` detects a new ``event`` *after* Astrality startup.

.. _actions:

Actions
=======

Actions are tasks for Astrality to perform, and are placed within :ref:`action blocks <modules_action_blocks>` in order to specify *when* to perform them. There are four available ``action`` types:

    :ref:`import_context <context_import_action>`:
        Import a ``context`` section from a YAML formatted file. ``context`` variables are used as replacement values for placeholders in your :ref:`templates <templating>`. See :ref:`context <context>` for more information.

    :ref:`compile <compile_action>`:
        Compile a specific template to a target path.

    :ref:`run <run_action>`:
        Execute a shell command, possibly referring to any compiled template and/or the last detected :ref:`event <event_listener_events>` defined by the :ref:`module event listener <event_listeners>`.

    :ref:`trigger <trigger_action>`:
        Perform *all* actions specified within another :ref:`action block <modules_action_blocks>`. With other words, this action *appends* all the actions within another action block to the actions already specified in the action block. Useful for not having to repeat yourself when you want the same actions to be performed during different events.


.. _context_import_action:

Context imports
---------------

The simplest way to define :ref:`context values <context>` is to just define their values in ``astrality.yml``.
Those context values are available for insertion into all your templates.

But you can also import context values from arbitrary YAML files. Among other use cases, this allows you to:

* Split context definitions into separate files in order to clean up your configuration. You can, for instance, create one dedicated context file for each of your modules.
* Combine context imports with :ref:`on_event <modules_action_blocks>` blocks in order to dynamically change how templates compile. This allows quite complex behaviour.

Context imports are defined as a dictionary, or a list of dictionaries if you need several imports, under the ``import_context`` keyword in an :ref:`action block <modules_action_blocks>` of a module.

This is best explained with an example. Let us create a color schemes file:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/modules/color_schemes/color_schemes.yml

    context/gruvbox_dark:
        background: 282828
        foreground: ebdbb2

Then let us import the gruvbox color scheme into the "colors" :ref:`context <context>` section:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/astrality.yml

    module/color_scheme:
        on_startup:
            import_context:
                from_path: modules/color_schemes/color_schemes.yml
                from_section: gruvbox_dark
                to_section: colors

This is functionally equivalent to writing:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/astrality.yml

    context/colors:
        background: 282828
        foreground: ebdbb2

.. hint::
    You may wonder why you would want to use this kind of redirection when definining context variables. The advantages are:

        * You can now use ``{{ colors.foreground }}`` in all your templates instead of ``{{ gruvbox_dark.foreground }}``. Since your templates do not know exactly *which* color scheme you are using, you can easily change it in the future by editing only one line in ``astrality.yml``.

        * You can use ``import_context`` in a ``on_event`` action block in order to change your colorscheme based on the time of day. Perhaps you want to use "gruvbox light" during daylight, but change to "gruvbox dark" after dusk?

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

Template compilations are defined as a dictionary, or a list of dictionaries, under the ``compile`` keyword in an :ref:`action block <modules_action_blocks>` of a module.

Each template compilation action has the following available attributes:

    ``template``
        Path to the template.
    ``target``: *[Optional]*
        Path which specifies where to put the *compiled* template.

        You can skip this option if you do not care where the compiled template is placed, and what it is named.
        You can still use the compiled result by writing ``{template_path}`` in the rest of your module. This placeholder will be replaced with the absolute path of the compiled template. You can for instance refer to the file in :ref:`a shell command <run_action>`.

        .. warning::
            When you do not provide Astrality with a ``target`` path for a template, Astrality will create a *temporary* file as the target for compilation. This file will be automatically deleted when you quit Astrality.

    ``permissions``: *[Optional]*
        The file mode (i.e. permission bits) assigned to the *compiled* template.
        Given either as a string, such as ``'755'``, or as an octal integer, such as ``0o755``.

        .. warning::
            Take care when specifying permission bits using integers, as they are interpreted literally w.r.t. the indicated base.

            ``permissions: 511`` is equal to running the shell command ``chmod 777 <compiled_template>``, as 511 *base 10* is equal to 777 *base 8*.
            ``permissions: 0o511`` is most often what you intended instead.

            You should therefore always prepend ``0o`` (this indicates an octal number) to the number you would usually use when using the shell command ``chmod``.

            Alternatively, specify permissions using a string instead, as ``permissions: '511'`` is equal to running the shell command ``chmod 511 <compiled_template>``.


Here is an example:

.. code-block:: yaml

    module/desktop:
        on_startup:
            compile:
                - source: modules/scripts/executable.sh.template
                  target: {{ env.XDG_CONFIG_HOME }}/bin/executable.sh
                  permissions: 0o555
                - source: modules/desktop/conky_module.template

            run:
                - shell: conky -c {modules/desktop/conky_module.template}
                - shell: polybar bar

Notice that the shell command ``conky -c {modules/desktop/conky_module.template}`` is replaced with something like ``conky -c /path/to/compiled/template.temp``.

.. note::
    All relative file paths are interpreted relative to the :ref:`config directory<config_directory>` of Astrality.


.. _run_action:

Run shell commands
------------------

You can instruct Astrality to run an arbitrary number of shell commands when different :ref:`action blocks <modules_action_blocks>` are triggered.
Each shell command is specified as a dictionary.
The shell command is specified as a string keyed to ``shell``.
Place the commands within a list under the ``run`` option of an :ref:`action block <modules_action_blocks>`.
See the example below.

You can place the following placeholders within your shell commands 

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
            run:
                - shell: 'notify-send "You just started Astrality, and the day is {event}"'

        on_event:
            run:
                - shell: 'notify-send "It is now midnight, have a great {event}! I'm creating a notes document for this day."'
                - shell: 'touch ~/notes/notes_for_{event}.txt'

        on_exit:
            run:
                - shell: 'echo "Deleting today's notes!"'
                - shell: 'rm ~/notes/notes_for_{event}.txt'

You can actually place these placeholders in any action type's string values.
Placeholders are replaced at runtime every time an action is triggered.

.. warning::
    ``template/path`` must be compiled when an action type with a
    ``{template/path}`` placeholder is executed. Otherwise, Astrality does not
    know what to replace the placeholder with, so it will leave it alone and
    log an error instead.

.. _trigger_action:

Trigger action blocks
---------------------

From one :ref:`action block <modules_action_blocks>` you can trigger another action block by specifying a ``trigger`` action.

Each trigger option is a dictionary with a mandatory ``block`` key, on of
``on_startup``, ``on_event``, ``on_exit``, or ``on_modified``. In the case of
setting ``block: on_modified``, you have to specify an additional ``path`` key
indicating which file modification block you want to trigger.

An example of a module using ``trigger`` actions:

.. code-block:: yaml

    module/module_using_triggers:
        event_listener:
            type: weekday

        on_startup:
            run:
                - shell: startup_command

            trigger:
                - block: on_event

        on_event:
            import_context:
                - from_path: contexts/A.yml
                  from_section: '{event}'
                  to_section: a_stuff

            trigger: 
                - block: on_modified
                  path: templates/templateA

        on_modified:
            templates/A.template:
                compile:
                    template: templates/A.template

                run: shell_command_dependent_on_templateA

This is equivalent to writing the following module:

.. code-block:: yaml

    module/module_using_triggers:
        event_listener:
            type: weekday

        on_startup:
            import_context:
                - from_path: contexts/A.yml
                  from_section: '{event}'
                  to_section: a_stuff

            compile:
                template: templates/templateA

            run:
                - shell: startup_command
                - shell: shell_command_dependent_on_templateA

        on_event:
            import_context:
                from_path: contexts/A.yml
                from_section: '{event}'
                to_section: a_stuff

            compile:
                template: templateA

            run:
                - shell: shell_command_dependent_on_templateA

        on_modified:
            templates/templateA:
                compile:
                    template: templates/templateA

                run:
                    - shell: shell_command_dependent_on_templateA


.. hint::
    You can use ``trigger: on_event`` in the ``on_startup`` block in order to
    consider the event detected on Astrality startup as a new ``event``.

    The ``trigger`` action can also help you reduce the degree of repetition in
    your configuration.


The execution order of module actions
-------------------------------------

The order of action execution is as follows:

    #. :ref:`context_import <context_import_action>` for each module.
    #. :ref:`compile <compile_action>` for each module.
    #. :ref:`run <run_action>` for each module.

Modules are iterated over from top to bottom such that they appear in ``astrality.yml``.
This ensures the following invariants:

    * When you compile templates, all ``context`` imports have been performed, and are available for placeholder substitution.
    * When you run shell commands, all templates have been compiled, and are available for reference.


.. _modules_global_config:

Global configuration options for modules
========================================

Global configuration options for all your modules are specified in ``astrality.yml`` within a dictionary named ``config/modules`` at root indentation, i.e.:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/astrality.yml

    config/modules:
        option1: value1
        option2: value2
        ...

**Available modules configuration options**:

.. _modules_config_requires_timeout:

``requires_timeout:``
    *Default:* ``1``

    Determines how long Astrality waits for :ref:`module requirements <module_requires>` to exit successfully, given in seconds. If the requirement times out, it will be considered failed.

    *Useful when requirements are costly to determine, but you still do not want them to time out.*

``run_timeout:``
    *Default:* ``0``

    Determines how long Astrality waits for module :ref:`run actions <run_action>` to exit, given in seconds.

    *Useful when you are dependent on shell commands running sequantially.*

``recompile_modified_templates:``
    *Default:* ``false``

    If enabled, Astrality will watch for file modifications in
    ``$ASTRALITY_CONFIG_HOME``.
    All ``compile_action`` items that contain ``template`` paths that have been
    modified will be compiled again.

    .. hint::
        You can have more fine-grained control over exactly *what* happens when
        a file is modified by using the ``on_modified`` :ref:`module event <modules_action_blocks>`.
        This way you can run shell commands, import context values, and compile
        arbitrary templates when specific files are modified on disk.

    .. caution::
        At the moment, Astrality only watches for file changes recursively within
        ``$ASTRALITY_CONFIG_HOME``.

.. _modules_directory:

``modules_directory:``
    *default:* ``modules``

    Where Astrality looks for externally defined configurations directories.

.. _modules_enabled_modules:

``enabled_modules:``
    *default:*

    .. code-block:: yaml

        enabled_modules:
            - name: '*'
            - name: '*::*'

    A list of modules which you want Astrality to use.
    By default, Astrality enables all defined modules.

    Specifying ``enabled_modules`` allows you to define a module without necessarily using it, making configuration switching easy.

    Modules defined in ``astrality.yml`` are enabled by appending ``name: name_of_module`` to ``enabled_modules``.
    If you have defined a module named ``vim`` in ``$ASTRALITY_CONFIG_HOME/<modules_directory>/text_editors/config.yml``,
    you can enable it by writing ``name: text_editors::vim``.

    **You can also use wildcards when specifying enabled modules:**

    * ``name: '*'`` enables all modules defined in: ``$ASTRALITY_CONFIG_HOME/astrality.yml``.
    * ``name: 'text_editors::*`` enables all modules defined in: ``$ASTRALITY_CONFIG_HOME/<modules_directory>/text_editors/config.yml``.
    * ``name: '*::*`` enables all modules defined in: ``$ASTRALITY_CONFIG_HOME/<modules_directory>/*/config.yml``.


.. _modules_external_modules:

Module subdirectories
=====================

You can define "external modules" in files named ``config.yml`` placed within separate subdirectories of your :ref:`modules directory <modules_directory>`.
This allows you to clean up your configuration and more easily share modules with others.

Another advantage of using module directories is that all :ref:`context values <context>` defined in ``astrality.yml`` are available for placeholder substitution in ``config.yml``.
Astrality compiles any enabled ``config.yml`` before parsing it.
This allows you to modify the behaviour of modules based on context, useful if you want to offer configuration options for modules.

#. Define your modules in ``$ASTRALITY_CONFIG_HOME/<modules_directory>/directory/config.yml``.
#. :ref:`Enable <modules_enabled_modules>` modules from this config file by appending ``name: directory::module_name`` to ``enabled_modules``.
   Alternatively, you can enable *all* modules defined in a module directory by appending ``name: directory::*`` instead.

By default, all module subdirectories are enabled.

Context values defined in ``astrality.yml`` have preference above context values defined in module subdirectories, allowing you to define default context values, while still allowing others to override these values.

.. caution::
    All relative paths and shell commands in external modules are interpreted relative to the external module directory,
    not ``$ASTRALITY_CONFIG_HOME``.
    This way it is more portable between different configurations.


.. _modules_github:

GitHub modules
==============

You can share a module directory with others by publishing the module subdirectory to `GitHub <https://github.com>`_.
Just define ``config.yml`` at the repository root, i.e. where ``.git`` exists, and include any dependent files within the repository.

Others can fetch your module by appending ``name: github::<your_github_username>/<repository>`` to ``enabled_modules``.

For example enabling the module named ``module_name`` defined in ``config.yml`` in the repository at https://github.com/username/repository:

.. code-block:: yaml

    config/modules:
        enabled_modules:
            - name: github::username/repository::module_name

Astrality will automatically fetch the module on startup and place it within ``$ASTRALITY_CONFIG_HOME/<modules_directory>/username/repository``.
If you want to automatically update the GitHub module, you can specify ``autoupdate: true``:

.. code-block:: yaml

    config/modules:
        enabled_modules:
            - name: github::username/repository::module_name
              autoupdate: true

If ``module_name`` is not specified, all modules will be enabled:

.. code-block:: yaml

    config/modules:
        enabled_modules:
            - name: github::username/repository
              autoupdate: true
