=========
Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

When updating this file, please add an entry for your change under
Unreleased_ and one of the following headings:

- Added - for new features.
- Changed - for changes in existing functionality.
- Deprecated - for soon-to-be removed features.
- Removed - for now removed features.
- Fixed - for any bug fixes.
- Security - in case of vulnerabilities.

If the heading does not yet exist under Unreleased_, then add it
as a 3rd level heading, underlined with pluses (see examples below).

When preparing for a public release add a new 2nd level heading,
underlined with dashes under Unreleased_ with the version number
and the release date, in year-month-day format (see examples below).


Unreleased
----------


0.5.0 (2023-07-26)
------------------

Added
^^^^^
- PanoID class added to pds.pid
- pano_products and create_pano added, still very preliminary, mostly just mock-ups.
- colorforge program for managing colormaps.
- mypy is now in the development dependencies to support type checking.
- lint/mypy target added to Makefile.
- tri2gpkg now has a --remove_facets option to remove facets with a particular value.


Changed
^^^^^^^
- Explicit in documentation about developing in Python 3.8 (although earlier versions
  should still be supported).
- Many changes to improve type checking.
- Added numeric instrument aliases and checking for them.
- Added information for procesingInfo and outputMask from Yamcs.
- Upgrade to SQLAlchemy >=2.
- Moved definition of Base class up to vis.db.
- heatmaps.py will now accept value data lists or arrays with np.nan or None values
  which will be appropriate ignored in the density heatmap calculation.


Fixed
^^^^^
- tri2gpkg - if the provided polygons have zero area, issue an error rather than
  making a confusing GeoPackage file.



0.4.0 (2023-03-01)
------------------

Added
^^^^^
- carto.bounds module added to unify functionality for both heatmaps and dotmaps.
- carto.dotmap module for creating simple heatmap-like visualizations from 2d scalar data.
- Makefile now has a "lint/twine" option to hopefully help me remember to test that.
- VIS image_statistics.py and raw_stats.py modules.
- A variety of unit tests.
- mypy configuration arguments.

Changed
^^^^^^^
- Flattened test directory structure.
- tri2gpkg -v is no longer an alias for --value-names, as it now determines verbosity
  since logging has been added.
- GitHub workflows have been re-arranged.  Black and flake8 are now run under the "Lint"
  action, and the flake8 tests are removed from the Python testing matrix.

Removed
^^^^^^^
- The pinned versions requirements_dev.txt

Fixed
^^^^^
- CHANGELOG.rst had an unescaped underbar which caused trouble with twine upload.
- setup.cfg arrangement in install_requires passed local testing, but not GitHub testing,
  have now fixed.
- heatmap's generate_density_heatmap() function now properly returns values of zero
  in the returned out_count numpy array when there are no counts in those grid cells
  instead of the provided nodata value.
- tri2gpkg now works correctly if --keep_z is specified
- tri2gpkg now uses the correct srs if a pre-defined site is selected.


0.3.0 (2022-11-15)
------------------

Added
^^^^^
- pds.datetime.fromisozformat() function.
- pds.pid.VISID.compression_class() function.
- pds.xml.py added, very minimal, functionality may be moved.
- vis.db.raw_products.RawProduct.from_xml() function.
- vis.db.raw_products.RawProduct.asdict() function.
- vis.pds.create_raw.check_bit_depth() function.
- vis.db.create_vis_dbs convenience program to add empty tables to database.

Changed
^^^^^^^
- Updated templates and modules for PDS information model 18.
- vis.db.raw_products.RawProduct has some improved error-checking in __init__() and
  validate_datetime_asutc().
- vis.db.raw_products.RawProduct product_id column is now unique in database.
- vis.db.raw_products.RawProduct md5_checksum changed to file_md4_checksum to
  clearly associate it with the other properties that begin with "file\_".
- vis.pds.create_raw.tiff_info() no longer raises an error if a bit depth other than 16
  is provided.
- vis.pds.create_raw now creates .JSON output files by default instead of XML PDS4
  labels, but XML files can still be made.
- carto.heatmap.write_geotiff_rasterio now supports compressed output and defaults to "deflate"


Fixed
^^^^^
- carto.tri2gpkg.replace_with() now correctly returns a float value in all circumstances.
- pds.pid.VIPERID.datetime() now properly returns datetimes with a UTC timezone.
- vis.db.raw_products.RawProduct.label_dict() now correctly sets sample_bits and
  sample_bit_mask if the image is a SLoG image.
- Added __init__.py files to all modules (some modules did not get incorporated into the
  PyPI package because they did not have __init__.py files.
- The setup.cfg now properly includes requirements that vipersci needs.

Removed
^^^^^^^
- Many modules still had if __name__ == "__main__" constructs from early development
  which are now not needed with the entry points in setup.cfg.


0.2.0 (2022-11-07)
------------------

Added
^^^^^
- Data Simulators for NSS, NIRVSS, and MSolo
- Lots of material to enaable PDS archiving of VIS data.
- Added GitHub workflow to perform Black format checking

Changed
^^^^^^^
- Many updates to heatmap.py
- Applied Black formatting to all code in the repo.
- Modified Python testing workflow to actually work.


0.1.0 (2022-10-05)
------------------
Initial release.
