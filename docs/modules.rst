.. _modules:

=======
Modules
=======

What are modules?
=================

Tasks to be performed by Astrality are grouped into so-called ``modules``.
These modules are used to define:

:ref:`modules_action_blocks`:
    A grouping of :ref:`actions <actions>` which is supposed to be performed at
    a specific time, such as "on Astrality startup", "on Astrality exit", or
    "on event".

:ref:`actions`
    Tasks to be performed by Astrality, for example :ref:`compiling templates
    <compile_action>` or :ref:`running shell commands <run_action>`.

:doc:`event_listeners`
    Event listeners can listen to predefined :ref:`events
    <event_listener_events>` and trigger the "on event" action block of the
    module.

You can easily enable and disable modules, making your configuration more
modular.

.. _modules_how_to_define:

How to define modules
=====================

There are two types of places where you can define your modules:

Directly in ``$ASTRALITY_CONFIG_HOME/modules.yml``:
    Useful if you don't have too many modules, and you want to keep everything
    easily accessible in one file.

In a file named ``modules.yml`` within a :ref:`modules directory <modules_directory>`:
    Useful if you have lots of modules, and want to separate them into separate
    directories with common responsibilities.

    See the :ref:`documentation <modules_external_modules>` for external
    modules for how to define modules this way.

    You can use templating features in ``modules.yml``, since they are compiled
    at startup with all context values defined in all ``context.yml`` files.

.. hint::
    A useful configuration structure is to define modules with "global
    responsibilities" in ``$ASTRALITY_CONFIG_HOME/modules.yml``, and group the
    remaining modules in seperate module directories by their categorical
    responsibilites (for example "terminals").

    Here "global responsibility" means having the responsibility to satisfy the
    dependecies of several other modules, such as defining context values used
    in several templates, creating directories, or installing common
    dependencies.

Module definition syntax
------------------------
Modules are formated as separate *dictionaries* placed at the root indentation
level of "modules.yml". The key used will become the module name.

The simplest module, with no specific behaviour, is:

.. code-block:: yaml

    # Source: $ASTRALITY_CONFIG_HOME/modules.yml

    my_module:
        enabled: true

Astrality skips parsing any modules which contain the option :code:`enabled: false`.
The default value of ``enabled`` is ``true``, so you do not have to specify it.


.. _module_requires:

Module dependencies
-------------------

You can specify conditionals that must be satisfied in order to consider a module enabled.
It can be useful if a module requires certain dependencies in order to work correctly

You can specify module requirements by setting the module option ``requires``
equal to a list of dictionaries containing one, or more, of the following
keywords:

``env``:
    Environment variable specified as a string. The environment variable must
    be set in order to consider the module enabled.

``installed``:
    Program name specified as a string. The program name must be invokable
    through the command line, i.e. available through the ``$PATH`` environment
    variable. You can test this by typing ``command -v program_name`` in your
    shell.

``shell``:
    Shell command specified as a string. The shell command must return a 0 exit
    code (which defines success), in order to consider the module enabled.

    If the shell command uses more than 1 second to return, it will be
    considered failed. You can change the default timeout by setting the
    :ref:`requires_timeout <modules_config_requires_timeout>` configuration
    option.

    You can also override the default timeout on a case-by-case basis by
    setting the ``timeout`` key to a numeric value (in seconds).

``module``:
    Module dependent on other module(s), specified with the same name syntax
    as with :ref:`enabled_modules <modules_enabled_modules>`.

    If a module is missing one or more module dependencies, it will be disabled,
    and an error will be logged.


*All* specified dependencies must be satisfied in order to enable the module.

For example, if your module depends on the ``docker`` shell command, another
module named ``docker-machine``, the environment variable ``$ENABLE_DOCKER``
being set, and "my_docker_container" existing, you can check this by setting
the following requirements:

.. code-block:: yaml

    # Souce: $ASTRALITY_CONFIG_HOME/modules.yml

    docker:
        requires:
            - installed: docker
            - module: docker-machine
            - env: ENABLE_DOCKER
            - shell: '[ $(docker ps -a | grep my_docker_container) ]'
              timeout: 10 # seconds

