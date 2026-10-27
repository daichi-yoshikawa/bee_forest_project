import geopandas as gpd
from pyproj import Geod, Transformer
from shapely import orient_polygons, transform

from constants import (
  NEST_DATA_DIR,
  NEST_FILENAME_TEMPLATE,
  ENV_DATA_DIR,
  AREA_OUTPUT_DIR as OUTPUT_DIR,
)


RADIUSES = (500, 1000, 2000)

ENV_NAMES = (
  'ユニオン緑地',
  '住宅緑地',
  '公園',
  '広葉樹',
  '果樹園',
  '混合林',
  '畑',
  '針葉樹・竹',
  '針葉樹・竹以外',
)

GEOD = Geod(ellps='WGS84')


def read_polygon_data(path):
  data = gpd.read_file(path, engine='pyogrio')

  if data.empty:
    raise ValueError(f'Empty data: {path}')
  if data.crs is None:
    raise ValueError(f'CRS is not configured: {path}')
  if data.geometry.isna().any() or data.geometry.is_empty.any():
    raise ValueError(f'Found broken or empty geometry: {path}')
  if not data.geometry.is_valid.all():
    raise ValueError(f'Found invalid geometry: {path}')
  if not data.geom_type.isin(('Polygon', 'MultiPolygon')).all():
    raise ValueError(f'Found unsupported geometry type: {path}')

  return data


def load_environment_geometries(target_crs):
  environments = {}

  for name in ENV_NAMES:
    path = ENV_DATA_DIR / f'{name}.gpkg'
    data = read_polygon_data(path).to_crs(target_crs)

    # Remove potential overlaps within each data to avoid double-counting intersection areas.
    geometry = data.geometry.union_all()

    if geometry.is_empty or not geometry.is_valid:
      raise ValueError(f'Union geometry is empty or invalid: {path}')

    environments[name] = geometry

  return environments


def calculate_area(geometry, transformer):
  if geometry.is_empty:
    return 0.0

  if geometry.geom_type == 'GeometryCollection':
    return sum(calculate_area(part, transformer) for part in geometry.geoms)

  # Boundary-only intersections have zero area.
  if geometry.geom_type not in ('Polygon', 'MultiPolygon'):
    return 0.0

  lonlat_geometry = transform(geometry, transformer.transform, interleaved=False)

  # Geodesic area calculation requires opposite ring orientations for holes.
  oriented_geometry = orient_polygons(lonlat_geometry)
  area, _ = GEOD.geometry_area_perimeter(oriented_geometry)
  return abs(area)


def calculate_nest_environment_intersection_areas(radius):
  path = NEST_DATA_DIR / NEST_FILENAME_TEMPLATE.format(radius=radius)
  regions = read_polygon_data(path)

  # Geod requires lon/lat to calculate ellipsoidal area in m^2.
  # This transformer is used only for area measurement; intersections use the input CRS.
  transformer = Transformer.from_crs(regions.crs, 'EPSG:4326', always_xy=True)

  regions['面積[m^2]'] = [calculate_area(geom, transformer) for geom in regions.geometry]

  if (regions['面積[m^2]'] <= 0).any():
    raise ValueError(f'Region area must be positive: {path}')

  environments = load_environment_geometries(regions.crs)

  for name, environment in environments.items():
    intersections = regions.geometry.intersection(environment)

    areas = [calculate_area(geom, transformer) for geom in intersections]

    regions[f'{name}面積[m^2]'] = areas
    regions[f'{name}面積率'] = regions[f'{name}面積[m^2]'] / regions['面積[m^2]']

    # Allow a small numerical tolerance around the upper bound.
    ratios = regions[f'{name}面積率']
    invalid = ~ratios.between(0, 1 + 1e-6)

    if invalid.any():
      ids = regions.index[invalid].to_list()
      raise ValueError(
        f'Invalid area ratio: radius={radius}, category={name}, row_indices={ids}'
      )

  output = regions.drop(columns=regions.geometry.name).copy()
  output['WKT'] = regions.geometry.to_wkt(rounding_precision=-1)
  output['CRS'] = regions.crs.to_string()

  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
  output_path = OUTPUT_DIR / f'奈良2021地域別環境面積{radius}m.csv'
  # Include a UTF-8 BOM so Excel can automatically recognize the encoding.
  output.to_csv(output_path, index=False, encoding='utf-8-sig')
  print(f'Saved: {output_path} ({len(output)} regions)')

  gpkg_path = output_path.with_suffix('.gpkg')
  regions.to_file(
    gpkg_path,
    layer=f'地域別環境面積{radius}m',
    driver='GPKG',
    engine='pyogrio',
    index=False,
  )
  print(f'Saved: {gpkg_path} ({len(regions)} regions)')


if __name__ == '__main__':
  for radius in RADIUSES:
    calculate_nest_environment_intersection_areas(radius)
