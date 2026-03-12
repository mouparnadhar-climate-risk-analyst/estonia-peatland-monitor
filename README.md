# 🌍 Alutaguse Peatland: Earth Observation (EO) Asset Monitoring & Risk Analytics

### 🛰️ Live Enterprise Dashboard: [Click Here to View App](https://huggingface.co/spaces/mouparnadhar-climate-risk-analyst/estonia-peatland-monitor)

**A strategic biodiversity audit and carbon risk framework for the 2,051-hectare Selisoo Bog, engineered for EU Nature Restoration Law and CSRD (ESRS E4) compliance.**

![Dashboard Screenshot](dashboard.png)

## 📊 The Business Case
Under the EU Nature Restoration Law, Estonia is mandated to restore 30% of its drained peatlands by 2030. Traditional field auditing is expensive, unscalable, and lacks historical context. Furthermore, under the Corporate Sustainability Reporting Directive (CSRD), degraded peatlands represent severe financial carbon liabilities. Stakeholders require an automated, auditable "Digital Twin" to verify intervention success and quantify risk mitigation.

## 🛠️ The Engineering Solution
I engineered an automated Python-based monitoring engine using the **Google Earth Engine (GEE) API**. By fusing multi-spectral optical data, synthetic aperture radar, and meteorological datasets, this platform moves beyond simple mapping to provide **Causal Attribution** and **Predictive Forecasting**.

## 🚀 Core Capabilities
1. **Climate Decoupling Analysis:** Cross-references **ERA5-Land** precipitation with **Sentinel-1 SAR** moisture data to statistically prove that rising water tables are the result of structural ditch-blocking interventions, not just seasonal rainfall anomalies.
2. **Predictive 2030 Trajectory:** Utilises linear regression on historical EO data (2019–2025) to forecast whether specific bog sectors will achieve the legal EU health benchmark (NDVI >0.60) by the 2030 deadline.
3. **Dynamic Financial Stress Testing:** Features an interactive scenario modeller to stress-test the asset against volatile EU ETS carbon pricing (€40–€180/tonne), instantly quantifying mitigated financial exposure.
4. **Multi-Sensor Spatial Verification:** An interactive map stack assessing:
   * **Vegetation Vigor:** Sentinel-2 Optical (NDVI)
   * **Sub-Surface Hydrology:** Sentinel-1 Radar (SAR VV)
   * **Wildfire Ignition Risk:** Sentinel-2 Canopy Moisture (NDMI)
5. **Audit-Ready Export:** One-click generation of ESRS-compliant CSV logs for third-party environmental auditors.

## 💻 Tech Stack & Architecture
* **Earth Observation:** Google Earth Engine (GEE), Copernicus Sentinel-1 & 2, ECMWF ERA5-Land
* **Data Science:** Python, Pandas, NumPy (Polyfit logic)
* **Frontend Visualisation:** Streamlit, Plotly Express, Plotly Graph Objects (Dual-Axis plotting)
* **Deployment:** Hugging Face Spaces (Containerised via Docker)

## 📄 Documentation
A comprehensive methodology detailing the remote sensing parameters, financial modelling logic, and 2026 Audit Findings is embedded within the live application.
* 👉 **[Download the Strategic Audit Report (PDF)](Selisoo_Restoration_Report.pdf)** directly from the GitHub repository or the live app.

---
*Architected and Developed by **Mouparna Dhar** | Climate Risk Analyst*
