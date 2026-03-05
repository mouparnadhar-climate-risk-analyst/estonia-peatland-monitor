import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_pipeline import get_satellite_data, authenticate_gee
from risk_scoring import calculate_restoration_score

# --- 1. PAGE CONFIGURATION (Must be the first Streamlit command) ---
st.set_page_config(page_title="Selisoo Restoration Monitor", layout="wide", page_icon="🌲")

# --- 2. AUTHENTICATE GEE ---
authenticate_gee()

# --- 3. CUSTOM CSS (The Beautiful "Glass" Look) ---
page_bg_img = '''
<style>
[data-testid="stAppViewContainer"] {
    background-image: linear-gradient(rgba(10, 15, 20, 0.85), rgba(10, 15, 20, 0.95)), url("https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?q=80&w=2013&auto=format&fit=crop");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}
[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}
[data-testid="stSidebar"] {
    background-color: rgba(15, 20, 25, 0.85) !important;
    backdrop-filter: blur(10px);
}
[data-testid="metric-container"] {
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 15px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
/* Fix for Plotly charts text color in dark mode */
.js-plotly-plot .plotly .gtitle { fill: white !important; }
.js-plotly-plot .plotly .xtitle { fill: white !important; }
.js-plotly-plot .plotly .ytitle { fill: white !important; }
</style>
'''
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- HEADER ---
st.title("🌲 Selisoo Bog Restoration Monitor")
st.markdown("**Alutaguse National Park | Live Satellite Feed: Sentinel-1 (SAR) & Sentinel-2 (Optical)**")
st.markdown("Monitoring the hydrological recovery of the 2,051 ha Selisoo Bog following the 2024-2025 interventions.")
st.markdown("---")

