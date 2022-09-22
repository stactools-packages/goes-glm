import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from geopandas import GeoDataFrame, GeoSeries
from netCDF4 import Dataset
from shapely.geometry import Point

from . import constants

logger = logging.getLogger(__name__)


def convert(dataset: Dataset, dest_folder: str) -> Dict[str, Dict[str, Any]]:
    """
    Converts a netCDF dataset to three geoparquet files (for events, flashes
    and groups) in the given folder.
    Returns a dict containing the three STAC Asset Objects for the geoparquet
    files.

    Args:
        dataset (Dataset): A netCDF4 Dataset
        dest_folder (str): The destination folder for the geoparquet files

    Returns:
        dict: Asset Objects
    """
    assets: Dict[str, Dict[str, Any]] = {}
    assets[constants.PARQUET_KEY_EVENTS] = create_event(dataset, dest_folder)
    assets[constants.PARQUET_KEY_FLASHES] = create_flashes(dataset, dest_folder)
    assets[constants.PARQUET_KEY_GROUPS] = create_groups(dataset, dest_folder)
    return assets


def create_event(dataset: Dataset, dest_folder: str) -> Dict[str, Any]:
    """
    Creates geoparquet file from a netCDF Dataset for the events.

    Args:
        dataset (Dataset): A netCDF4 Dataset

    Returns:
        dict: Asset Object for the geoparquet file
    """
    file = os.path.join(dest_folder, "events.parquet")
    cols = ["lat", "lon", "id", "time_offset", "energy", "parent_group_id"]
    return create_asset(dataset, file, "event", cols, constants.PARQUET_TITLE_EVENTS)


def create_flashes(dataset: Dataset, dest_folder: str) -> Dict[str, Any]:
    """
    Creates geoparquet file from a netCDF Dataset for the flashes.

    Args:
        dataset (Dataset): A netCDF4 Dataset

    Returns:
        dict: Asset Object for the geoparquet file
    """
    file = os.path.join(dest_folder, "flashes.parquet")
    cols = [
        "lat",
        "lon",
        "id",
        "time_offset_of_first_event",
        "time_offset_of_last_event",
        "frame_time_offset_of_first_event",
        "frame_time_offset_of_last_event",
        "area",
        "energy",
        "quality_flag",
    ]
    return create_asset(dataset, file, "flash", cols, constants.PARQUET_TITLE_FLASHES)


def create_groups(dataset: Dataset, dest_folder: str) -> Dict[str, Any]:
    """
    Creates geoparquet file from a netCDF Dataset for the groups.

    Args:
        dataset (Dataset): A netCDF4 Dataset

    Returns:
        dict: Asset Object for the geoparquet file
    """
    file = os.path.join(dest_folder, "groups.parquet")
    cols = [
        "lat",
        "lon",
        "id",
        "time_offset",
        "frame_time_offset",
        "area",
        "energy",
        "quality_flag",
        "parent_flash_id",
    ]
    return create_asset(dataset, file, "group", cols, constants.PARQUET_TITLE_GROUPS)