.. hint::
    ``requires`` can be useful if you want to use Astrality to manage your
    `dotfiles
    <https://medium.com/@webprolific/getting-started-with-dotfiles-43c3602fd789>`_.
    You can use module dependencies in order to only compile configuration
    templates to their respective directories if the dependent application is
    available on the system. This way, Astrality becomes a "conditional
    symlinker" for your dotfiles.


.. _modules_action_blocks:

Action blocks
=============

When you want to assign :ref:`tasks <actions>` for Astrality to perform, you
have to define *when* to perform them. This is done by defining those
``actions`` in one of five available ``action blocks``.

    .. _module_events_on_startup:

    ``on_setup``:
        Tasks to be performed only once and never again. Can be used for
        setting up dependencies.

        Executed actions are written to
        ``$XDG_DATA_HOME/astrality/setup.yml``, by default
        ``$HOME/.local/share``. Execute ``astrality --reset-setup module_name``
        if you want to re-execute a module's setup actions during the next
        run.

    ``on_startup``:
        Tasks to be performed when Astrality first starts up.
        Useful for compiling templates that don't need to change after they
        have been compiled.

        *Actions defined outside action blocks are considered to be part of this
        block.*

    .. _module_events_on_exit:

    ``on_exit``:
        Tasks to be performed when you kill the Astrality process.
        Useful for cleaning up any unwanted clutter.

    .. _module_events_on_event:

    ``on_event``:
        Tasks to be performed when the specified module ``event listener``
        detects a new ``event``.
        Useful for dynamic behaviour, periodic tasks, and templates that should
        change during runtime.
        The ``on_event`` block will never be triggered when no module event
        listener is defined.
        More on event listeners follows in :ref:`the next section
        <event_listeners>`.

    ``on_modified``:
        Tasks to be performed when specific files are modified on disk.
        You specify a set of tasks to performed on a *per-file-basis*.
        Useful for quick feedback when editing template files.

        .. caution::
            Only files within ``$ASTRALITY_CONFIG_HOME/**/*`` are observed for
            modifications.

            If this is an issue for you, please open a GitHub
            `issue <https://github.com/jakobgm/astrality/issues>`_!

Demonstration of module action blocks:

.. code-block:: yaml

    module_name:
        ...startup actions (option 1)...

        on_setup:
            ...setup actions...

        on_startup:
            ...startup actions (option 2)...

        on_event:
            ...event actions...

        on_exit:
            ...shutdow actions...

        on_modified:
            some/file/path:
                ...some/file/path modified actions...

.. note::
    On Astrality startup, the ``on_startup`` event will be triggered, but
    **not** ``on_event``. The ``on_event`` event will only be triggered when
    the ``event listener`` detects a new ``event`` *after* Astrality startup.

.. _actions:

Actions
=======

Actions are tasks for Astrality to perform, and are placed within :ref:`action
blocks <modules_action_blocks>` in order to specify *when* to perform them.
These are the available ``action`` types:

    :ref:`import_context <context_import_action>`:
        Import a ``context`` section from a YAML formatted file. ``context``
        variables are used as replacement values for placeholders in your
        :ref:`templates <templating>`. See :ref:`context <context>` for more
        information.

    :ref:`compile <compile_action>`:
        Compile a specific template or template directory to a target path.

    :ref:`copy <copy_action>`:
        Copy a specific file or directory to a target path.

    :ref:`symlink <symlink_action>`:
        Create symbolic link(s) pointing to a specific file or directory.

    :ref:`stow <stow_action>`:
        Combination of ``compile`` + ``copy`` or ``compile`` + ``symlink``,
        bisected based on filename pattern of files within a content directory.

    :ref:`run <run_action>`:
        Execute a shell command, possibly referring to any compiled template
        and/or the last detected :ref:`event <event_listener_events>` defined
        by the :ref:`module event listener <event_listeners>`.

    :ref:`trigger <trigger_action>`:
        Perform *all* actions specified within another :ref:`action block
        <modules_action_blocks>`. With other words, this action *appends* all
        the actions within another action block to the actions already
        specified in the action block. Useful for not having to repeat yourself
        when you want the same actions to be performed during different events.


.. _context_import_action:

Context imports
---------------

