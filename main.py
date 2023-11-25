#%%
"""
For each building in this dataset we include 
- the polygon describing its footprint on the ground
- a confidence score indicating how sure we are that this is a building
- a Plus Code corresponding to the centre of the building. 
There is no information about the type of building, its street address, or any details other than its geometry.

-------- DATA FORMAT --------
I) Building polygons and points
The dataset consists of 3 parts: building polygons, building points and score thresholds.
Each row in the CSV represents one building polygon or point and has the following columns:

latitude: latitude of the building polygon centroid,
longitude: longitude of the building polygon centroid,
area_in_meters: area in square meters of the polygon,
confidence: confidence score [0.65;1.0] assigned by the model,
geometry: the building polygon in the WKT format (POLYGON or MULTIPOLYGON). This feature is present in only in polygons data,
full_plus_code: the full Plus Code at the building polygon centroid,

II) Score thresholds

s2_token: S2 cell token of the bucket,
geometry: geometry in the WKT format of the S2 cell bucket,
confidence_threshold_80%_precision, confidence_threshold_85%_precision, confidence_threshold_90%_precision: estimated confidence score threshold to get specific precision for building polygons in this S2 cell bucket,
building_count_80%_precision, building_count_85%_precision, building_count_90%_precision: number of building polygons in this S2 cell bucket with confidence score greater than or equal to the score threshold needed to get the specific precision,
building_count: number of building polygons in this S2 cell bucket,
num_samples: number of samples used for generating the score threshold. This feature exists from v2 onwards.
"""

import gzip
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from IPython.display import display

#%% DOWNLOAD THE DATASET
import os
import urllib.request
from tqdm import tqdm

url_rio_buildings = 'https://storage.googleapis.com/open-buildings-data/v3/polygons_s2_level_4_gzip/009_buildings.csv.gz'
if not os.path.exists('data'):
    os.makedirs('data')
output_file = "data/009_buildings.csv.gz"

# Function to track download progress
def download_with_progress(url, output_file):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(output_file, 'wb') as out_file:
        # Get the file size from the response headers
        file_size = int(response.headers['Content-Length'])
        chunk_size = 1024 * 1024  # 1 MB chunks

        # Initialize tqdm with file size
        with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024, desc=url.split('/')[-1]) as progress:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                progress.update(len(chunk))
        
# Download the file with progress bar
if not os.path.exists(output_file):
    print(f"Downloading Rio de Janeiro buildings dataset from {url_rio_buildings}...")
    download_with_progress(url_rio_buildings, output_file)

#%% LOAD THE DATASET
file_path = '009_buildings.csv.gz'
with gzip.open(f"data/{file_path}", 'rt') as f:
    buildings = pd.read_csv(f, engine='c', usecols=['latitude', 'longitude', 'area_in_meters', 'confidence', 'geometry', 'full_plus_code'])

#%% Some statistics
# Size of the dataset
print(f"Dataset size: {buildings.memory_usage(deep=True).sum() / 1e6:.2f} MB\n")
# Data types
print("Data types:")
print(buildings.dtypes)
print()
# Length of the dataset
print(f"Dataset length: {len(buildings):,} rows\n")
# Display the first 5 rows
display(buildings.head())

#%% Visualize data
sample_size = 200000

buildings_sample = (buildings.sample(sample_size)
                    if len(buildings) > sample_size else buildings)

plt.plot(buildings_sample.longitude, buildings_sample.latitude, 'k.',
         alpha=0.25, markersize=0.5)
plt.gcf().set_size_inches(10, 10)
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.axis('equal');

# %% FIND THE CLOSEST BUILDING TO CRISTO REDENTOR
# Coordinates of Cristo Redentor
# Source https://latitude.to/articles-by-country/br/brazil/325/christ-the-redeemer-statue
cristo_redentor_coords = {'latitude': -22.950996196, 'longitude': -43.206499174}
cristo_redentor_coords_point = gpd.points_from_xy([cristo_redentor_coords['longitude']], [cristo_redentor_coords['latitude']])[0]

# Use geopandas to convert lattitude and longitude of the center of the building to a Point object
buildings = gpd.GeoDataFrame(buildings, geometry=gpd.points_from_xy(buildings.longitude, buildings.latitude))

# Compute distances from geometries to Cristo Redentor
buildings['distance_to_cristo'] = buildings['geometry'].distance(cristo_redentor_coords_point)
# Sort the buildings by distance to Cristo Redentor
buildings = buildings.sort_values(by='distance_to_cristo')
display(buildings.head())

# Find the building closest to Cristo Redentor
closest_building = buildings.loc[buildings['distance_to_cristo'].idxmin()]

# Display information about the closest building
closest_building_info = {
    'Latitude': closest_building['latitude'],
    'Longitude': closest_building['longitude'],
    'Area (m²)': closest_building['area_in_meters'],
    'Confidence': closest_building['confidence'],
    'Full Plus Code': closest_building['full_plus_code'],
    'Distance to Cristo Redentor': closest_building['distance_to_cristo']
}

print("Information about the building closest to Cristo Redentor:")
print(closest_building_info)

#%% Result: give the Full Plus Code of the building closest to Cristo Redentor
print(f"RESULT, THE FULL PLUS CODE OF THE BUILDING CLOSEST TO CRISTO REDENTOR: {closest_building['full_plus_code']}")
# %%
