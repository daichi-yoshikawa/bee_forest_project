import os

import numpy as np
import pandas as pd
from scipy import stats

from constants import *


def calculate_correlation(radius):
  df = pd.read_csv(os.path.join(OUTPUT_PATH, f'area_rates_{radius}.csv'))
  cols = [
      'GreenWOConiferAreaRate', 'ConiferAreaRate',
      'EstHardWoodAreaRate', 'FarmAreaRate', 'HardWoodAreaRate',
      'MixedForestAreaRate', 'OrchardAreaRate', 'ParkAreaRate',
      'ResidentialAreaRate', 'GreenSpaceAreaRate',]
  corrs1 = []
  ps1 = []
  for x_col in cols:
    x, y = df[x_col], df['NestingRate']
    ret = stats.pearsonr(x, y)
    corrs1.append(ret[0])
    ps1.append(ret[1])

  corrs2 = []
  ps2 = []
  for x_col in cols:
    x, y = df[x_col], df['NestingBinary']
    ret = stats.pearsonr(x, y)
    corrs2.append(ret[0])
    ps2.append(ret[1])

  new_df = pd.DataFrame(
      columns=['X', '営巣率との相関係数', 'p値', '営巣有無との相関係数', 'p値'],
      data=np.array([cols, corrs1, ps1, corrs2, ps2]).T)
  print(new_df)
  new_df.to_csv(os.path.join(OUTPUT_PATH, f'correlation_{radius}.csv'))

for radius in [500, 1000, 2000]:
  calculate_correlation(radius=radius)
