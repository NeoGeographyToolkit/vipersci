.. highlight:: shell

============
Installation
============


Stable release
--------------

To install vipersci, run this command in your terminal:

.. code-block:: console

    $ pip install vipersci 

This is the preferred method to install vipersci, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for vipersci can be downloaded from the `Github repo`_.

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/NeoGeographyToolkit/vipersci


XML Validation
--------------
In order to use this module to validate XML labels, some additional components 
need to be installed.  If you do not plan to validate XML labels, you can ignore
this section.

In order to enable the validation of PDS4 XML labels, you will need to install the
`Saxon/C library <https://www.saxonica.com/saxon-c/index.xml>`_ separately, and then enable
Python to access it.  Let's assume you have installed it in `/some/path/to/saxonc/`

In the conda context, once you have created a `vipersci` conda environment, execute these
commands to set the SAXONC_HOME and PYTHONPATH variables to include the locations of the
`saxonc` components::

    conda activate vipersci
    conda env config vars set SAXONC_HOME=/some/path/to/saxonc PYTHONPATH=/some/path/to/saxonc/Saxon.C.API/python-saxon
    conda activate vipersci

If you are using some other environment to manage your Python modules, you'll need to 
make sure to set these two environment variables, as appropriate.