The simplest way to define :ref:`context values <context>` is to just define
their values in ``$ASTRALITY_CONFIG_HOME/context.yml``.
Those context values are available for insertion into all your templates.

But you can also import context values from arbitrary YAML files. Among other
use cases, this allows you to:

* Split context definitions into separate files in order to clean up your
  configuration.
* Combine context imports with :ref:`on_event <modules_action_blocks>` blocks
  in order to dynamically change how templates compile. This allows quite
  complex behaviour.

Context imports are defined as a dictionary, or a list of dictionaries, if you
need several imports. Use the ``import_context`` keyword in an :ref:`action
block <modules_action_blocks>` of a module.

This is best explained with an example. Let us create a color schemes file:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/modules/color_schemes/color_schemes.yml

    gruvbox_dark:
        background: 282828
        foreground: ebdbb2

    gruvbox_light:
        background: fbf1c7
        foreground: 3c3836


Then let us import the gruvbox *dark* color scheme into the "colors"
:ref:`context <context>` section:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/modules.yml

    color_scheme:
        on_startup:
            import_context:
                from_path: modules/color_schemes/color_schemes.yml
                from_section: gruvbox_dark
                to_section: colors

This is functionally equivalent to writing the following global context file:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/context.yml

    colors:
        background: 282828
        foreground: ebdbb2

.. hint::
    You may wonder why you would want to use this kind of redirection when
    definining context variables. The advantages are:

        * You can now use ``{{ colors.foreground }}`` in all your templates
          instead of ``{{ gruvbox_dark.foreground }}``. Since your templates do
          not know exactly *which* color scheme you are using, you can easily
          change it in the future by editing only one line in ``modules.yml``.

        * You can use ``import_context`` in a ``on_event`` action block in
          order to change your colorscheme based on the time of day. Perhaps
          you want to use "gruvbox light" during daylight, but change to
          "gruvbox dark" after dusk?

The available attributes for ``import_context`` are:

    ``from_path``:
        A YAML formatted file containing :ref:`context sections <context>`.

    ``from_section``: *[Optional]*
        Which context section to import from the file specified in
        ``from_path``.

        If none is specified, all sections defined in ``from_path`` will be
        imported.

    ``to_section``: *[Optional]*
        What you want to name the imported context section. If this attribute
        is omitted, Astrality will use the same name as ``from_section``.

        This option will only have an effect if ``from_section`` is specified.


.. _compile_action:

Compile templates
-----------------

Template compilations are defined as a dictionary, or a list of dictionaries,
under the ``compile`` keyword in an :ref:`action block <modules_action_blocks>`
of a module.

Each template compilation action has the following available attributes:

    ``content:``
        Path to either a template file or template directory.

        If ``content`` is a directory, Astrality will compile all templates
        recursively to the ``target`` directory, preserving the directory
        hierarchy.

    ``target:`` *[Optional]*
        *Default:* Temporary file created by Astrality.

        Path which specifies where to put the *compiled* template.

        You can skip this option if you do not care where the compiled template
        is placed, and what it is named. You can still use the compiled result
        by writing ``{template_path}`` in the rest of your module. This
        placeholder will be replaced with the absolute path of the compiled
        template. You can for instance refer to the file in :ref:`a shell
        command <run_action>`.

        .. info::
            When you do not provide Astrality with a ``target`` path for
            a template, Astrality will compile the template to
            ``$XDG_DATA_HOME/astrality/compilations``.

    .. _compile_action_include:

    ``include`` *[Optional]*
        *Default:* ``'(.+)'``

        Regular expression defining which filenames that are considered to be
        templates. Useful when ``content`` is a directory which contains
        non-template files. By default Astrality will try to compile all files.

        If you specify a capture group, astrality will use the captured string
        as the target filename. For example, ``templates: 'template\.(.+)'``
        will match the file "template.kitty.conf" and rename the target to
        "kitty.conf".

        .. hint::
            You can test your regex `here <https://regex101.com/r/myMbmT/1>`_.
            Astrality uses the capture group with the greatest index.

    .. _compile_action_permissions:

    ``permissions:`` *[Optional]*
        *Default:* Same permissions as the template file.

        The file mode (i.e. permission bits) assigned to the *compiled* template.
        Given either as a string of octal permissions, such as ``'755'``, or as
        a string of symbolic permissions, such as ``'u+x'``. This option is
        passed to the linux shell command ``chmod``. Refer to ``chmod``'s
        manual for the full details on possible arguments.

        .. note::
            The permissions specified in the ``permissions`` option are applied
            *on top* of the default permissions copied from the template file.

            For example, if the template's permissions are ``rw-r--r-- (644)``
            and the value of ``'ug+x'`` is supplied for the ``permissions``
            option, the ``644`` permissions will first be copied to the
            resulting compiled file and then ``chmod ug+x`` will be applied on
            top of that to give a resulting permission on the file of
            ``rwxr-xr-- (754)``.

            If an invalid value is supplied for the ``permissions`` option,
            only the default permissions are copied to the compiled file.


