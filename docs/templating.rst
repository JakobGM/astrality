.. _templating:

==========
Templating
==========

Use cases
=========

The use of Astrality templates allows you to:

* Have one single source of truth for values that should remain equal on cross of configuration files.
* Make changes that are applied to several configuration files at once, making it easier to experiment with configurations that are interdependent.
* Insert :ref:`environment variables <parameter_expansion>` and :ref:`command substitutions <command_substitution>` in configuration files that otherwise can not support them.
* Insert replacements for placeholders which are :ref:`dynamically manipulated <context_import_action>` by Astrality :ref:`modules <modules>`.
* Making configurations more portable. Any references to display devices, network interfaces, usernames, etc., can be quickly changed when deploying on a new machine.
* Making it easier to switch between blocks of configurations, like quickly changing the color scheme of your terminal emulator, desktop manager and/or other desktop applications. This can be done by changing only one line of ``astrality.yml``.


.. _template_files:

Template files
==============

Templates can be of any file type, named whatever you want, and placed at any desirable path. It is customary, however, to place templates within ``$ASTRALITY_CONFIG_HOME/templates/name_of_application``, where ``name_of_application`` is the application that will use the compiled template.


.. _context:

Context
=======

When you write templates, you use ``placeholders`` which Astrality replaces with values defined in so-called ``context`` sections defined in ``astrality.yml``. 
Context sections **must** be named ``context/descriptive_name`` and placed at the root indentation level of ``astrality.yml``.

An example:

.. code-block:: yaml

    # $ASTRALITY_CONFIG_HOME/astrality.yml

    context/machine:
        user: $USER
        os: $( uname )
        hostname: $( hostname )

    context/fonts:
        1: FuraCode Nerd Font
        2: FuraMono Nerd Font


.. warning::
    Context section names, and any identifiers within a context block (i.e. anything left of a colon), must be valid Python 2.x `identifiers <http://jinja.pocoo.org/docs/2.10/api/#notes-on-identifiers>`_.
    In other words, they must match the regular expression ``[a-zA-Z_][a-zA-Z0-9_]*``, i.e. use ASCII letters, numbers, and underscores.
    **No spaces are allowed**.


.. _template_placeholders:

Inserting context variables into your templates
-----------------------------------------------

You should now be able to insert context values into your templates. You can refer to context variables in your templates by using the syntax ``{{ context_section.variable_name }}``. Using the contexts defined above, you could write the following template:

.. code-block:: dosini

    font-type = '{{ fonts.1 }}'
    home-directory = /home/{{ machine.user }}
    machine-name = {{ machine.hostname }}

When Astrality :ref:`compiles your template <template_how_to_compile>` the result would be:

.. code-block:: dosini

    font-type = 'FuraCode Nerd Font'
    home-directory = /home/your_username
    machine-name = your_hostname

.. hint::
    You can create arbitrarily nested structures within context sections. For instance:

    .. code-block:: yaml

        context/cosmetics:
            fonts:
                1:
                    family: FuraCode
                    font_size: 13
                2:
                    family: FuraMono
                    font_size: 9

    And refer to those nested variables with "dotted" syntax ``{{ cosmetics.fonts.1.family }}``.


.. _env_context:

The ``env`` context
-------------------

Astrality automatically inserts a context section at runtime named ``env``. It contains all your environment variables.
You can therefore insert environment variables into your templates by writing::

    {{ env.ENVIRONMENT_VARIABLE_NAME }}


.. _undefined_context_values:

Undefined context values
------------------------

When you refer to a context value which is not defined, it will be replaced with an empty string, and logged as a warning in Astrality's standard output.

.. _context_fallback_values:

Default fallback context values
-------------------------------

Sometimes you want to refer to context variables in your templates, but you want to insert a fallback value in case the context variable is not defined at compile time. This is often the case when referring to environment variables. Defining a fallback value is easy::

    {{ env.ENVIRONMENT_VARIABLE_NAME or 'defualt value' }}


.. _template_integer_placeholders:

Integer placeholder resolution
------------------------------

There exists another way to define fallback values, which sometimes is much more useful.
It can be used by naming your context sections, subsections, and/or values with numeric values.
Let's define context values with integer names.

.. code-block:: yaml

    section/fonts:
        1: FuraCode Nerd Font
        2: FuraMono Nerd Font

You can now write the following template::

    primary-font = '{{ fonts.1 }}'
    secondary-font = '{{ fonts.2 }}'
    tertiary-font = '{{ fonts.3 }}'

