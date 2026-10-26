import os

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

import matplotlib

from constants import *


hard_wood_ratios = {
  'Conifer': 0,
  'Farm': 0.5,
  'HardWood': 1.0,
  'MixedForest': 0.5,
  'Orchard': 1.0,
  'Park': 0.5,
  'Residential': 0.2,
}

def show_corr_matrix(df):
  cols = [
      'NestingRate', 'NestingBinary', 'GreenWOConiferAreaRate', 'ConiferAreaRate',
      'EstHardWoodAreaRate', 'FarmAreaRate', 'HardWoodAreaRate',
      'MixedForestAreaRate', 'OrchardAreaRate', 'ParkAreaRate',
      'ResidentialAreaRate', 'GreenSpaceAreaRate']
  corr = df.loc[:, cols].corr()
  sns.heatmap(corr, annot=True)
  plt.show()

def analysis(radius):
  df = pd.read_csv(os.path.join(
      DST_BEEHIVE_DATA_PATH, f'beehives_{radius}_w_area.csv'))

  # Drop invalid data row
  df = df.loc[df['BeeForest-No'] != 14, :]

  df['EstHardWoodArea'] = 0
  for env_type, ratio in hard_wood_ratios.items():
    area_col = env_type + 'Area'
    isnull = df[area_col].isnull()
    df.loc[isnull, area_col] = 0

    if area_col not in df:
      raise RuntimeError(f'{area_col} not found.')
    df['EstHardWoodArea'] += df[area_col] * ratio
    df[area_col + 'Rate'] = df[area_col] / df['Area']
  df['EstHardWoodAreaRate'] = df['EstHardWoodArea'] / df['Area']

  df['GreenWOConiferArea'] = 0
  for col in ['FarmArea', 'HardWoodArea', 'MixedForestArea', 'OrchardArea',
              'ParkArea', 'ResidentialArea']:
    df['GreenWOConiferArea'] += df[col]
  df['GreenWOConiferAreaRate'] = df['GreenWOConiferArea'] / df['Area']
  df['GreenSpaceAreaRate'] = df['GreenSpaceArea'] / df['Area']
  df['NestingBinary'] = df['NestingRate'] > 0

  df.to_csv(os.path.join(OUTPUT_PATH, f'area_rates_{radius}.csv'), index=False)
  show_corr_matrix(df)

for radius in [500, 1000, 2000]:
  analysis(radius=radius)
