#!/usr/bin/env python
# coding: utf-8

"""Defines the VIS raw_products table using the SQLAlchemy ORM."""

# Copyright 2022, United States Government as represented by the
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

from datetime import datetime, timedelta, timezone
from enum import Flag
from warnings import warn
import xml.etree.ElementTree as ET

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Identity,
    Integer,
    String,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column, synonym, validates

from vipersci.pds.pid import VISID, vis_instruments, vis_compression
from vipersci.pds.xml import ns
from vipersci.pds.datetime import fromisozformat, isozformat
from vipersci.vis.header import pga_gain as header_pga_gain
from vipersci.vis.db import Base
import vipersci.vis.db.validators as vld


luminaire_names = {
    "NavLight Left": "navlight_left_on",
    "NavLight Right": "navlight_right_on",
    "HazLight Aft Port": "hazlight_aft_port_on",
    "HazLight Aft Starboard": "hazlight_aft_starboard_on",
    "HazLight Center Port": "hazlight_center_port_on",
    "HazLight Center Starboard": "hazlight_center_starboard_on",
    "HazLight Fore Port": "hazlight_fore_port_on",
    "HazLight Fore Starboard": "hazlight_fore_starboard_on",
}


class ImageType(Flag):
    """This Flag class can be used to interpret the outputImageMask but not the
    immediateDownloadInfo Yamcs parameters, because only a single flag value can
    be set."""

    LOSSLESS_ICER_IMAGE = 1
    # RESERVED_2 = 2
    # RESERVED_4 = 4
    LOSSY_ICER_IMAGE = 8
    SLOG_ICER_IMAGE = 16

    @classmethod
    def _missing_(cls, value):
        return None


class ProcessingStage(Flag):
    # PROCESS_RESERVED = 1
    PROCESS_FLATFIELD = 2
    # PROCESS_RESERVED_2 = 4
    PROCESS_LINEARIZATION = 8
    PROCESS_SLOG = 16


