from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# False: aggregate by address. True: merge overlapping geographic regions.
USE_GEOGRAPHIC_MERGE = False

ENV_DATA_DIR = PROJECT_ROOT / 'data' / '環境ジオデータ_修正版'

if USE_GEOGRAPHIC_MERGE:
  NEST_DATA_DIR = PROJECT_ROOT / 'data' / '巣箱ジオデータ'
  NEST_FILENAME_TEMPLATE = '奈良2021巣箱{radius}m地理統合_統合結果.gpkg'
  RESULT_DIR_NAME = '地理統合結果'
else:
  NEST_DATA_DIR = PROJECT_ROOT / 'data' / '巣箱ジオデータ' / 'joined'
  NEST_FILENAME_TEMPLATE = '奈良2021巣箱{radius}mユニオン.gpkg'
  RESULT_DIR_NAME = '住所統合結果'

AREA_OUTPUT_DIR = (
  PROJECT_ROOT / 'data' / '最終アウトプット_修正版' / RESULT_DIR_NAME
)
CORRELATION_OUTPUT_DIR = AREA_OUTPUT_DIR / '相関解析'