And it will be compiled to::

    primary-font = 'FuraCode Nerd Font'
    secondary-font = 'FuraMono Nerd Font'
    tertiary-font = 'FuraMono Nerd Font'

With other words, references to *non-existent* numeric context identifiers are replaced with the greatest *available* numeric context identifier at the same indentation level.

.. hint::
    This construct can be very useful when you are expecting to change the underlying context of templates. Defining font types and color schemes using numeric identifiers allows you to switch between themes which define a different number of fonts and colors to be used.


.. _jinja2:

Advanced templating
===================

Astrality templating uses ``Jinja2`` under the hood. If you want to apply more advanced templating techniques than the ones described here, you can use the extended templating features available in the Jinja2 templating engine. Visit Jinja2's `templating documentation <http://jinja.pocoo.org/docs/2.10/templates/>`_ for more information.

Useful constructs include:

    `Filters <http://jinja.pocoo.org/docs/2.10/templates/#list-of-builtin-filters>`_:
        For manipulating context variables before insertion.

    `Template inheritance <http://jinja.pocoo.org/docs/2.10/templates/#template-inheritance>`_:
        For reuse of templates with common sections.

    `Iterating over context values <http://jinja.pocoo.org/docs/2.10/templates/#for>`_:
        For using both the context *name* and *value* in configuration files.

    `Conditionals <http://jinja.pocoo.org/docs/2.10/templates/#if>`_:
        For only including template content if some conditions(s) are satisfied.

A somewhat normal use case for advanced templating is key, value iteration. If you define the following color scheme context:

.. code-block:: yaml

    context/color_scheme:
        bg: 282828
        fg: ebdbb2
        red: cc241d
        green: 98971a
        yellow: d79921

And write the following template::

    {% for key, value in color_scheme %}
        {{ key }} = '0x{{ value|upper }}'
    {% endfor %}

It would result in the following compiled template::

    bg = '0x282828'
    fg = '0xEBDBB2'
    red = '0xCC241D'
    green = '0x98971A'
    yellow = '0xD79921'


.. _shell_filter:

The ``shell`` filter
--------------------

Astrality provides an additional ``shell`` template filter in addition to the standard Jinja2 filters. The syntax is::

    {{ 'shell command' | shell }}

.. note::
    Shell commands are run from ``$ASTRALITY_CONFIG_HOME``. If you need to refer to paths outside this directory, you can use absolute paths, e.g. ``{{ 'cat ~/.bashrc' | shell }}``.

You can use the :ref:`command substitution <command_substitution>` syntax in a context section of ``astrality.yml`` and get much of the same functionality, but with the ``shell`` filter you can specify a timeout in seconds::

    {{ 'shell command' | shell(5) }}

The default timeout is 2 seconds.

To provide a fallback value for functions that time out or return non-zero exit codes, do::

    {{ 'shell command' | shell(1.5, 'fallback value') }}

.. caution::
    The quotes around the shell command are important, since if you ommit the quotes, you end up refering to a context value instead. Though, this *can* be done intentionally when you have defined a shell command in a context variable.


.. _template_how_to_compile:

How to compile templates
========================

Now that you know how to write Astrality templates, you might wonder how to actually *compile* these templates. In order to do this, you need to:

    #. Create an Astrality :ref:`module <modules>`.
    #. Specify when to compile the template, by using an :ref:`event block <events>` within the module.
    #. Inserting a :ref:`compile action <compile_action>` into such an event block, telling Astrality to compile your template.

Here is a very simple example that demonstrate how to compile a template to a target path.
Let us assume that you have written the following template:

.. code-block:: dosini

    # Source: $ASTRALITY_CONFIG_HOME/modules/test/template
    
    current_user={{ host.user }}

Where you want to replace ``{{ host.user }}`` with your username. Let us define the context value used for insertion:

.. code-block:: yaml

    # Source: $ASTRALITY_CONFIG_HOME/astrality.yml

    context/host:
        user=${USER}

In order to compile this template to ``/tmp/config.ini`` we write the following module, 
which will compile the template on Astrality startup:

.. code-block:: yaml

    # Source: $ASTRALITY_CONFIG_HOME/astrality.yml

    context/host:
        user=${USER}

    module/some_name:
        on_startup:
            compile:
                template: modules/test/template
                target: /tmp/config.ini

Now we can compile the template by starting Astrality:

.. code-block:: console

    $ astrality

The result should be:

.. code-block:: dosini

    # Source: /tmp/config.ini
    
    current_user=yourusername

This is probably a bit overwhelming. I recommend to just continue to the next page to get a more gentle introduction to these concepts.
