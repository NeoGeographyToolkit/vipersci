.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/https://github.com/NeoGeographyToolkit/vipersci/issues .

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

This software could always use more documentation, whether as part of the
official docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/NeoGeographyToolkit/vipersci/issues

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `vipersci` for local development.

1. Fork the `vipersci` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/vipersci.git

3. Install your local copy into a virtual environment of your choice
(there are many to choose from like conda, etc.). We will assume
conda here, but any should work::

    $ cd vipersci/
    $ conda env create -n vipersci -f environment_dev.yml
    $ conda activate vipersci
    $ mamba env update -f environment.yml
    $ pip install --no-deps -e .

   The last `pip install` installs vipersci in "editable" mode which facilitates using the programs and testing.

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the
   tests, including testing other Python versions with tox::

    $ flake8 src/vipersci tests
    $ python setup.py test or pytest
    $ tox

   To get flake8 and tox, just pip install them into your virtual environment.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in CHANGELOG.rst.
3. The pull request should work for Python 3.6, 3.7 and 3.8, and optionally for PyPy.
   And make sure that the tests pass for all supported Python versions.


What to expect
--------------

Our development of vipersci is neither continuous, nor as well-funded as we
might like, and it is entirely possible that when you submit a PR
(pull request), none of us will have the time to evaluate or integrate
your PR.  If we don't, we'll try and communicate that with you via the
PR.

For large contributions, it is likely that you, or your employer,
will be retaining your copyrights, but releasing the contributions
via an open-source license.  It must be compatible with the Apache-2
license that vipersci is distributed with, so that we can redistribute
that contribution with vipersci, give you credit, and make vipersci even
better!  Please contact us if you have a contribution of that nature,
so we can be sure to get all of the details right.

For smaller contributions, where you (or your employer) are not
concerned about retaining copyright (but we will give you credit!),
you will need to fill out a Contributor License Agreement (CLA)
if we plan to accept your PR.  The CLA assigns your copyright in
your contribution to NASA, so that our NASA copyright statement
remains true:

    Copyright (c) YEAR, United States Government as represented by the
    Administrator of the National Aeronautics and Space Administration.
    All rights reserved.

There is an `Individual CLA <https://github.com/NeoGeographyToolkit/vipersci/blob/master/docs/vipersci_Individual_CLA.pdf>`_ and a `Corporate CLA
<https://github.com/NeoGeographyToolkit/vipersci/blob/master/docs/ASP_Corporate_CLA.pdf>`_.

vipersci People
----------

- A vipersci **Contributor** is any individual creating or commenting
  on an issue or pull request.  Anyone who has authored a PR that was
  merged should be listed in the AUTHORS.rst file.

- A vipersci **Committer** is a subset of contributors, typically NASA
  employees or contractors, who have been given write access to the
  repository.


Deploying
---------

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in HISTORY.rst).
Then run::

$ bump2version patch # possible: major / minor / patch
$ git push
$ git push --tags
