BeeRef — Notes For Developers
=============================

BeeRef is written in Python and PyQt6.

Clone the repository and install beeref and its dependencies::

  git clone https://github.com/rbreu/beeref.git
  cd beeref
  pip install -e .

Install additional development requirements::

  pip install -r requirements/dev.txt

Run unittests with::

  pytest .

Run codechecks with::

  flake8 .

Run unittests with coverage report::

  coverage run --source=beeref -m pytest
  coverage html

If your browser doesn't open automatically, view ``htmlcov/index.html``.

Beeref files are sqlite databases, so they can be inspected with any sqlite browser.

For debugging options, run::

  beeref --help

The Python version badge in the README is generated with pybadges::

  python -m pybadges --left-text=Python --right-text="3.6 | 3.7 | 3.8 | 3.9" > images/python_version_badge.svg
