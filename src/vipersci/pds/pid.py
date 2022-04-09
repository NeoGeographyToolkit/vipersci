#!/usr/bin/env python
"""A module contains classes for VIPER Product IDs."""

# Copyright 2022, vipersci developers.
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
    hbs="HazCam Back Starboard",
    hbp="HazCam Back Port",
    acl="AftCam Left",
    acr="AftCam Right",
)
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
    fr"(?P<date>{date_re.pattern})-"
    fr"(?P<time>{time_re.pattern})-"
    fr"(?P<instrument>{inst_re.pattern})"
)

vis_comp_re = re.compile("|".join(vis_compression.keys()))
vis_pid_re = re.compile(
    pid_re.pattern + fr"-(?P<compression>{vis_comp_re.pattern})"
)


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
            match = pid_re.search(str(args))
            if match:
                parsed = match.groupdict()
                self.date = parsed["date"]
                self.time = parsed["time"]
                self.instrument = parsed["instrument"]
            else:
                raise ValueError(
                    f"{args} did not match regex: {pid_re.pattern}"
                )
        else:
            if len(args) == 2:
                if isinstance(args[0], datetime.datetime):
                    date = args[0].date()
                    time = args[0].time()
                else:
                    raise ValueError(
                        "For two arguments, the first must be a datetime"
                        "object."
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
            else:
                raise ValueError(
                    f"{instrument} did not match regex: {inst_re.pattern}"
                )
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
            return (
                self.date,
                self.time,
                self.instrument,
            ) < (
                other.date,
                other.time,
                other.instrument,
            )
        else:
            return NotImplemented

    @staticmethod
    def format_date(date) -> str:
        if isinstance(date, datetime.date):
            if 2000 <= date < 2100:
                datestr = date.strftime("%y%m%d")
            else:
                raise ValueError(
                    "Date must be between the year 2000 and 2100."
                )
        else:
            match = date_re.search(date)
            if match:
                datestr = match[0]
            else:
                raise ValueError(
                    f"{date} did not match regex: {date_re.pattern}"
                )

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
                raise ValueError(
                    f"{time} did not match regex: {time_re.pattern}"
                )

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
            match = vis_pid_re.search(str(args))
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
            if args[3] in vis_compression:
                (date, time, instrument) = args[:3]
                compression = args[3]
            else:
                raise ValueError(
                    f"{args[3]} is not one of {vis_compression.keys()}"
                )
        else:
            raise IndexError("accepts 1 to 4 arguments")

        super().__init__(date, time, instrument)
        self.compression = compression

    def __str__(self):
        return "-".join((super().__str__(), self.compression))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                super().__eq__(other)
                and self.compression == other.compression
            )
        return False

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            if super().__eq__(other):
                return self.compression < other.compression
            else:
                return super().__lt__(other)
        else:
            return NotImplemented