Here is an example:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/modules.yml

    desktop:
        compile:
            - content: modules/scripts/executable.sh.template
              target: ${XDG_CONFIG_HOME}/bin/executable.sh
              permissions: 0o555
            - content: modules/desktop/conky_module.template

        run:
            - shell: conky -c {modules/desktop/conky_module.template}
            - shell: polybar bar

Notice that the shell command ``conky -c
{modules/desktop/conky_module.template}`` is replaced with something like
``conky -c /tmp/astrality/compiled.conky_module.template``.

.. note::
    All relative file paths in modules are interpreted relative to the
    directory which contains "module.yml" which defines the module.


.. _symlink_action:

Symlink files
-------------

You can ``symlink`` a file or directory to a target destination. Directories
will be recursively symlinked, leaving any non-conflicting files intact. The
``symlink`` action have the following available parameters.

    ``content:``
        The target of the symlinking, with other words a path to a file or
        directory with the actual file content.

        If ``content`` is a directory, Astrality will create an identical
        directory hierarchy at the ``target`` directory path and create
        separate symlinks for each file in ``content``.

    ``target:``
        Where to place the symlink(s).

        .. caution::
            This is the *location* of the symlink, **not** where the symlink
            *points to*.

    ``include`` *[Optional]*
        *Default:* ``'(.+)'``

        Regular expression restricting which filenames that should be
        symlinked. By default Astrality will try to symlink all files.

        If you specify a capture group, astrality will use the captured string
        as the symlink name. For example, ``include: 'symlink\.(.+)'`` will
        match the file "symlink.wallpaper.jpeg" and rename the symlink to
        "wallpaper.jpeg".

.. note::
    If you astrality encounters an existing **file** where it is supposed to
    place a symbolic link, it will rename the existing file to "filename.bak".

.. _copy_action:

Copy files
----------

You can ``copy`` a file or directory to a target destination. Directories will
be recursively copied, leaving non-conflicting files at the target destination
intact. The ``copy`` action have the following available parameters.

    ``content:``
        Where to copy *from*, with other words a path to a file or directory
        with existing content to be copied.

        If ``content`` is a directory, Astrality will create an identical
        directory hierarchy at the ``target`` directory path and recursively
        copy all files.

    ``target:``
        A path specifying where to copy *to*.
        Any non-conflicting files at the target destination will be left alone.

    ``include`` *[Optional]*
        *Default:* ``'(.+)'``

        Regular expression restricting which filenames that should be
        copied. By default Astrality will try to copy all files.

        If you specify a capture group, astrality will use the captured string
        as the name for the copied file. For example, ``include: 'copy\.(.+)'``
        will copy the file "copy.binary.blob" and rename the copy to
        "binary.blob".

    ``permissions:`` *[Optional]*
        *Default:* Same permissions as the original file(s).

        See :ref:`compilation permissions <compile_action_permissions>` for
        more information.



.. _stow_action:

Stow a directory
----------------

Often you want to:

#. Move all content from a directory in your dotfile repository to a specific
   target directory, while...
#. Compiling any template according to a consistent naming scheme, and...
#. Symlink or copy the remaining files which are *not* templates.

