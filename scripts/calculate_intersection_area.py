import os
import logging

import fiona
import geopandas as gpd
import fiona.crs as crs
from shapely.geometry import mapping, shape
from shapely.geometry import Polygon

from constants import *


logging.basicConfig(level=logging.INFO)

env_filenames = ENV_FILENAMES
env_filenames.pop(env_filenames.index('green_space'))
env_filenames.append('union_green_space')

radiuses = [500, 1000, 2000]


for radius in radiuses:
  src_path = os.path.join(DST_BEEHIVE_DATA_PATH, f'beehives_{radius}.gpkg')
  src = fiona.open(src_path)
  schema = src.schema

  schema['geometry'] = 'Polygon'
  dst_path = os.path.join(DST_BEEHIVE_DATA_PATH, 'beehives_{radius}_w_area.gpkg')
  dst = fiona.open(dst_path, 'w', driver='GPKG', schema=src.schema)

for feat in src:
  dst.write({
      'properties': feat['properties'],
      'geometry': mapping(shape(feat['geometry']).buffer(500.0))
  })

#layername = fiona.listlayers(path)[0]
#gdf = gpd.GeoDataFrame.from_features([feat for feat in src], crs=crs.from_epsg(3857))

#feats = gpd.read_file(path)
#feats = feats.buffer(500)
