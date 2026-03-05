import ee
import streamlit as st
import base64
import os

def authenticate_gee():
    """
    NUCLEAR OPTION: Recreates your local credentials file on the Cloud Server.
    """
    try:
        # 1. Decode the secret key string
        encoded_key = st.secrets["gee"]["private_key_data"]
        decoded_key = base64.b64decode(encoded_key).decode("utf-8")
        project_id = st.secrets["gee"]["project_id"]

        # 2. Force-create the credentials file on the server
        # This mimics exactly what you have on your laptop at ~/.config/earthengine/credentials
        home_dir = os.path.expanduser("~")
        gee_config_dir = os.path.join(home_dir, ".config", "earthengine")
        os.makedirs(gee_config_dir, exist_ok=True)
        
        credentials_path = os.path.join(gee_config_dir, "credentials")
        
        with open(credentials_path, "w") as f:
            f.write(decoded_key)

        # 3. Initialize normally (Now it finds the file!)
        ee.Initialize(project=project_id)
        print("✅ GEE Authenticated via File Injection!")

    except Exception as e:
        # Fallback for local testing if secrets don't exist
        print(f"Cloud Auth failed ({e}). Trying local...")
        ee.Initialize()

def get_satellite_data(lat, lon, peatland_id):
    """
    Extracts NDVI, NDWI, and SAR for a specific point.
    """
    point = ee.Geometry.Point([lon, lat])
    area = point.buffer(100)
    years = [2017, 2019, 2021, 2024]
    results = []
    
    for year in years:
        try:
            s2_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(area)
                .filterDate(f'{year}-06-01', f'{year}-08-31')
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                .median())
            
            ndvi = s2_col.normalizedDifference(['B8', 'B4']).rename('NDVI')
            ndwi = s2_col.normalizedDifference(['B3', 'B8']).rename('NDWI')
            
            s1_col = (ee.ImageCollection('COPERNICUS/S1_GRD')
                .filterBounds(area)
                .filter(ee.Filter.eq('instrumentMode', 'IW'))
                .filterDate(f'{year}-01-01', f'{year}-12-31')
                .select('VV')
                .median())
            
            combined = ndvi.addBands(ndwi).addBands(s1_col)
            
            stats = combined.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=area,
                scale=10
            ).getInfo()
            
            results.append({
                'peatland_id': peatland_id, 'year': year,
                'ndvi': round(stats.get('NDVI', 0), 3),
                'ndwi': round(stats.get('NDWI', 0), 3),
                'sar_vv': round(stats.get('VV', -20), 2)
            })
        except Exception as e:
            print(f"Error processing {year}: {e}")
            
    return results