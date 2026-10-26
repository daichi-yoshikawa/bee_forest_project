import os

import numpy as np
import pandas as pd
from scipy import stats

SRC_DATA_PATH = '../data/最終アウトプット/csv'
DST_DATA_PATH = '../data/最終アウトプット/csv_dst'
COLUMNS = (
  '針葉樹・竹', '混合林', '広葉樹', '果樹園', '畑', 'ユニオン緑地',
  '公園', '住宅緑地', '針葉樹以外')
FILE_NAMES = (
  '奈良2021巣箱500mユニオン.csv', '奈良2021巣箱1000mユニオン.csv',
  '奈良2021巣箱2000mユニオン.csv',)
DST_FILE_NAMES = (
  '奈良2021巣箱500m営巣率相関.csv', '奈良2021巣箱1000m営巣率相関.csv',
  '奈良2021巣箱2000m営巣率相関.csv',)

for file_name, dst_file_name in zip(FILE_NAMES, DST_FILE_NAMES):
  path = os.path.join(SRC_DATA_PATH, file_name)
  df = pd.read_csv(path)

  for col in COLUMNS:
    df[col + '率'] = df[col + '面積'] / df['面積']
  df['疑似自然率'] = (df['針葉樹以外面積'] - df['針葉樹・竹面積']) / df['面積']

  df['営巣有無'] = (df['営巣率'] > 0).astype(int)
  del df['WKT']
  df.to_csv(os.path.join(DST_DATA_PATH, file_name))

  cols = [col + '率' for col in COLUMNS]
  cols.append('疑似自然率')
  corrs1 = []
  ps1 = []
  for x_col in cols:
    x, y = df[x_col], df['営巣率']
    ret = stats.pearsonr(x, y)
    corrs1.append(ret[0])
    ps1.append(ret[1])

  corrs2 = []
  ps2 = []
  for x_col in cols:
    x, y = df[x_col], df['営巣有無']
    ret = stats.pearsonr(x, y)
    corrs2. append(ret[0])
    ps2.append(ret[1])

  dst_df = pd.DataFrame(
      columns=['環境', '営巣率との相関係数', 'p値', '営巣有無との相関係数', 'p値'],
      data=np.array([cols, corrs1, ps1, corrs2, ps2]).T)
  dst_df.to_csv(os.path.join(DST_DATA_PATH, dst_file_name))
