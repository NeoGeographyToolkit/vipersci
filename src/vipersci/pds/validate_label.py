"""Validates a VIS label."""

# Copyright 2021-2022, vipersci developers.
# The SchXslt Schematron processor used via the
# default --xsl argument is Copyright (c) 2018-2021 David Maus
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import argparse
import logging
import sys
from pathlib import Path

from lxml import etree
import pkg_resources

from vipersci import util

try:
    import saxonc
except ImportError as err:
    raise ImportError(
        "The saxonc Python library is not available.  You may need to set "
        "your PYTHONPATH, or read the vipersci Installation instructions for "
        "XML Validation."
    ) from err

logger = logging.getLogger(__name__)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        parents=[util.parent_parser()]
    )
    parser.add_argument(
        "--sch",
        type=Path,
        default=Path(pkg_resources.resource_filename(
            __name__,
            'data/pds/'
            )),
        help="Path to Schematron document or directory containing .sch files. "
             "Default: %(default)s"
    )
    parser.add_argument(
        "--xsd",
        type=Path,
        default=Path(pkg_resources.resource_filename(
            __name__,
            'data/pds/'
            )),
        help="Path(s) to XML Schema file or directory containing .xsd "
             "files to validate against. Default: %(default)s"
    )
    parser.add_argument(
        "--xsl",
        type=Path,
        default=Path(pkg_resources.resource_filename(
            __name__,
            "data/schxslt-1.7/2.0/pipeline-for-svrl.xsl"
        )),
        help="Path to .xsl file that will be used to compile the Schematron "
             "file(s).  Default: %(default)s"
    )
    parser.add_argument(
        "files",
        type=Path,
        nargs="*",
        help="XML files to validate."
    )
    return parser


def main():
    args = arg_parser().parse_args()
    util.set_logger(args.verbose)

    # Gather local schema
    nsmap = get_local_schema(args.xsd)

    # Gather Schematron paths
    if args.sch.is_dir():
        sch_list = list(args.sch.glob("*.sch"))
    elif args.sch.is_file():
        sch_list = [args.sch, ]
    else:
        raise ValueError(
            f"The path ({args.sch}) is neither a file nor a directory."
        )

    proc = saxonc.PySaxonProcessor(license=False)
    logger.info(proc.version)

    for x in args.files:
        doc = etree.parse(str(x))
        try:
            schema = get_schema(doc, nsmap)
            schema.assertValid(doc)
            print(f"Document {x} is XML Schema valid.")
        except etree.DocumentInvalid as err:
            print(f"Document {x} would not validate against XML Schema: "
                  f"{err}")

        try:
            sch_errors = schematron_errors(
                x,
                # pds_sch_dir / "PDS4_PDS_1F00.sch",
                sch_list,
                args.xsl,
                proc
            )
            if len(sch_errors) == 0:
                print(f"Document {x} is Schematron valid.")
            else:
                print(f"Document {x} has had Schematron errors:")
                for i, (k, v) in enumerate(sch_errors.items()):
                    print(f"- {i} - Schematron file: {v[0]}")
                    print(f"- {i} - Error: {v[1]}")
                    logger.debug(k)
        except NameError:
            print("The saxonc library could not be loaded, and so Schematron "
                  "validation could not be carried out.")

    proc.release()

    return 0


