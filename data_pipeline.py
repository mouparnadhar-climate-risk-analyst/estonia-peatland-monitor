import ee
import streamlit as st
import base64
import os

# ADD THIS DECORATOR - It prevents the app from freezing!
@st.cache_resource
def authenticate_gee():
    """
    Authenticates GEE. Cached to run only once per session.
    """
    try:
        # 1. Get the secret string
        if "GEE_PRIVATE_KEY" in os.environ:
            encoded_key = os.environ["GEE_PRIVATE_KEY"]
            project_id = os.environ["GEE_PROJECT_ID"]
        elif "gee" in st.secrets:
            encoded_key = st.secrets["gee"]["private_key_data"]
            project_id = st.secrets["gee"]["project_id"]
        else:
            return # Local fallback handled elsewhere

        # 2. Decode
        decoded_key = base64.b64decode(encoded_key).decode("utf-8")

        # 3. Force-create credentials file (Nuclear Option)
        home_dir = os.path.expanduser("~")
        gee_config_dir = os.path.join(home_dir, ".config", "earthengine")
        os.makedirs(gee_config_dir, exist_ok=True)
        
        credentials_path = os.path.join(gee_config_dir, "credentials")
        
        # Only write if it doesn't exist (Saves memory!)
        if not os.path.exists(credentials_path):
            with open(credentials_path, "w") as f:
                f.write(decoded_key)

        # 4. Initialize
        ee.Initialize(project=project_id)
        print("✅ GEE Authenticated!")

    except Exception as e:
        print(f"Auth Error: {e}")
        try:
            ee.Initialize()
        except:
            pass

# ... Keep your get_satellite_data function below exactly as it is ...
def get_satellite_data(lat, lon, peatland_id):
    # (Your existing code here)
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