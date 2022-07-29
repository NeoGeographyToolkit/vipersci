"""
This heatmaps module takes scalar values with 2D coordinates and creates a heatmap representation
with individual points effectively averaged together.
"""

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

import math
from multiprocessing import Pool
import subprocess
import time
from typing import Dict, Tuple, Any
import logging

import pyproj
import numpy as np
import rasterio
import rasterio.features
import shapely.geometry
from sklearn.neighbors import KernelDensity

logger = logging.getLogger(__name__)


def buffered_mask(
    linestring: shapely.geometry.LineString,
    transform: rasterio.Affine,
    buffer: float,
    all_touched=False,
):
    """
    Returns a boolean numpy array from rasterio.features.geometry_mask() that
    indicates the shape of *linestring* buffered by *buffer* interpreted into
    a grid defined by *transform*.

    In general, the returned array can be used as a numpy mask, where pixels
    that overlap the shapes are False.

    The parameter *all_touched* is passed directly to
    rasterio.features.geometry_mask(), and you can read more about it there.
    """
    logger.debug("Start buffer")
    start = time.perf_counter()
    logger.debug(linestring.bounds)
    buffered = linestring.buffer(buffer, resolution=2)
    if isinstance(buffered, shapely.geometry.Polygon):
        geometries = [
            buffered,
        ]
    else:  # MultiPolygon
        geometries = buffered.geoms
    logger.debug(f"Buffered geometries in {time.perf_counter() - start:.6f}s")

    # logger.debug(type(geometries))
    logger.debug(buffered.bounds)

    window = rasterio.windows.from_bounds(*buffered.bounds, transform).round_lengths(
        op="ceil"
    )

    logger.debug(window)

    logger.debug("Start geometry_mask")
    start = time.perf_counter()
    mask = rasterio.features.geometry_mask(
        geometries,
        rasterio.windows.shape(window),
        transform,
        all_touched=all_touched,
        invert=False,
    )
    logger.debug(f"Created geometry_mask in {time.perf_counter() - start:.6f}s")

    return mask


def transform_frombuffer_withgrid(west: float, north: float, buffer: float, gsd: float):
    """
    Returns a rasterio Affine transform based on the specified value of
    *gsd* (ground sample distance) and the location of a point north of *north*
    by *buffer* distance and west of *west* by *buffer* distance which are
    further moved to the northwest by a small amount to guarantee that the
    returned offset is an integer number of *gsd* intervals from the origin.
    """
    bwest = west - buffer
    bnorth = north + buffer

    # Make sure that "west" and "north" are snapped into a grid centered on the
    # origin with a *ground_sample_distance* step.
    west = math.floor(bwest / gsd) * gsd
    north = math.ceil(bnorth / gsd) * gsd

    logger.debug(f"west, north: {west}, {north}")

    transform = rasterio.transform.from_origin(west, north, gsd, gsd)
    return transform


def __run_samples(kde, sample_coords):
    return kde.score_samples(sample_coords)


