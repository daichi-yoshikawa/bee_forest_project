import os
import logging

import fiona
import geopandas as gpd
import fiona.crs as crs
from shapely.geometry import mapping, shape
from shapely.geometry import Polygon

from constants import *


logging.basicConfig(level=logging.INFO)

radiuses = [500, 1000, 2000]

for radius in radiuses:
  src_path = os.path.join(SRC_BEEHIVE_DATA_PATH, 'beehives.gpkg')
  src = fiona.open(src_path)
  schema = src.schema
  schema['geometry'] = 'Polygon'

  dst_path = os.path.join(DST_BEEHIVE_DATA_PATH, f'beehives_{radius}.gpkg')
  dst = fiona.open(dst_path, 'w', driver='GPKG', schema=src.schema)

  for feat in src:
    dst.write({
        'properties': feat['properties'],
        'geometry': mapping(shape(feat['geometry']).buffer(radius))
    })
