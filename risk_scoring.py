import numpy as np

# 🔥 UPDATED to accept a variable carbon price from the Streamlit slider
def calculate_restoration_score(site_data, area_ha, carbon_price_eur=85):
    """
    Calculates EU Law compliance score, 2030 predictions, and financial risk limits.
    """
    data = sorted(site_data, key=lambda x: x['year'])
    if not data:
        return {'status': 'Unknown', 'score': 0, 'carbon_eur': 0, 'predicted_ndvi_2030': 0}

    ndvi_values =[d['ndvi'] for d in data]
    sar_values = [d['sar_vv'] for d in data]
    years = [d['year'] for d in data]
    
    current_ndvi = ndvi_values[-1]
    current_sar = sar_values[-1] 

    # SCORING ALGORITHM (100 Pt Max)
    score = 0
    if current_ndvi >= 0.6: score += 40
    elif current_ndvi >= 0.5: score += 30
    elif current_ndvi >= 0.4: score += 15
    
    if current_sar > -10.5: score += 40
    elif current_sar > -12.0: score += 25
    elif current_sar > -14.0: score += 10

    # Trend Analysis
    if len(ndvi_values) >= 2:
        slope = np.polyfit(range(len(ndvi_values)), ndvi_values, 1)[0]
        if slope > 0.01: score += 20
        elif slope > 0: score += 10
        elif slope > -0.01: score += 5
        
        # PREDICTIVE ANALYTICS TO 2030 (For the Dubai DBA / Consultant perspective)
        try:
            trend = np.poly1d(np.polyfit(years, ndvi_values, 1))
            pred_2030 = trend(2030)
            pred_2030 = min(max(pred_2030, 0), 0.85) # Logical bounds
        except:
            pred_2030 = current_ndvi
    else:
        pred_2030 = current_ndvi

    # Determine Text Status
    if score >= 80: status = "Restored"
    elif score >= 50: status = "Recovering"
    elif score >= 30: status = "Partially Degraded"
    else: status = "Severely Degraded"

    # FINANCIAL RISK (DYNAMIC BASED ON UI SLIDER)
    # Assumes heavily degraded areas emit 10t CO2/ha/yr for the next 24 years (until 2050 Net-Zero)
    if score < 50:
        annual_loss = 10 * area_ha * carbon_price_eur
        total_risk = annual_loss * 24 
    else:
        total_risk = 0

    return {
        'restoration_score': int(score),
        'restoration_status': status,
        'financial_risk_eur': int(total_risk),
        'predicted_ndvi_2030': round(pred_2030, 3)
    }