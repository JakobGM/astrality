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
* Making it easier to switch between blocks of configurations, like quickly changing the color scheme of your terminal emulator, desktop manager and/or other desktop applications. This can be done by changing only one line of ``astrality.yaml``.


.. _template_files:

Template files
==============

Templates can be of any file type, named whatever you want, and placed at any desirable path. It is customary, however, to place templates within ``$ASTRALITY_CONFIG_HOME/templates/name_of_application``, where ``name_of_application`` is the application that will use the compiled template.


.. _context:

Context
=======

When you write templates, you use ``placeholders`` which Astrality replaces with values defined in so-called ``context`` sections defined in ``astrality.yaml``. 
Context sections **must** be named ``context/descriptive_name`` and placed at the root indentation level of ``astrality.yaml``.

An example:

.. code-block:: yaml

    # $ASTRALITY_CONFIG_HOME/astrality.yaml

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
