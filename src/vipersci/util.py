#!/usr/bin/env python
"""This module contains viss utility functions."""

# Copyright 2021-2022, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import argparse
import logging

import vipersci


def parent_parser() -> argparse.ArgumentParser:
    """Returns a parent parser with common arguments for viss programs."""
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Displays additional information."
    )
    parent.add_argument(
        '--version',
        action='version',
        version=f"vipersci Software version {vipersci.__version__}",
        help="Show library version number."
    )
    return parent


def set_logger(verblvl=None) -> None:
    """Sets the log level and configuration for applications."""
    logger = logging.getLogger(__name__.split(".")[0])
    lvl_dict = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    if verblvl in lvl_dict:
        lvl = lvl_dict[verblvl]
    else:
        lvl = lvl_dict[max(lvl_dict.keys())]

    logger.setLevel(lvl)

    ch = logging.StreamHandler()
    ch.setLevel(lvl)

    if lvl < 20:  # less than INFO
        formatter = logging.Formatter("%(name)s - %(levelname)s: %(message)s")
    else:
        formatter = logging.Formatter("%(levelname)s: %(message)s")

    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return
