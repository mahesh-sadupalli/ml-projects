import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pyproj import Transformer
import numpy as np
from pathlib import Path

# ---------------------------------------------------------------------------
# Config & Constants
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MedSat Health Intelligence",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

DASHBOARD_DIR = Path(__file__).resolve().parent
IMG_FEAT_DIR = DASHBOARD_DIR / "image_features"

OUTCOME_COLS = {
    "o_diabetes_quantity_per_capita": "Diabetes",
    "o_opioids_quantity_per_capita": "Opioids",
    "o_OME_per_capita": "Otitis Media (OME)",
    "o_total_quantity_per_capita": "Total Prescriptions",
    "o_asthma_quantity_per_capita": "Asthma",
    "o_hypertension_quantity_per_capita": "Hypertension",
    "o_depression_quantity_per_capita": "Depression",
    "o_anxiety_quantity_per_capita": "Anxiety",
}

ENV_COLS_DISPLAY = {
    "e_NO2": "NO\u2082 Concentration",
    "e_ozone": "Ozone",
    "e_ndvi": "NDVI (Vegetation)",
    "e_temperature_2m": "Temperature (2m)",
    "e_dewpoint_temperature_2m": "Dewpoint Temp.",
    "e_particulate_matter_d_less_than_25_um_surface": "PM2.5",
    "e_total_precipitation_sum": "Precipitation",
    "e_surface_pressure": "Surface Pressure",
    "e_water": "Land: Water",
    "e_trees": "Land: Trees",
    "e_grass": "Land: Grass",
    "e_built": "Land: Built-up",
    "e_crops": "Land: Crops",
}

SOCIO_COLS_DISPLAY = {
    "c_net annual income": "Net Annual Income (GBP)",
    "c_pop_density": "Population Density",
    "c_percent unemployed": "% Unemployed",
    "c_percent very good health": "% Very Good Health",
    "c_percent bad health": "% Bad Health",
    "c_percent very bad health": "% Very Bad Health",
    "c_percent households not deprived in any dimension": "% Not Deprived",
    "c_percent households deprived in one dimension": "% Deprived (1 dim)",
    "c_percent households deprived in two dimensions": "% Deprived (2 dims)",
    "c_percent households deprived in three dimensions": "% Deprived (3 dims)",
    "c_percent asian": "% Asian",
    "c_percent black": "% Black",
    "c_percent white": "% White",
    "c_percent mixed": "% Mixed Ethnicity",
    "c_total population": "Total Population",
    "c_percent male": "% Male",
}

REGION_COLORS = {
    "London": "#636EFA",
    "South East": "#EF553B",
    "East of England": "#00CC96",
    "East Midlands": "#AB63FA",
    "West Midlands": "#FFA15A",
    "Yorkshire and The Humber": "#19D3F3",
    "North West": "#FF6692",
    "North East": "#B6E880",
    "South West": "#FF97FF",
}


# ---------------------------------------------------------------------------
# Data Loading (cached)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading spatial data...")
def load_spatial_data(year: int) -> pd.DataFrame:
    return pd.read_parquet(DASHBOARD_DIR / f"{year}_spatial.parquet")


@st.cache_data(show_spinner="Loading region mappings...")
def load_regions() -> pd.DataFrame:
    return pd.read_csv(DASHBOARD_DIR / "regions_mapping.csv")


@st.cache_data(show_spinner="Converting coordinates...")
def add_latlon(df: pd.DataFrame) -> pd.DataFrame:
    """Convert British National Grid to WGS84 lat/lon."""
    transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(df["centroid_x"].values, df["centroid_y"].values)
    df = df.copy()
    df["lat"] = lat
    df["lon"] = lon
    return df


@st.cache_data(show_spinner="Preparing dashboard data...")
def prepare_data(year: int):
    df = load_spatial_data(year)
    regions = load_regions()
    df = df.merge(
        regions[["LSOA21CD", "RGN22NM"]],
        left_on="geography code",
        right_on="LSOA21CD",
        how="left",
    )
    df = df.rename(columns={"RGN22NM": "Region"})
    df = df.drop(columns=["LSOA21CD"], errors="ignore")
    df = add_latlon(df)
    return df


