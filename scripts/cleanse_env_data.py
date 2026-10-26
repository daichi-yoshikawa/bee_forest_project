import os
import logging

import numpy as np
import pandas as pd
from shapely import from_wkt, make_valid

from constants import *


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

env_filenames = ENV_FILENAMES


def polygon_parts(geom):
  if geom.is_empty:
    return
  if geom.geom_type == 'Polygon':
    yield geom
  elif geom.geom_type in ('MultiPolygon', 'GeometryCollection'):
    for part in geom.geoms:
      yield from polygon_parts(part)


def correct_invalid_geometries(df):
  geoms = [from_wkt(wkt) for wkt in df['WKT'].values]

  dst = []
  for polygon in geoms:
    if polygon.is_valid:
      dst.append(polygon.wkt)
      continue

    repaired = make_valid(polygon)
    for part in polygon_parts(repaired):
      dst.append(part.wkt)

  print(f'len(dst): {len(dst)}')
  return dst


for env_fn in env_filenames:
  df = pd.read_csv(os.path.join(RAW_ENV_DATA_PATH, env_fn + '.csv'))
  print(f'n_data(raw): {df.shape[0]}')
  cond_valid_geometry = df['WKT'] != 'POLYGON EMPTY'
  print(f'n_empty geometries: {(~cond_valid_geometry).sum()}')
  cleansed_df = df.loc[cond_valid_geometry, :]
  print(f'n_data(cleansed): {cleansed_df.shape[0]}')
  geoms = correct_invalid_geometries(cleansed_df)

  dst_df = pd.DataFrame(columns=['fid', 'WKT'], data=np.array([np.arange(len(geoms)) + 1, np.array(geoms)]).T)
  dst_df.to_csv(os.path.join(
      CLEANSED_ENV_DATA_PATH, env_fn + '.csv'), index=False)
  print(df.shape, dst_df.shape, cleansed_df.shape)

  print('='*77)
