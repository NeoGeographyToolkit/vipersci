========
vipersci
========

.. image:: https://github.com/NeoGeographyToolkit/vipersci/actions/workflows/python-test.yml/badge.svg
        :target: https://github.com/NeoGeographyToolkit/vipersci/actions

.. image:: https://codecov.io/github/NeoGeographyToolkit/vipersci/branch/main/graph/badge.svg?token=5U68VOAHGG 
 :target: https://codecov.io/github/NeoGeographyToolkit/vipersci

.. image:: https://img.shields.io/pypi/v/vipersci.svg
        :target: https://pypi.python.org/pypi/vipersci

This vipersci package is software to support the activities of the
Volatiles Investigating Polar Exploration Rover (VIPER) Science Team.

This software will implement scientific models to convert instrument
raw data to useful derived data (but not including any proprietary
instrument details). This includes functionality for running the
models "in reverse" in order to simulate instrument data for tests
and mission simulations. This software will enable and support the
creation of various geospatial data sets (maps) to help visualize
and understand data from the spacecraft. It will also support the
creation of PDS4 archive labels and structures for eventual data
delivery to the Planetary Data System (PDS).

At the moment, this repo is under significant development and change as we
attempt to craft various pieces of code.  It is definitely a work-in-progress.

The VIPER Science Team is developing this software "in the open"
in order to adhere to the new `NASA Science Information Policy for
the Science Mission Directorate (SPD-41)
<https://science.nasa.gov/science-red/s3fs-public/atoms/files/Scientific%20Information%20policy%20SPD-41.pdf>`_
as much as is possible.


* Free software: Apache 2 License

..    * Documentation: https://vipersci.readthedocs.io.
..    * `PlanetaryPy`_ Affiliate Package.


Installation
------------

The vipersci package is available on PyPI and pip-installable.

Installation via Conda will be forthcoming.

For the moment, follow the "Get Started!" directions in the CONTRIBUTING.rst document.


Contributing
------------

Feedback, issues, and contributions are always gratefully welcomed. See the
contributing guide for details on how to help and setup a development
environment.

Credits
-------

vipersci was developed in the open at NASA's Ames Research Center.

See the `AUTHORS
<https://github.com/NeoGeographyToolkit/vipersci/blob/master/AUTHORS.rst>`_
file for a complete list of developers.


License
-------

See LICENSE file for the full text of the license that applies to vipersci.

Copyright (c) 2022-2023, United States Government as represented by
the Administrator of the National Aeronautics and Space
Administration. All rights reserved.

The "vipersci" software is licensed under the Apache License, Version 2.0
(the "License"); you may not use this file except in compliance with the
License.  You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied. See the License for the specific language governing
permissions and limitations under the License.


.. _PlanetaryPy: https://github.com/planetarypy