The ``stow`` action type allows you to do just that! Stow has the following
available parameters:

    ``content:``
        Path to a directory of mixed content, i.e. both templates and
        non-templates.

    ``target:``
        Path to directory where processed content should be placed.
        Templates will be compiled to ``target``, and the remaining files will
        be treated according to the ``non_templates`` parameter.

    ``templates:`` *[Optional]*
        *Default:* ``'template\.(.+)'``

        Regular expression restricting which filenames that should be compiled
        as templates. By default, Astrality will only compile files named
        "template.*" and rename the compilation target to "*".

        See the compile action :ref:`include parameter <compile_action_include>`
        for more information.

    ``non_templates:`` *[Optional]*
        *Default:* ``'symlink'``

        *Accepts:* ``symlink``, ``copy``, ``ignore``

        What to do with files that do not match the ``templates`` regex.

    ``permissions:`` *[Optional]*
        *Default:* Same permissions as the original file(s).

        See :ref:`compilation permissions <compile_action_permissions>` for
        more information.


Here is an example module which compiles all files matching the glob
``$XDG_CONFIG_HOME/**/*.t``, and places the *compiled* template besides the
template, but *without* the file extension ".t". It leaves all other files
alone:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/modules.yml

    dotfiles:
        stow:
            content: $XDG_CONFIG_HOME
            target: $XDG_CONFIG_HOME
            templates: '(.+)\.t'
            non_templates: ignore



.. _run_action:

Run shell commands
------------------

You can instruct Astrality to run an arbitrary number of shell commands when
different :ref:`action blocks <modules_action_blocks>` are triggered.
Each shell command is specified as a dictionary.
The shell command is specified as a string keyed to ``shell``.
Place the commands within a list under the ``run`` option of an
:ref:`action block <modules_action_blocks>`.
See the example below.

You can place the following placeholders within your shell commands 

    ``{event}``:
        The last event detected by the
        :ref:`module event listener <event_listeners>`.

    ``{template_path}``:
        Replaced with the absolute path of the *compiled* version of the
        template placed at the path ``template_path``.

Example:

.. code-block:: yaml

    weekday_module:
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

From one :ref:`action block <modules_action_blocks>` you can trigger another
action block by specifying a ``trigger`` action.

Each trigger option is a dictionary with a mandatory ``block`` key, on of
``on_startup``, ``on_event``, ``on_exit``, or ``on_modified``. In the case of
setting ``block: on_modified``, you have to specify an additional ``path`` key
indicating which file modification block you want to trigger.

An example of a module using ``trigger`` actions:

.. code-block:: yaml

   module_using_triggers:
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
                    content: templates/A.template

                run: shell_command_dependent_on_templateA

This is equivalent to writing the following module:

.. code-block:: yaml

    module_using_triggers:
        event_listener:
            type: weekday

        on_startup:
            import_context:
                - from_path: contexts/A.yml
                  from_section: '{event}'
                  to_section: a_stuff

            compile:
                content: templates/templateA

            run:
                - shell: startup_command
                - shell: shell_command_dependent_on_templateA

        on_event:
            import_context:
                from_path: contexts/A.yml
                from_section: '{event}'
                to_section: a_stuff

            compile:
                content: templateA

            run:
                - shell: shell_command_dependent_on_templateA

        on_modified:
            templates/templateA:
                compile:
                    content: templates/templateA

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
    #. :ref:`symlink <symlink_action>` for each module.
    #. :ref:`copy <copy_action>` for each module.
    #. :ref:`compile <compile_action>` for each module.
    #. :ref:`stow <stow_action>` for each module.
    #. :ref:`run <run_action>` for each module.

Modules are iterated over from top to bottom such that they appear in
``modules.yml``. This ensures the following invariants:

    * When you compile templates, all ``context`` imports have been performed,
      and are available for placeholder substitution.
    * When you run shell commands, all (non-)templates have been
      compiled/copied/symlinked, and are available for reference.


.. _modules_global_config:

Global configuration options for modules
========================================

Global configuration options for all your modules are specified in
``$ASTRALITY_CONFIG_HOME/astrality.yml`` within a dictionary named ``modules``
at root indentation, i.e.:

.. code-block:: yaml

    # Source file: $ASTRALITY_CONFIG_HOME/astrality.yml

    modules:
        option1: value1
        option2: value2
        ...

**Available modules configuration options**:

.. _modules_config_requires_timeout:

