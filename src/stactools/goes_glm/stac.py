import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
from dateutil.parser import isoparse
from netCDF4 import Dataset
from pystac import (
    Asset,
    CatalogType,
    Collection,
    Extent,
    Item,
    Link,
    MediaType,
    RelType,
    SpatialExtent,
    Summaries,
    TemporalExtent,
)
from pystac.extensions.datacube import (  # AdditionalDimension,; Variable,
    DatacubeExtension,
    VariableType,
)
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.scientific import ScientificExtension
from pystac.extensions.table import TableExtension

from . import constants, parquet

logger = logging.getLogger(__name__)


def create_collection(
    license: str,
    id: str = "goes-glm",
    thumbnail: str = "",
    nogeoparquet: bool = False,
    nonetcdf: bool = False,
    start_time: Optional[str] = None,
) -> Collection:
    """Create a STAC Collection for NOAA MRMS QPE sub-products.

    Args:
        id (str): A custom collection ID, defaults to 'goes-glm'
        thumbnail (str): URL for the PNG or JPEG collection thumbnail asset (none if empty)
        nogeoparquet (bool): If set to True, the collections does not include the
            geoparquet-related metadata
        nonetcdf (bool): If set to True, the collections does not include the
            netCDF-related metadata
        start_time (str): The start timestamp for the temporal extent, default to now.
            Timestamps consist of a date and time in UTC and must follow RFC 3339, section 5.6.

    Returns:
        Collection: STAC Collection object
    """
    # Time must be in UTC
    if start_time is None:
        start_datetime = datetime.now(tz=timezone.utc)
    else:
        start_datetime = isoparse(start_time)

    extent = Extent(
        SpatialExtent(constants.BBOXES),
        TemporalExtent([[start_datetime, None]]),
    )

    keywords = [
        "NOAA",
        "GOES",
        "GOES-16",
        "GOES-17",
        "GLM",
        "Atmosphere",
        "Environmental",
        "Lightning",
        "Weather",
    ]
    if not nonetcdf:
        keywords.append("netCDF")
    if not nogeoparquet:
        keywords.append("GeoParquet")

    summaries = Summaries(
        {
            "mission": [constants.MISSION],
            "constellation": [constants.CONSTELLATION],
            "platform": constants.PLATFORMS,
            "instruments": constants.INSTRUMENTS,
            "gsd": [constants.RESOLUTION],
            "processing:level": [constants.PROCESSING_LEVEL],
            "goes:image-type": [constants.GOES_IMAGE_TYPE],
            "goes:orbital-slot": [e.value for e in constants.OrbitalSlot],
        }
    )

    collection = Collection(
        stac_extensions=[
            # todo: add extension again once released
            # constants.GOES_EXTENSION,
            constants.PROCESSING_EXTENSION,
        ],
        id=id,
        title=constants.TITLE,
        description=constants.DESCRIPTION,
        keywords=keywords,
        license="proprietary",
        providers=constants.PROVIDERS,
        extent=extent,
        summaries=summaries,
        catalog_type=CatalogType.RELATIVE_PUBLISHED,
    )

    collection.add_link(Link(target=license, rel=RelType.LICENSE, title="License"))
    collection.add_link(constants.LINK_LANDING_PAGE)
    collection.add_link(constants.LINK_USER_GUIDE_MAIN)
    collection.add_link(constants.LINK_USER_GUIDE_L2_PRODUCTS)

    sci_ext = ScientificExtension.ext(collection, add_if_missing=True)
    sci_ext.doi = constants.DOI
    sci_ext.citation = constants.CITATION

    if len(thumbnail) > 0:
        if thumbnail.endswith(".png"):
            media_type = MediaType.PNG
        else:
            media_type = MediaType.JPEG

        collection.add_asset(
            "thumbnail",
            Asset(
                href=thumbnail,
                title="Preview",
                roles=["thumbnail"],
                media_type=media_type,
            ),
        )

    item_assets = {}

    if not nogeoparquet:
        TableExtension.ext(collection, add_if_missing=True)
        item_assets[constants.PARQUET_KEY_EVENTS] = AssetDefinition(
            parquet.create_asset_metadata(constants.PARQUET_TITLE_EVENTS)
        )
        item_assets[constants.PARQUET_KEY_FLASHES] = AssetDefinition(
            parquet.create_asset_metadata(constants.PARQUET_TITLE_FLASHES)
        )
        item_assets[constants.PARQUET_KEY_GROUPS] = AssetDefinition(
            parquet.create_asset_metadata(constants.PARQUET_TITLE_GROUPS)
        )

    if not nonetcdf:
        asset = create_netcdf_asset_metadata()
        item_assets[constants.NETCDF_KEY] = AssetDefinition(asset)

    item_assets_attrs = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets_attrs.item_assets = item_assets

    return collection