@st.cache_data(show_spinner="Loading satellite features...")
def load_image_features(season_folder: str) -> pd.DataFrame:
    path = IMG_FEAT_DIR / f"{season_folder}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    """
    <div style='text-align:center; padding: 10px 0 20px 0;'>
        <h1 style='margin:0; font-size:1.6em;'>MedSat</h1>
        <p style='margin:0; color:#888; font-size:0.9em;'>Health Intelligence Dashboard</p>
    </div>
    """,
    unsafe_allow_html=True,
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Regional Health Map",
        "Environmental Correlations",
        "2019 vs 2020 (COVID Impact)",
        "Sociodemographic Analysis",
        "Satellite Features",
    ],
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.caption("Data: NeurIPS 2023 MedSat Dataset")
st.sidebar.caption("33,755 regions (LSOAs) across England")
st.sidebar.caption(
    "Built by Mahesh Sadupalli"
)


# ---------------------------------------------------------------------------
# PAGE: Overview
# ---------------------------------------------------------------------------
if page == "Overview":
    st.title("MedSat Health Intelligence Dashboard")
    st.markdown(
        "Multimodal public health analytics combining **census data**, "
        "**environmental indicators**, **satellite imagery**, and **prescription outcomes** "
        "across **33,755 regions** in England."
    )

    df = prepare_data(2019)

    # Key metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Regions (LSOAs)", f"{len(df):,}")
    col2.metric("Avg Population", f"{df['c_total population'].mean():,.0f}")
    col3.metric(
        "Avg Depression Rx",
        f"{df['o_depression_quantity_per_capita'].mean():.2f}",
    )
    col4.metric(
        "Avg Diabetes Rx",
        f"{df['o_diabetes_quantity_per_capita'].mean():.2f}",
    )
    col5.metric(
        "Avg Income (GBP)",
        f"£{df['c_net annual income'].mean():,.0f}",
    )

    st.divider()

    # Two-column layout: region summary + condition overview
    left, right = st.columns(2)

    with left:
        st.subheader("Prescription Rates by Region")
        outcome_choice = st.selectbox(
            "Select condition",
            list(OUTCOME_COLS.keys()),
            format_func=lambda x: OUTCOME_COLS[x],
            key="overview_outcome",
        )
        region_avg = (
            df.groupby("Region")[outcome_choice]
            .mean()
            .sort_values(ascending=True)
            .reset_index()
        )
        region_avg.columns = ["Region", "Mean Per Capita"]
        fig = px.bar(
            region_avg,
            x="Mean Per Capita",
            y="Region",
            orientation="h",
            color="Region",
            color_discrete_map=REGION_COLORS,
        )
        fig.update_layout(
            height=400, showlegend=False, margin=dict(l=0, r=20, t=10, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Health Outcomes Distribution")
        outcomes_mean = (
            df[list(OUTCOME_COLS.keys())]
            .mean()
            .reset_index()
        )
        outcomes_mean.columns = ["Condition", "Mean Per Capita"]
        outcomes_mean["Condition"] = outcomes_mean["Condition"].map(OUTCOME_COLS)
        # Exclude total for clearer view
        outcomes_mean = outcomes_mean[outcomes_mean["Condition"] != "Total Prescriptions"]
        fig2 = px.bar(
            outcomes_mean.sort_values("Mean Per Capita", ascending=True),
            x="Mean Per Capita",
            y="Condition",
            orientation="h",
            color="Mean Per Capita",
            color_continuous_scale="Reds",
        )
        fig2.update_layout(
            height=400, showlegend=False, margin=dict(l=0, r=20, t=10, b=0),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # Quick correlation heatmap: environment vs health
    st.subheader("Environment vs Health Outcomes — Correlation Matrix")
    env_subset = list(ENV_COLS_DISPLAY.keys())
    outcome_subset = list(OUTCOME_COLS.keys())
    corr = df[env_subset + outcome_subset].corr().loc[env_subset, outcome_subset]
    corr.index = [ENV_COLS_DISPLAY[c] for c in corr.index]
    corr.columns = [OUTCOME_COLS[c] for c in corr.columns]

    fig3 = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-0.5,
        zmax=0.5,
        aspect="auto",
    )
    fig3.update_layout(height=500, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig3, use_container_width=True)


# ---------------------------------------------------------------------------
# PAGE: Regional Health Map
# ---------------------------------------------------------------------------
elif page == "Regional Health Map":
    st.title("Regional Health Map")

    year = st.radio("Year", [2019, 2020], horizontal=True)
    df = prepare_data(year)

    outcome = st.selectbox(
        "Health outcome to visualize",
        list(OUTCOME_COLS.keys()),
        format_func=lambda x: OUTCOME_COLS[x],
        key="map_outcome",
    )

    # Sample for performance (full 33k points is heavy)
    sample_size = st.slider(
        "Map sample size (for performance)", 2000, 33000, 8000, step=1000
    )
    df_sample = df.dropna(subset=[outcome]).sample(
        n=min(sample_size, len(df)), random_state=42
    )

    fig = px.scatter_mapbox(
        df_sample,
        lat="lat",
        lon="lon",
        color=outcome,
        color_continuous_scale="YlOrRd",
        hover_name="LSOA21NM",
        hover_data={"Region": True, outcome: ":.3f", "lat": False, "lon": False},
        zoom=5.5,
        center={"lat": 52.5, "lon": -1.5},
        mapbox_style="carto-positron",
        opacity=0.6,
        size_max=6,
    )
    fig.update_traces(marker=dict(size=4))
    fig.update_layout(
        height=700,
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title=OUTCOME_COLS[outcome]),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Region breakdown table
    st.subheader("Regional Statistics")
    stats = (
        df.groupby("Region")[outcome]
        .agg(["mean", "median", "std", "min", "max", "count"])
        .round(3)
        .sort_values("mean", ascending=False)
    )
    stats.columns = ["Mean", "Median", "Std Dev", "Min", "Max", "Count"]
    st.dataframe(stats, use_container_width=True)


# ---------------------------------------------------------------------------
# PAGE: Environmental Correlations
# ---------------------------------------------------------------------------
elif page == "Environmental Correlations":
    st.title("Environmental Correlations with Health Outcomes")

    df = prepare_data(2019)

    col_l, col_r = st.columns(2)
    with col_l:
        env_var = st.selectbox(
            "Environmental variable (X-axis)",
            list(ENV_COLS_DISPLAY.keys()),
            format_func=lambda x: ENV_COLS_DISPLAY[x],
        )
    with col_r:
        health_var = st.selectbox(
            "Health outcome (Y-axis)",
            list(OUTCOME_COLS.keys()),
            format_func=lambda x: OUTCOME_COLS[x],
        )

    color_by = st.selectbox(
        "Color by",
        ["Region", "None"],
    )

    # Sample for scatter performance
    df_clean = df.dropna(subset=[env_var, health_var])
    df_plot = df_clean.sample(n=min(8000, len(df_clean)), random_state=42)

    if color_by == "Region":
        fig = px.scatter(
            df_plot,
            x=env_var,
            y=health_var,
            color="Region",
            color_discrete_map=REGION_COLORS,
            opacity=0.4,
            trendline="ols",
            labels={env_var: ENV_COLS_DISPLAY[env_var], health_var: OUTCOME_COLS[health_var]},
        )
    else:
        fig = px.scatter(
            df_plot,
            x=env_var,
            y=health_var,
            opacity=0.3,
            trendline="ols",
            labels={env_var: ENV_COLS_DISPLAY[env_var], health_var: OUTCOME_COLS[health_var]},
            color_discrete_sequence=["#636EFA"],
        )

    fig.update_traces(marker=dict(size=3))
    fig.update_layout(height=550, margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)

    # Correlation value
    corr_val = df_clean[env_var].corr(df_clean[health_var])
    st.metric(
        f"Pearson Correlation: {ENV_COLS_DISPLAY[env_var]} vs {OUTCOME_COLS[health_var]}",
        f"{corr_val:.4f}",
    )

    # Top correlations table
    st.subheader("All Environmental Correlations with Selected Health Outcome")
    corrs = []
    for e in ENV_COLS_DISPLAY:
        r = df[e].corr(df[health_var])
        corrs.append({"Variable": ENV_COLS_DISPLAY[e], "Correlation": round(r, 4)})
    corr_df = pd.DataFrame(corrs).sort_values("Correlation", key=abs, ascending=False)
    st.dataframe(corr_df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# PAGE: 2019 vs 2020 (COVID Impact)
# ---------------------------------------------------------------------------
elif page == "2019 vs 2020 (COVID Impact)":
    st.title("2019 vs 2020 — COVID-19 Impact on Prescriptions")

    df19 = prepare_data(2019)
    df20 = prepare_data(2020)

    # Regional comparison
    outcome = st.selectbox(
        "Health outcome",
        list(OUTCOME_COLS.keys()),
        format_func=lambda x: OUTCOME_COLS[x],
        key="covid_outcome",
    )

    reg19 = df19.groupby("Region")[outcome].mean().reset_index()
    reg19.columns = ["Region", "2019"]
    reg20 = df20.groupby("Region")[outcome].mean().reset_index()
    reg20.columns = ["Region", "2020"]
    merged = reg19.merge(reg20, on="Region")
    merged["Change (%)"] = ((merged["2020"] - merged["2019"]) / merged["2019"] * 100).round(2)
    merged = merged.sort_values("Change (%)", ascending=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Year-over-Year Comparison")
        melted = merged.melt(
            id_vars="Region", value_vars=["2019", "2020"], var_name="Year", value_name="Mean Per Capita"
        )
        fig = px.bar(
            melted,
            x="Mean Per Capita",
            y="Region",
            color="Year",
            barmode="group",
            orientation="h",
            color_discrete_map={"2019": "#636EFA", "2020": "#EF553B"},
        )
        fig.update_layout(height=400, margin=dict(l=0, r=20, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Percentage Change by Region")
        colors = ["#2ecc71" if v < 0 else "#e74c3c" for v in merged["Change (%)"]]
        fig2 = go.Figure(
            go.Bar(
                x=merged["Change (%)"],
                y=merged["Region"],
                orientation="h",
                marker_color=colors,
                text=merged["Change (%)"].apply(lambda x: f"{x:+.1f}%"),
                textposition="outside",
            )
        )
        fig2.update_layout(
            height=400,
            margin=dict(l=0, r=60, t=10, b=0),
            xaxis_title="Change (%)",
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # All conditions comparison
    st.subheader("All Conditions — National Average Change")
    changes = []
    for col, name in OUTCOME_COLS.items():
        if col == "o_total_quantity_per_capita":
            continue
        m19 = df19[col].mean()
        m20 = df20[col].mean()
        pct = (m20 - m19) / m19 * 100
        changes.append({"Condition": name, "2019 Mean": round(m19, 3), "2020 Mean": round(m20, 3), "Change (%)": round(pct, 2)})

    change_df = pd.DataFrame(changes).sort_values("Change (%)", ascending=True)
    colors = ["#2ecc71" if v < 0 else "#e74c3c" for v in change_df["Change (%)"]]

    fig3 = go.Figure(
        go.Bar(
            x=change_df["Change (%)"],
            y=change_df["Condition"],
            orientation="h",
            marker_color=colors,
            text=change_df["Change (%)"].apply(lambda x: f"{x:+.1f}%"),
            textposition="outside",
        )
    )
    fig3.update_layout(height=350, margin=dict(l=0, r=80, t=10, b=0), xaxis_title="Change (%)")
    st.plotly_chart(fig3, use_container_width=True)

    st.dataframe(change_df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# PAGE: Sociodemographic Analysis
# ---------------------------------------------------------------------------
elif page == "Sociodemographic Analysis":
    st.title("Sociodemographic Analysis")

    df = prepare_data(2019)

    col_l, col_r = st.columns(2)
    with col_l:
        socio_var = st.selectbox(
            "Sociodemographic variable (X-axis)",
            list(SOCIO_COLS_DISPLAY.keys()),
            format_func=lambda x: SOCIO_COLS_DISPLAY[x],
        )
    with col_r:
        health_var = st.selectbox(
            "Health outcome (Y-axis)",
            list(OUTCOME_COLS.keys()),
            format_func=lambda x: OUTCOME_COLS[x],
            key="socio_health",
        )

    df_clean = df.dropna(subset=[socio_var, health_var])
    df_plot = df_clean.sample(n=min(8000, len(df_clean)), random_state=42)

    fig = px.scatter(
        df_plot,
        x=socio_var,
        y=health_var,
        color="Region",
        color_discrete_map=REGION_COLORS,
        opacity=0.4,
        trendline="ols",
        labels={socio_var: SOCIO_COLS_DISPLAY[socio_var], health_var: OUTCOME_COLS[health_var]},
    )
    fig.update_traces(marker=dict(size=3))
    fig.update_layout(height=550, margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)

    corr_val = df_clean[socio_var].corr(df_clean[health_var])
    st.metric(
        f"Pearson Correlation",
        f"{corr_val:.4f}",
    )

    st.divider()

    # Income vs all health outcomes
    st.subheader("Income vs All Health Outcomes")
    income_corrs = []
    for col, name in OUTCOME_COLS.items():
        if col == "o_total_quantity_per_capita":
            continue
        r = df["c_net annual income"].corr(df[col])
        income_corrs.append({"Condition": name, "Correlation with Income": round(r, 4)})
    income_df = pd.DataFrame(income_corrs).sort_values("Correlation with Income")

    fig2 = px.bar(
        income_df,
        x="Correlation with Income",
        y="Condition",
        orientation="h",
        color="Correlation with Income",
        color_continuous_scale="RdBu_r",
        color_continuous_midpoint=0,
    )
    fig2.update_layout(height=350, margin=dict(l=0, r=20, t=10, b=0), coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # Deprivation breakdown
    st.subheader("Deprivation Dimensions vs Health")
    dep_cols = [
        "c_percent households not deprived in any dimension",
        "c_percent households deprived in one dimension",
        "c_percent households deprived in two dimensions",
        "c_percent households deprived in three dimensions",
    ]
    dep_names = ["Not Deprived", "1 Dimension", "2 Dimensions", "3 Dimensions"]

    dep_corrs = []
    for dc, dn in zip(dep_cols, dep_names):
        for oc, on in OUTCOME_COLS.items():
            if oc == "o_total_quantity_per_capita":
                continue
            r = df[dc].corr(df[oc])
            dep_corrs.append({"Deprivation": dn, "Condition": on, "Correlation": round(r, 4)})

    dep_df = pd.DataFrame(dep_corrs)
    dep_pivot = dep_df.pivot(index="Deprivation", columns="Condition", values="Correlation")
    dep_pivot = dep_pivot.reindex(dep_names)

    fig3 = px.imshow(
        dep_pivot,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-0.5,
        zmax=0.5,
        aspect="auto",
    )
    fig3.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig3, use_container_width=True)


# ---------------------------------------------------------------------------
# PAGE: Satellite Features
# ---------------------------------------------------------------------------
elif page == "Satellite Features":
    st.title("Sentinel-2 Satellite Features Analysis")

    df = prepare_data(2019)

    # Available seasons
    season_folders = sorted([
        f.stem for f in IMG_FEAT_DIR.iterdir() if f.suffix == ".parquet"
    ]) if IMG_FEAT_DIR.exists() else []

    if not season_folders:
        st.warning("No satellite feature data found.")
        st.stop()

    season = st.selectbox("Select season", season_folders)
    img_df = load_image_features(season)

    if img_df.empty:
        st.warning(f"No data found for {season}.")
        st.stop()

    st.markdown(f"**{len(img_df):,}** LSOAs with satellite statistics for **{season}**")

    # Merge with spatial data for region info
    regions = load_regions()
    img_merged = img_df.merge(
        regions[["LSOA21CD", "RGN22NM"]],
        left_on="geography code",
        right_on="LSOA21CD",
        how="left",
    )

    # Band statistics overview
    bands = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]
    band_names = {
        "B02": "Blue", "B03": "Green", "B04": "Red",
        "B05": "Veg Red Edge 1", "B06": "Veg Red Edge 2", "B07": "Veg Red Edge 3",
        "B08": "NIR", "B8A": "Narrow NIR", "B11": "SWIR 1", "B12": "SWIR 2",
    }

    st.subheader("Mean Reflectance by Region")
    band_choice = st.selectbox(
        "Select band",
        bands,
        format_func=lambda x: f"{x} — {band_names.get(x, x)}",
    )

    mean_col = f"mean_{band_choice}"
    if mean_col in img_merged.columns:
        region_band = (
            img_merged.groupby("RGN22NM")[mean_col]
            .mean()
            .sort_values(ascending=True)
            .reset_index()
        )
        region_band.columns = ["Region", f"Mean {band_choice}"]
        fig = px.bar(
            region_band,
            x=f"Mean {band_choice}",
            y="Region",
            orientation="h",
            color="Region",
            color_discrete_map=REGION_COLORS,
        )
        fig.update_layout(height=400, showlegend=False, margin=dict(l=0, r=20, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Satellite vs health outcome
    st.subheader("Satellite Features vs Health Outcomes")
    sat_col = st.selectbox(
        "Satellite feature",
        [c for c in img_df.columns if c != "geography code"],
        index=0,
    )
    health_out = st.selectbox(
        "Health outcome",
        list(OUTCOME_COLS.keys()),
        format_func=lambda x: OUTCOME_COLS[x],
        key="sat_health",
    )

    # Merge satellite with health data
    sat_health = img_df.merge(
        df[["geography code", health_out, "Region"]],
        on="geography code",
        how="inner",
    )
    sat_health = sat_health.dropna(subset=[sat_col, health_out])
    sat_sample = sat_health.sample(n=min(6000, len(sat_health)), random_state=42)

    fig2 = px.scatter(
        sat_sample,
        x=sat_col,
        y=health_out,
        color="Region",
        color_discrete_map=REGION_COLORS,
        opacity=0.3,
        trendline="ols",
        labels={health_out: OUTCOME_COLS[health_out]},
    )
    fig2.update_traces(marker=dict(size=3))
    fig2.update_layout(height=500, margin=dict(t=30))
    st.plotly_chart(fig2, use_container_width=True)

    corr_val = sat_health[sat_col].corr(sat_health[health_out])
    st.metric("Pearson Correlation", f"{corr_val:.4f}")
