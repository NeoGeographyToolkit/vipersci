#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

requirements = [
    "setuptools"
]

setup(
    entry_points={
        'console_scripts': [
            'accrual=vipersci.carto.accrual:main',
            'dice_buffer=vipersci.carto.dice_buffer:main',
            'dissolve_dice=vipersci.carto.dissolve_dice:main',
            'nss_modeler=vipersci.carto.nss_modeler:Main'
            'nss_simulator=vipersci.carto.nss_simulator:Main'
            'tri2gpkg=vipersci.carto.tri2gpkg:main',
            "template_test=vipersci.pds.template_test:main",
            "vis_create_raw=vipersci.pds.vis_create_raw:main",
            "vis_create_raw_tif=vipersci.pds.vis_create_raw_tif:main",
        ],
    },
    install_requires=requirements,
    include_package_data=True,
    # package_data={
    #     "vipersci": ["data/*"],
    # },
    packages=find_packages(
        include=['vipersci', 'vipersci.*'],
        where="src",
    ),
    test_suite="tests",
    zip_safe=False,
    keywords="VIPER",
    package_dir={"": "src"},
    tests_require=["pytest"],
)