def create_asset(
    dataset: Dataset, file: str, type: str, cols: List[str], title: str
) -> Dict[str, Any]:
    """
    Creates an asset object for a netCDF Dataset with some additional properties.

    The type is the prefix of the columns in the netCDF file and will be prefixed
    to the cols (with a underscore in-between) when reading the netCDF4 dataset.
    The geoparquet file will use the cols, but without the prefix.

    Args:
        dataset (Dataset): A netCDF4 Dataset
        file (str): The target file path
        type (str): The group of data to write (one of: flash, event or group)
        cols (List[str]): A list of columns to consider
        title (str): A title for the asset

    Returns:
        dict: Asset Object for the geoparquet file
    """
    # create a list of points
    geometries = []
    count_col = f"{type}_count"
    count = dataset.variables[count_col][...].tolist()
    if not isinstance(count, int):
        logger.warning(
            f"The value ({count}) for column {count_col} is not an integer. Assuming 0."
        )
        count = 0

    lat_col = f"{type}_lat"
    lat_var = dataset.variables[lat_col]
    lat_var_len = len(lat_var)
    if lat_var_len != count:
        logger.warning(
            f"{count_col} ({count}) != length of variable {lat_col} ({lat_var_len})"
        )

    lon_col = f"{type}_lon"
    lon_var = dataset.variables[lon_col]
    lon_var_len = len(lon_var)
    if lon_var_len != count:
        logger.warning(
            f"{count_col} ({count}) != length of variable {lon_col} ({lon_var_len})"
        )

    if lon_var_len != count or lat_var_len != count:
        if lon_var_len == lat_var_len:
            count = lon_var_len
        else:
            raise Exception(
                "length of {lat_col} ({lat_var_len}) != length of {lon_col} ({lon_var_len})"
            )

    for i in range(0, count):
        lat = lat_var[i]
        lon = lon_var[i]
        geometries.append(Point(lon, lat))

    # fill dict with all data in a columnar way
    table_data = {
        constants.PARQUET_GEOMETRY_COL: GeoSeries(geometries, crs=constants.SOURCE_CRS)
    }
    table_cols = [{"name": constants.PARQUET_GEOMETRY_COL, "type": dataset.featureType}]
    for col in cols:
        if col == "lat" or col == "lon":
            continue

        var_name = f"{type}_{col}"
        if var_name not in dataset.variables:
            if col.startswith("frame_time_offset"):
                # Some older datasets don't contain these variables so generate files without them.
                # See https://github.com/stactools-packages/goes-glm/issues/17
                continue
            else:
                raise Exception(f"Variable '{var_name}' is missing")

        variable = dataset.variables[var_name]
        attrs = variable.ncattrs()
        data = variable[...].tolist()
        table_col = {
            "name": col,
            "type": str(variable.datatype),  # todo: check data type #11
        }
        if "long_name" in attrs:
            table_col["description"] = variable.getncattr("long_name")

        if "units" in attrs:
            unit = variable.getncattr("units")
            if unit == "percent":
                table_col["unit"] = "%"
            elif unit not in constants.IGNORED_UNITS:
                table_col["unit"] = unit

            # Convert offsets into datetimes
            if "seconds since" in unit:
                new_col = col.replace("_offset", "")
                # Goes-Test uses milliseconds while all other slots use seconds
                milliseconds = True if "milliseconds" in unit else False
                extracted_timestamp = re.sub(r"^(milli)?seconds since\s+", "", unit)
                base = datetime.fromisoformat(extracted_timestamp).replace(
                    tzinfo=timezone.utc
                )

                new_data: List[Optional[datetime]] = []
                for val in data:
                    try:
                        if milliseconds:
                            delta = timedelta(milliseconds=val)
                        else:
                            delta = timedelta(seconds=val)
                        new_data.append(base + delta)
                    except TypeError:
                        raise Exception(
                            f"An invalid value '{val}' found in variable '{var_name}'"
                        )

                table_data[new_col] = new_data
                col_info = {
                    "name": new_col,
                    "type": constants.PARQUET_DATETIME_COL_TYPE,
                }

                table_cols.append(col_info)

        table_data[col] = data
        table_cols.append(table_col)

    # Create a geodataframe and store it as geoparquet file
    dataframe = GeoDataFrame(table_data)
    dataframe.to_parquet(file, version="2.6")

    # Create asset dict
    return create_asset_metadata(title, file, table_cols, count)


def create_asset_metadata(
    title: str,
    href: Optional[str] = None,
    cols: List[Dict[str, Any]] = [],
    count: int = -1,
) -> Dict[str, Any]:
    """
    Creates a basic geoparquet asset dict with shared core properties (title,
    type, roles), properties for the table extension  and optionally an href.
    An href should be given for normal assets, but can be None for Item Asset
    Definitions.

    Args:
        title (str): A title for the asset
        href (str): The URL to the asset (optional)
        cols (List[Dict[str, Any]]): A list of columns (optional;
            compliant to table:columns)
        count: The number of rows in the asset (optional)

    Returns:
        dict: Basic Asset object
    """
    asset: Dict[str, Any] = {
        "title": title,
        "type": constants.PARQUET_MEDIA_TYPE,
        "roles": constants.PARQUET_ROLES,
        "table:primary_geometry": constants.PARQUET_GEOMETRY_COL,
    }
    if href is not None:
        asset["href"] = href
    if len(cols) > 0:
        asset["table:columns"] = cols
    if count >= 0:
        asset["table:row_count"] = int(count)
    return asset
