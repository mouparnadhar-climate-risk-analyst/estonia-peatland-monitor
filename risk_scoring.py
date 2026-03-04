import numpy as np

def calculate_restoration_score(site_data, area_ha):
    """
    Calculates a Restoration Score (0-100) and Financial Carbon Risk.
    
    Inputs:
    - site_data: List of dicts [{'year': 2017, 'ndvi': 0.5...}, ...]
    - area_ha: Area in hectares (6.25 for our grid points)
    
    Returns:
    - status: 'Restored', 'Recovering', 'Degraded'
    - score: 0-100
    - carbon_eur: Monetary value of lost carbon sequestration
    """
    
    # 1. Sort data by year to ensure trends are accurate
    data = sorted(site_data, key=lambda x: x['year'])
    
    if not data:
        return {'status': 'Unknown', 'score': 0, 'carbon_eur': 0}

    # 2. Extract specific values
    ndvi_values = [d['ndvi'] for d in data]
    sar_values = [d['sar_vv'] for d in data]
    
    # Current (most recent) values
    current_ndvi = ndvi_values[-1]
    current_sar = sar_values[-1] # Moisture (Target: > -10dB is wet, < -14dB is dry)

    # 3. CALCULATE SCORE (Max 100)
    score = 0
    
    # A. Vegetation Health (Max 40 pts)
    # Healthy bog moss usually has NDVI 0.5 - 0.7
    if current_ndvi >= 0.6: score += 40
    elif current_ndvi >= 0.5: score += 30
    elif current_ndvi >= 0.4: score += 15
    else: score += 0
    
    # B. Moisture / Water Table (Max 40 pts)
    # SAR Backscatter: Higher (less negative) is wetter.
    # -8 to -10 dB is ideal for wet peat. -14 is dry.
    if current_sar > -10.5: score += 40      # Very Wet (Good)
    elif current_sar > -12.0: score += 25    # Moist
    elif current_sar > -14.0: score += 10    # Drying
    else: score += 0                         # Dry (Bad)

    # C. Trend Analysis (Max 20 pts)
    # Is it getting better over the last 7 years?
    if len(ndvi_values) >= 2:
        # Calculate slope (trend)
        slope = np.polyfit(range(len(ndvi_values)), ndvi_values, 1)[0]
        if slope > 0.01: score += 20     # Strong Recovery
        elif slope > 0: score += 10      # Slow Recovery
        elif slope > -0.01: score += 5   # Stable
        else: score += 0                 # Degrading

    # 4. DETERMINE STATUS LABEL
    if score >= 80: status = "Restored"
    elif score >= 50: status = "Recovering"
    elif score >= 30: status = "Partially Degraded"
    else: status = "Severely Degraded"

    # 5. FINANCIAL CARBON CALCULATION (The "CSRD" part)
    # A healthy hectare captures ~2 tonnes CO2/year.
    # A degraded hectare EMITS ~10 tonnes CO2/year.
    # Carbon Price = 85 EUR / tonne (EU ETS 2024 forecast)
    
    CARBON_PRICE = 85
    
    if score < 50:
        # It is emitting carbon!
        # Emission factor * Area * Price * 25 Years (to 2050)
        annual_loss = 10 * area_ha * CARBON_PRICE
        total_risk = annual_loss * 25 
    else:
        # It is sequestering (saving) money!
        # We represent this as 0 risk (or verified credits)
        annual_loss = 0
        total_risk = 0

    return {
        'restoration_score': int(score),
        'restoration_status': status,
        'financial_risk_eur': int(total_risk)
    }