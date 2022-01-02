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
            'tri2gpkg=vipersci.carto.tri2gpkg:main'
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