``requires_timeout:``
    *Default:* ``1``

    Determines how long Astrality waits for :ref:`module requirements
    <module_requires>` to exit successfully, given in seconds. If the
    requirement times out, it will be considered failed.

    *Useful when requirements are costly to determine, but you still do not
    want them to time out.*

``run_timeout:``
    *Default:* ``0``

    Determines how long Astrality waits for module :ref:`run actions
    <run_action>` to exit, given in seconds.

    *Useful when you are dependent on shell commands running sequantially.*

``reprocess_modified_files:``
    *Default:* ``false``

    If enabled, Astrality will watch for file modifications in
    ``$ASTRALITY_CONFIG_HOME``.
    All files that have been compiled or copied to a destination will be
    recompiled or recopied if they are modified.

    .. hint::
        You can have more fine-grained control over exactly *what* happens when
        a file is modified by using the ``on_modified`` :ref:`module event
        <modules_action_blocks>`. This way you can run shell commands, import
        context values, and compile arbitrary templates when specific files are
        modified on disk.

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

    Specifying ``enabled_modules`` allows you to define a module without
    necessarily using it, making configuration switching easy.

        Module defined in "*$ASTRALITY_CONFIG_HOME/modules.yml*":
            ``name: name_of_module``

        Module defined in "*<modules_directory>/dir_name/modules.yml*":
            ``name: dir_name::name_of_module``

        Module defined at "*github.com/<user>/<repo>/blob/master/modules.yml*":
            ``name: github::<user>/<repo>::name_of_module``


    **You can also use wildcards when specifying enabled modules:**

        * ``name: '*'`` enables all modules defined in:
          ``$ASTRALITY_CONFIG_HOME/modules.yml``.
        * ``name: 'text_editors::*`` enables all modules defined in: 
          ``$ASTRALITY_CONFIG_HOME/<modules_directory>/text_editors/modules.yml``.
        * ``name: '*::*`` enables all modules defined in: 
          ``$ASTRALITY_CONFIG_HOME/<modules_directory>/*/modules.yml``.


.. _modules_external_modules:

Module subdirectories
=====================

You can define "external modules" in files named ``modules.yml`` placed within
separate subdirectories of your :ref:`modules directory <modules_directory>`.
You can also place ``context.yml`` within these directories, and the context
values will become available for compilation in all templates.

Astrality compiles enabled ``modules.yml`` files with context from all enabled
``context.yml`` files before parsing it. This allows you to modify the
behaviour of modules based on context, useful if you want to offer
configuration options for modules.

#. Define your modules in ``$ASTRALITY_CONFIG_HOME/<modules_directory>/directory/modules.yml``.
#. :ref:`Enable <modules_enabled_modules>` modules from this config file by appending ``name: directory::module_name`` to ``enabled_modules``.
   Alternatively, you can enable *all* modules defined in a module directory by appending ``name: directory::*`` instead.

By default, all module subdirectories are enabled.

Context values defined in ``context.yml`` have preference above context values defined in module subdirectories, allowing you to define default context values, while still allowing others to override these values.

.. caution::
    All relative paths and shell commands in external modules are interpreted relative to the external module directory,
    not ``$ASTRALITY_CONFIG_HOME``.
    This way it is more portable between different configurations.


.. _modules_github:

GitHub modules
==============

You can share a module directory with others by publishing the module subdirectory to `GitHub <https://github.com>`_.
Just define ``modules.yml`` at the repository root, i.e. where ``.git`` exists, and include any dependent files within the repository.

Others can fetch your module by appending ``name: github::<your_github_username>/<repository>`` to ``enabled_modules``.

For example enabling the module named ``module_name`` defined in ``modules.yml`` in the repository at https://github.com/username/repository:

.. code-block:: yaml

    modules:
        enabled_modules:
            - name: github::username/repository::module_name

Astrality will automatically clone the module on first-time startup, placing it within
``$XDG_DATA_HOME/astrality/repositories/github/username/repository``.
If you want to automatically update the GitHub module, you can specify ``autoupdate: true``:

.. code-block:: yaml

    modules:
        enabled_modules:
            - name: github::username/repository::module_name
              autoupdate: true

If ``module_name`` is not specified, all modules will be enabled:

.. code-block:: yaml

    modules:
        enabled_modules:
            - name: github::username/repository
              autoupdate: true
