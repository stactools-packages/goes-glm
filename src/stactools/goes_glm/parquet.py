import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from geopandas import GeoDataFrame, GeoSeries
from netCDF4 import Dataset
from shapely.geometry import Point

from . import constants

logger = logging.getLogger(__name__)


def convert(dataset: Dataset, dest_folder: str) -> Dict[str, Dict[str, Any]]:
    assets: Dict[str, Dict[str, Any]] = {}
    assets[constants.PARQUET_KEY_EVENTS] = create_event(dataset, dest_folder)
    assets[constants.PARQUET_KEY_FLASHES] = create_flashes(dataset, dest_folder)
    assets[constants.PARQUET_KEY_GROUPS] = create_groups(dataset, dest_folder)
    return assets


def create_event(dataset: Dataset, dest_folder: str) -> Dict[str, Any]:
    file = os.path.join(dest_folder, "events.parquet")
    cols = ["lat", "lon", "id", "time_offset", "energy", "parent_group_id"]
    return create_asset(dataset, file, "event", cols, constants.PARQUET_TITLE_EVENTS)


def create_flashes(dataset: Dataset, dest_folder: str) -> Dict[str, Any]:
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
    # create a list of points
    geometries = []
    count = dataset.variables[f"{type}_count"][0]
    for i in range(0, count):
        lat = dataset.variables[f"{type}_lat"][i]
        lon = dataset.variables[f"{type}_lon"][i]
        geometries.append(Point(lon, lat))

    # fill dict with all data in a columnar way
    table_data = {
        constants.PARQUET_GEOMETRY_COL: GeoSeries(geometries, crs=constants.SOURCE_CRS)
    }
    table_cols = [{"name": constants.PARQUET_GEOMETRY_COL, "type": dataset.featureType}]
    for col in cols:
        if col == "lat" or col == "lon":
            continue

        variable = dataset.variables[f"{type}_{col}"]
        attrs = variable.ncattrs()
        data = variable[...].tolist()
        table_col = {
            "name": col,
            "type": str(variable.datatype),
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
            if unit.startswith("seconds since "):
                new_col = col.replace("_offset", "")
                base = datetime.fromisoformat(unit[14:]).replace(tzinfo=timezone.utc)

                new_data: List[datetime] = []
                for val in data:
                    delta = timedelta(seconds=val)
                    new_data.append(base + delta)

                table_data[new_col] = new_data
                table_cols.append(
                    {"name": new_col, "type": "datetime"}  # todo: correct data type?
                )

        table_data[col] = data
        table_cols.append(table_col)

    # Create a geodataframe and store it as geoparquet file
    dataframe = GeoDataFrame(table_data)

    # Convert using private API until the following bug is solved:
    # https://github.com/geopandas/geopandas/issues/2495
    # Replace later with somethine like:
    # dataframe.to_parquet(file, version = "2.6")
    import geopandas as gp

    table = gp.io.arrow._geopandas_to_arrow(dataframe)
    import pyarrow.parquet as pq

    pq.write_table(table, file, version="2.6")

    # Create asset dict
    return create_asset_metadata(title, file, table_cols, count)


def create_asset_metadata(
    title: str,
    href: Optional[str] = None,
    cols: List[Dict[str, Any]] = [],
    count: int = -1,
) -> Dict[str, Any]:
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
