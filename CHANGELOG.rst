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

Added
^^^^^
- pds.datetime.fromisozformat() function.
- pds.pid.VISID.compression_class() function.
- pds.xml.py added, very minimal, functionality may be moved.
- vis.db.raw_products.RawProduct.from_xml() function.
- vis.db.raw_products.RawProduct.asdict() function.
- vis.pds.create_raw.check_bit_depth() function.

Changed
^^^^^^^
- Updated templates and modules for PDS information model 18.
- vis.db.raw_products.RawProduct has some improved error-checking in __init__() and
  validate_datetime_asutc().
- vis.db.raw_products.RawProduct product_id column is now unique in database.
- vis.db.raw_products.RawProduct md5_checksum changed to file_md4_checksum to
  clearly associate it with the other properties that begin with "file_".
- vis.pds.create_raw.tiff_info() no longer raises an error if a bit depth other than 16
  is provided.
- vis.pds.create_raw now creates .JSON output files by default instead of XML PDS4
  labels, but XML files can still be made.


Fixed
^^^^^
- pds.pid.VIPERID.datetime() now properly returns datetimes with a UTC timezone.
- vis.db.raw_products.RawProduct.label_dict() now correctly sets sample_bits and
  sample_bit_mask if the image is a SLoG image.

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
