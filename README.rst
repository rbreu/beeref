BeeRef — A Simple Reference Image Viewer
========================================

View your references while you art!

.. image:: https://github.com/rbreu/beeref/blob/main/images/screenshot.jpg

|github-ci-flake8| |github-ci-pytest| |codecov|

.. |github-ci-flake8| image:: https://github.com/rbreu/beeref/actions/workflows/flake8.yml/badge.svg
   :target: https://github.com/rbreu/beeref/actions/workflows/flake8.yml

.. |github-ci-pytest| image:: https://github.com/rbreu/beeref/actions/workflows/pytest.yml/badge.svg
   :target: https://github.com/rbreu/beeref/actions/workflows/pytest.yml

.. |codecov| image:: https://codecov.io/gh/rbreu/beeref/branch/main/graph/badge.svg?token=QA8HR1VVAL
   :target: https://codecov.io/gh/rbreu/beeref


Installation via Python & pip
-----------------------------

At the moment, you need to have a working Python 3 environment to install BeeRef. Run the following command to install the development version::

  pip install git+https://github.com/rbreu/beeref.git

Then run ``beeref`` or ``beeref filename.bee``.

If there are issues starting the applictaion, run it with the environment varibale ``QT_DEBUG_PLUGINS`` set to 1, for example from a Linux shell::

  QT_DEBUG_PLUGINS=1 beeref

This should tell you whether you need to install any additional libraries, most likely regarding opengl.


Regarding the bee file format
-----------------------------

Currently, all images are embedded into the bee file as png files. While png is a lossless format, it may also produce larger file sizes than compressed jpg files, so bee files may become bigger than the imported images. More embedding options are to come later.

The bee file format is a sqlite database inside which the images are stored in an sqlar table—meaning they can be extracted with the `sqlite command line program <https://www.sqlite.org/cli.html>`_::

  sqlite3 myfile.bee -Axv

Options for exporting from inside BeeRef are planned, but the above always works independently of BeeRef.


Notes for developers
--------------------

BeeRef is written in Python and PyQt6. For more info, see `CONTRIBUTING.rst <https://github.com/rbreu/beeref/blob/main/CONTRIBUTING.rst>`_.
