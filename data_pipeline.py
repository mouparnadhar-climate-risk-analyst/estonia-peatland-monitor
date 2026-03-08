import ee
import streamlit as st
import base64
import json

def authenticate_gee():
    """Professional Authentication for Cloud & Local."""
    try:
        # 1. Get Secret String
        if "gee" in st.secrets:
            encoded_key = st.secrets["gee"]["private_key_data"]
            project_id = st.secrets["gee"]["project_id"]
        elif "GEE_PRIVATE_KEY" in os.environ:
            encoded_key = os.environ["GEE_PRIVATE_KEY"]
            project_id = os.environ["GEE_PROJECT_ID"]
        else:
            # Local Fallback
            ee.Initialize()
            return

        # 2. Decode and Parse JSON
        decoded_bytes = base64.b64decode(encoded_key)
        key_dict = json.loads(decoded_bytes)

        # 3. Use Service Account Credentials (No file writing needed!)
        credentials = ee.ServiceAccountCredentials(
            key_dict.get('client_email'),
            key_data=json.dumps(key_dict)
        )
        
        ee.Initialize(credentials, project=project_id)
        print("✅ GEE Authenticated Successfully")

    except Exception as e:
        st.error(f"Authentication Failed: {e}")
        st.stop()

def get_satellite_data(lat, lon, peatland_id):
    """Fetches data from GEE."""
    point = ee.Geometry.Point([lon, lat])
    area = point.buffer(100)
    years = [2019, 2021, 2023, 2024] 
    results = []
    
    for year in years:
        try:
            s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")\
                .filterBounds(area)\
                .filterDate(f'{year}-06-01', f'{year}-08-31')\
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))\
                .median()
            
            ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
            
            s1 = ee.ImageCollection("COPERNICUS/S1_GRD")\
                .filterBounds(area)\
                .filter(ee.Filter.eq('instrumentMode', 'IW'))\
                .filterDate(f'{year}-01-01', f'{year}-12-31')\
                .select('VV')\
                .median()
            
            stats = ndvi.addBands(s1).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=area,
                scale=10
            ).getInfo()
            
            results.append({
                'peatland_id': peatland_id, 'year': year,
                'ndvi': round(stats.get('NDVI', 0), 3),
                'sar_vv': round(stats.get('VV', -20), 2)
            })
        except:
            continue
            
    return results