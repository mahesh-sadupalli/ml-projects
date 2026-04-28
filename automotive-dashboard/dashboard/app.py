import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Porsche Sales Intelligence",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

PORSCHE_RED = "#d5001c"
PORSCHE_DARK = "#0a0a0a"
PORSCHE_GOLD = "#c9b037"

MODEL_COLORS = {
    "911 Carrera": "#d5001c",
    "Taycan": "#00a19a",
    "Panamera": "#4a4a4a",
    "Cayenne": "#c9b037",
    "Macan": "#2c5f8a",
    "718 Boxster": "#e87722",
}

REGION_COLORS = {
    "Germany": "#d5001c",
    "USA": "#2c5f8a",
    "China": "#c9b037",
    "UK": "#4a4a4a",
    "France": "#00a19a",
}

CHANNEL_COLORS = {
    "Dealership": "#d5001c",
    "Online": "#00a19a",
    "Corporate Sales": "#c9b037",
    "Leasing": "#2c5f8a",
}

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f0f0f0"),
    margin=dict(l=20, r=20, t=40, b=20),
)


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
@st.cache_data
def load_sales() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "sales_data_csv.txt", parse_dates=["Date"])
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    df["Month_dt"] = df["Date"].dt.to_period("M").apply(lambda p: p.start_time)
    return df


@st.cache_data
def load_leads() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "leads_data_csv.txt", parse_dates=["Date"])
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    df["Converted"] = df["Status"] == "Won"
    return df


@st.cache_data
def load_models() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "models_info_csv.txt")


@st.cache_data
def load_regions() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "regions_info_csv.txt")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    """
    <div style='text-align:center; padding: 10px 0 20px 0;'>
        <h1 style='margin:0; font-size:1.6em; color:#d5001c;'>PORSCHE</h1>
        <p style='margin:0; color:#888; font-size:0.85em; letter-spacing:3px;'>
        SALES INTELLIGENCE</p>
    </div>
    """,
    unsafe_allow_html=True,
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Executive Overview",
        "Sales Trends",
        "Model Performance",
        "Regional Analysis",
        "Lead Funnel",
        "Channel & Customer Mix",
    ],
    label_visibility="collapsed",
)

st.sidebar.divider()

# Global filters
sales = load_sales()
leads = load_leads()
models = load_models()
regions = load_regions()

all_models = sorted(sales["Model"].unique())
all_regions = sorted(sales["Region"].unique())

selected_models = st.sidebar.multiselect(
    "Filter Models", all_models, default=all_models
)
selected_regions = st.sidebar.multiselect(
    "Filter Regions", all_regions, default=all_regions
)

sf = sales[sales["Model"].isin(selected_models) & sales["Region"].isin(selected_regions)]
lf = leads[
    leads["Model_Interest"].isin(selected_models)
    & leads["Region"].isin(selected_regions)
]

st.sidebar.divider()
st.sidebar.caption("Data: Porsche Sales H1 2024")
st.sidebar.caption(f"{len(sf)} transactions · {len(lf)} leads")
st.sidebar.caption("Built by Mahesh Sadupalli")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def fmt_eur(val: float) -> str:
    if val >= 1_000_000:
        return f"€{val / 1_000_000:.2f}M"
    if val >= 1_000:
        return f"€{val / 1_000:.0f}K"
    return f"€{val:,.0f}"


def styled_metric_row(metrics: list[tuple[str, str, str | None]]):
    """Render a row of styled metric cards. Each tuple: (label, value, delta)."""
    cols = st.columns(len(metrics))
    for col, (label, value, delta) in zip(cols, metrics):
        col.metric(label, value, delta)


