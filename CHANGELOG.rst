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


0.11.0 (2024-06-24)
-------------------
The large number of minor changes in this release are the result of applying ufmt
to organize the imports that the top of each module, and the application of pylint
to tidy up a variety of code structures.

Added
^^^^^
- image_records.py - Added ccu_temperature and external_temperature columns to record the
  AD590 sensor data.

Fixed
^^^^^
- get_position.py - The get_position_and_pose functions now have an explicit timeout
  and throw exceptions if they have difficulties with their connection.

Changed
^^^^^^^
- requirements.txt - Added version number requirements that reflect the current testing
  environment.


0.10.0 (2024-05-28)
-------------------

Added
^^^^^
- image_records.py - Added various light_on_x columns to record the state of the
  lights in ImageRecord objects.

Changed
^^^^^^^
- create_raw.py - For the get_lights() function, session is now optional, and by default,
  the get_lights() function now relies on the values in the passed ImageRecord, but if
  given a session, the values in the light_records table will override what is in the
  ImageRecord.

0.9.2 (2024-04-15)
------------------

Fixed
^^^^^
- nss.py - The DataModeler class would incorrectly always return a weh_arr of all-NaN
  values.  This bug has been fixed, and additional safeguards and error reporting have
  been placed in the class, and tests written.

0.9.1 (2024-04-10)
------------------

Fixed
^^^^^
- anaglyph.py - when used with scikit-image versions greater than 0.21 changed the
  argument signature for phase_cross_correlation().  Fixed call, and should now
  work more globally.

0.9.0 (2024-04-08)
------------------

Added
^^^^^
- get_position.py - Now has support for http basic auth and can now handle returns
  from the REST service that could be either a sequence of elements or a single
  element.
- create_raw.py - Updated to accommodate the icer_minloss and icer_byte_quota properties
  of an ImageRecord.
- image_records.py - Added properties for the new image_nickname and waypoint_id
  properties, and updated the concept of capture_id to be a combination of the
  waypoint_id and the locally unique_capture_id, instead of a combination of the
  locally unique_capture_id and the image_request_id.

Fixed
^^^^^
- pano_check.py - removed a redundant argument.
- create_mmgis_pano.py - outpaths for saving the pano and thumbnail were being
  incorrectly generated.


0.8.0 (2024-02-21)
------------------

Changed
^^^^^^^
- The instrument_name() function in pid.py now can deal with alias names that are
  within a given string, not just an exact match.
- Now that pid.instrument_name() is more robust, ImageRecord.__init__() can handle a
  wider variety of Yamcs parameter names, should they change in the future.
- create_mmgis_pano.py - create() now takes a thumbsize int or tuple of ints that
  will control the creation and size of an output thumbnail JPG file, with naming
  convention set by Yamcs/OpenMCT.
- image_records.py - Added icer_byte_quota and icer_minloss parameters to ImageRecord,
  as well as a variety of improved handling related to this change and in pid.py.
- pid.py - Changed handling of the compression value to match the kinds of data we'll
  get from telemetry, so that the letters are assigned to cover an interval of possible
  compression ratios, and to reflect the new default byte quota value for driving
  images.

0.7.0 (2024-02-05)
------------------

Changed
^^^^^^^
- The light_records.py table now just records state changes (from 'on' to 'off' or
  vice-versa).
- create_image.py's create() method now has an imgtype argument that default to TIFF
  (but can be PNG).
- junc_image_req_ldst.py got some additional columns to manage the Science Team
  evaluation of images acquired from Image Requests.
- create_pano.py's make_pano_product() function renamed to make_pano_record().
- nss_simulator.py - nodata defaults for ideal detector count maps updated to more
  realistic values for dry terrain.
- image_statistics.py - Added additional stats in the compute() function, and added
  a pprint() function to format the info nicely.

Added
^^^^^
- pds.Purpose now provides names and explanations for the PDS-allowable values
  for "purpose."
- yamcs_reception_time column added to the image_records.py table.
- Association table junc_image_pano created which provides a many-to-many
  connection between ImageRecords and PanoRecords and added bidirectional
  relationship entries to each table.