def generate_density_heatmap(
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    values: np.ndarray,
    gsd: float = 1,  # in same units of x, y
    radius: float = 1,  # radius of "data disk", in units of x, y
    padding: float = None,  # in pixels
    nodata_value: float = 0,
    transform=None,
    processes: int = 1,
):
    """
    Perform tophat kernel density estimation to build a continuous heatmap
    representation of scalar values with 2d coordinates.

    Parameters:
        x_coords: x coordinates of the data points
        y_coords: y coordinates of the data points
        values: values of the data points
        gsd: Coordinate interval at which to sample the output distribution,
            or the ground sample distance of the output arrays.
        radius:  This is the kernel bandwidth used in the density estimation,
            and should be the sensing "radius" of the instrument.
        padding: Square padding in pixels to add to the bounds of data when
            returning an array.  If None (the default), the value of *radius*
            converted to pixels will be used.
        nodata_value: Defaults to zero, but a different value can be specified.
        transform: If a rasterio Affine transform is not supplied (the
            default), then one will be generated, and returned.
        processes: Number of processes to use when sampling the output distribution.

    Returns:
        A tuple (transform, counts, avg)
        transform: transform used to georeference the output data
        counts: The number of observations (data points defined by the x/y
            center location and *radius*) that overlap a given grid cell.
        avg: Averaged value of all the individual observations that overlap
            a given grid cell.

    The *counts* and *avg* objects are numpy arrays.
    """

    if processes < 1:
        raise ValueError("Processes must be a positive integer.")

    if not (len(x_coords) == len(y_coords) == len(values)):
        raise ValueError("Input arrays must be of the same length.")

    points = shapely.geometry.LineString(
        tuple(zip(x_coords.tolist(), y_coords.tolist()))
    )

    if (
        gsd > points.bounds[2] - points.bounds[0]
        or gsd > points.bounds[3] - points.bounds[1]
    ):
        raise ValueError("GSD can not be larger than the bounds of the input data.")

    if padding is None:
        buffer = radius
    else:
        # Convert from pixels of padding to a buffer in x/y distance units.
        buffer = (padding * gsd) + radius
    logger.debug(f"buffer: {buffer}")

    if transform is None:
        transform = transform_frombuffer_withgrid(
            np.amin(x_coords), np.amax(y_coords), buffer, gsd
        )
    else:
        if transform.a != gsd or transform.e != gsd:
            raise ValueError(
                f"The scale factors of the transform ({transform.a}, "
                f"{transform.e}) must both equal the ground sample distance, "
                f"({gsd})."
            )

    start = time.perf_counter()
    mask = buffered_mask(points, transform, buffer)
    end = time.perf_counter()
    logger.debug(f"Created mask in {end - start:.6f}s")

    train = np.column_stack([y_coords, x_coords])
    kde = KernelDensity(
        bandwidth=radius, metric="euclidean", kernel="tophat", algorithm="auto"
    )
    start = time.perf_counter()
    kde.fit(train)
    end = time.perf_counter()
    logger.debug(f"Trained unweighted KDE in {end - start:.6f}s")

    # Now get unmasked coordinates:
    start = time.perf_counter()
    row_coords, col_coords = np.meshgrid(
        range(mask.shape[0]), range(mask.shape[1]), indexing="ij"
    )
    row_masked = np.ma.MaskedArray(row_coords, mask)
    col_masked = np.ma.MaskedArray(col_coords, mask)

    x_tosample, y_tosample = rasterio.transform.xy(
        transform, row_masked.compressed().tolist(), col_masked.compressed().tolist()
    )
    sample_coords = np.column_stack([y_tosample, x_tosample])
    end = time.perf_counter()
    logger.debug(f"Created unmasked coordinates {end - start:.6f}s")

    start = time.perf_counter()
    if processes > 1:
        with Pool(processes=processes) as pool:
            results = pool.starmap(
                __run_samples,
                zip([kde] * processes, np.array_split(sample_coords, processes)),
            )
        samples = np.concatenate(results)
    else:
        samples = kde.score_samples(sample_coords)

    start = time.perf_counter()
    kde.fit(train, sample_weight=values)
    end = time.perf_counter()
    logger.debug(f"Trained weighted KDE in {end - start:.6f}s")

    if processes > 1:
        with Pool(processes=processes) as pool:
            results = pool.starmap(
                __run_samples,
                zip([kde] * processes, np.array_split(sample_coords, processes)),
            )
        weighted_samples = np.concatenate(results)
    else:
        weighted_samples = kde.score_samples(sample_coords)
    end = time.perf_counter()
    logger.info(f"Sampled {samples.shape[0]} points in {end - start:.6f}s.")

    # compute our required stats
    start = time.perf_counter()
    out_unweighted = np.exp(samples)
    out_weighted = np.exp(weighted_samples)
    out_weighted = (out_weighted > 1e-9) * out_weighted
    total_counts = np.sum(values) * out_weighted
    total_observations = len(train)
    frequencies = out_unweighted * total_observations
    frequencies = (frequencies > 1e-9) * frequencies
    with np.errstate(divide="ignore", invalid="ignore"):
        avg_values = np.nan_to_num(total_counts / frequencies, posinf=0, copy=False)
    # frequencies starts as the height of cylinders with radius of bandwidth,
    # but the meaningful value is their volume
    frequencies = frequencies * math.pi * math.pow(radius, 2)
    frequencies = np.around(frequencies)
    end = time.perf_counter()
    logger.info(f"Computed stats in {end - start:.6f}s")

    out_avg = np.full_like(mask, nodata_value, dtype=np.double)
    out_counts = np.full_like(mask, nodata_value, dtype=np.int32)
    for x, y, avg, freq in zip(x_tosample, y_tosample, avg_values, frequencies):
        r, c = rasterio.transform.rowcol(transform, x, y)
        # logger.debug(f"row,col: {r}, {c} avg: {avg} freq: {freq}")
        out_avg[r, c] = avg
        out_counts[r, c] = freq

    return transform, out_counts, out_avg


