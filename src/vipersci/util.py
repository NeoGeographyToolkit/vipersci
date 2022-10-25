#!/usr/bin/env python
"""This module contains viss utility functions."""

# Copyright 2021-2022, United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
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
        help="Displays additional information.",
    )
    parent.add_argument(
        "--version",
        action="version",
        version=f"vipersci Software version {vipersci.__version__}",
        help="Show library version number.",
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
