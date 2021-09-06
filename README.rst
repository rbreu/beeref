BeeRef — A Simple Reference Image Viewer
========================================

.. raw:: html

   <img align="left" width="100" height="100" src="https://raw.githubusercontent.com/rbreu/beeref/main/beeref/assets/logo.png">

`BeeRef <https://beeref.org>`_ lets you quickly arrange your reference images and view them while you create. Its minimal interface is designed not to get in the way of your creative process.

|python-version| |github-ci-flake8| |github-ci-pytest| |codecov|

.. image:: https://github.com/rbreu/beeref/blob/main/images/screenshot.png

.. |python-version| image:: https://github.com/rbreu/beeref/blob/main/images/python_version_badge.svg
   :target: https://www.python.org/

.. |github-ci-flake8| image:: https://github.com/rbreu/beeref/actions/workflows/flake8.yml/badge.svg
   :target: https://github.com/rbreu/beeref/actions/workflows/flake8.yml

.. |github-ci-pytest| image:: https://github.com/rbreu/beeref/actions/workflows/pytest.yml/badge.svg
   :target: https://github.com/rbreu/beeref/actions/workflows/pytest.yml

.. |codecov| image:: https://codecov.io/gh/rbreu/beeref/branch/main/graph/badge.svg?token=QA8HR1VVAL
   :target: https://codecov.io/gh/rbreu/beeref


Installation
------------

Stable Release
~~~~~~~~~~~~~~

Get the file for your operating system (Windows, Linux, macOS) from the `latest release <https://github.com/rbreu/beeref/releases>`_.

**Linux users** need to give the file executable rights before running it. Optional: If you want to have BeeRef appear in the app menu, save the desktop file from the `release section <https://github.com/rbreu/beeref/releases>`_ in ``~/.local/share/applications``, save the `logo <https://raw.githubusercontent.com/rbreu/beeref/main/beeref/assets/logo.png>`_, and adjust the path names in the desktop file to match the location of your BeeRef installation.

**MacOS X users**, look at `detailed instructions <https://beeref.org/macosx-run.html>`_ if you have problems running BeeRef.

Follow further releases via the `atom feed <https://github.com/rbreu/beeref/releases.atom>`_.


Development Version
~~~~~~~~~~~~~~~~~~~

To get the current delevopment version, you need to have a working Python 3 environment. Run the following command to install the development version::

  pip install git+https://github.com/rbreu/beeref.git

Then run ``beeref`` or ``beeref filename.bee``.

If there are issues starting the application, run it with the environment variable ``QT_DEBUG_PLUGINS`` set to 1, for example from a Linux shell::

  QT_DEBUG_PLUGINS=1 beeref

This should tell you whether you need to install any additional libraries.


Features
--------

* Move, scale, rotate and flip images
* Mass-scale images to the same width, height or size
* Mass-arrange images vertically, horizontally or for optimal usage of space
* Add text notes
* Enable alaways-on-top-mode and disable the title bar to let the BeeRef window unobtrusively float above your art program:

.. image:: https://github.com/rbreu/beeref/blob/main/images/screenshot.png


Regarding the bee file format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, all images are embedded into the bee file as png files. While png is a lossless format, it may also produce larger file sizes than compressed jpg files, so bee files may become bigger than the imported images on their own. More embedding options are to come later.

The bee file format is a sqlite database inside which the images are stored in an sqlar table—meaning they can be extracted with the `sqlite command line program <https://www.sqlite.org/cli.html>`_::

  sqlite3 myfile.bee -Axv

Options for exporting from inside BeeRef are planned, but the above always works independently of BeeRef.


Notes for developers
--------------------

BeeRef is written in Python and PyQt6. For more info, see `CONTRIBUTING.rst <https://github.com/rbreu/beeref/blob/main/CONTRIBUTING.rst>`_.
