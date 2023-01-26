import logging
import math
import os
import re
from datetime import datetime, timezone
from typing import Optional

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
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.scientific import ScientificExtension
from pystac.extensions.table import TableExtension

from . import constants, netcdf, parquet

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
        SpatialExtent(constants.COLLECTION_BBOXES),
        TemporalExtent([[start_datetime, None]]),
    )

    keywords = [
        "NOAA",
        "GOES",
        "GOES-16",
        "GOES-17",
        "GOES-18",
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
            "goes:orbital_slot": [e.value for e in constants.OrbitalSlot],
        }
    )

    collection = Collection(
        stac_extensions=[
            constants.GOES_EXTENSION,
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

    if license is not None:
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
        asset = netcdf.create_asset()
        item_assets[constants.NETCDF_KEY] = AssetDefinition(asset)

    item_assets_attrs = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets_attrs.item_assets = item_assets

    return collection


def create_item(
    asset_href: str,
    collection: Optional[Collection] = None,
    nogeoparquet: bool = False,
    nonetcdf: bool = False,
    fixnetcdf: bool = False,
    appendctime: bool = False,
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
        fixnetcdf (bool): If set to True, fixes missing _Unsigned attributes in some of
            the older netCDF files
        appendctime (bool): Appends the creation time to the ID of the item if set to `TRUE`.

    Returns:
        Item: STAC Item object
    """

    with Dataset(asset_href, "a", format="NETCDF4") as dataset:
        id = dataset.dataset_name.replace(".nc", "")
        if not appendctime:
            id = re.sub(r"_c\d+$", "", id)
        sys_env = id[:2]
        if sys_env != "OR":
            logger.warning("You are ingesting test data.")

        var_count = len(dataset.variables)
        if var_count != 45 and var_count != 48:
            raise Exception(
                f"The number of variables is expected to be 45 or 48, but it is {var_count}"
            )

        # See page 14-15 for details:
        # https://www.noaasis.noaa.gov/pdf/ps-pvr/goes-16/GLM/Full/GOES16_GLM_FullValidation_ProductPerformanceGuide.pdf
        defect_vars = {
            "event_time_offset": False,
            "group_time_offset": False,
            "flash_time_offset_of_first_event": False,
            "flash_time_offset_of_last_event": False,
            "group_frame_time_offset": False,
            "flash_frame_time_offset_of_first_event": False,
            "flash_frame_time_offset_of_last_event": False,
        }
        for key in defect_vars:
            if key in dataset.variables:
                if not hasattr(dataset.variables[key], "_Unsigned"):
                    dataset.variables[key]._Unsigned = "true"
                    defect_vars[key] = True

        computed_datetime = center_datetime(
            dataset.time_coverage_start, dataset.time_coverage_end
        )

        try:
            platform = constants.Platforms[dataset.platform_ID]
        except ValueError:
            raise Exception(
                f"The dataset contains an invalid platform identifier: {dataset.platform_ID}"
            )

        try:
            slot_str = dataset.orbital_slot.replace("-", "_")
            slot = constants.OrbitalSlot[slot_str]
        except KeyError:
            raise Exception(
                f"The value for 'orbital_slot' is invalid: {dataset.orbital_slot}"
            )

        properties = {
            "start_datetime": dataset.time_coverage_start,
            "end_datetime": dataset.time_coverage_end,
            "mission": constants.MISSION,
            "constellation": constants.CONSTELLATION,
            "platform": platform,
            "instruments": [dataset.instrument_ID],
            "gsd": constants.RESOLUTION,
            "processing:level": constants.PROCESSING_LEVEL,
            "processing:facility": dataset.production_site,
            "goes:orbital_slot": slot,
            "goes:system_environment": sys_env,
        }

        if slot == constants.OrbitalSlot.GOES_East:
            bbox = constants.ITEM_BBOX_EAST
            geometry = constants.GEOMETRY_EAST
        elif slot == constants.OrbitalSlot.GOES_West:
            bbox = constants.ITEM_BBOX_WEST
            geometry = constants.GEOMETRY_WEST
        elif slot == constants.OrbitalSlot.GOES_Test:
            bbox = constants.ITEM_BBOX_TEST
            geometry = constants.GEOMETRY_TEST
        else:
            bbox = None
            geometry = None

        centroid = {}
        for key, var in dataset.variables.items():
            if len(var.dimensions) != 0 or var.name == "product_time":
                continue

            ma = var[...]
            if ma.count() == 1:
                val = ma.tolist()
                name = f"goes:{var.name}"
                if var.name == "lat_field_of_view":
                    centroid["lat"] = val
                elif var.name == "lon_field_of_view":
                    centroid["lon"] = val
                elif var.name.endswith("_count") or var.name == "yaw_flip_flag":
                    val = val
                    if val >= 0:
                        properties[name] = val
                elif var.name.startswith("nominal_") or var.name.startswith("percent_"):
                    val = val
                    if not math.isclose(val, -999.0):
                        properties[name] = val
                else:
                    properties[name] = val

        item = Item(
            stac_extensions=[
                constants.GOES_EXTENSION,
                constants.PROCESSING_EXTENSION,
            ],
            id=id,
            properties=properties,
            geometry=geometry,
            bbox=bbox,
            datetime=computed_datetime,
            collection=collection,
        )

        proj = ProjectionExtension.ext(item, add_if_missing=True)
        proj.epsg = constants.TARGET_CRS
        if len(centroid) == 2:
            proj.centroid = centroid

        if not nogeoparquet:
            target_folder = os.path.dirname(asset_href)
            assets = parquet.convert(dataset, target_folder)
            for key, asset_dict in assets.items():
                asset = Asset.from_dict(asset_dict)
                item.add_asset(key, asset)
                TableExtension.ext(asset, add_if_missing=True)

        if not nonetcdf:
            # todo: replace with DataCube extension from PySTAC #16
            item.stac_extensions.append(constants.DATACUBE_EXTENSION)
            asset_dict = netcdf.create_asset(asset_href)
            asset_dict["created"] = dataset.date_created
            asset_dict["cube:dimensions"] = netcdf.to_cube_dimensions(dataset)
            asset_dict["cube:variables"] = netcdf.to_cube_variables(dataset)
            asset = Asset.from_dict(asset_dict)
            item.add_asset(constants.NETCDF_KEY, asset)

        if not fixnetcdf:
            for key, is_defect in defect_vars.items():
                if is_defect:
                    del dataset.variables[key]._Unsigned

        return item


def center_datetime(start: str, end: str) -> datetime:
    """
    Takes the start and end datetime and computes the central datetime.

    Args:
        start (str): ISO 8601 compliant date-time (as string)
        end (str): ISO 8601 compliant date-time (as string)

    Returns:
        datetime: ISO 8601 compliant date-time (as datetime)
    """
    a: datetime = isoparse(start)
    b: datetime = isoparse(end)
    return a + (b - a) / 2