# --- SIDEBAR & DATA LOADING ---
st.sidebar.header("Control Panel")
try:
    df = pd.read_csv('data/selisoo_grid.csv')
    
    # CRITICAL FIX: Force coordinates to be numeric to prevent blank maps
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    
    st.sidebar.success(f"Loaded Selisoo Grid ({len(df)} Points)")
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- ANALYSIS LOGIC ---
if st.sidebar.button("🛰️ Analyze Restoration Status", type="primary"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results_list = []
    history_list = []
    
    for i, row in df.iterrows():
        status_text.text(f"Scanning Point: {row['name']}...")
        
        # Get Data from GEE
        site_history = get_satellite_data(row['lat'], row['lon'], row['peatland_id'])
        
        # Calculate Scores
        risk_metrics = calculate_restoration_score(site_history, row['area_ha'])
        
        # Combine Data
        combined = {**row.to_dict(), **risk_metrics}
        history_list.extend(site_history)
        
        if site_history:
            combined['latest_ndvi'] = site_history[-1]['ndvi']
            combined['latest_sar'] = site_history[-1]['sar_vv']
            
        results_list.append(combined)
        progress_bar.progress((i + 1) / len(df))

    # Save to Session State
    st.session_state['results'] = pd.DataFrame(results_list)
    st.session_state['history'] = pd.DataFrame(history_list)
    
    status_text.text("Analysis Complete!")
    progress_bar.empty()

# --- PDF DOWNLOAD BUTTON ---
st.sidebar.markdown("---")
st.sidebar.subheader("📄 Project Documentation")
try:
    with open("Selisoo_Restoration_Report.pdf", "rb") as pdf_file:
        st.sidebar.download_button(
            label="📥 Download Methodology Report",
            data=pdf_file,
            file_name="Selisoo_Restoration_Report.pdf",
            mime="application/pdf"
        )
except:
    st.sidebar.info("Report PDF not found in repository.")

# --- DASHBOARD VISUALS ---
if 'results' in st.session_state:
    results_df = st.session_state['results']
    history_df = st.session_state['history']
    
    # 1. KPIs
    col1, col2, col3, col4 = st.columns(4)
    avg_score = results_df['restoration_score'].mean()
    total_risk = results_df['financial_risk_eur'].sum()
    restored_area = results_df[results_df['restoration_status'] == 'Restored']['area_ha'].sum()
    
    col1.metric("Avg Restoration Score", f"{avg_score:.1f}/100", "Goal: >80")
    col2.metric("Financial Carbon Liability", f"€{total_risk:,.0f}", "Projected to 2050")
    col3.metric("Restored Area", f"{restored_area:.1f} ha", f"of {df['area_ha'].sum():.0f} ha")
    col4.metric("Active Monitor Points", len(results_df))

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. TOP ROW: MAPS & PIE CHART
    st.subheader("🛰️ Spatial Analysis (2024 Current State)")
    map_col, pie_col = st.columns([2, 1])
    
    colors = {'Restored': '#2ca02c', 'Recovering': '#1f77b4', 'Partially Degraded': '#ff7f0e', 'Severely Degraded': '#d62728'}
    
    with map_col:
        tab1, tab2, tab3 = st.tabs(["🚦 Restoration Status", "🌿 Vegetation (NDVI)", "💧 Moisture (SAR)"])
        
        # Common Map Layout Settings
        map_layout = dict(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        
        # Map 1
        fig1 = px.scatter_mapbox(results_df, lat="lat", lon="lon", color="restoration_status",
                                 color_discrete_map=colors, hover_name="name",
                                 mapbox_style="open-street-map", zoom=12.5, height=500)
        fig1.update_traces(marker=dict(size=14))
        fig1.update_layout(**map_layout)
        tab1.plotly_chart(fig1, use_container_width=True)
        
        # Map 2
        fig2 = px.scatter_mapbox(results_df, lat="lat", lon="lon", color="latest_ndvi",
                                 color_continuous_scale="Greens", hover_name="name",
                                 mapbox_style="open-street-map", zoom=12.5, height=500)
        fig2.update_traces(marker=dict(size=14))
        fig2.update_layout(**map_layout)
        tab2.plotly_chart(fig2, use_container_width=True)

        # Map 3
        fig3 = px.scatter_mapbox(results_df, lat="lat", lon="lon", color="latest_sar",
                                 color_continuous_scale="Blues", hover_name="name",
                                 mapbox_style="open-street-map", zoom=12.5, height=500)
        fig3.update_traces(marker=dict(size=14))
        fig3.update_layout(**map_layout)
        tab3.plotly_chart(fig3, use_container_width=True)

    with pie_col:
        fig_pie = px.pie(results_df, names='restoration_status', hole=0.5, 
                         color='restoration_status', color_discrete_map=colors)
        fig_pie.update_layout(
            title="Site Status Breakdown", 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            legend=dict(font=dict(color="white"))
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # 3. BOTTOM ROW: BAR CHART & TREND CHART
    st.subheader("📊 Financial Risk & Hydrological Trends")
    bar_col, trend_col = st.columns([1, 2])

    with bar_col:
        risk_df = results_df[results_df['financial_risk_eur'] > 0].sort_values('financial_risk_eur', ascending=False)
        if not risk_df.empty:
            fig_bar = px.bar(risk_df.head(5), x='name', y='financial_risk_eur', 
                             color='financial_risk_eur', color_continuous_scale="Reds")
            fig_bar.update_layout(
                title="Highest Financial Risk (€)",
                xaxis_title="", 
                yaxis_title="Euros (€)",
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.success("No significant financial risk detected!")

    with trend_col:
        # Time Series
        selected_point = st.selectbox("Select a point to view history:", results_df['name'])
        point_id = results_df[results_df['name'] == selected_point]['peatland_id'].values[0]
        point_history = history_df[history_df['peatland_id'] == point_id].sort_values('year')
        
        if not point_history.empty:
            fig_trend = go.Figure()
            
            # NDVI Line
            fig_trend.add_trace(go.Scatter(x=point_history['year'], y=point_history['ndvi'],
                                           name='Vegetation (NDVI)', marker_color='#2ca02c', mode='lines+markers',
                                           yaxis='y1'))
            
            # SAR Line
            fig_trend.add_trace(go.Scatter(x=point_history['year'], y=point_history['sar_vv'],
                                           name='Moisture (SAR dB)', marker_color='#4da6ff', mode='lines+markers',
                                           yaxis='y2'))
            
            fig_trend.update_layout(
                title=f"Recovery Trajectory: {selected_point}",
                xaxis=dict(title="", tickmode='linear', dtick=1, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white')),
                yaxis=dict(
                    title=dict(text="NDVI", font=dict(color="#2ca02c")), 
                    tickfont=dict(color="#2ca02c"),
                    gridcolor='rgba(255,255,255,0.1)'
                ),
                yaxis2=dict(
                    title=dict(text="SAR dB", font=dict(color="#4da6ff")), 
                    tickfont=dict(color="#4da6ff"),
                    anchor="x", overlaying="y", side="right"
                ),
                hovermode="x unified",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                legend=dict(orientation="h", y=1.1, font=dict(color="white"))
            )
            st.plotly_chart(fig_trend, use_container_width=True)

else:
    st.info("👈 Click 'Analyze Restoration Status' in the sidebar to begin.")