def create_item(
    asset_href: str,
    collection: Optional[Collection] = None,
    nogeoparquet: bool = False,
    nonetcdf: bool = False,
) -> Item:
    """Create a STAC Item

    This function should include logic to extract all relevant metadata from an
    asset, metadata asset, and/or a constants.py file.

    See `Item<https://pystac.readthedocs.io/en/latest/api.html#item>`_.

    Args:
        asset_href (str): The HREF pointing to an asset associated with the item
        collection (pystac.Collection): HREF to an existing collection
        nogeoparquet (bool): If set to True, no geoparquet file is generated for the Item
        nonetcdf (bool): If set to True, the netCDF file is not added to the Item

    Returns:
        Item: STAC Item object
    """

    dataset = Dataset(asset_href, "r", format="NETCDF4")

    id = dataset.dataset_name.replace(".nc", "")
    sys_env = id[:2]
    if sys_env != "OR":
        logger.warning("You are ingesting test data.")

    bbox = constants.BBOXES[0]
    geometry = bbox_to_polygon(bbox)  # todo: check whether this makes sense

    properties = {
        "start_datetime": dataset.time_coverage_start,
        "end_datetime": dataset.time_coverage_end,
        "mission": constants.MISSION,
        "constellation": constants.CONSTELLATION,
        "platform": constants.Platforms[dataset.platform_ID],
        "instruments": [dataset.instrument_ID],
        "gsd": constants.RESOLUTION,
        "processing:level": constants.PROCESSING_LEVEL,
        "processing:facility": dataset.production_site,
        "goes:orbital-slot": constants.OrbitalSlot[
            dataset.orbital_slot.replace("-", "_")
        ],
        "goes:system-environment": sys_env,
        "goes:image-type": constants.GOES_IMAGE_TYPE,
    }

    for key, var in dataset.variables.items():
        if len(var.dimensions) != 0:
            continue

        ma = var[...]
        if ma.count() > 0:
            properties[f"goes-glm:{var.name}"] = ma.tolist()

    item = Item(
        stac_extensions=[
            # todo: add extension again once released
            # constants.GOES_EXTENSION,
            constants.PROCESSING_EXTENSION,
        ],
        id=id,
        properties=properties,
        geometry=geometry,
        bbox=bbox,
        datetime=center_datetime(
            dataset.time_coverage_start, dataset.time_coverage_end
        ),
        collection=collection,
    )

    proj = ProjectionExtension.ext(item, add_if_missing=True)
    proj.epsg = constants.TARGET_CRS

    if not nogeoparquet:
        target_folder = os.path.dirname(asset_href)
        assets = parquet.convert(dataset, target_folder)
        for key, asset_dict in assets.items():
            asset = Asset.from_dict(asset_dict)
            item.add_asset(key, asset)

            TableExtension.ext(asset, add_if_missing=True)

    if not nonetcdf:
        asset_dict = create_netcdf_asset_metadata(asset_href)

        asset_dict["created"] = dataset.date_created

        asset_dict["cube:dimensions"] = {}
        for key, dim in dataset.dimensions.items():
            stac_dim = {"type": dim.name, "extent": [None, None]}
            if not dim.isunlimited():
                dim_vars = [
                    var
                    for var in dataset.variables.values()
                    if dim.name in var.dimensions
                ]
                if len(dim_vars) == 1:
                    data = np.asarray(dim_vars).tolist()
                    stac_dim["extent"] = data[0]
                elif len(dim_vars) > 1:
                    flat = np.asarray(dim_vars).flatten().tolist()
                    stac_dim["extent"] = [min(flat), max(flat)]

            asset_dict["cube:dimensions"][dim.name] = stac_dim

        asset_dict["cube:variables"] = {}
        for key, var in dataset.variables.items():
            attrs = var.ncattrs()
            stac_var = {
                "dimensions": var.dimensions,
                "type": VariableType.DATA
                if "standard_name" in attrs and len(var.dimensions) > 0
                else VariableType.AUXILIARY,
            }
            if "long_name" in attrs:

                stac_var["description"] = var.getncattr("long_name").replace(
                    "GLM L2+ Lightning Detection: ", ""
                )
            if "units" in attrs:
                unit = var.getncattr("units")
                if unit == "percent":
                    stac_var["unit"] = "%"
                elif unit == "percent":
                    stac_var["unit"] = "%"
                elif unit != "1" and unit != "count":
                    stac_var["unit"] = unit
            # not defined in the datacube extension, but might be useful
            if "axis" in attrs:
                stac_var["axis"] = var.getncattr("axis")
            asset_dict["cube:variables"][var.name] = stac_var

        asset = Asset.from_dict(asset_dict)
        item.add_asset(constants.NETCDF_KEY, asset)

        DatacubeExtension.ext(asset, add_if_missing=True)

        """
        dc = DatacubeExtension.ext(asset, add_if_missing=True)
        for key, dim in dataset.dimensions.items():
            dc.dimensions[dim.name] = AdditionalDimension(stac_dim)
        for key, var in dataset.variables.items():
            dc.variables[var.name] = Variable(stac_var)
        """

    return item


def create_netcdf_asset_metadata(href: Optional[str] = None) -> Dict[str, Any]:
    asset: Dict[str, Any] = {
        "title": constants.NETCDF_TITLE,
        "type": constants.NETCDF_MEDIA_TYPE,
        "roles": constants.NETCDF_ROLES,
    }
    if href is not None:
        asset["href"] = href
    return asset


def bbox_to_polygon(b: List[float]) -> Dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [
            [[b[0], b[3]], [b[2], b[3]], [b[2], b[1]], [b[0], b[1]], [b[0], b[3]]]
        ],
    }


def center_datetime(start: str, end: str) -> datetime:
    a: datetime = isoparse(start)
    b: datetime = isoparse(end)
    return a + (b - a) / 2
