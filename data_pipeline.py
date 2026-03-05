import ee
import streamlit as st
import base64
import json
from google.oauth2.credentials import Credentials

def authenticate_gee():
    """Authenticates GEE with error reporting for Streamlit Cloud."""
    
    # CASE 1: We are on Streamlit Cloud (Secrets exist)
    if "gee" in st.secrets:
        try:
            # 1. Get the secrets
            private_key_data = st.secrets["gee"]["private_key_data"]
            project_id = st.secrets["gee"]["project_id"]
            
            # 2. Decode the Base64 string
            try:
                decoded_json = json.loads(base64.b64decode(private_key_data))
            except Exception as e:
                st.error(f"⚠️ Secret Decoding Failed. Your 'private_key_data' might be cut off or formatted wrong. Error: {e}")
                st.stop()

            # 3. Create Credentials
            # We use .get() to avoid crashing if a key is missing
            creds = Credentials(
                None,
                refresh_token=decoded_json.get('refresh_token'),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=decoded_json.get('client_id'),
                client_secret=decoded_json.get('client_secret')
            )
            
            # 4. Initialize Earth Engine
            ee.Initialize(credentials=creds, project=project_id)
            print("✅ GEE Authenticated via Streamlit Cloud Secrets!")
            
        except Exception as e:
            # If this fails, we PRINT the error to the app so you can see it
            st.error(f"⚠️ Cloud Authentication Error: {e}")
            st.warning("Please check your Streamlit Cloud Secrets format.")
            st.stop() # Stop the app so it doesn't crash with the other error

    # CASE 2: We are on Localhost (No secrets found)
    else:
        try:
            ee.Initialize()
            print("✅ GEE Authenticated via Local Credentials.")
        except Exception as e:
            st.error(f"⚠️ Local Authentication Failed: {e}")
            st.stop()

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
            # Sentinel-2 (Optical)
            s2_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(area)
                .filterDate(f'{year}-06-01', f'{year}-08-31')
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                .median())
            
            ndvi = s2_col.normalizedDifference(['B8', 'B4']).rename('NDVI')
            ndwi = s2_col.normalizedDifference(['B3', 'B8']).rename('NDWI')
            
            # Sentinel-1 (Radar)
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
            print(f"Error processing {year} for {peatland_id}: {e}")
            
    return results