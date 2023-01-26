import enum

from pystac import Link, Provider, ProviderRole

# A lot of information has been collected from:
# https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C01527

# Collection
TITLE = "GLM L2 Lightning Detections: Events, Groups, and Flashes"
DESCRIPTION = (
    "The Lightning Detections: Events, Groups, and Flashes product consists"
    " of a hierarchy of earth-located lightning radiant energy measures including events,"
    " groups, and flashes. Lightning events are detected by the instrument. Lightning groups"
    " are a collection of one or more lightning events that satisfy temporal and spatial"
    " coincidence thresholds. Similarly, lightning flashes are a collection of one or more"
    " lightning groups that satisfy temporal and spatial coincidence thresholds. The product"
    " includes the relationship among lightning events, groups, and flashes, and the area"
    " coverage of lightning groups and flashes. The product also includes processing and"
    " data quality metadata, and satellite state and location information."
)
PROVIDERS = [
    Provider(
        name="DOC/NOAA/NESDIS",
        roles=[ProviderRole.PRODUCER, ProviderRole.LICENSOR],
        description=(
            "Provided by:\n\n"
            "* U.S. Department of Commerce\n"
            "* National Oceanic and Atmospheric Administration\n"
            "* National Environmental Satellite, Data, and Information Services"
        ),
        url="https://www.goes.noaa.gov",
    ),
]

LINK_LANDING_PAGE = Link(
    target="https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C01527",
    media_type="text/html",
    title="Product Landing Page",
    rel="about",
)
LINK_USER_GUIDE_MAIN = Link(
    target="https://www.goes-r.gov/users/docs/PUG-main-vol1.pdf",
    media_type="application/pdf",
    title="Product Definition and Users' Guide (PUG) Vol.1 Main",
    rel="about",
)
LINK_USER_GUIDE_L2_PRODUCTS = Link(
    target="https://www.goes-r.gov/products/docs/PUG-L2+-vol5.pdf",
    media_type="application/pdf",
    title="Product Definition and Users' Guide (PUG) Vol.5 Level 2+ Products",
    rel="about",
)

# Extensions
GOES_EXTENSION = "https://stac-extensions.github.io/goes/v1.0.0/schema.json"
PROCESSING_EXTENSION = "https://stac-extensions.github.io/processing/v1.1.0/schema.json"
DATACUBE_EXTENSION = "https://stac-extensions.github.io/datacube/v2.1.0/schema.json"

# Scientific
DOI = "10.7289/V5KH0KK6"
CITATION = (
    "GOES-R Algorithm Working Group and GOES-R Series Program, (2018): "
    "NOAA GOES-R Series Geostationary Lightning Mapper (GLM) Level 2 Lightning Detection: "
    "Events, Groups, and Flashes. [indicate subset used]."
    "NOAA National Centers for Environmental Information. doi:10.7289/V5KH0KK6. [access date]."
)

# Shared metadata
PROCESSING_LEVEL = "L2"
RESOLUTION = 8000
MISSION = "GOES"
CONSTELLATION = "GOES"
PLATFORM_R = "GOES-16"
PLATFORM_S = "GOES-17"
PLATFORM_T = "GOES-18"
PLATFORMS = [PLATFORM_R, PLATFORM_S, PLATFORM_T]
INSTRUMENTS = ["FM1", "FM2", "FM3"]


class Platforms(str, enum.Enum):
    G16 = PLATFORM_R
    G17 = PLATFORM_S
    G18 = PLATFORM_T


class OrbitalSlot(str, enum.Enum):
    GOES_West = "West"
    GOES_East = "East"
    GOES_Test = "Test"


# Assets
PARQUET_TITLE_FLASHES = "Processed GeoParquet file for flashes"
PARQUET_TITLE_GROUPS = "Processed GeoParquet file for groups"
PARQUET_TITLE_EVENTS = "Processed GeoParquet file for events"
PARQUET_KEY_FLASHES = "geoparquet_flashes"
PARQUET_KEY_GROUPS = "geoparquet_groups"
PARQUET_KEY_EVENTS = "geoparquet_events"
PARQUET_MEDIA_TYPE = "application/x-parquet"
PARQUET_ROLES = ["data", "cloud-optimized"]
PARQUET_GEOMETRY_COL = "geometry"
# todo: is this the correct data type? #11
PARQUET_DATETIME_COL_TYPE = "datetime"

IGNORED_UNITS = ["1", "count"]

NETCDF_TITLE = "Original netCDF 4 file"
NETCDF_MEDIA_TYPE = "application/netcdf"
NETCDF_ROLES = ["data", "source"]
NETCDF_KEY = "netcdf"

# Source file attributes
SOURCE_CRS = "EPSG:4326"
TARGET_CRS = 4326

# Bounding boxes and geometries - note: west crosses the antimeridian!
ITEM_BBOX_WEST = [156.44, -66.56, -70.44, 66.56]
ITEM_BBOX_EAST = [-141.56, -66.56, -8.44, 66.56]
ITEM_BBOX_TEST = [-156.06, -66.56, -22.94, 66.56]
COLLECTION_BBOXES = [
    # Union
    [156.44, -66.56, -8.44, 66.56],
    # Split west into two parts as it crosses the antimeridian
    [156.44, -66.56, 180.0, 66.56],
    [-180.0, -66.56, -70.44, 66.56],
    # East
    ITEM_BBOX_EAST,
    # Test
    ITEM_BBOX_TEST,
]

# Split west into two polygons as propsoed by the GeoJSON spec as it crosses the antimeridian
GEOMETRY_WEST = {
    "type": "Polygon",
    "coordinates": [
        [
            [156.44, 66.56],
            [156.44, -66.56],
            [180, -66.56],
            [180, 66.56],
            [156.44, 66.56],
        ],
        [
            [-180, 66.56],
            [-180, -66.56],
            [-70.44, -66.56],
            [-70.44, 66.56],
            [-180, 66.56],
        ],
    ],
}
# East
GEOMETRY_EAST = {
    "type": "Polygon",
    "coordinates": [
        [
            [-141.56, 66.56],
            [-141.56, -66.56],
            [-8.44, -66.56],
            [-8.44, 66.56],
            [-141.56, 66.56],
        ]
    ],
}
# Test
GEOMETRY_TEST = {
    "type": "Polygon",
    "coordinates": [
        [
            [-156.06, 66.56],
            [-156.06, -66.56],
            [-22.94, -66.56],
            [-22.94, 66.56],
            [-156.06, 66.56],
        ]
    ],
}