- pano_records table now has pan and tilt angle min/max values to indicate
  angular range of panorama coverage.
- ImageRecord objects will now extract an ImageRequest ID from the provided capture_id
  if it is larger than the 16 bit range.
- image_requests.py - "Acquired," "Not Acquired," "Not Planned," and "Not Obtainable"
  statuses added to enum.  Also added asdict() method.
- ptu_records.py - Tables to record the pan and tilt of the rover's pan-tilt-unit (PTU).
- create_browse.py - For making browse products from existing image products.
- create_mmgis_pano.py - For making pano products for use in MMGIS.
- create_pano.py - updated to correctly add PanoRecord associations, can now query
  database for ImageRecords.
- create_pano_product.py - takes PanoRecords and makes a PDS Pano Product.
- get_position.py - Gets position and yaw from a REST-based service.
- create_vis_dbs.py - Now also supports spatialite databases, primarily for testing.
- create_raw.py - Added components for adding observational intent and data quality
  to the XML label.
- labelmaker - A program to help build PDS4 bundle and collection labels.
- bundle_install - A program to copy just the files related to a PDS4 bundle into a
  new location.  Fundamentally allowing a "make install" for PDS4 bundles.

Removed
^^^^^^^
- ldst_verification.py because the evaluation activity reflected here was on a per-image
  basis, but it has been revised to be on a per-Image-Request basis.


0.6.1 (2023-09-25)
------------------

Fixed
^^^^^
- validators.validate_dateimte_asutc now properly raises a ValueError if the provided
  tz-aware datetime has a non-UTC tz offset (before any tz-aware datetime would pass
  the validator).
- image_records.ImageRecord object now has pgaGain instead of ppaGain (which was surely
  a typo in the early upstream data.
- create_image.py now correctly imports all of the tables that have a relation to the
  image_records table so that SQLAlchemy can properly resolve them, and downstream
  users of the create_image.create() function don't need to worry about sorting that
  out.
- nss_simulator.py, when asked to produce an output set of maps, uses a zero nodata value
  rather than whatever nodata value was present in the input burial depth map.
- anaglyph.py needed some minor changes to align with upcoming changes in the
  scikit-image architecture.


0.6.0 (2023-09-25)
------------------

Changed the concept of primarily recording PDS-like "products" in the database and data
structures, and changed the concept to capture "records" of various kinds (ImageRecords,
LightRecords, and derived things like PanoRecords) in the database and as the primary
data unit for use and interaction.  And then PDS "products" will be made at a later
time via a process that sources one or many records.

Added
^^^^^
- image_records.py (this replaces the concept of raw_products.py)
- create_image.py (this replaces most of the functionality of the previous
  create_raw.py)
- image_tags.py which contains image tag information.
- image_requests.py defines the table for holding image requests.
- Junction tables to connect LDST information to ImageRequests and ImageTags
  to ImageRecords.
- ldst.py table which contains LDST information.
- light_records.py which handles information about luminaire state.
- anaglyph.py
- pano_check.py to sort through image records and figure out what would be a good
  panorama set.

Changed
^^^^^^^
- header.pga_gain_dict structure now has values that are always floats, which helps
  to determine whether this transformation needs to be applied.
- image_stats.py is the new raw_stats.py, supporting ImageRecord objects.
- pano_products.py is now pano_records.py, supporting ImageRecord objects.
- create_pano.py now supports ImageRecords and PanoRecords.
- create_raw.py rearchitected to gather information from "records" to build XML PDS
  labels.
- create_vis_dbs entry point changed to vis_create_dbs to conform with other vis-related
  entry points.
- pid.VISID now properly sorts the uncompressed "z" state lower (better) than the
  lossless compressed "a" state.
- pid.VISID now has a best_compression() function to sort out the best compression state
  from an iterable containing may compression states from a single observation.


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
- Updated templates and modules for PDS information model 21.
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
- raw-template.xml can only have one Image_Filter object.
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
