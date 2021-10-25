#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

requirements = [
    "lxml",
    "setuptools"
]

setup(
    entry_points={
        'console_scripts': [

        ]
    },
    install_requires=requirements,
    include_package_data=True,
    # package_data={
    #     "hiproc": ["data/*"],
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
