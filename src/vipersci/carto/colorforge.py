#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Displays color maps and can create output colorization files.
"""

# Copyright 2023, United States Government as represented by the
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
from io import StringIO
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

from vipersci import __version__
from vipersci import util

logger = logging.getLogger(__name__)

presets = dict(
    dice=dict(
        label="Depth to Ice Stability (m)",
        cmap="Blues_r",
        vmin=0,
        vmax=1.1,
        bounded=False,
        extend="neither"
    ),
    isr=dict(
        label="Depth to Ice Stability (m)",
        cmap="Blues_r",
        vmin=0,
        vmax=1.1,
        bounded=[0, 0.01, 0.5, 1, 1.1],
        extend="neither"
    ),
    verve_slope=dict(
        label="Slope (°)",
        cmap="",
        vmin=0,
        vmax=20,
        bounded=False,
        extend="max"
    ),
    verve_slope_discrete=dict(
        label="Slope (°)",
        cmap="",
        vmin=0,
        vmax=20,
        bounded=[0, 5, 10, 15, 20],
        extend="max"
    ),
    stoplight_slope=dict(
        label="Slope (°)",
        cmap="RdYlGn_r",
        vmin=0,
        vmax=20,
        bounded=False,
        extend="max"
    ),
    slope=dict(
        label="Slope (°)",
        cmap="viridis",
        vmin=0,
        vmax=20,
        bounded=False,
        extend="max"
    ),
    slope_disc=dict(
        label="Slope (°)",
        cmap="viridis",
        vmin=0,
        vmax=20,
        bounded=[0, 5, 10, 15, 20],
        extend="max"
    ),
    tmax=dict(
        label="Max Temperature (K)",
        cmap="inferno",
        vmin=22,
        vmax=351,
        bounded=False,
        extend="neither"
    ),
)


class Palette:
    def __init__(
        self, cmap, vmin, vmax, label="Some Units", bounded=False, extend=False,
        nodata_color="none", under_color=0, over_color=0.999999
    ):
        self.nodata_color = mpl.colors.to_rgba(nodata_color)
        if isinstance(cmap, mpl.colors.Colormap):
            self.cmap = cmap
        else:
            self.cmap = mpl.colormaps[cmap]

        self.cmap.colorbar_extend = extend

        if isinstance(under_color, (float, int)):
            under_color = self.cmap(under_color)

        if isinstance(over_color, (float, int)):
            over_color = self.cmap(over_color)

        if extend == "max":
            self.cmap.set_under(under_color, alpha=0)
        elif extend == "neither":
            self.cmap.set_under(under_color, alpha=0)
            self.cmap.set_over(over_color, alpha=0)
        else:
            raise ValueError(f"extend={extend} is not accepted.")
        self.vmin = vmin
        self.vmax = vmax
        self.label = label
        self.bounded = bounded
        if bounded:
            self.norm = mpl.colors.BoundaryNorm(bounded, self.cmap.N)
        else:
            self.norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    def to_gdal_colormap(self, epsilon=0.001):
        s = [
            f"# Color table for {self.label}",
            f"# created by {__name__} version {__version__} ",
            "# value, R, G, B, A"
        ]
        if self.bounded:
            if self.cmap.colorbar_extend in ("max", "neither"):
                values = [self.bounded[0] - epsilon]
            else:
                values = list()

            values.append(self.bounded[0])
            for v in self.bounded[1:-1]:
                values.append(v - epsilon)
                values.append(v)

            if self.cmap.colorbar_extend in ("min", "neither"):
                values.append(self.bounded[-1] - epsilon)

            values.append(self.bounded[-1])
        else:
            values = np.linspace(self.vmin, self.vmax, num=self.cmap.N)
            if self.cmap.colorbar_extend in ("max", "neither"):
                values = np.insert(values, 0, self.vmin - epsilon)

            if self.cmap.colorbar_extend in ("min", "neither"):
                values = np.append(values, self.vmax + epsilon)

        for v in values:
            rgba = self.cmap(self.norm(v), bytes=True)
            s.append(f"{v} {' '.join(map(str, rgba))}")

        if not mpl.colors.same_color(self.nodata_color, (0, 0, 0, 0) ):
            s.append(f"nv {' '.join(color_to_bytes(self.nodata_color))}")

        return "\n".join(s)


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, parents=[util.parent_parser()]
    )

    parser.add_argument(
        "-b", "--bar",
        choices=["v", "h"],
        help="If given will plot just a colorbar."
    )
    parser.add_argument(
        "-c",
        "--colormap",
        help="Name of matplotlib colormap.",
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Optional name of output file.", required=False
    )
    parser.add_argument(
        "-p",
        "--preset",
        choices=presets.keys(),
        required=False,
        help="Specifying a preset, sets the colormap, vmin, and vmax.",
    )
    parser.add_argument(
        "--plot", action="store_true", help="If given will create example plot, ignores -b."
    )
    parser.add_argument(
        "--vmin", default=0, type=float, help="Minimum value for data range."
    )
    parser.add_argument(
        "--vmax", default=1, type=float, help="Maximum value for data range."
    )
    return parser


def main():
    parser = arg_parser()
    args = parser.parse_args()
    util.set_logger(args.verbose)

    if args.preset:
        if args.preset in ("verve_slope", "verve_slope_discrete"):
            d = presets[args.preset]
            d["cmap"] = verve_stoplight()
            pal = Palette(**d)
        else:
            pal = Palette(**presets[args.preset])
    else:
        pal = Palette(
            cmap=mpl.colormaps[args.colormap],
            vmin=args.vmin,
            vmax=args.vmax,
        )

    if args.plot:
        plt.ioff()
        # data = rescale(moon(), pal.vmin, pal.vmax)  # (512, 512) uint8 ndarray
        # make these smaller to increase the resolution
        dx, dy = 0.05, 0.05

        x = np.arange(-3.0, 3.0, dx)
        y = np.arange(-3.0, 3.0, dy)
        X, Y = np.meshgrid(x, y)
        Z = rescale(func3(X, Y), pal.vmin, pal.vmax)
        extent = np.min(x), np.max(x), np.min(y), np.max(y)

        checkerboard = np.add.outer(range(32), range(32)) % 2
        plt.imshow(
            checkerboard,
            cmap=plt.cm.gray,
            vmin=-1,
            vmax=2,
            interpolation='nearest',
            extent=extent
        )

        # plt.imshow(data, cmap=pal.cmap, norm=pal.norm)
        plt.imshow(
            Z, cmap=pal.cmap, norm=pal.norm, interpolation='bilinear', extent=extent
        )

        plt.colorbar(label=pal.label)
        plt.title(f"Colormap: {pal.cmap.name}")
        plt.tick_params(
            left=False, right=False, labelleft=False, labelbottom=False, bottom=False
        )
        plt.xlabel(f"Colormap range: {pal.vmin} to {pal.vmax}, Data range: {Z.min():.3g} to {Z.max():.3g}")

        if args.output is None:
            plt.show()
        else:
            plt.savefig(args.output)

    elif args.bar is not None:
        ori = {"h": "horizontal", "v": "vertical"}

        plt.ioff()
        if args.bar == "h":
            fig, ax = plt.subplots(figsize=(5, 1))
            fig.subplots_adjust(bottom=0.5)
        elif args.bar == "v":
            fig, ax = plt.subplots(figsize=(1.2, 5))
            fig.subplots_adjust(right=0.4)

        fig.colorbar(
            mpl.cm.ScalarMappable(norm=pal.norm, cmap=pal.cmap),
            cax=ax,
            orientation=ori[args.bar],
            label=pal.label
        )

        if args.output is None:
            plt.show()
        else:
            plt.savefig(args.output)
    else:
        if args.output is None:
            print(pal.to_gdal_colormap())
        else:
            args.output.write_text(pal.to_gdal_colormap())


def color_to_bytes(color_tuple):
    converted = map(lambda x: int(x * 255), color_tuple)
    return tuple(converted)


def func3(x, y):
    return (1 - x / 2 + x**5 + y**3) * np.exp(-(x**2 + y**2))


def rescale(arr, min, max):
    data = arr.astype('float64')
    minmax_range = max - min
    real_min = min - (minmax_range * 0.1)
    real_max = max + (minmax_range * 0.1)
    return (
        (
            ((data - np.min(data)) / (np.max(data) - np.min(data))) * (real_max - real_min)
        ) + real_min
    )


def verve_stoplight():
    color_arr = np.flipud(np.loadtxt(StringIO("""100 254 14 2