def get_local_schema(xsd_path: Path):
    schema_locs = dict()

    # If there's a need to understand XML Catalog files, we could
    # do that here, but I'm not convinced there is.
    # if catalog is not None:
    #     pass

    if xsd_path.is_dir():
        sch_list = xsd_path.glob("*.xsd")
    elif xsd_path.is_file():
        sch_list = [xsd_path, ]
    else:
        raise ValueError(
            f"The path ({xsd_path}) is neither a file nor a directory."
        )

    name_map = {
        # It is important that more specific items like
        # PDS4_IMG_SURFACE come before less specific, but
        # similarly spelled items like PDS4_IMG
        "PDS4_PDS": "http://pds.nasa.gov/pds4/pds/v1",
        "PDS4_DISP": "http://pds.nasa.gov/pds4/disp/v1",
        "PDS4_GEOM": "http://pds.nasa.gov/pds4/geom/v1",
        "PDS4_IMG_SURFACE": "http://pds.nasa.gov/pds4/img_surface/v1",
        "PDS4_IMG": "http://pds.nasa.gov/pds4/img/v1",
        "PDS4_MSN_SURFACE": "http://pds.nasa.gov/pds4/msn_surface/v1",
        "PDS4_MSN": "http://pds.nasa.gov/pds4/msn/v1",
        "PDS4_PROC": "http://pds.nasa.gov/pds4/proc/v1"
    }
    for f in sch_list:
        for k, v in name_map.items():
            if f.stem.startswith(k):
                schema_locs[v] = f
                break

    logger.debug(f"local schema: {schema_locs}")

    return schema_locs


def get_schema(doc=None, nsmap=None):
    # Elements of this function are from
    # https://gist.github.com/tomkralidis/7168870

    if nsmap is not None:
        schema_locs = nsmap
    else:
        schema_locs = dict()

    # Figure out what XML Schemas this document has, if any:
    if doc is not None:
        sl = doc.getroot().get(
            "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"
        )
        if sl is not None:
            for ns, location in zip(sl[::2], sl[1::2]):
                schema_locs[ns] = location
        else:
            logger.info(
                f"Document {doc.docinfo.URL} does not have any "
                f"schemaLocation fragments."
            )

    # Build the XML Schema
    schema_def = etree.Element(
        "schema",
        attrib={
            "elementFormDefault": "qualified",
            "version": "1.0.0",
        },
        nsmap={None: "http://www.w3.org/2001/XMLSchema"}
    )

    for ns, location in schema_locs.items():
        # logger.info(ns)
        # logger.info(location)

        etree.SubElement(
            schema_def,
            "import",
            attrib={"namespace": ns, "schemaLocation": location.as_uri()}
        )

    # return etree.XMLSchema(etree=schema_def)
    return etree.XMLSchema(etree.XML(etree.tostring(schema_def)))


def schematron_errors(
    path: Path,
    sch_list: list,
    xslt_stylesheet: Path,
    proc: saxonc.PySaxonProcessor,
) -> dict:
    """Returns a dict where the keys are the "locations" in the file at
    *path* where assertions failed, and the values are two-tuples, which
    contains the filename of the Schematron file that was being validated
    against in the first position, and the plain text description of the
    failure in the second position.

    If there are no failures, the returned dict will be empty.

    :param path: The .xml file that should be validated with Schematron.
    :param sch_list: List of paths to one or more .sch files.
    :param xslt_stylesheet: Path to the XSLT Stylesheet that will be
        used to transform the stylesheet.
    :param proc: PySaxonProcessor to use for validation.

    This function uses the Saxon/C-HE processor from Saxonica.com to
    do the work of processing the Schematron and XSLT Stylesheets.
    """
    errors = dict()

    for p in sch_list:
        xslt30_processor = proc.new_xslt30_processor()
        xslt30_processor.set_cwd(".")
        compiled_schematron = xslt30_processor.transform_to_value(
            source_file=str(p),
            stylesheet_file=str(xslt_stylesheet)
        )
        stylesheet_node = compiled_schematron.item_at(0).get_node_value()
        xslt30_processor.compile_stylesheet(stylesheet_node=stylesheet_node)
        # xslt30_processor.transform_to_file(
        #     source_file=str(p),
        #     output_file="test.xml"
        # )
        result = xslt30_processor.transform_to_string(
            source_file=str(path),
        )
        report = etree.fromstring(result.encode())
        failed = report.findall(
            "{http://purl.oclc.org/dsdl/svrl}failed-assert"
        )
        for fa in failed:
            loc = fa.get("location")
            # For reasons that I don't understand, it appears that
            # there are multiple identical failed-assert fragments
            # in the output, so this condenses them.
            if loc not in errors:
                errors[loc] = (p, fa[0].text.strip())

    return errors


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