# ---------------------------------------------------------------------------
# PAGE: Executive Overview
# ---------------------------------------------------------------------------
if page == "Executive Overview":
    st.markdown(
        "<h1 style='margin-bottom:0;'>Executive Overview</h1>"
        "<p style='color:#888; margin-top:0;'>H1 2024 · Porsche Sales Performance</p>",
        unsafe_allow_html=True,
    )

    total_rev = sf["Sales_Revenue"].sum()
    total_units = sf["Units_Sold"].sum()
    avg_deal = sf["Sales_Revenue"].mean()
    total_leads = len(lf)
    converted = lf["Converted"].sum()
    conv_rate = converted / total_leads * 100 if total_leads > 0 else 0

    styled_metric_row([
        ("Total Revenue", fmt_eur(total_rev), None),
        ("Units Sold", f"{total_units}", None),
        ("Avg Deal Size", fmt_eur(avg_deal), None),
        ("Total Leads", f"{total_leads}", None),
        ("Conversion Rate", f"{conv_rate:.1f}%", None),
    ])

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Monthly Revenue Trend")
        monthly = (
            sf.groupby("Month_dt")
            .agg(Revenue=("Sales_Revenue", "sum"), Units=("Units_Sold", "sum"))
            .reset_index()
        )
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=monthly["Month_dt"],
                y=monthly["Revenue"],
                mode="lines+markers",
                line=dict(color=PORSCHE_RED, width=3),
                marker=dict(size=8),
                name="Revenue",
                hovertemplate="%{x|%b %Y}<br>€%{y:,.0f}<extra></extra>",
            )
        )
        fig.update_layout(
            **PLOT_LAYOUT,
            height=350,
            xaxis=dict(
                showgrid=False,
                dtick="M1",
                tickformat="%b",
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
                tickprefix="€",
            ),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Revenue by Model")
        model_rev = (
            sf.groupby("Model")["Sales_Revenue"]
            .sum()
            .sort_values(ascending=True)
            .reset_index()
        )
        fig2 = px.bar(
            model_rev,
            x="Sales_Revenue",
            y="Model",
            orientation="h",
            color="Model",
            color_discrete_map=MODEL_COLORS,
        )
        fig2.update_layout(
            **PLOT_LAYOUT,
            height=350,
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="€"),
            yaxis=dict(showgrid=False),
        )
        fig2.update_traces(
            hovertemplate="%{y}<br>€%{x:,.0f}<extra></extra>"
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    left2, right2 = st.columns(2)

    with left2:
        st.subheader("Revenue Share by Region")
        region_rev = sf.groupby("Region")["Sales_Revenue"].sum().reset_index()
        fig3 = px.pie(
            region_rev,
            values="Sales_Revenue",
            names="Region",
            color="Region",
            color_discrete_map=REGION_COLORS,
            hole=0.45,
        )
        fig3.update_layout(**PLOT_LAYOUT, height=350, showlegend=True)
        fig3.update_traces(
            textinfo="label+percent",
            textfont_size=12,
            hovertemplate="%{label}<br>€%{value:,.0f}<br>%{percent}<extra></extra>",
        )
        st.plotly_chart(fig3, use_container_width=True)

    with right2:
        st.subheader("Channel Distribution")
        channel = sf.groupby("Sales_Channel")["Sales_Revenue"].sum().reset_index()
        fig4 = px.pie(
            channel,
            values="Sales_Revenue",
            names="Sales_Channel",
            color="Sales_Channel",
            color_discrete_map=CHANNEL_COLORS,
            hole=0.45,
        )
        fig4.update_layout(**PLOT_LAYOUT, height=350, showlegend=True)
        fig4.update_traces(
            textinfo="label+percent",
            textfont_size=12,
            hovertemplate="%{label}<br>€%{value:,.0f}<br>%{percent}<extra></extra>",
        )
        st.plotly_chart(fig4, use_container_width=True)


# ---------------------------------------------------------------------------
# PAGE: Sales Trends
# ---------------------------------------------------------------------------
elif page == "Sales Trends":
    st.markdown(
        "<h1 style='margin-bottom:0;'>Sales Trends</h1>"
        "<p style='color:#888; margin-top:0;'>Monthly revenue & volume analysis</p>",
        unsafe_allow_html=True,
    )

    monthly = (
        sf.groupby("Month_dt")
        .agg(Revenue=("Sales_Revenue", "sum"), Units=("Units_Sold", "sum"))
        .reset_index()
    )
    monthly["Avg_Price"] = monthly["Revenue"] / monthly["Units"]
    monthly["Rev_Change"] = monthly["Revenue"].pct_change() * 100

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("Revenue (€)", "Units Sold"),
    )
    fig.add_trace(
        go.Bar(
            x=monthly["Month_dt"],
            y=monthly["Revenue"],
            marker_color=PORSCHE_RED,
            name="Revenue",
            hovertemplate="%{x|%b %Y}<br>€%{y:,.0f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=monthly["Month_dt"],
            y=monthly["Units"],
            marker_color="#2c5f8a",
            name="Units",
            hovertemplate="%{x|%b %Y}<br>%{y} units<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.update_layout(
        **PLOT_LAYOUT,
        height=500,
        showlegend=False,
    )
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
    fig.update_xaxes(showgrid=False, dtick="M1", tickformat="%b %Y")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Model-level monthly breakdown
    st.subheader("Monthly Revenue by Model")
    model_monthly = (
        sf.groupby(["Month_dt", "Model"])["Sales_Revenue"]
        .sum()
        .reset_index()
    )
    fig2 = px.area(
        model_monthly,
        x="Month_dt",
        y="Sales_Revenue",
        color="Model",
        color_discrete_map=MODEL_COLORS,
        labels={"Sales_Revenue": "Revenue (€)", "Month_dt": ""},
    )
    fig2.update_layout(
        **PLOT_LAYOUT,
        height=400,
        xaxis=dict(showgrid=False, dtick="M1", tickformat="%b"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="€"),
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Month-over-month table
    st.subheader("Month-over-Month Summary")
    monthly_display = monthly[["Month_dt", "Revenue", "Units", "Avg_Price", "Rev_Change"]].copy()
    monthly_display["Month_dt"] = monthly_display["Month_dt"].dt.strftime("%b %Y")
    monthly_display.columns = ["Month", "Revenue (€)", "Units", "Avg Price (€)", "MoM Change (%)"]
    st.dataframe(
        monthly_display.style.format({
            "Revenue (€)": "€{:,.0f}",
            "Avg Price (€)": "€{:,.0f}",
            "MoM Change (%)": "{:+.1f}%",
        }),
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# PAGE: Model Performance
# ---------------------------------------------------------------------------
elif page == "Model Performance":
    st.markdown(
        "<h1 style='margin-bottom:0;'>Model Performance</h1>"
        "<p style='color:#888; margin-top:0;'>Product-level analytics across the lineup</p>",
        unsafe_allow_html=True,
    )

    model_stats = (
        sf.groupby("Model")
        .agg(
            Revenue=("Sales_Revenue", "sum"),
            Units=("Units_Sold", "sum"),
            Avg_Price=("Sales_Revenue", "mean"),
            Transactions=("Sale_ID", "count"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    model_stats = model_stats.merge(
        models[["Model", "Category", "Engine_Type", "Base_Price"]],
        on="Model",
        how="left",
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Revenue vs Volume")
        fig = px.scatter(
            model_stats,
            x="Units",
            y="Revenue",
            size="Avg_Price",
            color="Model",
            color_discrete_map=MODEL_COLORS,
            text="Model",
            size_max=50,
        )
        fig.update_traces(textposition="top center", textfont_size=11)
        fig.update_layout(
            **PLOT_LAYOUT,
            height=420,
            showlegend=False,
            xaxis=dict(title="Units Sold", showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(title="Revenue (€)", showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="€"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Avg Deal Size vs Base Price")
        fig2 = go.Figure()
        fig2.add_trace(
            go.Bar(
                name="Base Price",
                x=model_stats["Model"],
                y=model_stats["Base_Price"],
                marker_color="rgba(255,255,255,0.15)",
                hovertemplate="%{x}<br>Base: €%{y:,.0f}<extra></extra>",
            )
        )
        fig2.add_trace(
            go.Bar(
                name="Avg Deal",
                x=model_stats["Model"],
                y=model_stats["Avg_Price"],
                marker_color=PORSCHE_RED,
                hovertemplate="%{x}<br>Avg Deal: €%{y:,.0f}<extra></extra>",
            )
        )
        fig2.update_layout(
            **PLOT_LAYOUT,
            height=420,
            barmode="group",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="€"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # Engine type breakdown
    st.subheader("Revenue by Engine Type")
    engine_rev = (
        sf.merge(models[["Model", "Engine_Type"]], on="Model", how="left")
        .groupby("Engine_Type")["Sales_Revenue"]
        .sum()
        .reset_index()
        .sort_values("Sales_Revenue", ascending=False)
    )
    engine_colors = {"Gasoline": "#d5001c", "Hybrid": "#c9b037", "Electric": "#00a19a"}
    fig3 = px.bar(
        engine_rev,
        x="Engine_Type",
        y="Sales_Revenue",
        color="Engine_Type",
        color_discrete_map=engine_colors,
        labels={"Sales_Revenue": "Revenue (€)", "Engine_Type": ""},
    )
    fig3.update_layout(
        **PLOT_LAYOUT,
        height=350,
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="€"),
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Detailed table
    st.subheader("Model Summary Table")
    display = model_stats[["Model", "Category", "Engine_Type", "Base_Price", "Units", "Revenue", "Avg_Price"]].copy()
    display.columns = ["Model", "Category", "Engine", "Base Price", "Units", "Total Revenue", "Avg Deal"]
    st.dataframe(
        display.style.format({
            "Base Price": "€{:,.0f}",
            "Total Revenue": "€{:,.0f}",
            "Avg Deal": "€{:,.0f}",
        }),
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# PAGE: Regional Analysis
# ---------------------------------------------------------------------------
elif page == "Regional Analysis":
    st.markdown(
        "<h1 style='margin-bottom:0;'>Regional Analysis</h1>"
        "<p style='color:#888; margin-top:0;'>Geographic performance & target achievement</p>",
        unsafe_allow_html=True,
    )

    region_stats = (
        sf.groupby("Region")
        .agg(Revenue=("Sales_Revenue", "sum"), Units=("Units_Sold", "sum"))
        .reset_index()
    )
    region_stats = region_stats.merge(regions, on="Region", how="left")
    # H1 target = monthly target * 6
    region_stats["H1_Target"] = region_stats["Sales_Target_Monthly"] * 6
    region_stats["Achievement"] = (
        region_stats["Revenue"] / region_stats["H1_Target"] * 100
    ).round(1)

    # KPIs per region
    for _, row in region_stats.iterrows():
        st.metric(
            f"{row['Region']} ({row['Country_Code']})",
            fmt_eur(row["Revenue"]),
            f"{row['Achievement']:.1f}% of target",
        )

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Revenue vs H1 Target")
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                name="H1 Target",
                x=region_stats["Region"],
                y=region_stats["H1_Target"],
                marker_color="rgba(255,255,255,0.15)",
            )
        )
        fig.add_trace(
            go.Bar(
                name="Actual Revenue",
                x=region_stats["Region"],
                y=region_stats["Revenue"],
                marker_color=PORSCHE_RED,
            )
        )
        fig.update_layout(
            **PLOT_LAYOUT,
            height=400,
            barmode="group",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="€"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Model Mix by Region")
        region_model = (
            sf.groupby(["Region", "Model"])["Sales_Revenue"]
            .sum()
            .reset_index()
        )
        fig2 = px.bar(
            region_model,
            x="Region",
            y="Sales_Revenue",
            color="Model",
            color_discrete_map=MODEL_COLORS,
            labels={"Sales_Revenue": "Revenue (€)"},
        )
        fig2.update_layout(
            **PLOT_LAYOUT,
            height=400,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="€"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # Monthly trend per region
    st.subheader("Monthly Trend by Region")
    region_monthly = (
        sf.groupby(["Month_dt", "Region"])["Sales_Revenue"]
        .sum()
        .reset_index()
    )
    fig3 = px.line(
        region_monthly,
        x="Month_dt",
        y="Sales_Revenue",
        color="Region",
        color_discrete_map=REGION_COLORS,
        markers=True,
        labels={"Sales_Revenue": "Revenue (€)", "Month_dt": ""},
    )
    fig3.update_layout(
        **PLOT_LAYOUT,
        height=400,
        xaxis=dict(showgrid=False, dtick="M1", tickformat="%b"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="€"),
    )
    st.plotly_chart(fig3, use_container_width=True)


# ---------------------------------------------------------------------------
# PAGE: Lead Funnel
# ---------------------------------------------------------------------------
elif page == "Lead Funnel":
    st.markdown(
        "<h1 style='margin-bottom:0;'>Lead Funnel</h1>"
        "<p style='color:#888; margin-top:0;'>Lead generation, conversion & source attribution</p>",
        unsafe_allow_html=True,
    )

    total_leads = len(lf)
    won = lf["Converted"].sum()
    lost = (lf["Status"] == "Lost").sum()
    pipeline = (lf["Status"] == "Pipeline").sum()
    conv_rate = won / total_leads * 100 if total_leads > 0 else 0

    styled_metric_row([
        ("Total Leads", f"{total_leads}", None),
        ("Won", f"{won}", None),
        ("Lost", f"{lost}", None),
        ("Pipeline", f"{pipeline}", None),
        ("Conversion Rate", f"{conv_rate:.1f}%", None),
    ])

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Conversion Rate by Source")
        source_conv = (
            lf.groupby("Source")
            .agg(Total=("Lead_ID", "count"), Converted=("Converted", "sum"))
            .reset_index()
        )
        source_conv["Rate"] = (source_conv["Converted"] / source_conv["Total"] * 100).round(1)
        source_conv = source_conv.sort_values("Rate", ascending=True)

        colors = [PORSCHE_RED if r > 50 else "#2c5f8a" for r in source_conv["Rate"]]
        fig = go.Figure(
            go.Bar(
                x=source_conv["Rate"],
                y=source_conv["Source"],
                orientation="h",
                marker_color=colors,
                text=source_conv["Rate"].apply(lambda x: f"{x:.0f}%"),
                textposition="outside",
            )
        )
        fig.update_layout(
            **PLOT_LAYOUT,
            height=350,
            xaxis=dict(title="Conversion Rate (%)", showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Lead Volume by Source")
        source_status = (
            lf.groupby(["Source", "Status"])["Lead_ID"]
            .count()
            .reset_index()
            .rename(columns={"Lead_ID": "Count"})
        )
        status_colors = {"Won": "#00a19a", "Lost": "#d5001c", "Pipeline": "#c9b037"}
        fig2 = px.bar(
            source_status,
            x="Source",
            y="Count",
            color="Status",
            color_discrete_map=status_colors,
            barmode="stack",
        )
        fig2.update_layout(
            **PLOT_LAYOUT,
            height=350,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # Monthly lead trend
    st.subheader("Monthly Lead Volume & Conversions")
    monthly_leads = (
        lf.groupby("Month")
        .agg(Leads=("Lead_ID", "count"), Conversions=("Converted", "sum"))
        .reset_index()
    )
    monthly_leads["Rate"] = (monthly_leads["Conversions"] / monthly_leads["Leads"] * 100).round(1)

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(
        go.Bar(
            x=monthly_leads["Month"],
            y=monthly_leads["Leads"],
            name="Leads",
            marker_color="rgba(255,255,255,0.15)",
        ),
        secondary_y=False,
    )
    fig3.add_trace(
        go.Scatter(
            x=monthly_leads["Month"],
            y=monthly_leads["Rate"],
            name="Conversion %",
            mode="lines+markers",
            line=dict(color=PORSCHE_RED, width=3),
            marker=dict(size=8),
        ),
        secondary_y=True,
    )
    fig3.update_layout(
        **PLOT_LAYOUT,
        height=380,
    )
    fig3.update_yaxes(
        title_text="Lead Count",
        showgrid=True,
        gridcolor="rgba(255,255,255,0.05)",
        secondary_y=False,
    )
    fig3.update_yaxes(
        title_text="Conversion Rate (%)",
        showgrid=False,
        secondary_y=True,
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Conversion by model interest
    st.subheader("Conversion by Model Interest")
    model_conv = (
        lf.groupby("Model_Interest")
        .agg(Total=("Lead_ID", "count"), Won=("Converted", "sum"))
        .reset_index()
    )
    model_conv["Rate"] = (model_conv["Won"] / model_conv["Total"] * 100).round(1)
    model_conv = model_conv.sort_values("Rate", ascending=False)
    st.dataframe(
        model_conv.rename(columns={"Model_Interest": "Model", "Total": "Leads", "Rate": "Conv Rate (%)"})
        .style.format({"Conv Rate (%)": "{:.1f}%"}),
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# PAGE: Channel & Customer Mix
# ---------------------------------------------------------------------------
elif page == "Channel & Customer Mix":
    st.markdown(
        "<h1 style='margin-bottom:0;'>Channel & Customer Mix</h1>"
        "<p style='color:#888; margin-top:0;'>Sales channel effectiveness & customer segmentation</p>",
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Revenue by Channel")
        channel = (
            sf.groupby("Sales_Channel")
            .agg(Revenue=("Sales_Revenue", "sum"), Units=("Units_Sold", "sum"))
            .reset_index()
            .sort_values("Revenue", ascending=True)
        )
        channel["Avg_Deal"] = channel["Revenue"] / channel["Units"]
        fig = px.bar(
            channel,
            x="Revenue",
            y="Sales_Channel",
            orientation="h",
            color="Sales_Channel",
            color_discrete_map=CHANNEL_COLORS,
        )
        fig.update_layout(
            **PLOT_LAYOUT,
            height=350,
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="€"),
            yaxis=dict(showgrid=False, title=""),
        )
        fig.update_traces(hovertemplate="%{y}<br>€%{x:,.0f}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Customer Type Split")
        cust = (
            sf.groupby("Customer_Type")
            .agg(Revenue=("Sales_Revenue", "sum"), Units=("Units_Sold", "sum"))
            .reset_index()
        )
        cust_colors = {"Individual": PORSCHE_RED, "Business": "#c9b037"}
        fig2 = px.pie(
            cust,
            values="Revenue",
            names="Customer_Type",
            color="Customer_Type",
            color_discrete_map=cust_colors,
            hole=0.45,
        )
        fig2.update_layout(**PLOT_LAYOUT, height=350)
        fig2.update_traces(
            textinfo="label+percent",
            textfont_size=13,
            hovertemplate="%{label}<br>€%{value:,.0f}<br>%{percent}<extra></extra>",
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # Channel x Region heatmap
    st.subheader("Channel × Region Revenue Heatmap")
    pivot = sf.pivot_table(
        index="Sales_Channel",
        columns="Region",
        values="Sales_Revenue",
        aggfunc="sum",
        fill_value=0,
    )
    fig3 = px.imshow(
        pivot,
        text_auto="€,.0f",
        color_continuous_scale=["#1a1a1a", PORSCHE_RED],
        aspect="auto",
    )
    fig3.update_layout(
        **PLOT_LAYOUT,
        height=350,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # Channel x Model breakdown
    st.subheader("Channel × Model Breakdown")
    channel_model = (
        sf.groupby(["Sales_Channel", "Model"])["Sales_Revenue"]
        .sum()
        .reset_index()
    )
    fig4 = px.bar(
        channel_model,
        x="Sales_Channel",
        y="Sales_Revenue",
        color="Model",
        color_discrete_map=MODEL_COLORS,
        labels={"Sales_Revenue": "Revenue (€)", "Sales_Channel": ""},
    )
    fig4.update_layout(
        **PLOT_LAYOUT,
        height=400,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="€"),
    )
    st.plotly_chart(fig4, use_container_width=True)

    # Top salesperson performance
    st.subheader("Salesperson Performance")
    sp = (
        sf.groupby("Salesperson_ID")
        .agg(
            Revenue=("Sales_Revenue", "sum"),
            Units=("Units_Sold", "sum"),
            Deals=("Sale_ID", "count"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    sp["Avg_Deal"] = sp["Revenue"] / sp["Deals"]
    sp.columns = ["Salesperson", "Revenue (€)", "Units", "Deals", "Avg Deal (€)"]
    st.dataframe(
        sp.style.format({
            "Revenue (€)": "€{:,.0f}",
            "Avg Deal (€)": "€{:,.0f}",
        }),
        use_container_width=True,
        hide_index=True,
    )
