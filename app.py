import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(page_title="Dashboard Omset & AR Tahun 2026", page_icon="📊", layout="wide")

# =====================================================
# LOAD DATA
# =====================================================


@st.cache_data
def load_data():

    df = pd.read_excel("data.xlsx", sheet_name=0)

    # Bersihkan nama kolom
    df.columns = df.columns.str.strip()

    # Pastikan kolom numerik
    numeric_cols = ["TARGET", "OMSET", "TARGET AR", "REALISASI"]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


df = load_data()

# =====================================================
# URUTAN BULAN
# =====================================================

bulan_order = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "Mei",
    "Jun",
    "Jul",
    "Agu",
    "Sep",
    "Okt",
    "Nov",
    "Des",
]

df["BULAN"] = pd.Categorical(df["BULAN"], categories=bulan_order, ordered=True)

df = df.sort_values("BULAN")

# =====================================================
# FILTER
# =====================================================

st.sidebar.header("Filter Dashboard")

bulan_list = df["BULAN"].dropna().astype(str).unique().tolist()

selected_bulan = st.sidebar.selectbox("Pilih Bulan", ["Semua"] + bulan_list)

depo_list = sorted(df["DEPO"].dropna().unique())

selected_depo = st.sidebar.selectbox("Pilih Depo", ["Semua"] + depo_list)

filtered = df.copy()

if selected_bulan != "Semua":
    filtered = filtered[filtered["BULAN"] == selected_bulan]

if selected_depo != "Semua":
    filtered = filtered[filtered["DEPO"] == selected_depo]

# =====================================================
# KPI
# =====================================================

target = filtered["TARGET"].sum()
omset = filtered["OMSET"].sum()

target_ar = filtered["TARGET AR"].sum()
realisasi = filtered["REALISASI"].sum()

persen_omset = omset / target * 100 if target > 0 else 0

persen_realisasi = realisasi / target_ar * 100 if target_ar > 0 else 0

st.title("📊 Dashboard Omset & AR Tahun 2026")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Target Omset", f"Rp {target/1_000_000_000:.2f} M")

col2.metric("Omset", f"Rp {omset/1_000_000_000:.2f} M", f"Achv {persen_omset:.2f}%")

col3.metric("Target AR", f"Rp {target_ar/1_000_000_000:.2f} M")

col4.metric(
    "Realisasi AR", f"Rp {realisasi/1_000_000_000:.2f} M", f"Achv {persen_realisasi:.2f}%"
)

st.divider()

# =====================================================
# TARGET VS REALISASI
# =====================================================

st.subheader("Target vs Realisasi")

summary = pd.DataFrame(
    {
        "Kategori": ["Target Omset", "Omset", "Target AR", "Realisasi AR"],
        "Nilai": [
            target / 1_000_000_000,
            omset / 1_000_000_000,
            target_ar / 1_000_000_000,
            realisasi / 1_000_000_000,
        ],
    }
)

fig1 = px.bar(summary, x="Kategori", y="Nilai", text="Nilai")

fig1.update_traces(texttemplate="%{y:.2f} M", textposition="outside")

fig1.update_layout(height=500, yaxis_title="Miliar Rupiah")

st.plotly_chart(fig1, use_container_width=True)

# =====================================================
# TREND BULANAN
# =====================================================

if selected_bulan == "Semua":

    st.subheader("Trend % Omset & % Realisasi")

    monthly = filtered.groupby("BULAN", as_index=False, observed=True).agg(
        {"TARGET": "sum", "OMSET": "sum", "TARGET AR": "sum", "REALISASI": "sum"}
    )

    monthly = monthly.sort_values("BULAN")

    monthly["% OMSET"] = monthly["OMSET"] / monthly["TARGET"] * 100

    monthly["% REALISASI"] = monthly["REALISASI"] / monthly["TARGET AR"] * 100

    fig2 = go.Figure()

    # ==========================
    # OMSET
    # ==========================

    fig2.add_trace(
        go.Scatter(
            x=monthly["BULAN"],
            y=monthly["% OMSET"],
            mode="lines+markers+text",
            name="% Omset",
            text=[f"{x:.2f}%" for x in monthly["% OMSET"]],
            textposition="top center",
            textfont=dict(size=12),
            hovertemplate="<b>%{x}</b><br>" "Omset: %{y:.2f}%<extra></extra>",
        )
    )

    # ==========================
    # REALISASI
    # ==========================

    fig2.add_trace(
        go.Scatter(
            x=monthly["BULAN"],
            y=monthly["% REALISASI"],
            mode="lines+markers+text",
            name="% Realisasi",
            text=[f"{x:.2f}%" for x in monthly["% REALISASI"]],
            textposition="bottom center",
            textfont=dict(size=12),
            hovertemplate="<b>%{x}</b><br>" "Realisasi: %{y:.2f}%<extra></extra>",
        )
    )

    # ==========================
    # HIGHLIGHT BULAN TERAKHIR
    # ==========================

    last_month = monthly.iloc[-1]

    fig2.add_trace(
        go.Scatter(
            x=[last_month["BULAN"]],
            y=[last_month["% OMSET"]],
            mode="markers",
            name="Latest Omset",
            marker=dict(size=18, line=dict(width=3)),
            showlegend=False,
        )
    )

    fig2.add_trace(
        go.Scatter(
            x=[last_month["BULAN"]],
            y=[last_month["% REALISASI"]],
            mode="markers",
            name="Latest Realisasi",
            marker=dict(size=18, line=dict(width=3)),
            showlegend=False,
        )
    )

    fig2.update_layout(
        height=550,
        hovermode="x unified",
        yaxis_title="Persentase (%)",
        title="Trend Kinerja Bulanan",
    )

    fig2.update_yaxes(tickformat=".2f")

    st.plotly_chart(fig2, use_container_width=True)

