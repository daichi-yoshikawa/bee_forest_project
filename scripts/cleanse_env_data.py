import os
import logging

import numpy as np
import pandas as pd
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import polygonize, unary_union

from constants import *


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

env_filenames = ENV_FILENAMES

def correct_invalid_geometries(df):
  geoms = list(df['WKT'].values)
  geoms = [geom.lstrip('POLYGON ((').rstrip('))').split(',') for geom in geoms]

  x = dict()
  y = dict()
  for i, geom in enumerate(geoms):
    x[i] = []
    y[i] = []
    for vertex in geom:
      xy = vertex.split(' ')
      x[i].append(float(xy[0].lstrip('(').rstrip(')')))
      y[i].append(float(xy[1].lstrip('(').rstrip(')')))

  dst = []
  for geom_id, ((_, xs), (_, ys)) in enumerate(zip(x.items(), y.items())):
    geoms = [[x_, y_] for x_, y_ in zip(xs, ys)]
    polygon = Polygon(geoms)
    if polygon.is_valid:
      dst.append(polygon.wkt)
      continue

    ls = LineString(geoms)
    mls = unary_union(ls)
    for polygon in list(polygonize(mls)):
      dst.append(polygon.wkt)

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
