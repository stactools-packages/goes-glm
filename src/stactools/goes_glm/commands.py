import logging
from typing import Optional

import click
from click import Command, Group
from pystac import Collection

from stactools.goes_glm import stac

logger = logging.getLogger(__name__)


def create_goesglm_command(cli: Group) -> Command:
    """Creates the stactools-goes-glm command line utility."""

    @cli.group(
        "goes-glm",
        short_help=("Commands for working with stactools-goes-glm"),
    )
    def goesglm() -> None:
        pass

    @goesglm.command(
        "create-collection",
        short_help="Creates a STAC collection",
    )
    @click.argument("destination")
    @click.option(
        "--license",
        help="URL or path to the license file",
    )
    @click.option(
        "--id",
        default="goes-glm",
        help="A custom collection ID, defaults to 'goes-glm'",
    )
    @click.option(
        "--thumbnail",
        default="",
        help="URL for the PNG or JPEG collection thumbnail asset (none if empty)",
    )
    @click.option(
        "--nogeoparquet",
        default=False,
        help="Does not include the geoparquet-related metadata in the collection if set to `TRUE`.",
    )
    @click.option(
        "--nonetcdf",
        default=False,
        help="Does not include the netCDF-related metadata in the collection if set to `TRUE`.",
    )
    @click.option(
        "--start_time",
        default=None,
        help="The start timestamp for the temporal extent, defaults to now. "
        "Timestamps consist of a date and time in UTC and must be follow RFC 3339, section 5.6.",
    )
    def create_collection_command(
        destination: str,
        license: str,
        id: str = "",
        thumbnail: str = "",
        nogeoparquet: bool = False,
        nonetcdf: bool = False,
        start_time: Optional[str] = None,
    ) -> None:
        """Creates a STAC Collection

        Args:
            destination (str): An HREF for the Collection JSON
        """
        collection = stac.create_collection(
            license, id, thumbnail, nogeoparquet, nonetcdf, start_time
        )
        collection.set_self_href(destination)
        collection.save_object()

        return None

    @goesglm.command("create-item", short_help="Create a STAC item")
    @click.argument("source")
    @click.argument("destination")
    @click.option(
        "--collection",
        default="",
        help="An HREF to the Collection JSON. "
        "This adds the collection details to the item, but doesn't add the item to the collection.",
    )
    @click.option(
        "--nogeoparquet",
        default=False,
        help="Does not create geoparquet files for the given netCDF file if set to `TRUE`.",
    )
    @click.option(
        "--nonetcdf",
        default=False,
        help="Does not include the netCDF file in the created metadata if set to `TRUE`.",
    )
    @click.option(
        "--fixnetcdf",
        default=False,
        help="Fixes missing _Unsigned attributes in some older netCDF files if set to `TRUE`.",
    )
    @click.option(
        "--appendctime",
        default=False,
        help="Appends the creation time to the ID of the item if set to `TRUE`.",
    )
    def create_item_command(
        source: str,
        destination: str,
        collection: str = "",
        nogeoparquet: bool = False,
        nonetcdf: bool = False,
        fixnetcdf: bool = False,
        appendctime: bool = False,
    ) -> None:
        """Creates a STAC Item

        Args:
            source (str): HREF of the Asset associated with the Item
            destination (str): An HREF for the STAC Item
        """
        stac_collection = None
        if len(collection) > 0:
            stac_collection = Collection.from_file(collection)

        item = stac.create_item(
            source, stac_collection, nogeoparquet, nonetcdf, fixnetcdf, appendctime
        )
        item.save_object(dest_href=destination)

        return None

    return goesglm
