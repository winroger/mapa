from pystac import Item
from datetime import datetime
from mapa import convert_bbox_to_stl

"""
example output: ALPSMLC30_N051E013_DSM.tiff  ALPSMLC30_N067E012_DSM.tiff
ALPSMLC30_N035W114_DSM.tiff  ALPSMLC30_N043E007_DSM.tiff  ALPSMLC30_N051E014_DSM.tiff  ALPSMLC30_N067E013_DSM.tiff
ALPSMLC30_N035W116_DSM.tiff  ALPSMLC30_N043E008_DSM.tiff  ALPSMLC30_N051E015_DSM.tiff  ALPSMLC30_N067E014_DSM.tiff
ALPSMLC30_N035W118_DSM.tiff  ALPSMLC30_N043E009_DSM.tiff  ALPSMLC30_N051W010_DSM.tiff  ALPSMLC30_N067E015_DSM.tif



the input item need to be generated in order to skip the Client request. The item needs an id and the ID is e.g. ALPSMLC30_N067E015_DSM (without tiff)
the id needs to be generated from the coordinates bbox, so it might have 2 items, such as ALPSMLC30_N047W123_DSM and ALPSMLC30_N047W122_DSM
for this input: bbox = [-122.2751, 47.5469, -121.9613, 47.7458].


current code:
def _get_tiff_file(stac_item: Item, allow_caching: bool, cache_dir: Path, count: int, max: int) -> Path:
    tiff = cache_dir / f"{stac_item.id}.tiff"
    if tiff.is_file() and allow_caching:
        log.info(f"🚀  {count}/{max} using cached stac item {stac_item.id}")
        return tiff
    else:
        log.info(f"🏞  {count}/{max} downloading stac item {stac_item.id}")
        return _download_file(stac_item.assets["data"].href, tiff)


def fetch_stac_items_for_bbox(
    geojson: dict, allow_caching: bool, cache_dir: Path, progress_bar: Union[None, ProgressBar] = None
) -> List[Path]:
    bbox = _turn_geojson_into_bbox(geojson)
    client = Client.open(conf.PLANETARY_COMPUTER_API_URL, ignore_conformance=True)
    search = client.search(collections=[conf.PLANETARY_COMPUTER_COLLECTION], bbox=bbox)
    items = list(search.items())
    n = len(items)
    if progress_bar:
        progress_bar.steps += n
    if n > 0:
        log.info(f"⬇️  fetching {n} stac items...")
        files = []
        for cnt, item in enumerate(items):
            files.append(_get_tiff_file(item, allow_caching, cache_dir, cnt + 1, n))
            if progress_bar:
                progress_bar.step()
        return files
    else:
        raise NoSTACItemFound("Could not find the desired STAC item for the given bounding box.")

"""


def generate_stac_items_custom(bbox: list[float]) -> list[Item]:
    min_lon, min_lat, max_lon, max_lat = bbox
    items = []
    for lon in range(int(min_lon), int(max_lon) + 1):
        for lat in range(int(min_lat), int(max_lat) + 1):
            lon_prefix = 'E' if lon >= 0 else 'W'
            lat_prefix = 'N' if lat >= 0 else 'S'
            item_id = f"ALPSMLC30_{lat_prefix}{abs(lat):03d}{lon_prefix}{abs(lon):03d}_DSM"
            item = Item(
                id=item_id,
                geometry=None,
                bbox=bbox,
                datetime=datetime.utcnow(),
                properties={}
            )
            items.append(item)
    return items
"""
# Example usage
bbox = [-122.2751, 47.5469, -121.9613, 47.7458]
stac_items = generate_stac_items(bbox)
for item in stac_items:
    print(item)
"""



convert_bbox_to_stl(
            bbox_geometry=bbox,
            output_file="",  # There was error in the older version on deployment with wrong paths
            model_size=100,
            z_offset=0,  # Offset on bottom
            z_scale=1,
            max_res=False,
            compress=False,
            allow_caching=True,
            cache_dir="/tmp"
        )