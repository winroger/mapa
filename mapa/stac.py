import logging
from pathlib import Path
from typing import List, Union
from urllib import request

import geojson
from pystac.item import Item
from pystac_client import Client
import requests

import planetary_computer

from mapa import conf
from mapa.exceptions import NoSTACItemFound
from mapa.utils import ProgressBar

import datetime
import ssl

import certifi


log = logging.getLogger(__name__)


def _download_file(url: str, local_file: Path) -> Path:
    signed_url = planetary_computer.sign(url)
    request.urlretrieve(signed_url, local_file)
    return local_file

def _download_file_try2(url: str, local_file: Path) -> Path:
    log.info(f"Downloading from URL: {url}")
    response = requests.get(url)
    log.info(f"XXXXXXXXXXXXX")
    response.raise_for_status()  # Raise an error for bad status codes
    log.info(f"AAAAAAAAAAAAA")
    with open(local_file, 'wb') as f:
        f.write(response.content)
        log.info(f"BBBBBBBBBBBBBB")

    return local_file

def _download_file_fixed(url: str, local_file: Path) -> Path:
    context = ssl.create_default_context(cafile=certifi.where())
    signed_url = planetary_computer.sign(url)
    log.info(f"Downloading from URL: {url}")
    with request.urlopen(signed_url, context=context) as response, open(local_file, 'wb') as out_file:
        out_file.write(response.read())
    return local_file


def _bbox(coord_list):
    box = []
    for i in (0, 1):
        res = sorted(coord_list, key=lambda x: x[i])
        box.append((res[0][i], res[-1][i]))
    return [box[0][0], box[1][0], box[0][1], box[1][1]]


def _turn_geojson_into_bbox(geojson_bbox: dict) -> List[float]:
    coordinates = geojson_bbox["coordinates"]
    return _bbox(list(geojson.utils.coords(geojson.Polygon(coordinates))))


def _get_tiff_file(stac_item: Item, allow_caching: bool, cache_dir: Path, count: int, max: int) -> Path:
    log.info(f"----1.8.1-----") 
    tiff = cache_dir / f"{stac_item.id}.tiff"
    log.info(f"----1.8.2-----")
    if tiff.is_file() and allow_caching:
        log.info(f"----1.8.3-----")
        log.info(f"tiff: ", tiff)
        log.info(f"🚀  {count}/{max} using cached stac item {stac_item.id}")
        return tiff
    else:
        log.info(f"----1.8.4-----")
        log.info(f"🏞  {count}/{max} downloading stac item {stac_item.id}")
        return _download_file(stac_item.assets["data"].href, tiff)


def fetch_stac_items_for_bbox(
    geojson: dict, allow_caching: bool, cache_dir: Path, progress_bar: Union[None, ProgressBar] = None
) -> List[Path]:
    log.info(f"----1.6.1-----") 
    bbox = _turn_geojson_into_bbox(geojson)
    log.info(f"----1.6.2-----") 
    client = Client.open(conf.PLANETARY_COMPUTER_API_URL, ignore_conformance=True)
    log.info(f"----1.6.3-----") 
    search = client.search(collections=[conf.PLANETARY_COMPUTER_COLLECTION], bbox=bbox)
    log.info(f"----1.6.4-----") 
    items = list(search.items())
    log.info(f"----1.6.5-----") 
    n = len(items)

    if progress_bar:
        progress_bar.steps += n
    if n > 0:
        log.info(f"----1.6.6-----") 
        log.info(f"⬇️  fetching {n} stac items...")
        files = []
        log.info(f"----1.6.7-----") 
        for cnt, item in enumerate(items):
            files.append(_get_tiff_file(item, allow_caching, cache_dir, cnt + 1, n))
            if progress_bar:
                progress_bar.step()
        log.info(f"----1.6.8-----") 
        return files
    else:
        raise NoSTACItemFound("Could not find the desired STAC item for the given bounding box.")


def fetch_stac_items_for_bbox_custom(
    geojson: dict, allow_caching: bool, cache_dir: Path, progress_bar: Union[None, ProgressBar] = None
) -> List[Path]:
    bbox = _turn_geojson_into_bbox(geojson)
    #client = Client.open(conf.PLANETARY_COMPUTER_API_URL, ignore_conformance=True)
    #search = client.search(collections=[conf.PLANETARY_COMPUTER_COLLECTION], bbox=bbox)
    #items = list(search.items())
    items = generate_stac_items_custom(bbox)
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
                datetime=datetime.datetime.now(),
                properties={}
            )
            items.append(item)
    return items