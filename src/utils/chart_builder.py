"""
Chart Builder untuk aplikasi Prediksi Jumlah Pengangguran Sulawesi Utara.

File ini bertanggung jawab untuk membuat visualisasi:
- grafik dataset historis,
- grafik aktual vs prediksi,
- grafik prediksi masa depan,
- grafik gabungan aktual, prediksi test, dan prediksi masa depan,
- heatmap korelasi,
- grafik loss training.

Visualisasi utama menggunakan Plotly agar interaktif di Streamlit.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config.settings import TARGET_COLUMN, YEAR_COLUMN


# ============================================================
# GENERAL CHART CONFIG
# ============================================================

DEFAULT_TEMPLATE = "plotly_white"


def apply_default_layout(
    fig: go.Figure,
    title: str,
    xaxis_title: str = "Tahun",
    yaxis_title: str = "Jumlah Pengangguran",
) -> go.Figure:
    """
    Menerapkan layout standar untuk chart Plotly.
    """

    fig.update_layout(
        title=title,
        template=DEFAULT_TEMPLATE,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        hovermode="x unified",
        legend_title_text="Keterangan",
        margin=dict(l=20, r=20, t=70, b=20),
    )

    fig.update_xaxes(
        showgrid=True,
        tickmode="linear",
    )

    fig.update_yaxes(
        showgrid=True,
        separatethousands=True,
    )

    return fig


def empty_figure(message: str = "Data belum tersedia.") -> go.Figure:
    """
    Membuat figure kosong dengan pesan.
    """

    fig = go.Figure()

    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=16),
    )

    fig.update_layout(
        template=DEFAULT_TEMPLATE,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=20, r=20, t=20, b=20),
    )

    return fig


# ============================================================
# DATASET CHARTS
# ============================================================

def build_target_history_chart(
    df: pd.DataFrame,
    year_column: str = YEAR_COLUMN,
    target_column: str = TARGET_COLUMN,
) -> go.Figure:
    """
    Membuat grafik historis target Total_Pengangguran.
    """

    if df is None or df.empty:
        return empty_figure("Dataset belum tersedia.")

    if year_column not in df.columns or target_column not in df.columns:
        return empty_figure(
            f"Kolom {year_column} atau {target_column} tidak ditemukan."
        )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df[year_column],
            y=df[target_column],
            mode="lines+markers",
            name="Aktual",
            hovertemplate=(
                "Tahun: %{x}<br>"
                "Jumlah Pengangguran: %{y:,.0f} jiwa"
                "<extra></extra>"
            ),
        )
    )

    return apply_default_layout(
        fig=fig,
        title="Data Historis Jumlah Pengangguran",
        xaxis_title="Tahun",
        yaxis_title="Jumlah Pengangguran",
    )


def build_all_variables_chart(
    df: pd.DataFrame,
    year_column: str = YEAR_COLUMN,
) -> go.Figure:
    """
    Membuat grafik semua variabel numerik dalam dataset.

    Grafik ini berguna untuk melihat pola setiap variabel dari tahun ke tahun.
    """

    if df is None or df.empty:
        return empty_figure("Dataset belum tersedia.")

    if year_column not in df.columns:
        return empty_figure(f"Kolom {year_column} tidak ditemukan.")

    numeric_columns = [
        column for column in df.columns
        if column != year_column and pd.api.types.is_numeric_dtype(df[column])
    ]

    if not numeric_columns:
        return empty_figure("Tidak ada kolom numerik untuk divisualisasikan.")

    fig = go.Figure()

    for column in numeric_columns:
        fig.add_trace(
            go.Scatter(
                x=df[year_column],
                y=df[column],
                mode="lines+markers",
                name=column,
                hovertemplate=(
                    "Tahun: %{x}<br>"
                    f"{column}: "
                    "%{y:,.2f}"
                    "<extra></extra>"
                ),
            )
        )

    return apply_default_layout(
        fig=fig,
        title="Visualisasi Seluruh Variabel Dataset",
        xaxis_title="Tahun",
        yaxis_title="Nilai",
    )


# ============================================================
# PREDICTION CHARTS
# ============================================================

def build_test_prediction_chart(
    test_predictions: pd.DataFrame,
) -> go.Figure:
    """
    Membuat grafik aktual vs prediksi pada data test.

    Dataframe harus memiliki kolom:
    - Tahun
    - Aktual
    - Prediksi
    """

    if test_predictions is None or test_predictions.empty:
        return empty_figure("Data hasil prediksi test belum tersedia.")

    required_columns = ["Tahun", "Aktual", "Prediksi"]
    missing_columns = [
        column for column in required_columns
        if column not in test_predictions.columns
    ]

    if missing_columns:
        return empty_figure(
            "Kolom berikut tidak ditemukan: "
            + ", ".join(missing_columns)
        )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=test_predictions["Tahun"],
            y=test_predictions["Aktual"],
            mode="lines+markers",
            name="Aktual",
            hovertemplate=(
                "Tahun: %{x}<br>"
                "Aktual: %{y:,.0f} jiwa"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=test_predictions["Tahun"],
            y=test_predictions["Prediksi"],
            mode="lines+markers",
            name="Prediksi",
            hovertemplate=(
                "Tahun: %{x}<br>"
                "Prediksi: %{y:,.0f} jiwa"
                "<extra></extra>"
            ),
        )
    )

    return apply_default_layout(
        fig=fig,
        title="Aktual vs Prediksi pada Data Test",
        xaxis_title="Tahun",
        yaxis_title="Jumlah Pengangguran",
    )


def build_future_prediction_chart(
    future_predictions: pd.DataFrame,
) -> go.Figure:
    """
    Membuat grafik prediksi masa depan.

    Dataframe harus memiliki kolom:
    - Tahun
    - Prediksi
    """

    if future_predictions is None or future_predictions.empty:
        return empty_figure("Data prediksi masa depan belum tersedia.")

    required_columns = ["Tahun", "Prediksi"]
    missing_columns = [
        column for column in required_columns
        if column not in future_predictions.columns
    ]

    if missing_columns:
        return empty_figure(
            "Kolom berikut tidak ditemukan: "
            + ", ".join(missing_columns)
        )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=future_predictions["Tahun"],
            y=future_predictions["Prediksi"],
            mode="lines+markers",
            name="Prediksi Masa Depan",
            line=dict(dash="dash"),
            hovertemplate=(
                "Tahun: %{x}<br>"
                "Prediksi: %{y:,.0f} jiwa"
                "<extra></extra>"
            ),
        )
    )

    return apply_default_layout(
        fig=fig,
        title="Prediksi Jumlah Pengangguran Masa Depan",
        xaxis_title="Tahun",
        yaxis_title="Jumlah Pengangguran",
    )


def build_combined_prediction_chart(
    test_predictions: Optional[pd.DataFrame] = None,
    future_predictions: Optional[pd.DataFrame] = None,
) -> go.Figure:
    """
    Membuat grafik gabungan:
    - Aktual data test,
    - Prediksi data test,
    - Prediksi masa depan.
    """

    has_test = test_predictions is not None and not test_predictions.empty
    has_future = future_predictions is not None and not future_predictions.empty

    if not has_test and not has_future:
        return empty_figure("Data prediksi belum tersedia.")

    fig = go.Figure()

    if has_test:
        if {"Tahun", "Aktual", "Prediksi"}.issubset(test_predictions.columns):
            fig.add_trace(
                go.Scatter(
                    x=test_predictions["Tahun"],
                    y=test_predictions["Aktual"],
                    mode="lines+markers",
                    name="Aktual",
                    hovertemplate=(
                        "Tahun: %{x}<br>"
                        "Aktual: %{y:,.0f} jiwa"
                        "<extra></extra>"
                    ),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=test_predictions["Tahun"],
                    y=test_predictions["Prediksi"],
                    mode="lines+markers",
                    name="Prediksi Test",
                    hovertemplate=(
                        "Tahun: %{x}<br>"
                        "Prediksi Test: %{y:,.0f} jiwa"
                        "<extra></extra>"
                    ),
                )
            )

    if has_future:
        if {"Tahun", "Prediksi"}.issubset(future_predictions.columns):
            fig.add_trace(
                go.Scatter(
                    x=future_predictions["Tahun"],
                    y=future_predictions["Prediksi"],
                    mode="lines+markers",
                    name="Prediksi Masa Depan",
                    line=dict(dash="dash"),
                    hovertemplate=(
                        "Tahun: %{x}<br>"
                        "Prediksi Masa Depan: %{y:,.0f} jiwa"
                        "<extra></extra>"
                    ),
                )
            )

    return apply_default_layout(
        fig=fig,
        title="Aktual, Prediksi Test, dan Prediksi Masa Depan",
        xaxis_title="Tahun",
        yaxis_title="Jumlah Pengangguran",
    )


# ============================================================
# CORRELATION CHARTS
# ============================================================

def build_correlation_heatmap(
    correlation_matrix: pd.DataFrame,
) -> go.Figure:
    """
    Membuat heatmap korelasi antar variabel.

    Data input adalah correlation_matrix dari pandas.
    """

    if correlation_matrix is None or correlation_matrix.empty:
        return empty_figure("Data korelasi belum tersedia.")

    fig = px.imshow(
        correlation_matrix,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="Viridis",
        zmin=-1,
        zmax=1,
        title="Heatmap Korelasi Antar Variabel",
    )

    fig.update_layout(
        template=DEFAULT_TEMPLATE,
        margin=dict(l=20, r=20, t=70, b=20),
    )

    return fig


def build_correlation_bar_chart(
    correlation_values: dict,
) -> go.Figure:
    """
    Membuat grafik batang korelasi fitur terhadap target.
    """

    if not correlation_values:
        return empty_figure("Nilai korelasi belum tersedia.")

    df_corr = pd.DataFrame(
        {
            "Fitur": list(correlation_values.keys()),
            "Korelasi": list(correlation_values.values()),
        }
    )

    df_corr = df_corr.sort_values("Korelasi", ascending=False)

    fig = px.bar(
        df_corr,
        x="Fitur",
        y="Korelasi",
        title="Korelasi Fitur terhadap Total Pengangguran",
        template=DEFAULT_TEMPLATE,
    )

    fig.update_layout(
        xaxis_title="Fitur",
        yaxis_title="Nilai Korelasi",
        margin=dict(l=20, r=20, t=70, b=20),
    )

    fig.update_yaxes(range=[-1, 1])

    return fig


# ============================================================
# TRAINING HISTORY CHART
# ============================================================

def build_training_loss_chart(history: dict) -> go.Figure:
    """
    Membuat grafik loss training dan validation loss.

    Input:
        history dari Keras:
        {
            "loss": [...],
            "val_loss": [...]
        }
    """

    if not history or "loss" not in history:
        return empty_figure("Riwayat training belum tersedia.")

    epochs = list(range(1, len(history["loss"]) + 1))

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=epochs,
            y=history["loss"],
            mode="lines",
            name="Training Loss",
            hovertemplate=(
                "Epoch: %{x}<br>"
                "Loss: %{y:.6f}"
                "<extra></extra>"
            ),
        )
    )

    if "val_loss" in history and history["val_loss"]:
        fig.add_trace(
            go.Scatter(
                x=epochs,
                y=history["val_loss"],
                mode="lines",
                name="Validation Loss",
                hovertemplate=(
                    "Epoch: %{x}<br>"
                    "Validation Loss: %{y:.6f}"
                    "<extra></extra>"
                ),
            )
        )

    return apply_default_layout(
        fig=fig,
        title="Grafik Loss Training Model LSTM",
        xaxis_title="Epoch",
        yaxis_title="Loss",
    )