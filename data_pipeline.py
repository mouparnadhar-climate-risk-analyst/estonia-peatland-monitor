import ee
import streamlit as st
import base64
import json

# This function is now the only thing in this file
def authenticate_gee():
    """Authenticates GEE for Streamlit Cloud or local development."""
    try:
        private_key_data = st.secrets["gee"]["private_key_data"]
        project_id = st.secrets["gee"]["project_id"]
        
        private_key_json = json.loads(base64.b64decode(private_key_data))
        
        credentials = ee.ServiceAccountCredentials(
            private_key_json['client_email'], 
            key_data=json.dumps(private_key_json)
        )
        ee.Initialize(credentials, project=project_id)
        print("GEE Authenticated via Streamlit Secrets.")
    except:
        ee.Initialize()
        print("GEE Authenticated via local credentials.")

# We also still need the data-getting function for the app to call
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
            print(f"Error processing {year} for {peatland_id}: {e}")
    return results