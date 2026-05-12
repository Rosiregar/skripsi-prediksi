from __future__ import annotations

import html
from typing import Iterable

import streamlit as st


def _safe(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        /* =========================================================
           GLOBAL
        ========================================================= */
        html, body, [class*="css"] {
            font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(59, 130, 246, 0.07), transparent 22%),
                radial-gradient(circle at bottom left, rgba(14, 165, 233, 0.06), transparent 18%),
                linear-gradient(180deg, #F4F7FB 0%, #EEF3F9 100%);
        }

        .main .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* =========================================================
           SIDEBAR FINAL - JANGAN UBAH BAGIAN INI
        ========================================================= */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0B1120 0%, #111827 55%, #1E293B 100%) !important;
            border-right: 1px solid rgba(255,255,255,0.08) !important;
        }

        section[data-testid="stSidebar"] * {
            color: #F8FAFC !important;
        }

        section[data-testid="stSidebar"] .sidebar-title {
            color: #FFFFFF !important;
            font-size: 1.35rem !important;
            font-weight: 900 !important;
            letter-spacing: -0.03em !important;
            margin-bottom: 0.2rem !important;
        }

        section[data-testid="stSidebar"] .sidebar-subtitle {
            color: #CBD5E1 !important;
            font-size: 0.88rem !important;
            line-height: 1.45 !important;
            margin-bottom: 1rem !important;
        }

        section[data-testid="stSidebar"] .sidebar-status {
            background: rgba(16, 185, 129, 0.12) !important;
            color: #A7F3D0 !important;
            border: 1px solid rgba(16, 185, 129, 0.25) !important;
            border-radius: 16px !important;
            padding: 0.8rem 0.9rem !important;
            margin-bottom: 1rem !important;
            font-size: 0.9rem !important;
            font-weight: 700 !important;
        }

        section[data-testid="stSidebar"] .menu-label {
            color: #CBD5E1 !important;
            font-size: 0.78rem !important;
            font-weight: 850 !important;
            letter-spacing: 0.08em !important;
            text-transform: uppercase !important;
            margin: 1rem 0 0.45rem 0 !important;
        }

        section[data-testid="stSidebar"] .stButton > button {
            width: 100% !important;
            justify-content: flex-start !important;
            text-align: left !important;
            border-radius: 14px !important;
            min-height: 2.75rem !important;
            padding: 0.45rem 0.85rem !important;
            border: 1px solid transparent !important;
            background: transparent !important;
            color: #F8FAFC !important;
            font-weight: 750 !important;
            box-shadow: none !important;
            transition: all 0.16s ease !important;
        }

        section[data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(59, 130, 246, 0.14) !important;
            border-color: rgba(96, 165, 250, 0.28) !important;
            color: #FFFFFF !important;
            transform: translateX(2px) !important;
            box-shadow: none !important;
        }

        section[data-testid="stSidebar"] .stButton > button:focus {
            box-shadow: none !important;
            outline: none !important;
        }

        section[data-testid="stSidebar"] .stButton > button:active {
            background: rgba(59, 130, 246, 0.18) !important;
            color: #FFFFFF !important;
            box-shadow: none !important;
        }

        section[data-testid="stSidebar"] .nav-active {
            background: linear-gradient(135deg, #2563EB 0%, #0EA5E9 100%) !important;
            color: white !important;
            padding: 0.72rem 0.9rem !important;
            border-radius: 14px !important;
            font-weight: 850 !important;
            margin-bottom: 0.35rem !important;
            box-shadow: 0 12px 26px rgba(37, 99, 235, 0.35) !important;
        }

        /* =========================================================
           HERO / KOTAK BIRU BAGIAN ATAS
        ========================================================= */
        .hero {
            position: relative;
            overflow: hidden;
            padding: 2.4rem 2.2rem;
            border-radius: 30px;
            background:
                radial-gradient(circle at 86% 18%, rgba(255,255,255,0.16), transparent 18%),
                radial-gradient(circle at 12% 85%, rgba(255,255,255,0.08), transparent 18%),
                linear-gradient(135deg, #1D4ED8 0%, #2563EB 35%, #3B82F6 68%, #38BDF8 100%);
            color: white;
            margin-bottom: 1.5rem;
            box-shadow:
                0 28px 60px rgba(37, 99, 235, 0.20),
                inset 0 1px 0 rgba(255,255,255,0.15);
            border: 1px solid rgba(255,255,255,0.16);
        }

        .hero::before {
            content: "";
            position: absolute;
            top: -60px;
            right: -30px;
            width: 220px;
            height: 220px;
            border-radius: 999px;
            background: rgba(255,255,255,0.08);
            filter: blur(2px);
        }

        .hero::after {
            content: "";
            position: absolute;
            bottom: -70px;
            left: -30px;
            width: 210px;
            height: 210px;
            border-radius: 999px;
            background: rgba(255,255,255,0.06);
        }

        .hero-label {
            display: inline-block;
            padding: 0.48rem 0.9rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.16);
            border: 1px solid rgba(255,255,255,0.25);
            backdrop-filter: blur(8px);
            font-size: 0.82rem;
            font-weight: 800;
            margin-bottom: 1rem;
            color: #FFFFFF;
            letter-spacing: 0.01em;
        }

        .hero h1 {
            position: relative;
            z-index: 1;
            font-size: 2.6rem;
            line-height: 1.15;
            font-weight: 950;
            letter-spacing: -0.045em;
            margin: 0 0 0.9rem 0;
            max-width: 900px;
            color: #FFFFFF;
        }

        .hero p {
            position: relative;
            z-index: 1;
            max-width: 860px;
            font-size: 1.04rem;
            line-height: 1.75;
            color: #EAF4FF;
            margin: 0.45rem 0 0 0;
            font-weight: 500;
        }

        /* =========================================================
           PAGE HEADER
        ========================================================= */
        .page-head {
            margin-bottom: 1.15rem;
        }

        .page-head span {
            display: inline-block;
            padding: 0.40rem 0.82rem;
            border-radius: 999px;
            background: #DBEAFE;
            color: #1D4ED8;
            font-size: 0.8rem;
            font-weight: 850;
            margin-bottom: 0.6rem;
        }

        .page-head.admin span {
            background: #FEF3C7;
            color: #B45309;
        }

        .page-head h1 {
            margin: 0;
            color: #0F172A;
            font-size: 2.05rem;
            font-weight: 950;
            letter-spacing: -0.04em;
            line-height: 1.18;
        }

        .page-head p {
            margin-top: 0.38rem;
            color: #64748B;
            font-size: 1rem;
            line-height: 1.7;
            max-width: 900px;
        }

        /* =========================================================
           DETAIL PANEL
        ========================================================= */
        .detail-panel {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.96), rgba(255,255,255,0.99));
            border: 1px solid #DCE5F0;
            border-radius: 28px;
            padding: 1.55rem;
            box-shadow:
                0 18px 40px rgba(15, 23, 42, 0.06),
                inset 0 1px 0 rgba(255,255,255,0.80);
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        .detail-panel h3 {
            margin: 0 0 0.8rem 0;
            color: #0F172A;
            font-size: 1.35rem;
            font-weight: 900;
            letter-spacing: -0.03em;
        }

        .detail-panel p {
            margin: 0.5rem 0;
            color: #475569;
            font-size: 0.98rem;
            line-height: 1.8;
        }

        /* =========================================================
           CARD UMUM
        ========================================================= */
        .card {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,255,255,0.96));
            padding: 1.25rem;
            border-radius: 24px;
            border: 1px solid #E2E8F0;
            box-shadow:
                0 16px 34px rgba(15, 23, 42, 0.06),
                inset 0 1px 0 rgba(255,255,255,0.80);
            height: 100%;
            transition: all 0.18s ease;
        }

        .card:hover {
            transform: translateY(-3px);
            box-shadow:
                0 20px 44px rgba(15, 23, 42, 0.09),
                inset 0 1px 0 rgba(255,255,255,0.85);
        }

        .card h3 {
            color: #0F172A;
            font-size: 1.05rem;
            margin: 0 0 0.45rem 0;
            font-weight: 900;
            letter-spacing: -0.015em;
        }

        .card p {
            color: #64748B;
            font-size: 0.93rem;
            line-height: 1.65;
            margin: 0;
        }

        /* =========================================================
           KARTU TOPIK INFORMASI / 6 KOTAK
        ========================================================= */
        .topic-card {
            background:
                linear-gradient(180deg, #FFFFFF 0%, #F8FBFF 100%);
            border: 1px solid #D8E4F0;
            border-radius: 24px;
            padding: 1.2rem 1.1rem;
            min-height: 150px;
            box-shadow:
                0 16px 36px rgba(15, 23, 42, 0.07),
                0 4px 10px rgba(59, 130, 246, 0.05),
                inset 0 1px 0 rgba(255,255,255,0.95);
            transition: all 0.18s ease;
        }

        .topic-card:hover {
            transform: translateY(-4px);
            box-shadow:
                0 24px 50px rgba(15, 23, 42, 0.09),
                0 8px 20px rgba(59, 130, 246, 0.08),
                inset 0 1px 0 rgba(255,255,255,1);
        }
        .topic-card-link {
            text-decoration: none !important;
            color: inherit !important;
                display: block;
                margin-bottom: 1rem;
        }

        .topic-card.selected {
            border-color: #93C5FD;
            box-shadow:
                0 22px 48px rgba(37, 99, 235, 0.16),
                0 8px 18px rgba(59, 130, 246, 0.12),
                inset 0 1px 0 rgba(255,255,255,1);
        }

        .topic-card-eyebrow {
            color: #64748B;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.75rem;
        }

        .topic-card-title {
            color: #0F172A;
            font-size: 1.35rem;
            font-weight: 950;
            letter-spacing: -0.03em;
            line-height: 1.2;
            margin-bottom: 0.55rem;
        }

        .topic-card-text {
            color: #64748B;
            font-size: 0.94rem;
            line-height: 1.68;
            margin: 0;
        }

        /* =========================================================
           METRIC TILE
        ========================================================= */
        .metric-tile {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,255,255,0.96));
            padding: 1.15rem;
            border-radius: 22px;
            border: 1px solid #E2E8F0;
            box-shadow:
                0 14px 30px rgba(15, 23, 42, 0.06),
                inset 0 1px 0 rgba(255,255,255,0.78);
        }

        .metric-tile .label {
            color: #64748B;
            font-size: 0.82rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.35rem;
        }

        .metric-tile .value {
            color: #0F172A;
            font-size: 1.55rem;
            font-weight: 950;
            letter-spacing: -0.04em;
            line-height: 1.2;
        }

        /* =========================================================
           FEATURE BADGES
        ========================================================= */
        .feature-badge-wrap {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 0.35rem;
            margin-bottom: 0.75rem;
        }

        .feature-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.45rem 0.8rem;
            border-radius: 999px;
            background: #E0F2FE;
            color: #0369A1;
            border: 1px solid #BAE6FD;
            font-size: 0.86rem;
            font-weight: 850;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.38rem 0.72rem;
            border-radius: 999px;
            background: #DBEAFE;
            color: #1D4ED8;
            border: 1px solid #BFDBFE;
            font-size: 0.78rem;
            font-weight: 850;
        }

        .status-badge.success {
            background: #DCFCE7;
            color: #15803D;
            border-color: #BBF7D0;
        }

        .status-badge.warning {
            background: #FEF3C7;
            color: #B45309;
            border-color: #FDE68A;
        }

        .status-badge.danger {
            background: #FEE2E2;
            color: #B91C1C;
            border-color: #FECACA;
        }

        /* =========================================================
           STEP INDICATOR
        ========================================================= */
        .step-wrap {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 1rem 0 1.1rem 0;
        }

        .step-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 18px;
            padding: 0.95rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.045);
        }

        .step-card .step-number {
            width: 1.85rem;
            height: 1.85rem;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #DBEAFE;
            color: #1D4ED8;
            font-size: 0.84rem;
            font-weight: 950;
            margin-bottom: 0.55rem;
        }

        .step-card .step-title {
            color: #0F172A;
            font-size: 0.92rem;
            font-weight: 900;
            letter-spacing: -0.01em;
        }

        .step-card .step-desc {
            margin-top: 0.2rem;
            color: #64748B;
            font-size: 0.78rem;
            line-height: 1.45;
        }

        /* =========================================================
           STREAMLIT COMPONENT STYLE - HANYA KONTEN UTAMA
        ========================================================= */
        div[data-testid="stMetric"] {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,255,255,0.96));
            border: 1px solid #E2E8F0;
            padding: 1rem;
            border-radius: 18px;
            box-shadow:
                0 10px 24px rgba(15, 23, 42, 0.055),
                inset 0 1px 0 rgba(255,255,255,0.82);
        }

        .main .stButton > button {
            border-radius: 14px;
            font-weight: 800;
            border: 1px solid #CBD5E1;
            min-height: 2.75rem;
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
            color: #0F172A;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
            transition: all 0.18s ease;
        }

        .main .stButton > button:hover {
            border-color: #93C5FD;
            color: #0F172A;
            box-shadow: 0 12px 22px rgba(37, 99, 235, 0.08);
            transform: translateY(-1px);
        }

        .stDownloadButton > button {
            border-radius: 14px;
            font-weight: 800;
            min-height: 2.75rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.35rem;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding: 0.45rem 1rem;
            font-weight: 700;
            color: #334155;
            background: rgba(255,255,255,0.65);
            border: 1px solid #DCE5F0;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #2563EB 0%, #38BDF8 100%) !important;
            color: white !important;
            border-color: transparent !important;
        }

        .footer-note {
            color: #64748B;
            border-top: 1px solid #E2E8F0;
            margin-top: 2rem;
            padding-top: 1rem;
            font-size: 0.9rem;
        }

        @media (max-width: 900px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .hero {
                padding: 1.6rem;
            }

            .hero h1 {
                font-size: 1.8rem;
            }

            .step-wrap {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 560px) {
            .step-wrap {
                grid-template-columns: 1fr;
            }
        }

        /* =========================================================
           LOGIN ADMIN MODERN 3D
        ========================================================= */

        .login-hero {
            position: relative;
            overflow: hidden;
            border-radius: 30px;
            padding: 2.4rem;
            margin-bottom: 1.4rem;
            background:
                radial-gradient(circle at 88% 20%, rgba(255,255,255,0.18), transparent 20%),
                radial-gradient(circle at 8% 92%, rgba(255,255,255,0.09), transparent 22%),
                linear-gradient(135deg, #0F172A 0%, #1D4ED8 48%, #38BDF8 100%);
            color: #FFFFFF;
            border: 1px solid rgba(255,255,255,0.18);
            box-shadow:
                0 28px 65px rgba(37, 99, 235, 0.22),
                inset 0 1px 0 rgba(255,255,255,0.15);
        }

        .login-hero-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.48rem 0.9rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.16);
            border: 1px solid rgba(255,255,255,0.28);
            color: #FFFFFF;
            font-size: 0.82rem;
            font-weight: 850;
            margin-bottom: 1rem;
            backdrop-filter: blur(8px);
        }

        .login-hero h1 {
            margin: 0;
            max-width: 760px;
            color: #FFFFFF;
            font-size: 2.45rem;
            line-height: 1.15;
            font-weight: 950;
            letter-spacing: -0.045em;
        }

        .login-hero p {
            max-width: 760px;
            color: #EAF4FF;
            margin-top: 0.9rem;
            font-size: 1.02rem;
            line-height: 1.75;
            font-weight: 500;
        }

        .login-card {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,251,255,0.98));
            border: 1px solid #DCE5F0;
            border-radius: 30px;
            padding: 1.6rem;
            box-shadow:
                0 24px 55px rgba(15, 23, 42, 0.09),
                0 8px 18px rgba(59, 130, 246, 0.05),
                inset 0 1px 0 rgba(255,255,255,0.90);
        }

        .login-card-title {
            color: #0F172A;
            font-size: 1.5rem;
            font-weight: 950;
            letter-spacing: -0.035em;
            margin-bottom: 0.35rem;
        }

        .login-card-subtitle {
            color: #64748B;
            font-size: 0.96rem;
            line-height: 1.7;
            margin-bottom: 1.1rem;
        }

        .login-mini-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 24px;
            padding: 1.1rem;
            box-shadow:
                0 16px 34px rgba(15, 23, 42, 0.055),
                inset 0 1px 0 rgba(255,255,255,0.8);
            height: 100%;
        }

        .login-mini-card h3 {
            margin: 0 0 0.35rem 0;
            color: #0F172A;
            font-size: 1rem;
            font-weight: 900;
        }

        .login-mini-card p {
            margin: 0;
            color: #64748B;
            font-size: 0.9rem;
            line-height: 1.55;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, label: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-label">{_safe(label)}</div>
            <h1>{_safe(title)}</h1>
            <p>{_safe(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "", label: str = "Halaman") -> None:
    st.markdown(
        f"""
        <div class="page-head">
            <h1>{_safe(title)}</h1>
            <p>{_safe(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def admin_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="page-head admin">
            <h1>{_safe(title)}</h1>
            <p>{_safe(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="card">
            <h3>{_safe(title)}</h3>
            <p>{_safe(text)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def topic_card(eyebrow: str, title: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="topic-card">
            <div class="topic-card-eyebrow">{_safe(eyebrow)}</div>
            <div class="topic-card-title">{_safe(title)}</div>
            <p class="topic-card-text">{_safe(text)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_tile(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="metric-tile">
            <div class="label">{_safe(label)}</div>
            <div class="value">{_safe(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def quick_panel(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="card">
            <h3>{_safe(title)}</h3>
            <p>{_safe(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def detail_panel(
    title: str,
    text: str | None = None,
    paragraphs: Iterable[str] | None = None,
    body: str | None = None,
    label: str | None = None,
) -> None:
    """
    Panel detail fleksibel.
    Bisa dipanggil dengan:
    - detail_panel(title, text="...")
    - detail_panel(title, body="...")
    - detail_panel(title, paragraphs=[...])
    """

    content_items: list[str] = []

    if paragraphs is not None:
        content_items.extend([str(item) for item in paragraphs if str(item).strip()])

    selected_text = text or body

    if selected_text:
        raw_parts = str(selected_text).split("\n")
        content_items.extend([part.strip() for part in raw_parts if part.strip()])

    paragraph_html = "".join(
        f"<p>{_safe(paragraph)}</p>"
        for paragraph in content_items
    )

    st.markdown(
        f"""
        <div class="detail-panel">
            <h3>{_safe(title)}</h3>
            {paragraph_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def nav_active(label: str) -> None:
    st.sidebar.markdown(
        f"""
        <div class="nav-active">{_safe(label)}</div>
        """,
        unsafe_allow_html=True,
    )


def nav_group(label: str) -> None:
    st.sidebar.markdown(
        f"""
        <div class="menu-label">{_safe(label)}</div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_status(text: str) -> None:
    st.sidebar.markdown(
        f"""
        <div class="sidebar-status">{_safe(text)}</div>
        """,
        unsafe_allow_html=True,
    )


def admin_title(title: str, subtitle: str = "") -> None:
    admin_header(title, subtitle)


def page_title(title: str, subtitle: str = "", badge: str = "Halaman") -> None:
    page_header(title, subtitle, badge)


def info_card(title: str, text: str) -> None:
    card(title, text)


def workflow_box(text: str) -> None:
    quick_panel("Alur Proses", text)


def admin_box(text: str) -> None:
    quick_panel("Informasi Admin", text)


def workflow(text: str) -> None:
    quick_panel("Workflow", text)


def admin_workflow(text: str) -> None:
    quick_panel("Workflow Admin", text)