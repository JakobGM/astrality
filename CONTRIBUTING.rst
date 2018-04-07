=================
How to contribute
=================

First, thanks for considering contributing to Astrality, that means a lot!
Here we describe how you can help out, either by improving the documentation, submitting issues, or creating pull requests.

If you end up contributing, please consider adding yourself to the file ``CONTRIBUTORS.rst``.

.. _contributing_issues:

Bug reports and feature requests
================================

You can browse any existing bug reports and feature requests on Astrality's `issues page <https://github.com/JakobGM/astrality/issues>`_ on GitHub.
New issues issues can be submitted `here <https://github.com/JakobGM/astrality/issues/new>`_.


.. _contributing_documentation:

Improving the documentation
===========================

If find something you would like to improve in `the documentation <https://astrality.readthedocs.io/en/latest/index.html>`_, follow these steps:

* Navigate to the page that you would like to edit on https://astrality.readthedocs.io.
* Press the "Edit on GitHub" link in the upper right corner.
* Press the "pencil" edit icon to the right of the "History" button.
* Make the changes you intended.
* Write a title and description for your change on the bottom of the page.
* Select the radio button marked as: "Create a new branch for this commit and start a pull request".
* Press "Propose file change".

The documentation is written in the "RestructuredText" markup language. If this is unfamiliar to you, take a look at `this cheatsheet <https://github.com/ralsina/rst-cheatsheet/blob/master/rst-cheatsheet.rst>`_ for more information.


.. _contributing_code:

Contributing code
=================

Getting up and running
----------------------

Cloning the repository
~~~~~~~~~~~~~~~~~~~~~~

First we need to clone the repository. Open your terminal and navigate to the directory you wish to place project directory and run:

.. code-block:: console

    git clone https://github.com/jakobgm/astrality
    cd astrality


Installing python3.6
~~~~~~~~~~~~~~~~~~~~

Astrality runs on ``python3.6``, so you need to ensure that you have it installed. If you have no specific preferred way of installing software on your computer, you can download and install it from `here <https://www.python.org/downloads/>`_. Alternatively, if you use `brew <https://brew.sh/>`_ on MacOS, you can install it by running:

.. code-block:: console

    brew install python3

Or on ArchLinux:

.. code-block:: console

    sudo pacman -S python


Installing dependencies into a virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You should create a separate python3.6 "virtual environment" exclusively for Astrality.
If this is new to you, take a look at the `official tutorial <https://docs.python.org/3/tutorial/venv.html>`_ for ``venv``.

A quick summation:

.. code-block:: console

    python3.6 -m venv astrality-env
    source astrality-env/bin/activate

Your terminal prompt should now show the name of the activated virtual environment, for example ``(astrality-env) $ your_commands_here``.
You can double check your environment by running ``echo $VIRTUAL_ENV``.
Later you can deactivate it by running ``deactivate`` or restarting your terminal.
The activated virtual environment is necessary in order to run the developer version of Astrality, including the test suite.

Now you can install all the developer dependencies of Astrality by running:

.. code-block:: console

    pip3 install -r requirements.txt

You should now make sure that the environment variable ``PYTHONPATH`` is set to the root directory of the repository. Check it by running:

.. code-block:: console

    $ echo $PYTHONPATH
    /home/jakobgm/dev/astrality

With ``/home/jakobgm/dev/astrality`` being whatever makes sense on your system. If the value is incorrect you should run the following from the repository root:

.. code-block:: console

    export PYTHONPATH=$(pwd)


Running the developer version of Astrality
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You should now be able to run the developer version of Astrality by running the following command:

.. code-block:: bash

    ./bin/astrality


.. _contributing_writing_code:

Writing code
------------

The python code in Astrality follows some conventions which we will describe here.


Tests
~~~~~

Astrality strives for 100% test coverage, and all new lines of code should preferably be covered by tests. That being said, if testing is unfamiliar to you, submitting code without test coverage is better than no code at all.

Tests are written with the `pytest <https://docs.pytest.org/en/latest/>`_ test framework, and you can read a "getting started" tutorial `here <https://docs.pytest.org/en/latest/getting-started.html#getstarted>`_.

You can run the test suite from the root of the repository by running:

.. code-block:: console

    pytest

.. warning::
    For now, it is important that you run pytest from the root of the repository, else you will get a whole lot of ``ModuleNotFoundError`` exceptions.

Additionally, there are some tests which are hidden behind the ``--runslow`` flag, as some tests are slow due to writing files to disk and running certain shell commands. These slow tests can be run by writing:

.. code-block:: console

    pytest --runslow

When you submit a pull request, `travis-ci <http://travis-ci.org/>`_ will automatically check if all the tests pass with your submitted code.
`Coveralls <http://coveralls.io/>`_ will also check if the test coverage decreases.

If this feels intimidating, do not worry. We are happy to help guide you along if you encounter any issues with testing, so please submit pull requests even if the test suite fails for some reason.


Type annotations
~~~~~~~~~~~~~~~~

Astrality's code base heavily utilizes the new static type annotations available in python3.6.

The correctness of the type annotations are ensured by using `mypy <http://mypy-lang.org/>`_.
You can check for type errors by running the following command from the repository root:

.. code-block:: console

    mypy .

``mypy`` is a part of the test suite, enabled by the ``pytest-mypy`` `plugin <https://pypi.python.org/pypi/pytest-mypy>`_.
Therefore, if the test suite passes, ``mypy`` must also be satisfied with your code!

All non-testing code should be completely type annotated, as strictly as possible.
If this is new to you, or if you want to learn more, I recommend reading `mypy documentation <http://mypy.readthedocs.io/en/latest/introduction.html>`_.

The offer to help with testing also holds for type annotations of course!


Continuous testing
~~~~~~~~~~~~~~~~~~

Although this is mainly a matter of taste, running tests continuously while writing code is a great feedback mechanism.

`pytest-watch <https://github.com/joeyespo/pytest-watch>`_ should be already be installed on your system as part of Astrality's developer dependencies. You can use it to rerun the test suite every time you save any ``*.py`` file within the repository.

You can run it in a separate terminal by running:

.. code-block:: console

    ptw

It is often useful to run ``pytest-watch`` in verbose mode, stop on first test failure, and only run one specific test file at a time. You can do all this by running:

.. code-block:: console

    ptw -- -vv -x astrality/tests/test_compiler.py


Code style
~~~~~~~~~~

All code should try to adhere to the `PEP 8 style guide <https://www.python.org/dev/peps/pep-0008/>`_.
An integrated ``PEP 8`` linter in your editor is recommended!

In addition to this, some additional styling conventions are applied to the project:

* String literals should use single quotes. With other words: ``'this is a string'`` instead of ``"this is a string"``.
* Always use keyword arguments when invoking functions.
* Function arguments split over several lines should use trailing commas. With other words, we prefer to write code like this:

      .. code-block:: python

          compile_template(
              template=template,
              target=target,
          )

      Instead of this:

      .. code-block:: python

          compile_template(
              template=template,
              target=target
          )

These conventions are mainly enforced in order to stay consistent for choices where ``PEP 8`` do not tell us what to do.


Local documentation
-------------------

Astrality uses the `sphinx <http://www.sphinx-doc.org/en/master/>`_ ecosystem in conjunction with `readthedocs <http://readthedocs.org/>`_ for its documentation.

You can run a local instance of the documentation by running:

.. code-block:: console

    cd docs
    sphinx-autobuild . _build

The entire documentation should now be available on http://127.0.0.1:8000.
When you edit the documentation files placed with ``docs``, your web browser should automatically refresh the website with the new content!
