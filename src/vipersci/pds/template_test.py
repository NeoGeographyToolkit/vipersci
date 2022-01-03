"""Test creation of VIS labels."""

# Copyright 2021-2022, vipersci developers.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import argparse
import json
import logging
import sys
from pathlib import Path

# import genshi
# from genshi.template import TemplateLoader
from genshi.template import MarkupTemplate

from vipersci import util

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        parents=[util.parent_parser()]
    )
    parser.add_argument(
        "-j", "--json",
        type=Path,
        help="Path to .json file to load. "
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Genshi XML file template."
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Output XML label."
    )
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    with open(args.json, "r") as f:
        info = json.load(f)

    # loader = TemplateLoader()
    # tmpl = loader.load(str(args.input))
    tmpl = MarkupTemplate(args.input.read_text())
    stream = tmpl.generate(**info)
    args.output.write_text(stream.render())


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