99 253 20 4
98 253 27 5
97 253 33 7
96 252 39 9
95 252 45 10
94 252 51 12
93 252 57 13
92 251 63 15
91 251 69 16
90 250 74 18
89 250 80 20
88 249 86 21
87 249 90 22
86 249 96 24
85 249 102 25
84 249 106 27
83 248 112 29
82 247 117 30
81 247 122 32
80 247 126 33
79 246 132 34
78 246 136 35
77 246 141 37
76 245 145 39
75 245 150 40
74 245 154 42
73 244 159 43
72 244 163 45
71 244 167 46
70 243 171 47
69 243 176 49
68 242 180 51
67 242 183 52
66 242 188 53
65 242 192 55
64 241 195 56
63 241 199 58
62 241 203 59
61 240 206 60
60 240 209 62
59 239 213 63
58 239 216 64
57 238 220 67
56 239 223 68
55 238 226 68
54 237 228 70
53 237 232 72
52 236 235 73
51 235 236 75
50 231 236 76
49 229 235 77
48 225 236 79
47 222 234 80
46 218 234 81
45 215 234 82
44 213 234 83
43 209 234 85
42 207 233 87
41 203 233 87
40 201 233 89
39 198 232 90
38 195 232 92
37 193 231 93
36 190 231 95
35 187 231 96
34 185 231 96
33 183 230 98
32 180 230 99
31 178 229 100
30 176 229 102
29 174 229 103
28 172 228 105
27 169 228 106
26 168 228 107
25 166 227 108
24 164 227 109
23 162 226 110
22 160 225 112
21 159 226 113
20 157 225 114
19 156 225 116
18 154 224 117
17 153 224 118
16 152 224 119
15 150 224 121
14 149 223 121
13 148 222 123
12 146 222 124
11 146 222 125
10 144 221 126
9 143 221 127
8 143 221 128
7 142 220 130
6 141 220 130
5 141 220 132
4 140 220 133
3 139 220 134
2 139 219 135
1 139 219 135
0 139 219 135"""), dtype=np.dtype(int), usecols=(1, 2, 3)))

    return mpl.colors.ListedColormap(color_arr / 255, name="VERVE_stoplight")