def apply_gdal_colorrelief(
    in_filepath: str, out_filepath: str, colormap_filepath: str
) -> None:
    """
    Creates a new false-color image from a 1-band source file using the provided colormap file.  Requires GDAL

    Parameters:
        in_filepath: path of existing 1-band geotiff file to color
        out_filepath: path to write new RGBA geotiff
        colormap_filepath: path to a text colormap file
    """
    # TODO: convert to gdal library bindings or rasterio
    subprocess.run(
        f"gdaldem color-relief {in_filepath} {colormap_filepath} {out_filepath} -alpha -q",
        shell=True,
    )


def write_geotiff_rasterio(
    out_filepath, dest_crs, transform, source_crs=None, nodata_value=0, *data
):
    """
    Writes 2D data to a geotiff file

    Parameters
        out_filepath: Absolute filepath for writing
        dest_crs: The Rasterio CRS that applies to the data
        transform: The affine transform used for geolocating the data
        source_crs: The Rasterio CRS the data was projected from, if applicable.  Used to calculate 'extent' in the returned info.
        data: 2D array of data to write to the geotiff.  Multiple arrays will be written to separate bands in order

    Returns
        A dictionary that mimics the information provided by gdalinfo
    """
    with rasterio.open(
        out_filepath,
        "w",
        driver="GTiff",
        height=data[0].shape[0],
        width=data[0].shape[1],
        count=len(data),
        dtype=data[0].dtype,
        crs=dest_crs,
        transform=transform,
        nodata=nodata_value,
    ) as raster:
        for i, d in enumerate(data, start=1):
            raster.write(d, i)
        gdalinfo = get_gdal_info_from_rasterio(raster, source_crs)

    return gdalinfo


def get_gdal_info_from_rasterio(
    input: rasterio.DatasetReader, source_crs: pyproj.crs.CRS
) -> Dict[str, Any]:
    """
    Construct a block of gdal-info style json from the metadata about a rasterio dataset
    Parameters:
        input: loaded rasterio dataset
    Returns:
        dict
    """
    geotransform = input.transform.to_gdal()
    result = {
        "size": [input.shape[0], input.shape[1]],
        "coordinateSystem": {"proj4": input.crs.to_proj4()},
        "geoTransform": geotransform,
        "resolution": {"xResolution": geotransform[1], "yResolution": geotransform[5]},
        "driverShortName": input.driver,
        "metadata": {
            "IMAGE_STRUCTURE": {
                "INTERLEAVE": input.interleaving.name if input.interleaving else "None",
                "COMPRESSION": input.compression.name if input.compression else "None",
            }
        },
        "files": input.files,
    }

    bands = []
    for index in range(0, input.count):
        band = {
            "band": input.indexes[index],
            "mask": {"flags": [f.name for f in input.mask_flag_enums[index]]},
            "type": input.dtypes[index],
            "block": list(input.block_shapes[index]),
            "description": str(input.descriptions[index]),
            "noDataValue": input.nodata,
            "colorInterpretation": input.colorinterp[index].name,
        }
        bands.append(band)

    result["bands"] = bands

    if source_crs is not None:
        x = [
            input.bounds.left,
            input.bounds.left,
            input.bounds.right,
            input.bounds.right,
        ]
        y = [
            input.bounds.bottom,
            input.bounds.top,
            input.bounds.top,
            input.bounds.bottom,
        ]
        lon_bnds, lat_bnds = pyproj.Transformer.from_crs(
            input.crs, source_crs
        ).transform(x, y)

        result["extent"] = {
            "type": "Polygon",
            "coordinates": [
                [
                    [lon_bnds[0], lat_bnds[0]],
                    [lon_bnds[1], lat_bnds[1]],
                    [lon_bnds[2], lat_bnds[2]],
                    [lon_bnds[3], lat_bnds[3]],
                    [lon_bnds[0], lat_bnds[0]],
                ]
            ],
        }

    result["cornerCoordinates"] = {
        "center": [
            (input.bounds.left + input.bounds.right) / 2,
            (input.bounds.top + input.bounds.bottom) / 2,
        ],
        "lowerLeft": [input.bounds.left, input.bounds.bottom],
        "upperLeft": [input.bounds.left, input.bounds.top],
        "lowerRight": [input.bounds.right, input.bounds.bottom],
        "upperRight": [input.bounds.right, input.bounds.top],
    }

    return result


