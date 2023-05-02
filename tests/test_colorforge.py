#!/usr/bin/env python
"""This module has tests for the pano_products module."""

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

import unittest
from argparse import ArgumentParser
from unittest.mock import create_autospec, patch

import matplotlib as mpl
import numpy as np

from vipersci import __version__
from vipersci.carto import colorforge as cf


class TestPalette(unittest.TestCase):
    def test_init(self):
        p = cf.Palette("viridis", 0, 100)
        self.assertIsInstance(p.cmap, mpl.colors.ListedColormap)
        self.assertIsInstance(p.norm, mpl.colors.Normalize)
        self.assertEqual(p.vmin, 0)
        self.assertEqual(p.vmax, 100)

        p2 = cf.Palette(mpl.colormaps["viridis"], 0, 100, bounded=[1, 50, 100])
        self.assertIsInstance(p2.cmap, mpl.colors.ListedColormap)
        self.assertIsInstance(p2.norm, mpl.colors.BoundaryNorm)

    def test_init_error(self):
        self.assertRaises(ValueError, cf.Palette, "viridis", 0, 100, extend="foo")

    def test_gdal_colormap(self):
        p = cf.Palette("viridis", 0, 100)
        t = p.to_gdal_colormap()

        self.assertEqual(
            t,
            f"""# Color table for Some Units
# created by vipersci.carto.colorforge version {__version__}
# value, R, G, B, A
-0.001 68 1 84 0
0.0 68 1 84 255
0.39215686274509803 68 2 85 255
0.7843137254901961 68 3 87 255
1.1764705882352942 69 5 88 255
1.5686274509803921 69 6 90 255
1.9607843137254901 69 8 91 255
2.3529411764705883 70 9 92 255
2.7450980392156863 70 11 94 255
3.1372549019607843 70 12 95 255
3.5294117647058822 70 14 97 255
3.9215686274509802 71 15 98 255
4.313725490196078 71 17 99 255
4.705882352941177 71 18 101 255
5.098039215686274 71 20 102 255
5.490196078431373 71 21 103 255
5.88235294117647 71 22 105 255
6.2745098039215685 71 24 106 255
6.666666666666667 72 25 107 255
7.0588235294117645 72 26 108 255
7.450980392156863 72 28 110 255
7.8431372549019605 72 29 111 255
8.235294117647058 72 30 112 255
8.627450980392156 72 32 113 255
9.019607843137255 72 33 114 255
9.411764705882353 72 34 115 255
9.803921568627452 72 35 116 255
10.196078431372548 71 37 117 255
10.588235294117647 71 38 118 255
10.980392156862745 71 39 119 255
11.372549019607844 71 40 120 255
11.76470588235294 71 42 121 255
12.156862745098039 71 43 122 255
12.549019607843137 71 44 123 255
12.941176470588236 70 45 124 255
13.333333333333334 70 47 124 255
13.72549019607843 70 48 125 255
14.117647058823529 70 49 126 255
14.509803921568627 69 50 127 255
14.901960784313726 69 52 127 255
15.294117647058822 69 53 128 255
15.686274509803921 69 54 129 255
16.07843137254902 68 55 129 255
16.470588235294116 68 57 130 255
16.862745098039216 67 58 131 255
17.254901960784313 67 59 131 255
17.647058823529413 67 60 132 255
18.03921568627451 66 61 132 255
18.431372549019606 66 62 133 255
18.823529411764707 66 64 133 255
19.215686274509803 65 65 134 255
19.607843137254903 65 66 134 255
20.0 64 67 135 255
20.392156862745097 64 68 135 255
20.784313725490197 63 69 135 255
21.176470588235293 63 71 136 255
21.56862745098039 62 72 136 255
21.96078431372549 62 73 137 255
22.352941176470587 61 74 137 255
22.745098039215687 61 75 137 255
23.137254901960784 61 76 137 255
23.52941176470588 60 77 138 255
23.92156862745098 60 78 138 255
24.313725490196077 59 80 138 255
24.705882352941178 59 81 138 255
25.098039215686274 58 82 139 255
25.49019607843137 58 83 139 255
25.88235294117647 57 84 139 255
26.274509803921568 57 85 139 255
26.666666666666668 56 86 139 255
27.058823529411764 56 87 140 255
27.45098039215686 55 88 140 255
27.84313725490196 55 89 140 255
28.235294117647058 54 90 140 255
28.627450980392158 54 91 140 255
29.019607843137255 53 92 140 255
29.41176470588235 53 93 140 255
29.80392156862745 52 94 141 255
30.19607843137255 52 95 141 255
30.588235294117645 51 96 141 255
30.980392156862745 51 97 141 255
31.372549019607842 50 98 141 255
31.764705882352942 50 99 141 255
32.15686274509804 49 100 141 255
32.549019607843135 49 101 141 255
32.94117647058823 49 102 141 255
33.333333333333336 48 103 141 255
33.72549019607843 48 104 141 255
34.11764705882353 47 105 141 255
34.509803921568626 47 106 141 255
34.90196078431372 46 107 142 255
35.294117647058826 46 108 142 255
35.68627450980392 46 109 142 255
36.07843137254902 45 110 142 255
36.470588235294116 45 111 142 255
36.86274509803921 44 112 142 255
37.254901960784316 44 113 142 255
37.64705882352941 44 114 142 255
38.03921568627451 43 115 142 255
38.431372549019606 43 116 142 255
38.8235294117647 42 117 142 255
39.21568627450981 42 118 142 255
39.6078431372549 42 119 142 255
40.0 41 120 142 255
40.3921568627451 41 121 142 255
40.78431372549019 40 122 142 255
41.1764705882353 40 122 142 255
41.568627450980394 40 123 142 255
41.96078431372549 39 124 142 255
42.35294117647059 39 125 142 255
42.745098039215684 39 126 142 255
43.13725490196078 38 127 142 255
43.529411764705884 38 128 142 255
43.92156862745098 38 129 142 255
44.31372549019608 37 130 142 255
44.705882352941174 37 131 141 255
45.09803921568627 36 132 141 255
45.490196078431374 36 133 141 255
45.88235294117647 36 134 141 255
46.27450980392157 35 135 141 255
46.666666666666664 35 136 141 255
47.05882352941176 35 137 141 255
47.450980392156865 34 137 141 255
47.84313725490196 34 138 141 255
48.23529411764706 34 139 141 255
48.627450980392155 33 140 141 255
49.01960784313725 33 141 140 255
49.411764705882355 33 142 140 255
49.80392156862745 32 143 140 255
50.19607843137255 32 144 140 255
50.588235294117645 32 145 140 255
50.98039215686274 31 146 140 255
51.372549019607845 31 147 139 255
51.76470588235294 31 148 139 255
52.15686274509804 31 149 139 255
52.549019607843135 31 150 139 255
52.94117647058823 30 151 138 255
53.333333333333336 30 152 138 255
53.72549019607843 30 153 138 255
54.11764705882353 30 153 138 255
54.509803921568626 30 154 137 255
54.90196078431372 30 155 137 255
55.294117647058826 30 156 137 255
55.68627450980392 30 157 136 255
56.07843137254902 30 158 136 255
56.470588235294116 30 159 136 255
56.86274509803921 30 160 135 255
57.254901960784316 31 161 135 255
57.64705882352941 31 162 134 255
58.03921568627451 31 163 134 255
58.431372549019606 32 164 133 255
58.8235294117647 32 165 133 255
59.2156862745098 33 166 133 255
59.6078431372549 33 167 132 255
60.0 34 167 132 255
60.3921568627451 35 168 131 255
60.78431372549019 35 169 130 255
61.17647058823529 36 170 130 255
61.568627450980394 37 171 129 255
61.96078431372549 38 172 129 255
62.35294117647059 39 173 128 255
62.745098039215684 40 174 127 255
63.13725490196078 41 175 127 255
63.529411764705884 42 176 126 255
63.92156862745098 43 177 125 255
64.31372549019608 44 177 125 255
64.70588235294117 46 178 124 255
65.09803921568627 47 179 123 255
65.49019607843137 48 180 122 255
65.88235294117646 50 181 122 255
66.27450980392157 51 182 121 255
66.66666666666667 53 183 120 255
67.05882352941177 54 184 119 255
67.45098039215686 56 185 118 255
67.84313725490196 57 185 118 255
68.23529411764706 59 186 117 255
68.62745098039215 61 187 116 255
69.01960784313725 62 188 115 255
69.41176470588235 64 189 114 255
69.80392156862744 66 190 113 255
70.19607843137254 68 190 112 255
70.58823529411765 69 191 111 255
70.98039215686275 71 192 110 255
71.37254901960785 73 193 109 255
71.76470588235294 75 194 108 255
72.15686274509804 77 194 107 255
72.54901960784314 79 195 105 255
72.94117647058823 81 196 104 255
73.33333333333333 83 197 103 255
73.72549019607843 85 198 102 255
74.11764705882352 87 198 101 255
74.50980392156863 89 199 100 255
74.90196078431373 91 200 98 255
75.29411764705883 94 201 97 255
75.68627450980392 96 201 96 255
76.07843137254902 98 202 95 255
76.47058823529412 100 203 93 255
76.86274509803921 103 204 92 255
77.25490196078431 105 204 91 255
77.6470588235294 107 205 89 255
78.0392156862745 109 206 88 255
78.43137254901961 112 206 86 255
78.82352941176471 114 207 85 255
79.2156862745098 116 208 84 255
79.6078431372549 119 208 82 255
80.0 121 209 81 255
80.3921568627451 124 210 79 255
80.7843137254902 126 210 78 255
81.17647058823529 129 211 76 255
81.56862745098039 131 211 75 255
81.96078431372548 134 212 73 255
82.3529411764706 136 213 71 255
82.74509803921569 139 213 70 255
83.13725490196079 141 214 68 255
83.52941176470588 144 214 67 255
83.92156862745098 146 215 65 255
84.31372549019608 149 215 63 255
84.70588235294117 151 216 62 255
85.09803921568627 154 216 60 255
85.49019607843137 157 217 58 255
85.88235294117646 159 217 56 255
86.27450980392156 162 218 55 255
86.66666666666667 165 218 53 255
87.05882352941177 167 219 51 255
87.45098039215686 170 219 50 255
87.84313725490196 173 220 48 255
88.23529411764706 175 220 46 255
88.62745098039215 178 221 44 255
89.01960784313725 181 221 43 255
89.41176470588235 183 221 41 255
89.80392156862744 186 222 39 255
90.19607843137254 189 222 38 255
90.58823529411765 191 223 36 255
90.98039215686275 194 223 34 255
91.37254901960785 197 223 33 255
91.76470588235294 199 224 31 255
92.15686274509804 202 224 30 255
92.54901960784314 205 224 29 255
92.94117647058823 207 225 28 255
93.33333333333333 210 225 27 255
93.72549019607843 212 225 26 255
94.11764705882352 215 226 25 255
94.50980392156863 218 226 24 255
94.90196078431373 220 226 24 255
95.29411764705883 223 227 24 255
95.68627450980392 225 227 24 255
96.07843137254902 228 227 24 255
96.47058823529412 231 228 25 255
96.86274509803921 233 228 25 255
97.25490196078431 236 228 26 255
97.6470588235294 238 229 27 255
98.0392156862745 241 229 28 255
98.43137254901961 243 229 30 255
98.82352941176471 246 230 31 255
99.2156862745098 248 230 33 255
99.6078431372549 250 230 34 255
100.0 253 231 36 255
100.001 253 231 36 0""",
        )


