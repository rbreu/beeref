BeeRef — A Simple Reference Image Viewer
========================================

View your references while you art!


|github-ci-flake8|

.. |github-ci-flake8| image:: https://github.com/rbreu/beeref/actions/workflows/flake8.yml/badge.svg
   :target: https://github.com/rbreu/beeref/actions/workflows/flake8.yml


Installation via Python & pip
-----------------------------

At the moment, you need to have a working Python 3 environment to install BeeRef. Run the following command to install the development version::

  pip install git+https://github.com/rbreu/beeref.git

Then run ``beeref`` or ``beeref filename.bee``.


Notes for developers
--------------------

BeeRef is written in Python and PyQt6.

Clone the repository and install beeref and its dependencies::

  git clone https://github.com/rbreu/beeref.git
  pip install -e beeref

Install additional development requirements::

  cd beeref
  pip install -r requirements/dev.txt

Run unittests with::

  pytest .

Run codechecks with::

  flake8 .