def reproject(
    x: np.ndarray, y: np.ndarray, crs: pyproj.crs.CRS
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Projects a set of x and y coordinates using the provided CRS

        Parameters:
            x: np array of x (longitude, easting) coordinates
            y: np array of y (latitude, northing) coordinates
            crs: pyproj CRS defining the projection
        Returns:
            x, y: projected coordinate arrays
    """
    proj = pyproj.Proj(crs)
    return proj(longitude=x, latitude=y)


def generate_area_bin_heatmap(
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    values: np.ndarray,
    bin_size: float = 1,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates a 1-band floating point geotiff heatmap by binning data into a grid and averaging the values

    Parameters:
        x_coords: array of x coordinates. Should be projected
        y_coords: array of y coordinates. Should be projected
        values: array of scalar values at each provided location
        crs: coordinate reference system used to project the locations to cartesian coordinates
        bin_size: size of square bins in meters

    Returns:
        A tuple (transform, out_counts, out_avg)
        transform: transform used to georeference the output data
        out_counts: The number of observations (data points) in a given area
        out_avg: Averaged values of measurements in a given area
    """

    def get_transform_from_coords(
        x_coords: np.ndarray, y_coords: np.ndarray, padding=0, grid_size: float = 1
    ) -> Tuple[rasterio.Affine, rasterio.windows.Window, rasterio.coords.BoundingBox]:
        """
        Given a set of coordinates and a desired grid size, build a transform representing a uniform
        grid over the bounds of the coordinates

        Parameters
            x_coords: array of x coordinates
            y_coords: array of y coordinates
            padding: square padding value to use around the bounding box of hte provided coordinates
            grid_size: resolution of the grid
        """
        x_min = grid_size * math.floor(np.amin(x_coords) / grid_size) - padding
        y_min = grid_size * math.floor(np.amin(y_coords) / grid_size) - padding
        x_max = grid_size * math.ceil(np.amax(x_coords) / grid_size) + padding
        y_max = grid_size * math.ceil(np.amax(y_coords) / grid_size) + padding

        width = x_max - x_min
        height = y_max - y_min

        if width < padding * 4 or height < padding * 4:
            raise ValueError(
                "Total padding should not be larger than the original shape of the data"
            )

        # w = rasterio.windows.get_data_window()

        bounds = rasterio.coords.BoundingBox(x_min, y_min, x_max, y_max)
        transform = rasterio.transform.from_bounds(
            x_min, y_max, x_max, y_min, width / grid_size, height / grid_size
        )
        window = rasterio.windows.Window(0, 0, width, height)

        return transform, window, bounds

    transform, window = get_transform_from_coords(
        x_coords, y_coords, grid_size=bin_size
    )
    averages, counts = area_bin(values, x_coords, y_coords, transform, window)

    out_avg = np.transpose(np.fliplr(averages))
    out_counts = np.transpose(np.fliplr(counts))

    return transform, out_counts, out_avg


def area_bin(
    values: np.ndarray,
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    transform: rasterio.Affine,
    window: rasterio.windows.Window,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Bins data into a square grid.

    Parameters:
        values: Array of scalar values at each location
        x_coords: Array of x locations
        y_coords: Array of y locations
        bin_size: size of square bins in meters

    Returns:
        (averages, counts, transform): Average of the values contained in each bin, and a count of the values contained in each bin.
    """

    # determine grid sizing from a window of dimension 1x1
    w = rasterio.windows.Window(0, 0, 1, 1)
    left, bottom, right, top = rasterio.windows.bounds(w, transform)
    x_bin_size = abs(right - left)
    y_bin_size = abs(top - bottom)

    left, bottom, right, top = rasterio.windows.bounds(window, transform)

    # bin values into a square meter grid and compute averages
    x_bins = np.arange(left, right + x_bin_size, step=x_bin_size)
    y_bins = np.arange(bottom, top + y_bin_size, step=y_bin_size)
    bins = (x_bins, y_bins)

    counts, _, _ = np.histogram2d(x_coords, y_coords, bins=bins)
    value_totals, _, _ = np.histogram2d(x_coords, y_coords, bins=bins, weights=values)

    with np.errstate(divide="ignore", invalid="ignore"):
        averages = np.nan_to_num(value_totals / counts, posinf=0, copy=False)

    return averages, counts