class TestFunctions(unittest.TestCase):
    def test_arg_parser(self):
        p = cf.arg_parser()
        self.assertIsInstance(p, ArgumentParser)

    def test_color_to_bytes(self):
        self.assertEqual(cf.color_to_bytes((0, 0.5, 1)), (0, 127, 255))

    @patch("vipersci.carto.colorforge.plt")
    def test_example_plot(self, m_plt):
        p = cf.Palette("viridis", 0, 100)
        cf.example_plot(p)
        m_plt.ioff.assert_called_once()
        m_plt.imshow.assert_called()
        m_plt.colorbar.assert_called_once()
        m_plt.title.assert_called_once()
        m_plt.tick_params.assert_called_once()
        m_plt.xlabel.assert_called_once()
        m_plt.show.assert_called_once()

    @patch("vipersci.carto.colorforge.plt")
    def test_plot_colorbar(self, m_plt):
        p = cf.Palette("viridis", 0, 100)
        m_fig = create_autospec(mpl.figure.Figure)
        m_plt.subplots.return_value = (m_fig, "ax")
        cf.plot_colorbar(p, "h")
        m_plt.ioff.assert_called_once()
        m_plt.show.assert_called_once()

    def test_rescale(self):
        a = np.array((0, 50, 100))
        r = cf.rescale(a, 0, 100)
        np.testing.assert_array_equal(r, np.array([-10.0, 50.0, 110.0]))

    def test_verve_stoplight(self):
        vs = cf.verve_stoplight()
        self.assertIsInstance(vs, mpl.colors.ListedColormap)
