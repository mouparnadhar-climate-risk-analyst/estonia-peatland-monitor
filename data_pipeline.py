import ee
import streamlit as st
import base64
import os
import json
from google.oauth2.credentials import Credentials

@st.cache_resource
def authenticate_gee():
    """Authenticates Google Earth Engine."""
    try:
        if "GEE_PRIVATE_KEY" in os.environ:
            encoded_key = os.environ["GEE_PRIVATE_KEY"]
            project_id = os.environ["GEE_PROJECT_ID"]
        elif "gee" in st.secrets:
            encoded_key = st.secrets["gee"]["private_key_data"]
            project_id = st.secrets["gee"]["project_id"]
        else:
            return 
            
        decoded_key = base64.b64decode(encoded_key).decode("utf-8")
        home_dir = os.path.expanduser("~")
        gee_config_dir = os.path.join(home_dir, ".config", "earthengine")
        os.makedirs(gee_config_dir, exist_ok=True)
        credentials_path = os.path.join(gee_config_dir, "credentials")
        if not os.path.exists(credentials_path):
            with open(credentials_path, "w") as f:
                f.write(decoded_key)
        ee.Initialize(project=project_id)
        print("✅ GEE Authenticated via Injection")
    except Exception as e:
        print(f"Auth Error: {e}")
        try:
            ee.Initialize()
        except:
            pass

def get_satellite_data(lat, lon, peatland_id):
    """
    Extracts Vegetation (NDVI), Moisture (SAR), Rainfall (ERA5), and Wildfire Risk (NDMI)
    """
    point = ee.Geometry.Point([lon, lat])
    area = point.buffer(100)
    years =[2019, 2021, 2023, 2025] 
    results =[]
    
    for year in years:
        try:
            # 1. Optical (Vegetation & Fire Risk)
            s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')\
                .filterBounds(area).filterDate(f'{year}-06-01', f'{year}-08-31')\
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)).median()
            
            ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
            ndwi = s2.normalizedDifference(['B3', 'B8']).rename('NDWI')
            
            # 🔥 NEW: Normalized Difference Moisture Index (Wildfire Risk in Peatlands)
            # Uses Near Infrared (B8) and Shortwave Infrared (B11)
            ndmi = s2.normalizedDifference(['B8', 'B11']).rename('NDMI') 
            
            # 2. Radar (Water Table)
            s1 = ee.ImageCollection('COPERNICUS/S1_GRD')\
                .filterBounds(area).filter(ee.Filter.eq('instrumentMode', 'IW'))\
                .filterDate(f'{year}-01-01', f'{year}-12-31').select('VV').median()
                
            # 3. ERA5 Meteorological Data (Rainfall Context)
            era5 = ee.ImageCollection('ECMWF/ERA5_LAND/MONTHLY_AGGR')\
                .filterBounds(area).filterDate(f'{year}-06-01', f'{year}-08-31')\
                .select('total_precipitation_sum').sum()
            
            combined = ndvi.addBands(ndwi).addBands(ndmi).addBands(s1).addBands(era5)
            stats = combined.reduceRegion(reducer=ee.Reducer.mean(), geometry=area, scale=10).getInfo()
            
            results.append({
                'peatland_id': peatland_id, 'year': year,
                'ndvi': round(stats.get('NDVI', 0), 3),
                'ndwi': round(stats.get('NDWI', 0), 3),
                'ndmi': round(stats.get('NDMI', 0), 3),
                'sar_vv': round(stats.get('VV', -20), 2),
                'precip_mm': round((stats.get('total_precipitation_sum', 0) * 1000), 1)
            })
        except Exception as e:
            continue
            
    return results