# =====================================================
# RANKING DEPO
# =====================================================

if selected_depo == "Semua":

    st.subheader("Ranking Omset Depo")

    ranking = (
        filtered.groupby("DEPO", as_index=False)
        .agg({"OMSET": "sum"})
        .sort_values(by="OMSET", ascending=False)
    )

    ranking["OMSET_M"] = ranking["OMSET"] / 1_000_000_000

    fig3 = px.bar(ranking, x="OMSET_M", y="DEPO", orientation="h", text="OMSET_M")

    fig3.update_traces(texttemplate="%{x:.2f} M", textposition="outside")

    fig3.update_layout(
        height=600, xaxis_title="Omset (Miliar Rupiah)", yaxis_title="Depo"
    )

    st.plotly_chart(fig3, use_container_width=True)

# =====================================================
# KONTRIBUSI OMSET DEPO
# =====================================================

st.subheader("Kontribusi Omset per Depo")

kontribusi = filtered.groupby("DEPO", as_index=False).agg({"OMSET": "sum"})

total_omset = kontribusi["OMSET"].sum()

kontribusi["KONTRIBUSI"] = kontribusi["OMSET"] / total_omset * 100

fig_kontribusi = px.pie(kontribusi, names="DEPO", values="OMSET", hole=0.4)

fig_kontribusi.update_traces(
    textinfo="label+percent",
    hovertemplate="<b>%{label}</b><br>"
    + "Omset: Rp %{value:,.0f}<br>"
    + "Kontribusi: %{percent}<extra></extra>",
)

fig_kontribusi.update_layout(height=600)

st.plotly_chart(fig_kontribusi, use_container_width=True)

st.subheader("Detail Kontribusi Depo")

kontribusi_display = kontribusi.copy()

kontribusi_display["OMSET"] = kontribusi_display["OMSET"].apply(
    lambda x: f"{x:,.0f}".replace(",", ".")
)

kontribusi_display["KONTRIBUSI"] = kontribusi_display["KONTRIBUSI"].apply(
    lambda x: f"{x:.2f}%"
)

kontribusi_display = kontribusi_display.sort_values("KONTRIBUSI", ascending=False)

st.dataframe(kontribusi_display, use_container_width=True, hide_index=True)

# =====================================================
# BREAKDOWN DEPO
# =====================================================

if selected_depo != "Semua":

    st.subheader(f"Trend Omset {selected_depo}")

    depo_monthly = filtered.sort_values("BULAN")

    fig4 = go.Figure()

    fig4.add_trace(
        go.Bar(
            x=depo_monthly["BULAN"],
            y=depo_monthly["TARGET"] / 1_000_000_000,
            name="Target",
        )
    )

    fig4.add_trace(
        go.Bar(
            x=depo_monthly["BULAN"],
            y=depo_monthly["OMSET"] / 1_000_000_000,
            name="Omset",
        )
    )

    fig4.update_layout(barmode="group", yaxis_title="Miliar Rupiah", height=500)

    st.plotly_chart(fig4, use_container_width=True)

# =====================================================
# DATA DETAIL
# =====================================================

st.subheader("Data Detail")

filtered = filtered.sort_values(["BULAN", "DEPO"])

display_df = filtered.copy()

# Hitung persentase untuk ditampilkan
display_df["% OMSET"] = display_df.apply(
    lambda x: (x["OMSET"] / x["TARGET"] * 100) if x["TARGET"] > 0 else 0, axis=1
)

display_df["% REALISASI"] = display_df.apply(
    lambda x: (x["REALISASI"] / x["TARGET AR"] * 100) if x["TARGET AR"] > 0 else 0,
    axis=1,
)

# Format angka Indonesia
for col in ["TARGET", "OMSET", "TARGET AR", "REALISASI"]:
    display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}".replace(",", "."))

# Format persen 2 digit
display_df["% OMSET"] = display_df["% OMSET"].apply(lambda x: f"{x:.2f}%")

display_df["% REALISASI"] = display_df["% REALISASI"].apply(lambda x: f"{x:.2f}%")

st.dataframe(display_df, use_container_width=True, hide_index=True)
# =====================================================
# DOWNLOAD
# =====================================================

csv = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    "📥 Download CSV", data=csv, file_name="dashboard_export.csv", mime="text/csv"
)
