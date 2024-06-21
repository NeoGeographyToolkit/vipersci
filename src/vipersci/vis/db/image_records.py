# coding: utf-8

"""Defines the VIS image_records table using the SQLAlchemy ORM."""

# Copyright 2022-2024, United States Government as represented by the
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

import enum
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from warnings import warn

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Identity,
    Integer,
    String,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column, relationship, synonym, validates

import vipersci.vis.db.validators as vld
from vipersci.pds import Purpose
from vipersci.pds.datetime import fromisozformat, isozformat
from vipersci.pds.pid import vis_instruments, VISID
from vipersci.pds.xml import find_text, ns
from vipersci.vis.db import Base
from vipersci.vis.header import pga_gain as header_pga_gain


class ImageType(enum.Flag):
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


class ProcessingStage(enum.Flag):
    # PROCESS_RESERVED = 1
    FLATFIELD = 2
    # PROCESS_RESERVED_2 = 4
    LINEARIZATION = 8
    SLOG = 16


class ImageRecord(Base):
    """An object to represent rows in the image_records table for VIS."""

    # This class is derived from SQLAlchemy's orm.DeclarativeBase
    # which means that it has a variety of class properties that are
    # then swept up into properties on the instantiated object via
    # super().__init__().

    # The table represents many of these objects, so the __tablename__ is
    # plural while the class name is singular.
    __tablename__ = "image_records"

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
    # bad_pixel_table_id = mapped_column(
    #     Integer,
    #     nullable=False,
    #     # There is a Defective Pixel Map (really a list of 128 coordinates) for
    #     # each MCAM.  The "state" of this is managed by the ground and not
    #     # reflected in any Image Header information attached to an individual
    #     # image.  It is not clear how to obtain this information from Yamcs,
    #     # or even what might be recorded, so this column's value is TBD.
    # )
    capture_id = mapped_column(
        Integer,
        nullable=False,
        doc="The captureId from the command sequence.",
        # TODO: learn more about captureIds to provide better doc here.
    )
    captureId = synonym("capture_id")
    ccu_temperature = mapped_column(
        Float,
        nullable=True,
        doc="The temperature in degrees C from the AD590 sensor mounted "
        "on the interior wall of the warmbox near the CCU.",
    )
    _exposure_duration = mapped_column(
        "exposure_duration",
        Integer,
        nullable=False,
        doc="The exposure time in microseconds, the result of decoding the "
        "EXP_STEP and EXP paramaters from the MCSE Image Header.",
    )
    exposureTime = synonym("exposure_duration")  # Yamcs parameter name.
    external_temperature = mapped_column(
        Float,
        nullable=True,
        doc="The temperature in degrees C from the AD590 sensor mounted "
        "on the outside of the camera body.",
    )
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
    haz1LightState = synonym("light_on_hfp")
    haz2LightState = synonym("light_on_hap")
    haz3LightState = synonym("light_on_hfs")
    haz4LightState = synonym("light_on_has")
    haz5LightState = synonym("light_on_hcp")
    haz6LightState = synonym("light_on_hcs")
    HS_STBD_AD590_1 = synonym("ccu_temperature")
    icer_byte_quota = mapped_column(
        Integer,
        doc="The byteQuota value during onboard ICER compression.  In the returned "
        "Yamcs info, the value is in kilobytes, but this value is in bytes.",
    )
    icer_minloss = mapped_column(
        Integer, doc="The minLoss value during onboard ICER compression."
    )
    image_id = mapped_column(
        Integer,
        nullable=False,
        doc="The IMG_ID from the MCSE Image Header used for CCU storage and "
        "retrieval.",
    )
    image_nickname = mapped_column(
        String,
        nullable=True,
        doc="This was designed to be a unique nickname for the waypoint+camera. It has "
        "the form: <camera>-<waypoint>-<index>, where the index is represented as "
        "letters A, B, C, ..., Z, AA, AB, ...",
    )
    # This image_request_id column and image_request relationship allow a many
    # ImageRecords to one ImageRequest relationship, and the nullable allows it to be
    # optional.  So an ImageRecord may be connected to an ImageRequest, but it may not.
    image_request_id = mapped_column(ForeignKey("image_requests.id"), nullable=True)
    image_request = relationship("ImageRequest", back_populates="image_records")

    # The image_tags and image_tag_associations allow a many ImageTag to many
    # ImageRecord relationship.
    image_tags = relationship(
        "ImageTag",
        secondary="junc_image_record_tags",
        back_populates="image_records",
        viewonly=True,
    )
    image_tag_associations = relationship(
        "JuncImageRecordTag", back_populates="image_record"
    )
    imageHeight = synonym("lines")
    imageId = synonym("image_id")
    imageNickname = synonym("image_nickname")
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
    light_on_hfp = mapped_column(
        Boolean,
        nullable=True,
        doc="haz1LightState as reported by image metadata.",
    )
    light_on_hap = mapped_column(
        Boolean,
        nullable=True,
        doc="haz2LightState as reported by image metadata.",
    )
    light_on_hfs = mapped_column(
        Boolean,
        nullable=True,
        doc="haz3LightState as reported by image metadata.",
    )
    light_on_has = mapped_column(
        Boolean,
        nullable=True,
        doc="haz4LightState as reported by image metadata.",
    )
    light_on_hcp = mapped_column(
        Boolean,
        nullable=True,
        doc="haz5LightState as reported by image metadata.",
    )
    light_on_hcs = mapped_column(
        Boolean,
        nullable=True,
        doc="haz6LightState as reported by image metadata.",
    )
    light_on_nl = mapped_column(
        Boolean,
        nullable=True,
        doc="navLeftLightState as reported by image metadata.",
    )
    light_on_nr = mapped_column(
        Boolean,
        nullable=True,
        doc="navRightLightState as reported by image metadata.",
    )
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
    navLeftLightState = synonym("light_on_nl")
    navRightLightState = synonym("light_on_nr")
    # mcam_id, The MCAM_ID from the MCSE Image Header is not returned to the ground.
    offset = mapped_column(
        Integer,
        nullable=False,
        doc="The OFFSET parameter from the MCSE Image Header describing the dark "
        "level offset.",
    )
    # onboard_compression_ratio = mapped_column(
    #     Float,
    #     doc="The PDS img:Onboard_Compression parameter.  Will be NULL for "
    #     "uncompressed images, 1 for LOSSLESS compressed, 16 for 16x compressed, etc."
    #     # This is a PDS img:Onboard_Compression parameter which is the ratio
    #     # of the size, in bytes, of the original uncompressed data object
    #     # to its compressed size.  This operation is done by RFSW, and fixed
    #     # by that process.  The output_image_mask determines what happened,
    #     # and then we must look up to find this value.
    # )
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
    # The pano_records and pano_record_associations allow a many PanoRecords to many
    # ImageRecords relationship.
    pano_records = relationship(
        "PanoRecord",
        secondary="junc_image_pano",
        back_populates="image_records",
        viewonly=True,
    )
    pano_record_associations = relationship(
        "JuncImagePano", back_populates="image_record"
    )
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
    pgaGain = synonym("pga_gain")
    processing_info = mapped_column(
        Integer,
        nullable=False,
        doc="The processingInfo parameter from the Yamcs imageHeader. This integer "
        "value must correspond to a valid value of ProcessingStage, and indicates "
        "what onboard processing occurred.",
    )
    processingInfo = synonym("processing_info")
    requestId = synonym("image_request_id")
    samples = mapped_column(
        Integer,
        nullable=False,
        doc="The imageWidth parameter from the Yamcs imageHeader.",
    )
    # slog = mapped_column(
    #     Boolean,
    #     nullable=False,
    #     doc="Indicates whether onboard SLoG processing occurred.",
    # )
    software_name = mapped_column(String, nullable=False)
    software_version = mapped_column(String, nullable=False)
    software_program_name = mapped_column(String, nullable=False)
    start_time = mapped_column(DateTime(timezone=True), nullable=False)
    stereo = mapped_column(
        Boolean,
        nullable=False,
        doc="The stereo parameter from the Yamcs imageHeader.",
        # TODO: learn more about stereo to provide better doc here.
    )
    stop_time = mapped_column(DateTime(timezone=True), nullable=False)
    temperature = synonym("instrument_temperature")
    unique_capture_id = mapped_column(
        Integer,
        nullable=True,
        doc="The unique portion from the lower 16 bits of the captureId.  Ironically, "
        "this isn't guaranteed to be a mission-long globally unique value, only "
        "locally unique in time.  It gets set and linearly increases, but can "
        "be reset to zero.",
    )
    verification_notes = mapped_column(
        String,
        nullable=True,
        doc="Any notes about the verification of this image by the VIS Operator.",
    )
    verification_purpose = mapped_column(
        Enum(Purpose), nullable=True, doc="Purpose of Observation, as defined by PDS."
    )
    verified = mapped_column(
        Boolean,
        nullable=True,
        doc="True if a VIS Operator has indicated that this image is a good image, if "
        "false, the VIS Operator has determined that there is an error of some kind "
        "with this image.",
    )
    verifier = mapped_column(
        String,
        nullable=True,
        doc="The name of the individual that reviewed this image.",
    )
    voltage_ramp = mapped_column(
        Integer,
        nullable=False,
        doc="The VOLTAGE_RAMP parameter from the MCSE Image Header.",
    )
    voltageRamp = synonym("voltage_ramp")
    waypoint_id = mapped_column(
        Integer,
        nullable=True,
        doc="The waypoint id extracted from the upper 16 bits of the captureId.",
    )
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
    yamcs_reception_time = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="The reception time of the source record from Yamcs.",
    )

    def __init__(self, **kwargs):
        if "lobt" in kwargs:
            lobt_dt = datetime.fromtimestamp(kwargs["lobt"], tz=timezone.utc)
        else:
            lobt_dt = None

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

        # Adjust the byteQuota value
        if "byteQuota" in kwargs and "icer_byte_quota" not in kwargs:
            kwargs["icer_byte_quota"] = int(kwargs["byteQuota"]) * 1000
            del kwargs["byteQuota"]

        if "minLoss" in kwargs and "icer_minloss" not in kwargs:
            kwargs["icer_minloss"] = int(kwargs["minLoss"])
            del kwargs["minLoss"]

        rpargs = {}
        otherargs = {}
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
            self.instrument_name = VISID.instrument_name(
                self.yamcs_name.split("/")[-1].replace("_", " ")
            )

        if "cameraId" in otherargs:
            if VISID.instrument_name(otherargs["cameraId"]) != self.instrument_name:
                warn(
                    f"cameraId ({otherargs['cameraId']}) does not match the "
                    f"instrument_name ({self.instrument_name})."
                )

        # # Derive slog, if possible.
        # if self.processing_info is not None:
        #     try:
        #         if "slog" in kwargs:
        #             # check against processing_info
        #             if kwargs[
        #                 "slog"
        #             ] and ProcessingStage.PROCESS_SLOG not in ProcessingStage(
        #                 self.processing_info
        #             ):
        #                 warn(
        #                     "slog is True, but ProcessingStage.PROCESS_SLOG not "
        #                     f"in {ProcessingStage(self.processing_info)}"
        #                 )

        #             if not kwargs[
        #                 "slog"
        #             ] and ProcessingStage.PROCESS_SLOG in ProcessingStage(
        #                 self.processing_info
        #             ):
        #                 warn(
        #                     "slog is False, but ProcessingStage.PROCESS_SLOG "
        #                     f"in {ProcessingStage(self.processing_info)}"
        #                 )
        #         else:
        #             if ProcessingStage.PROCESS_SLOG in ProcessingStage(
        #                 self.processing_info
        #             ):
        #                 self.slog = True
        #             else:
        #                 self.slog = False
        #     except ValueError as err:
        #         warn(str(err))
        #         if "slog" not in kwargs and "yamcs_name" in kwargs:
        #             self.slog = self.yamcs_name.endswith("slog")
        # else:
        #     if "slog" not in kwargs and "yamcs_name" in kwargs:
        #         self.slog = self.yamcs_name.endswith("slog")

        # Ensure product_id consistency
        if pid:
            # Check datetimes
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

            # Check instrument
            if (
                self.instrument_name is not None
                and vis_instruments[pid.instrument] != self.instrument_name
            ):
                raise ValueError(
                    f"The product_id instrument code ({pid.instrument}) and "
                    f"the provided instrument_name "
                    f"({self.instrument_name}) disagree."
                )

            # Check compression letter
            if self.output_image_mask is None:
                if self.yamcs_name is not None:
                    if "slog" in self.yamcs_name and pid.compression != "s":
                        raise ValueError(
                            f"The product_id compression code ({pid.compression}) is "
                            "not s, but yamcs_name indicates it should be "
                            f"({self.yamcs_name}). "
                        )
            else:
                t = ImageType(self.output_image_mask)
                if ImageType.SLOG_ICER_IMAGE == t and pid.compression == "s":
                    pass
                elif (
                    VISID.compression_letter(compression_ratio(self.icer_byte_quota))
                    != pid.compression
                ):
                    raise ValueError(
                        f"The product_id compression code ({pid.compression}) and "
                        "the compression ratio "
                        f"({compression_ratio(self.icer_byte_quota)}) based on "
                        f"the icer_byte_quota ({self.icer_byte_quota}) disagree."
                    )
        elif self.start_time is not None and self.instrument_name is not None:
            c = None
            if self.output_image_mask is not None:
                try:
                    if ImageType(self.output_image_mask) == ImageType.SLOG_ICER_IMAGE:
                        c = "s"
                except ValueError:
                    # output_image_mask has bad value
                    pass

            if c is None and self.yamcs_name is not None and "slog" in self.yamcs_name:
                c = "s"

            if c is None and self.icer_byte_quota is not None:
                c = compression_ratio(self.icer_byte_quota)

            if c is None:
                raise ValueError(
                    "Could not determine the compression information "
                    f"from output_image_mask ({self.output_image_mask}), "
                    f"processing_info ({self.processing_info}), or "
                    f"icer_byte_quota ({self.icer_byte_quota})."
                )

            pid = VISID(
                self.start_time.date(),
                self.start_time.time(),
                self.instrument_name,
                c,
            )
        else:
            got = {}
            for k in (
                "product_id",
                "start_time",
                "instrument_name",
                "output_image_mask",
                "processing_info",
                "icer_byte_quota",
            ):
                v = getattr(self, k)
                if v is not None:
                    got[k] = v

            raise ValueError(
                "Either product_id must be given, or each of start_time, "
                f"instrument_name, and output_image_mask plus some other things."
                f"Got: {got}"
            )

        self._pid = str(pid)

        if self.capture_id is not None and self.capture_id > int(
            "1111111111111111", base=2
        ):  # 65535
            self.waypoint_id = int(bin(self.capture_id)[:-16], base=2)
            self.unique_capture_id = int(bin(self.capture_id)[-16:], base=2)

        # Extract relevant AD590 sensor, if available
        ad590_names = {
            "acl": "AFTCAM_STEREO_L_AD590",
            "acr": "AFTCAM_STEREO_R_AD590",
            "hap": "HAZCAM2_AFT_PORT_AD590",
            "has": "HAZCAM4_AFT_STBD_AD590",
            "hfp": "HAZCAM1_FWD_PORT_AD590",
            "hfs": "HAZCAM3_FWD_STBD_AD590",
            "ncl": "NAVCAM_STEREO_L_AD590",
            "ncr": "NAVCAM_STEREO_R_AD590",
        }
        if ad590_names[pid.instrument] in otherargs:
            self.external_temperature = otherargs[ad590_names[pid.instrument]]
            del otherargs[ad590_names[pid.instrument]]

        # Remove other AD590 temperatures
        for t in ad590_names.values():
            otherargs.pop(t, None)

        # Remove pan and tilt from non-NavCams:
        if not pid.instrument.startswith("nc"):
            otherargs.pop("pan", None)
            otherargs.pop("tilt", None)

        # Is this really a good idea?  Not sure.  This instance variable plus
        # label_dict() and update() allow other key/value pairs to be carried around
        # in this object, which is handy.  If these are well enough known, perhaps
        # they should just be pre-defined properties and not left to chance?
        self.labelmeta = otherargs

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return VISID(self.product_id) < VISID(other.product_id)

        return NotImplemented

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
        "yamcs_reception_time",
    )
    def validate_datetime_asutc(self, key, value):
        return vld.validate_datetime_asutc(key, value)

    @validates(
        "light_on_hap",
        "light_on_has",
        "light_on_hcp",
        "light_on_hcs",
        "light_on_hfp",
        "light_on_hfs",
        "light_on_nl",
        "light_on_nr",
    )
    def validate_lights(self, _, value):
        if isinstance(value, str):
            if value.casefold() == "on":
                return True

            if value.casefold() == "off":
                return False

        return bool(value)

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

    def asdict(self):
        d = {}

        for c in self.__table__.columns:
            if isinstance(getattr(self, c.name), datetime):
                d[c.name] = isozformat(getattr(self, c.name))
            else:
                d[c.name] = getattr(self, c.name)

        if hasattr(self, "labelmeta"):
            d.update(self.labelmeta)

        return d

    @classmethod
    def from_xml(cls, text: str):
        """
        Returns an instantiated RawProduct object from parsing the provided *text*
        as XML.
        """
        d = {}

        root = ET.fromstring(text)
        lid = find_text(root, "./pds:Identification_Area/pds:logical_identifier").split(
            ":"
        )

        if lid[3] != "viper_vis":
            raise ValueError(
                f"XML text has a logical_identifier which is not viper_vis: {lid[3]}"
            )

        if lid[4] != "raw":
            raise ValueError(
                f"XML text has a logical_identifier which is not raw: {lid[4]}"
            )
        d["product_id"] = lid[5]

        d["auto_exposure"] = find_text(root, ".//img:exposure_type") == "Auto"
        d["bad_pixel_table_id"] = int(
            find_text(root, ".//img:bad_pixel_replacement_table_id")
        )
        d["exposure_duration"] = int(
            find_text(root, ".//img:exposure_duration", unit_check="microseconds")
        )

        d["file_creation_datetime"] = fromisozformat(
            find_text(root, ".//pds:creation_date_time")
        )
        d["file_path"] = find_text(root, ".//pds:file_name")

        # for k, v in luminaire_names.items():
        #     light = root.find(f".//img:LED_Illumination_Source[img:name='{k}']", ns)
        #     d[v] = (
        #         True if _find_text(light, "img:illumination_state") == "On" else False
        #     )

        osc = root.find(".//pds:Observing_System_Component[pds:type='Instrument']", ns)
        d["instrument_name"] = find_text(osc, "pds:name")

        d["instrument_temperature"] = float(
            find_text(root, ".//img:temperature_value", unit_check="K")
        )

        aa = root.find(".//pds:Axis_Array[pds:axis_name='Line']", ns)
        d["lines"] = int(find_text(aa, "./pds:elements"))
        d["file_md5_checksum"] = find_text(root, ".//pds:md5_checksum")
        d["mission_phase"] = find_text(root, ".//msn:mission_phase_name")
        d["offset"] = find_text(root, ".//img:analog_offset")

        try:
            d["onboard_compression_ratio"] = float(
                find_text(root, ".//img:onboard_compression_ratio")
            )
        except ValueError:
            pass

        d["purpose"] = find_text(root, ".//pds:purpose")

        aa = root.find(".//pds:Axis_Array[pds:axis_name='Sample']", ns)
        d["samples"] = int(find_text(aa, "./pds:elements"))

        sw = root.find(".//proc:Software", ns)
        d["software_name"] = find_text(sw, "./proc:name")
        d["software_version"] = find_text(sw, "./proc:software_version_id")
        d["software_program_name"] = find_text(sw, "./proc:Software_Program/proc:name")

        # Start times must be on the whole second, which is why we don't use
        # fromisozformat() here.
        d["start_time"] = datetime.strptime(
            find_text(root, ".//pds:start_date_time"), "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)

        d["stop_time"] = fromisozformat(find_text(root, ".//pds:stop_date_time"))

        return cls(**d)

    def update(self, other):
        for k, v in other.items():
            if k in self.__table__.columns or k in self.__mapper__.synonyms:
                setattr(self, k, v)
            else:
                self.labelmeta[k] = v


def compression_ratio(byte_quota):
    """Returns the result of dividing the number of bytes in a grayscale image
    (2048 * 2048 * 2 == 8,388,608) by the byte_quota of the returned image.
    """
    return (2048 * 2048 * 2) / byte_quota
