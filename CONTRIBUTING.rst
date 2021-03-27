BeeRef — Notes For Developers
=============================

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

Run unittests with coverage report::

  coverage run --source=beeref -m pytest;
  coverage html

If your browser doesn't open automatically, view ``htmlcov/index.html``.

Beeref files are sqlite databases, so they can be inspected with any sqlite browser.
