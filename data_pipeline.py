import ee
import streamlit as st
import base64
import json
from google.oauth2.credentials import Credentials

def authenticate_gee():
    """Authenticates GEE for Streamlit Cloud or local development."""
    try:
        # Load the secret from Streamlit Cloud
        private_key_data = st.secrets["gee"]["private_key_data"]
        project_id = st.secrets["gee"]["project_id"]
        
        # Decode the Base64 string back into JSON
        private_key_json = json.loads(base64.b64decode(private_key_data))
        
        # Tell Google we are using your Personal Refresh Token
        creds = Credentials(
            None,
            refresh_token=private_key_json.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=private_key_json.get('client_id'),
            client_secret=private_key_json.get('client_secret')
        )
        
        # Initialize Google Earth Engine with these credentials
        ee.Initialize(credentials=creds, project=project_id)
        print("GEE Authenticated via Streamlit Secrets.")
        
    except Exception as e:
        print(f"Cloud Auth Status: Running locally or failed ({e})")
        # Fallback for when you run it on your own laptop
        try:
            ee.Initialize(project='estonia-peatland-monitor')
        except:
            ee.Initialize()
        print("GEE Authenticated via local credentials.")

def get_satellite_data(lat, lon, peatland_id):
    """
    Extracts NDVI, NDWI, and SAR for a specific point.
    """
    point = ee.Geometry.Point([lon, lat])
    area = point.buffer(100)
    years =[2017, 2019, 2021, 2024]
    results =[]
    
    for year in years:
        try:
            # Optical Data (Sentinel-2)
            s2_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(area)
                .filterDate(f'{year}-06-01', f'{year}-08-31')
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                .median())
            
            ndvi = s2_col.normalizedDifference(['B8', 'B4']).rename('NDVI')
            ndwi = s2_col.normalizedDifference(['B3', 'B8']).rename('NDWI')
            
            # Radar Data (Sentinel-1)
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