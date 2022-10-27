#!/usr/bin/env python
"""This module contains classes for VIPER Product IDs."""

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

import datetime
import re

instruments = dict()
vis_instruments = dict(
    ncl="NavCam Left",
    ncr="NavCam Right",
    hfp="HazCam Forward Port",
    hfs="HazCam Forward Starboard",
    hap="HazCam Aft Port",
    has="HazCam Aft Starboard",
    acl="AftCam Left",
    acr="AftCam Right",
)
vis_instrument_aliases = {
    "navcam left": "ncl",
    "navcam right": "ncr",
    "aftcam left": "acl",
    "aftcam right": "acr",
    "hazcam forward port": "hfp",
    "hazcam forward starboard": "hfs",
    "hazcam aft port": "hap",
    "hazcam aft starboard": "has",
    "hazcam front left": "hfp",
    "hazcam front right": "hfs",
    "hazcam back left": "hap",
    "hazcam back right": "has",
}
instruments.update(vis_instruments)
vis_compression = dict(
    a=None,  # Lossless compression
    b=5,  # 5:1 compression
    c=16,  # 16:1 compression
    d=64,  # 64:1 compression
    s="SLoG",  # SLoG compression
)

nirvss_instruments = dict(
    aim="Ames Imaging Module",
)
instruments.update(nirvss_instruments)

# Create some compiled regex Patterns to use in this module.
date_re = re.compile(r"(2\d)(1[0-2]|0[1-9])(3[01]|[12][0-9]|0[1-9])")  # YYMMDD
time_re = re.compile(r"(2[0-3]|[01]\d)([0-5]\d)([0-5]\d)(\d{3})?")  # hhmmssfff
inst_re = re.compile("|".join(instruments.keys()))

pid_re = re.compile(
    rf"(?P<date>{date_re.pattern})-"
    rf"(?P<time>{time_re.pattern})-"
    rf"(?P<instrument>{inst_re.pattern})"
)

vis_comp_re = re.compile("|".join(vis_compression.keys()))
vis_pid_re = re.compile(pid_re.pattern + rf"-(?P<compression>{vis_comp_re.pattern})")


def get_key(value, dictionary):
    for k, v in dictionary.items():
        if v == value:
            return k
    else:
        raise KeyError(f"No value, {value}, was found in the dictionary.")


class VIPERID:
    """A Class for VIPER Product IDs.

    :ivar date: a six digit string denoting YYMMDD (or strftime %y%m%d) where
        the two digit year can be prefixed with "20" to get the four-digit year.
    :ivar time: a six or nine digit string denoting hhmmss (or strftime
        %H%M%S%f) or hhmmssuuu, similar to the first, but where the trailing
        three digits are miliseconds.
    :ivar instrument: A three character sequence denoting the instrument.
    """

    def __init__(self, *args):

        if len(args) == 1:
            match = pid_re.search(str(args).lower())
            if match:
                parsed = match.groupdict()
                self.date = parsed["date"]
                self.time = parsed["time"]
                self.instrument = parsed["instrument"]
            else:
                raise ValueError(f"{args} did not match regex: {pid_re.pattern}")
        else:
            if len(args) == 2:
                if isinstance(args[0], datetime.datetime):
                    date = args[0].date()
                    time = args[0].time()
                else:
                    raise ValueError(
                        "For two arguments, the first must be a datetime" "object."
                    )
                instrument = args[1]

            elif len(args) == 3:
                if isinstance(args[0], (datetime.date, str)):
                    date = args[0]
                else:
                    raise ValueError(
                        "For three arguments, the first must be a date or "
                        "string object."
                    )

                if isinstance(args[1], (datetime.time, str)):
                    time = args[1]
                else:
                    raise ValueError(
                        "For three arguments, the second must be a time or "
                        "string object."
                    )

                instrument = args[2]

            else:
                raise IndexError("accepts 1 to 3 arguments")

            self.date = self.format_date(date)
            self.time = self.format_time(time)

            match = inst_re.search(instrument)
            if match:
                self.instrument = match[0]
            elif instrument in instruments.values():
                self.instrument = get_key(instrument, instruments)
            else:
                raise ValueError(f"{instrument} did not match regex: {inst_re.pattern}")
        return

    def __str__(self):
        return "-".join((self.date, self.time, self.instrument))

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.__str__()}')"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.date == other.date
                and self.time == other.time
                and self.instrument == other.instrument
            )
        return False

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return (self.date, self.time, self.instrument,) < (
                other.date,
                other.time,
                other.instrument,
            )
        else:
            return NotImplemented

    @staticmethod
    def format_date(date) -> str:
        if isinstance(date, datetime.date):
            if datetime.date(2000, 1, 1) <= date < datetime.date(2100, 1, 1):
                datestr = date.strftime("%y%m%d")
            else:
                raise ValueError("Date must be between the year 2000 and 2100.")
        else:
            match = date_re.search(date)
            if match:
                datestr = match[0]
            else:
                raise ValueError(f"{date} did not match regex: {date_re.pattern}")

        return datestr

    @staticmethod
    def format_time(time) -> str:
        if isinstance(time, datetime.time):
            if time.microsecond == 0:
                timestr = time.strftime("%H%M%S")
            elif time.microsecond >= 1000:
                timestr = time.strftime("%H%M%S%f")[:9]
            else:
                raise ValueError(
                    "The provided time has more precision "
                    "than a milisecond, which is not allowed for "
                    "VIPER IDs."
                )
        else:
            match = time_re.search(time)
            if match:
                timestr = match[0]
            else:
                raise ValueError(f"{time} did not match regex: {time_re.pattern}")

        return timestr

    def datetime(self):
        fmt = "%y%m%d-%H%M%S"
        time_string = f"{self.date}-{self.time}"
        if len(self.time) == 9:
            fmt += "%f"
            time_string += "000"
        return datetime.datetime.strptime(time_string, fmt)


