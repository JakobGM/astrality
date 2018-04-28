.. _templating:

==========
Templating
==========

.. _template_files:

Template files
==============

Templates can be of any file type, named whatever you want, and placed at any
desirable path. If you want to write a template for a file named "example.conf"
it is recommended that you name it "template.example.conf".

.. _context:

Context
=======

When you write templates, you use ``{{ placeholders }}`` which Astrality
replaces with values defined in so-called ``context`` sections defined in
``$ASTRALITY_CONFIG_HOME/context.yml``.

Here is an example which defines context values in "context.yml":

.. code-block:: none

    # $ASTRALITY_CONFIG_HOME/context.yml

    machine:
        user: jakobgm
        os: linux
        hostname: hyperion

    fonts:
        1: FuraCode Nerd Font
        2: FuraMono Nerd Font


.. warning::
    Context keys (anything left of a colon) can only consist of ASCII letters,
    numbers and underscores.
    **No spaces are allowed**.


.. _template_placeholders:

Inserting context variables into your templates
-----------------------------------------------

You should now be able to insert context values into your templates. You can
refer to context variables in your templates by using the syntax
``{{ context_section.variable_name }}``.

Using the contexts defined above, you could write the following template:

.. code-block:: dosini

    font-type = '{{ fonts.1 }}'
    home-directory = /home/{{ machine.user }}
    machine-name = {{ machine.hostname }}

When Astrality :ref:`compiles your template <template_how_to_compile>` the
result would be:

.. code-block:: dosini

    font-type = 'FuraCode Nerd Font'
    home-directory = /home/jakobgm
    machine-name = hyperion

.. hint::
    You can create arbitrarily nested structures within context sections. For
    instance:

    .. code-block:: yaml

        cosmetics:
            fonts:
                1:
                    family: FuraCode
                    font_size: 13
                2:
                    family: FuraMono
                    font_size: 9

    And refer to those nested variables with "dotted" syntax
    ``{{ cosmetics.fonts.1.family }}``.


.. _env_context:

The ``env`` context
-------------------

Astrality automatically inserts a context section at runtime named ``env``. It
contains all your environment variables. You can therefore insert environment
variables into your templates by writing::

    {{ env.ENVIRONMENT_VARIABLE_NAME }}


.. _undefined_context_values:

Undefined context values
------------------------

When you refer to a context value which is not defined, it will be replaced
with an empty string, and logged as a warning in Astrality's standard output.

.. _context_fallback_values:

Default fallback context values
-------------------------------

Sometimes you want to refer to context variables in your templates, but you
want to insert a fallback value in case the context variable is not defined at
compile time. This is often the case when referring to environment variables.
Defining a fallback value is easy::

    {{ env.ENVIRONMENT_VARIABLE_NAME or 'defualt value' }}


.. _template_integer_placeholders:

Integer placeholder resolution
------------------------------

There exists another way to define fallback values, which sometimes is much
more useful.

Let's define context values with integer names:

.. code-block:: yaml

    # $ASTRALITY_CONFIG_HOME/context.yml

    fonts:
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

With other words, references to *non-existent* numeric context identifiers are
replaced with the greatest *available* numeric context identifier at the same
indentation level.

.. hint::
    This construct can be very useful when you are expecting to change the
    underlying context of templates. Defining font types and color schemes
    using numeric identifiers allows you to switch between themes which define
    a different number of fonts and colors to be used!


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


.. _shell_filter:

The ``shell`` filter
--------------------

Astrality provides an additional ``shell`` template filter in addition to the
standard Jinja2 filters. The syntax is::

    {{ 'shell command' | shell }}

.. note::
    Shell commands are run from the directory which contains the configuration
    for the template compilation, most often ``$ASTRALITY_CONFIG_HOME``. If you
    need to refer to paths outside this directory, you can use absolute paths,
    e.g. ``{{ 'cat ~/.bashrc' | shell }}``.

You can specify a timeout for the shell command given in seconds::

    {{ 'shell command' | shell(5) }}

The default timeout is 2 seconds.

To provide a fallback value for functions that time out or return non-zero exit
codes, do::

    {{ 'shell command' | shell(1.5, 'fallback value') }}

.. caution::
    The quotes around the shell command are important, since if you ommit the
    quotes, you end up refering to a context value instead. Though, this *can*
    be done intentionally when you have defined a shell command in a context
    variable.


.. _template_how_to_compile:

How to compile templates
========================

Now that you know how to write Astrality templates, you might wonder how to
actually *compile* these templates. You can instruct Astrality to compile
templates by defining a module in "$ASTRALITY_CONFIG_HOME/modules.yml".
More on this on the next page of this documentation, but here is a simple
example:

Let us assume that you have written the following template:

.. code-block:: dosini

    # Source: $ASTRALITY_CONFIG_HOME/templates/some_template

    current_user={{ host.user }}

Where you want to replace ``{{ host.user }}`` with your username. Let us define
the context value used for insertion in "$ASTRALITY_CONFIG_HOME/context.yml":

.. code-block:: yaml

    # Source: $ASTRALITY_CONFIG_HOME/context.yml

    host:
        user: {{ env.USER }}

In order to compile this template to ``$XDG_CONFIG_HOME/config.ini`` we write
the following module, which will compile the template on Astrality startup:

.. code-block:: yaml

    # Source: $ASTRALITY_CONFIG_HOME/astrality.yml

    my_module:
        on_startup:
            compile:
                - content: templates/template
                  target: $XDG_CONFIG_HOME/config.ini

Now we can compile the template by starting Astrality:

.. code-block:: console

    $ astrality

The result should be:

.. code-block:: dosini

    # Source: $XDG_CONFIG_HOME/config.ini

    current_user=yourusername

This is probably a bit overwhelming. I recommend to just continue to the next
page to get a more gentle introduction to these concepts.