class RawProduct(Base):
    """An object to represent rows in the raw_products table for VIS."""

    # This class is derived from SQLAlchemy's orm.DeclarativeBase
    # which means that it has a variety of class properties that are
    # then swept up into properties on the instantiated object via
    # super().__init__().

    # The table represents many of these objects, so the __tablename__ is
    # plural while the class name is singular.
    __tablename__ = "raw_products"

    # The mapped_column() names below should use "snake_case" for the names that are
    # committed to the database as column names.  Furthermore, those names
    # should be similar, if not identical, to the PDS4 Class and Attribute
    # names that they represent.  Other names (like Yamcs parameter camelCase
    # names) are implemented as synonyms. Aside from the leading "id" column,
    # the remainder are in alphabetical order, since there are so many.

    id = mapped_column(Integer, Identity(start=1), primary_key=True)
    adc_gain = mapped_column(
        Integer, nullable=False, doc="ADC_GAIN from the MCSE Image Header."
    )
    adcGain = synonym("adc_gain")
    auto_exposure = mapped_column(
        Boolean,
        nullable=False,
        doc="AUTO_EXPOSURE from the MCSE Image Header.",
    )
    autoExposure = synonym("auto_exposure")
    bad_pixel_table_id = mapped_column(
        Integer,
        nullable=False,
        # There is a Defective Pixel Map (really a list of 128 coordinates) for
        # each MCAM.  The "state" of this is managed by the ground and not
        # reflected in any Image Header information attached to an individual
        # image.  It is not clear how to obtain this information from Yamcs,
        # or even what might be recorded, so this column's value is TBD.
    )
    capture_id = mapped_column(
        Integer,
        nullable=False,
        doc="The captureId from the command sequence."
        # TODO: learn more about captureIds to provide better doc here.
    )
    captureId = synonym("capture_id")
    _exposure_duration = mapped_column(
        "exposure_duration",
        Integer,
        nullable=False,
        doc="The exposure time in microseconds, the result of decoding the "
        "EXP_STEP and EXP paramaters from the MCSE Image Header.",
    )
    exposureTime = synonym("exposure_duration")  # Yamcs parameter name.
    file_creation_datetime = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="The time at which file_name was created.",
    )
    file_md5_checksum = mapped_column(
        String,
        nullable=False,
        doc="The md5 checksum of the file described by file_path.",
    )
    file_path = mapped_column(
        String,
        nullable=False,
        doc="The absolute path (POSIX style) that contains the Array_2D_Image "
        "that this metadata refers to.",
    )
    # Not sure where we're getting info for these light booleans yet.
    hazlight_aft_port_on = mapped_column(Boolean, nullable=False)
    hazlight_aft_starboard_on = mapped_column(Boolean, nullable=False)
    hazlight_center_port_on = mapped_column(Boolean, nullable=False)
    hazlight_center_starboard_on = mapped_column(Boolean, nullable=False)
    hazlight_fore_port_on = mapped_column(Boolean, nullable=False)
    hazlight_fore_starboard_on = mapped_column(Boolean, nullable=False)
    image_id = mapped_column(
        Integer,
        nullable=False,
        doc="The IMG_ID from the MCSE Image Header used for CCU storage and "
        "retrieval.",
    )
    imageHeight = synonym("lines")
    imageId = synonym("image_id")
    imageWidth = synonym("samples")
    instrument_name = mapped_column(
        String, nullable=False, doc="The full name of the instrument."
    )
    instrument_temperature = mapped_column(
        Float,
        nullable=False,
        doc="The TEMPERATURE from the MCSE Image Header.  TBD how to convert "
        "this 16-bit integer into degrees C.",
    )
    # There is a sensor in the camera body (PT1000) which is apparently not
    # connected (sigh).  And there is also a sensor external to each camera
    # body (AD590), need to track down its Yamcs feed.
    lines = mapped_column(
        Integer,
        nullable=False,
        doc="The imageHeight parameter from the Yamcs imageHeader.",
    )
    _lobt = mapped_column(
        "lobt",
        Integer,
        nullable=False,
        doc="The TIME_TAG from the MCSE Image Header.",
    )
    # mcam_id, The MCAM_ID from the MCSE Image Header is not returned to the ground.
    mission_phase = mapped_column(
        String,
        nullable=False,
        # Not sure what form this will take, nor where it can be looked up.
    )
    navlight_left_on = mapped_column(Boolean, nullable=False)
    navlight_right_on = mapped_column(Boolean, nullable=False)
    offset = mapped_column(
        Integer,
        nullable=False,
        doc="The OFFSET parameter from the MCSE Image Header describing the dark "
        "level offset.",
    )
    onboard_compression_ratio = mapped_column(
        Float,
        doc="The PDS img:Onboard_Compression parameter.  Will be NULL for "
        "lossless compression or uncompressed images."
        # This is a PDS img:Onboard_Compression parameter which is the ratio
        # of the size, in bytes, of the original uncompressed data object
        # to its compressed size.  This operation is done by RFSW, but not
        # sure where to get this parameter from ...?
    )
    output_image_mask = mapped_column(
        Integer,
        nullable=False,
        doc="The outputImageMask from the Yamcs imageHeader.  For each downlinked "
        "image this can be exactly one value of the ImageType class.  This value "
        "indicates whether the image is SLoG or not, and what level of compression "
        "has been set.",
    )
    # outputImageType is redundant with the outputImageMask, as it is just the
    # longform name of the value specified in the outputImageMask.
    outputImageMask = synonym("output_image_mask")
    _pid = mapped_column(
        "product_id", String, nullable=False, unique=True, doc="The PDS Product ID."
    )
    padding = mapped_column(
        Integer,
        nullable=False,
        doc="The padding parameter from the Yamcs imageHeader.",
        # Not sure what this value means or where it comes from.
    )
    pga_gain = mapped_column(
        Float,
        nullable=False,
        doc="The translated floating point multiplier derived from PGA_GAIN "
        "from the MCSE Image Header.",
    )
    ppaGain = synonym("pga_gain")  # Surely, this is a Yamcs typo, should be pgaGain
    processing_info = mapped_column(
        Integer,
        nullable=False,
        doc="The processingInfo parameter from the Yamcs imageHeader. This integer "
        "value must correspond to a valid value of ProcessingStage, and indicates "
        "what onboard processing occurred.",
    )
    processingInfo = synonym("processing_info")
    purpose = mapped_column(
        String,
        nullable=False,
        doc="This is the value for the PDS "
        "Observation_Area/Primary_Result_Summary/purpose parameter, it "
        "has a restricted set of allowable values.",
    )
    samples = mapped_column(
        Integer,
        nullable=False,
        doc="The imageWidth parameter from the Yamcs imageHeader.",
    )
    slog = mapped_column(
        Boolean,
        nullable=False,
        doc="Indicates whether onboard SLoG processing occurred.",
    )
    software_name = mapped_column(String, nullable=False)
    software_version = mapped_column(String, nullable=False)
    software_program_name = mapped_column(String, nullable=False)
    start_time = mapped_column(DateTime(timezone=True), nullable=False)
    stereo = mapped_column(
        Boolean,
        nullable=False,
        doc="The stereo parameter from the Yamcs imageHeader."
        # TODO: learn more about stereo to provide better doc here.
    )
    stop_time = mapped_column(DateTime(timezone=True), nullable=False)
    temperature = synonym("instrument_temperature")
    voltage_ramp = mapped_column(
        Integer,
        nullable=False,
        doc="The VOLTAGE_RAMP parameter from the MCSE Image Header.",
    )
    voltageRamp = synonym("voltage_ramp")
    yamcs_generation_time = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="The generation time of the source record from Yamcs.",
    )
    yamcs_name = mapped_column(
        String,
        nullable=False,
        doc="The full parameter name from Yamcs that this product data came from, "
        "formatted like a / separated string.",
    )

    def __init__(self, **kwargs):
        if "lobt" in kwargs:
            lobt_dt = datetime.fromtimestamp(kwargs["lobt"], tz=timezone.utc)

        if kwargs.keys() >= {"start_time", "lobt"}:
            if isinstance(kwargs["start_time"], str):
                dt = fromisozformat(kwargs["start_time"])
            else:
                dt = kwargs["start_time"]

            if lobt_dt != dt:
                raise ValueError(
                    f"The start_time {kwargs['start_time']} does not equal "
                    f"the lobt ({kwargs['lobt']}, {lobt_dt})"
                )

        # Exposure duration is a hybrid_property that also sets the stop_time,
        # if super().__init() processes exposure duration while self.start_time
        # is still None, then object initiation will fail.  Removing it from
        # the parameters we pass to super().__init() and then setting it
        # after avoids this error condition.
        exp_dur = None
        for k in ("exposureTime", "exposure_duration"):
            if k in kwargs:
                exp_dur = kwargs[k]
                del kwargs[k]

        # If present, product_id needs some special handling:
        if "product_id" in kwargs:
            pid = VISID(kwargs["product_id"])
            del kwargs["product_id"]
        else:
            pid = False

        rpargs = dict()
        otherargs = dict()
        for k, v in kwargs.items():
            if k in self.__table__.columns or k in self.__mapper__.synonyms:
                rpargs[k] = v
            else:
                otherargs[k] = v

        # Instantiate early, so that the parent orm_declarative Base can
        # resolve all of the synonyms.
        super().__init__(**rpargs)

        # Ensure stop_time consistency by setting this *after* start_time is set in
        # super().__init__()
        self.exposure_duration = exp_dur

        # Ensure instrument_name consistency and existence.
        if "instrument_name" in kwargs:
            self.instrument_name = VISID.instrument_name(self.instrument_name)
        elif "yamcs_name" in kwargs:
            maybe_name = self.yamcs_name.split("/")[-1].replace("_", " ")
            if maybe_name.endswith((" icer", " jpeg", " slog")):
                maybe_name = maybe_name[:-5]

            self.instrument_name = VISID.instrument_name(maybe_name)

        if "cameraId" in otherargs:
            if VISID.instrument_name(otherargs["cameraId"]) != self.instrument_name:
                warn(
                    f"cameraId ({otherargs['cameraId']}) does not match the "
                    f"instrument_name ({self.instrument_name})."
                )

        # Derive slog, if possible.
        if self.processing_info is not None:
            try:
                if "slog" in kwargs:
                    # check against processing_info
                    if kwargs[
                        "slog"
                    ] and ProcessingStage.PROCESS_SLOG not in ProcessingStage(
                        self.processing_info
                    ):
                        warn(
                            "slog is True, but ProcessingStage.PROCESS_SLOG not "
                            f"in {ProcessingStage(self.processing_info)}"
                        )

                    if not kwargs[
                        "slog"
                    ] and ProcessingStage.PROCESS_SLOG in ProcessingStage(
                        self.processing_info
                    ):
                        warn(
                            "slog is False, but ProcessingStage.PROCESS_SLOG "
                            f"in {ProcessingStage(self.processing_info)}"
                        )
                else:
                    if ProcessingStage.PROCESS_SLOG in ProcessingStage(
                        self.processing_info
                    ):
                        self.slog = True
                    else:
                        self.slog = False
            except ValueError as err:
                warn(str(err))
                if "slog" not in kwargs and "yamcs_name" in kwargs:
                    self.slog = self.yamcs_name.endswith("slog")
        else:
            if "slog" not in kwargs and "yamcs_name" in kwargs:
                self.slog = self.yamcs_name.endswith("slog")

        # Ensure product_id consistency
        if pid:
            if "lobt" in kwargs:
                if pid.datetime() != lobt_dt:
                    raise ValueError(
                        f"The product_id datetime ({pid.datetime()}) and the "
                        f"provided lobt ({kwargs['lobt']}, {lobt_dt}) disagree."
                    )

            if "start_time" in kwargs and pid.datetime() != self.start_time:
                raise ValueError(
                    f"The product_id datetime ({pid.datetime()}) and the "
                    f"provided start_time ({kwargs['start_time']}) disagree."
                )

            if (
                self.instrument_name is not None
                and vis_instruments[pid.instrument] != self.instrument_name
            ):
                raise ValueError(
                    f"The product_id instrument code ({pid.instrument}) and "
                    f"the provided instrument_name "
                    f"({self.instrument_name}) disagree."
                )

            if self.onboard_compression_ratio is None:
                if self.slog and pid.compression != "s":
                    raise ValueError(
                        f"The product_id compression code ({pid.compression}) is not "
                        f"s, but onboard_compression_ratio is None and slog is true. "
                    )
                elif not self.slog and pid.compression != "a":
                    raise ValueError(
                        f"The product_id compression code ({pid.compression}) is not "
                        f"a, but onboard_compression_ratio is None and slog is false. "
                    )
            elif vis_compression[pid.compression] != self.onboard_compression_ratio:
                raise ValueError(
                    f"The product_id compression code ({pid.compression}) and "
                    f"the provided onboard_compression_ratio "
                    f"({self.onboard_compression_ratio}) disagree."
                )
        elif (
            self.start_time is not None
            and self.instrument_name is not None
            and self.slog is not None
        ):
            c = "s" if self.slog else self.onboard_compression_ratio
            pid = VISID(
                self.start_time.date(), self.start_time.time(), self.instrument_name, c
            )
        else:
            got = dict()
            for k in (
                "product_id",
                "start_time",
                "instrument_name",
                "slog",
            ):
                v = getattr(self, k)
                if v is not None:
                    got[k] = v

            raise ValueError(
                "Either product_id must be given, or each of start_time, "
                f"instrument_name, and slog. Got: {got}"
            )

        self._pid = str(pid)

        # Is this really a good idea?  Not sure.  This instance variable plus
        # label_dict() and update() allow other key/value pairs to be carried around
        # in this object, which is handy.  If these are well enough known, perhaps
        # they should just be pre-defined properties and not left to chance?
        self.labelmeta = otherargs

        return

    @hybrid_property
    def exposure_duration(self):
        return self._exposure_duration

    @exposure_duration.inplace.setter
    def _exposure_duration_setter(self, value: int):
        """Takes an exposure time in microseconds."""
        self._exposure_duration = value
        self.stop_time = self.start_time + timedelta(microseconds=value)

    @hybrid_property
    def lobt(self):
        return self._lobt

    @lobt.inplace.setter
    def _lobt_setter(self, lobt):
        self._lobt = lobt
        self.start_time = datetime.fromtimestamp(lobt, tz=timezone.utc)

    @hybrid_property
    def product_id(self):
        # Really am going back and forth about whether this should be returned as
        # a full VISID object or just as the string as it is now.
        return self._pid

    @product_id.inplace.setter
    def _product_id_setter(self, pid):
        # In this class, the source of product_id information really is what
        # comes from Yamcs, and so this should not be monkeyed with.  Theoretically
        # changing this would imply changes to start time, lobt, stop time,
        # intrument name and onboard_compression_ratio directly, but those changes then
        # also divorce this object from the Yamcs parameters that it came from and
        # has all manner of other implications.  So at this time, this can only be
        # set when this object is instantiated.
        raise NotImplementedError(
            "product_id cannot be set directly after instantiation."
        )

    @validates("pga_gain")
    def validate_pga_gain(self, key, value):
        return header_pga_gain(value)

    @validates(
        "file_creation_datetime",
        "start_time",
        "stop_time",
        "yamcs_generation_time",
    )
    def validate_datetime_asutc(self, key, value):
        return vld.validate_datetime_asutc(key, value)

    @validates("output_image_mask")
    def validate_output_image_mask(self, key, value):
        try:
            ImageType(value)
        except ValueError:
            warn(f"{key} ({value}) is not one of {list(ImageType)}")

        return value

    @validates("processing_info")
    def validate_processing_info(self, key, value):
        try:
            ProcessingStage(value)
        except ValueError:
            warn(f"{key} ({value}) is not one of {list(ProcessingStage)}")

        return value

    @validates("purpose")
    def validate_purpose(self, key, value: str):
        return vld.validate_purpose(value)

    def asdict(self):
        d = {}

        for c in self.__table__.columns:
            if isinstance(getattr(self, c.name), datetime):
                d[c.name] = isozformat(getattr(self, c.name))
            else:
                d[c.name] = getattr(self, c.name)

        d.update(self.labelmeta)

        return d

    @classmethod
    def from_xml(cls, text: str):
        """
        Returns an instantiated RawProduct object from parsing the provided *text*
        as XML.
        """
        d = {}

        def _find_text(root, xpath, unit_check=None):
            element = root.find(xpath, ns)
            if element is not None:
                if unit_check is not None:
                    if element.get("unit") != unit_check:
                        raise ValueError(
                            f"The {xpath} element does not have units of "
                            f"{unit_check}, has {element.get('unit')}"
                        )
                el_text = element.text
                if el_text:
                    return el_text
                else:
                    raise ValueError(
                        f"The XML {xpath} element contains no information."
                    )
            else:
                raise ValueError(f"XML text does not have a {xpath} element.")

        root = ET.fromstring(text)
        lid = _find_text(
            root, "./pds:Identification_Area/pds:logical_identifier"
        ).split(":")

        if lid[3] != "viper_vis":
            raise ValueError(
                f"XML text has a logical_identifier which is not viper_vis: {lid[3]}"
            )

        if lid[4] != "raw":
            raise ValueError(
                f"XML text has a logical_identifier which is not raw: {lid[4]}"
            )
        d["product_id"] = lid[5]

        d["auto_exposure"] = (
            True if _find_text(root, ".//img:exposure_type") == "Auto" else False
        )
        d["bad_pixel_table_id"] = int(
            _find_text(root, ".//img:bad_pixel_replacement_table_id")
        )
        d["exposure_duration"] = int(
            _find_text(root, ".//img:exposure_duration", unit_check="microseconds")
        )

        d["file_creation_datetime"] = fromisozformat(
            _find_text(root, ".//pds:creation_date_time")
        )
        d["file_path"] = _find_text(root, ".//pds:file_name")

        for k, v in luminaire_names.items():
            light = root.find(f".//img:LED_Illumination_Source[img:name='{k}']", ns)
            d[v] = (
                True if _find_text(light, "img:illumination_state") == "On" else False
            )

        osc = root.find(".//pds:Observing_System_Component[pds:type='Instrument']", ns)
        d["instrument_name"] = _find_text(osc, "pds:name")

        d["instrument_temperature"] = float(
            _find_text(root, ".//img:temperature_value", unit_check="K")
        )

        aa = root.find(".//pds:Axis_Array[pds:axis_name='Line']", ns)
        d["lines"] = int(_find_text(aa, "./pds:elements"))
        d["file_md5_checksum"] = _find_text(root, ".//pds:md5_checksum")
        d["mission_phase"] = _find_text(root, ".//msn:mission_phase_name")
        d["offset"] = _find_text(root, ".//img:analog_offset")

        try:
            d["onboard_compression_ratio"] = float(
                _find_text(root, ".//img:onboard_compression_ratio")
            )
        except ValueError:
            pass

        d["purpose"] = _find_text(root, ".//pds:purpose")

        aa = root.find(".//pds:Axis_Array[pds:axis_name='Sample']", ns)
        d["samples"] = int(_find_text(aa, "./pds:elements"))

        sw = root.find(".//proc:Software", ns)
        d["software_name"] = _find_text(sw, "./proc:name")
        d["software_version"] = _find_text(sw, "./proc:software_version_id")
        d["software_program_name"] = _find_text(sw, "./proc:Software_Program/proc:name")

        # Start times must be on the whole second, which is why we don't use
        # fromisozformat() here.
        d["start_time"] = datetime.strptime(
            _find_text(root, ".//pds:start_date_time"), "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)

        d["stop_time"] = fromisozformat(_find_text(root, ".//pds:stop_date_time"))

        return cls(**d)

    def label_dict(self):
        """Returns a dictionary suitable for label generation."""
        _inst = self.instrument_name.lower().replace(" ", "_")
        _sclid = "urn:nasa:pds:context:instrument_host:spacecraft.viper"
        onoff = {True: "On", False: "Off", None: None}
        pid = VISID(self.product_id)
        d = dict(
            lid=f"urn:nasa:pds:viper_vis:raw:{self.product_id}",
            mission_lid="urn:nasa:pds:viper",
            sc_lid=_sclid,
            inst_lid=f"{_sclid}.{_inst}",
            gain_number=(self.adc_gain * self.pga_gain),
            exposure_type="Auto" if self.auto_exposure else "Manual",
            image_filters=list(),
            led_wavelength=453,  # nm
            luminaires={},
            compression_class=pid.compression_class(),
            onboard_compression_type="ICER",
            sample_bits=12,
            sample_bit_mask="2#0000111111111111",
        )
        for k, v in luminaire_names.items():
            d["luminaires"][k] = onoff[getattr(self, v)]

        proc_info = ProcessingStage(self.processing_info)
        if ProcessingStage.PROCESS_FLATFIELD in proc_info:
            d["image_filters"].append(("Onboard", "Flat field normalization."))

        if ProcessingStage.PROCESS_LINEARIZATION in proc_info:
            d["image_filters"].append(("Onboard", "Linearization."))

        if self.slog:
            d["image_filters"].append(
                ("Onboard", "Sign of the Laplacian of the Gaussian, SLoG")
            )
            d["sample_bits"] = 8
            d["sample_bit_mask"] = "2#11111111"

        d.update(self.asdict())

        return d

    def update(self, other):
        for k, v in other.items():
            if k in self.__table__.columns or k in self.__mapper__.synonyms:
                setattr(self, k, v)
            else:
                self.labelmeta[k] = v