class VISID(VIPERID):
    """A Class for VIPER VIS Product IDs.

    :ivar date: a six digit string denoting YYMMDD (or strftime %y%m%d) where
        the two digit year can be prefixed with "20" to get the four-digit year.
    :ivar time: a six or nine digit string denoting hhmmss (or strftime
        %H%M%S%f) or hhmmssuuu, similar to the first, but where the trailing
        three digits are miliseconds.
    :ivar instrument: A three character sequence denoting the instrument.
    """

    def __init__(self, *args):

        if len(args) == 1:
            if isinstance(args[0], dict):
                if "start_time" in args[0] or "lobt" in args[0]:
                    if args[0].keys() >= {"start_time", "lobt"}:
                        if (
                            datetime.datetime.fromtimestamp(
                                args[0]["lobt"], tz=datetime.timezone.utc
                            )
                            != args[0]["start_time"]
                        ):
                            raise ValueError(
                                f"The start_time {args[0]['start_time']} does not "
                                f"equal the lobt {args[0]['lobt']}"
                            )
                    if "lobt" in args[0]:
                        dt = datetime.datetime.fromtimestamp(
                            args[0]["lobt"], tz=datetime.timezone.utc
                        )
                    else:
                        dt = args[0]["start_time"]

                    date = dt.date()
                    time = dt.time()
                else:
                    raise ValueError(
                        "The dictionary had neither 'start_time' nor 'lobt' " "keys."
                    )
                instrument = args[0]["instrument_name"]
                compression = args[0]["onboard_compression_ratio"]
            else:
                match = vis_pid_re.search(str(args).lower())
                if match:
                    parsed = match.groupdict()
                    date = parsed["date"]
                    time = parsed["time"]
                    instrument = parsed["instrument"]
                    compression = parsed["compression"]
                else:
                    raise ValueError(
                        f"{args} did not match regex: {vis_pid_re.pattern}"
                    )
        elif len(args) == 4:
            (date, time, instrument, compression) = args
        else:
            raise IndexError("accepts 1 or 4 arguments")

        if instrument in vis_instruments:
            pass
        elif instrument.casefold() in vis_instrument_aliases:
            instrument = vis_instrument_aliases[instrument.casefold()]
        else:
            raise ValueError(f"{instrument} is not a VIS instrument.")

        if compression in vis_compression:
            pass
        elif compression in vis_compression.values():
            compression = get_key(compression, vis_compression)
        else:
            raise ValueError(f"{args[3]} is not one of {vis_compression.keys()}")

        super().__init__(date, time, instrument)
        self.compression = compression

    def __str__(self):
        return "-".join((super().__str__(), self.compression))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return super().__eq__(other) and self.compression == other.compression
        return False

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            if super().__eq__(other):
                return self.compression < other.compression
            else:
                return super().__lt__(other)
        else:
            return NotImplemented

    @staticmethod
    def instrument_name(name):
        """Returns fullname of VIS instrument based on *name*."""
        if name.casefold() in vis_instruments:
            return vis_instruments[name.casefold()]
        elif name.casefold() in vis_instrument_aliases:
            return vis_instruments[vis_instrument_aliases[name.casefold()]]
        else:
            raise ValueError(f"No instrument name based on {name} could be found.")
