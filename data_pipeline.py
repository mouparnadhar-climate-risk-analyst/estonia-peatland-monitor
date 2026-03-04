import ee
import pandas as pd
import time

# 1. Initialize Earth Engine
try:
    ee.Initialize(project='estonia-peatland-monitor')
except:
    ee.Initialize()

def get_satellite_data(lat, lon, peatland_id):
    """
    Extracts NDVI (Vegetation), NDWI (Water), and SAR (Moisture) 
    for a specific point over the last 10 years.
    """
    point = ee.Geometry.Point([lon, lat])
    area = point.buffer(100) # 100m radius for precision

    # Years to analyze
    years = [2017, 2019, 2021, 2024]
    results = []

    for year in years:
        try:
            # --- SENTINEL-2 (VEGETATION & WATER) ---
            # Summer composite (June-August) for best moss detection
            s2_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(area)
                .filterDate(f'{year}-06-01', f'{year}-08-31')
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                .median())

            # NDVI = (B8 - B4) / (B8 + B4) -> Plant health
            ndvi = s2_col.normalizedDifference(['B8', 'B4']).rename('NDVI')
            # NDWI = (B3 - B8) / (B3 + B8) -> Surface water/wetness
            ndwi = s2_col.normalizedDifference(['B3', 'B8']).rename('NDWI')

            # --- SENTINEL-1 (RADAR SOIL MOISTURE) ---
            # SAR VV backscatter - higher values mean wetter soil
            s1_col = (ee.ImageCollection('COPERNICUS/S1_GRD')
                .filterBounds(area)
                .filter(ee.Filter.eq('instrumentMode', 'IW'))
                .filterDate(f'{year}-01-01', f'{year}-12-31')
                .select('VV')
                .median())

            # Combine bands
            combined = ndvi.addBands(ndwi).addBands(s1_col)

            # Reduce to mean values for the area
            stats = combined.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=area,
                scale=10
            ).getInfo()

            results.append({
                'peatland_id': peatland_id,
                'year': year,
                'ndvi': round(stats.get('NDVI', 0), 3),
                'ndwi': round(stats.get('NDWI', 0), 3),
                'sar_vv': round(stats.get('VV', -20), 2)
            })
            print(f"  Processed {peatland_id} for {year}")

        except Exception as e:
            print(f"  Error processing {year} for {peatland_id}: {e}")
    
    return results

if __name__ == "__main__":
    # Test script for the first 3 points to ensure it works
    print("Testing Pipeline with 3 points from Selisoo...")
    df = pd.read_csv('data/selisoo_grid.csv')
    test_df = df.head(3)
    
    all_data = []
    for _, row in test_df.iterrows():
        point_data = get_satellite_data(row['lat'], row['lon'], row['peatland_id'])
        all_data.extend(point_data)
    
    # Save test results
    test_results = pd.DataFrame(all_data)
    print("\n--- SAMPLE DATA EXTRACTED ---")
    print(test_results.head())
    print("\nPipeline is ready!")