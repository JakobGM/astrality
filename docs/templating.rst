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

.. _context:

Context
=======
