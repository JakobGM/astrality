.. _example_configuration:

Example configuration
=====================

Here is an example configuration of ``$ASTRALITY_CONFIG_HOME``, which you can
copy as a starting point by running ``astrality --create-example-config``.

First the global configuration options:

.. literalinclude:: ../astrality/config/astrality.yml
    :caption: $ASTRALITY_CONFIG_HOME/astrality.yml

Then some example modules:

.. literalinclude:: ../astrality/config/modules.yml
    :caption: $ASTRALITY_CONFIG_HOME/modules.yml

Finally some useful context values to be used in templates:

.. literalinclude:: ../astrality/config/context.yml
    :caption: $ASTRALITY_CONFIG_HOME/context.yml
