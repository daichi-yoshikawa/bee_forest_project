import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import pearsonr


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / 'data' / '最終アウトプット_修正版'
OUTPUT_DIR = INPUT_DIR / '相関解析'

RADIUSES = (500, 1000, 2000)

ENVIRONMENT_COLUMNS = (
  '針葉樹・竹面積率',
  '混合林面積率',
  '広葉樹面積率',
  '果樹園面積率',
  '畑面積率',
  '公園面積率',
  '住宅緑地面積率',
  'ユニオン緑地面積率',
  '針葉樹・竹以外面積率',
  '疑似自然率',
)


def load_correlation_data(radius):
  path = INPUT_DIR / f'奈良2021地域別環境面積{radius}m.csv'
  data = pd.read_csv(path, encoding='utf-8-sig')

  data['営巣有無'] = (data['営巣数'] > 0).astype(int)
  data['疑似自然率'] = data['針葉樹・竹以外面積率'] - data['針葉樹・竹面積率']

  return data


def calculate_correlation(x, y):
  x = x.to_numpy(dtype=float)
  y = y.to_numpy(dtype=float)

  if len(x) != len(y) or len(x) < 2:
    raise ValueError(f'At least two paired observations are required.')
  if not np.isfinite(x).all() or not np.isfinite(y).all():
    raise ValueError('Correlation inputs contain missing or infinite values.')
  if np.all(x == x[0]) or np.all(y == y[0]):
    raise ValueError('Correlation is undefined for constant values.')

  return pearsonr(x, y, alternative='two-sided')


def calculate_correlations(data):
  rows = []

  for column in ENVIRONMENT_COLUMNS:
    rate_result = calculate_correlation(data[column], data['営巣率'])
    presence_result = calculate_correlation(data[column], data['営巣有無'])

    rows.append({
      '環境': column,
      '地域数': len(data),
      '営巣率との相関係数': rate_result.statistic,
      '営巣率とのp値': rate_result.pvalue,
      '営巣有無との相関係数': presence_result.statistic,
      '営巣有無とのp値': presence_result.pvalue,
    })

  return pd.DataFrame(rows)


if __name__ == '__main__':
  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

  for radius in RADIUSES:
    data = load_correlation_data(radius)
    correlations = calculate_correlations(data)

    path = OUTPUT_DIR / f'奈良2021地域別営巣相関{radius}m.csv'

    # Include a UTF-8 BOM so Excel can automatically recognize the encoding.
    correlations.to_csv(path, index=False, encoding='utf-8-sig')
    print(f'Saved: {path} ({len(data)} regions)')
