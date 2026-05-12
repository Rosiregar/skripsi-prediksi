from __future__ import annotations

import streamlit as st

from src.auth.auth_service import authenticate_admin, ensure_default_admin
from src.auth.session_manager import (
    initialize_session_state,
    is_admin_logged_in,
    login_admin_session,
    logout_admin_session,
)
from src.database.connection import create_tables


def get_logged_admin_name() -> str:
    """
    Mengambil nama admin dari session_state tanpa bergantung pada fungsi tambahan.
    """

    possible_admin_data = [
        st.session_state.get("admin"),
        st.session_state.get("current_admin"),
        st.session_state.get("admin_data"),
        st.session_state.get("logged_in_admin"),
    ]

    for admin_data in possible_admin_data:
        if isinstance(admin_data, dict):
            return (
                admin_data.get("full_name")
                or admin_data.get("name")
                or admin_data.get("username")
                or "Administrator"
            )

    return (
        st.session_state.get("admin_full_name")
        or st.session_state.get("admin_name")
        or st.session_state.get("username")
        or "Administrator"
    )


def render_admin_login_page() -> None:
    initialize_session_state()
    create_tables()
    ensure_default_admin()

    if is_admin_logged_in():
        st.query_params["page"] = "admin-dashboard"
        st.rerun()
        return

    render_login_view()


def render_login_view() -> None:
    render_login_hero()

    col_left, col_center, col_right = st.columns([0.85, 1.35, 0.85])

    with col_center:
        st.markdown(
            """
            <div class="login-card">
                <div class="login-card-subtitle">
                    Masukkan username dan password admin untuk melanjutkan.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")

        with st.form("admin_login_form"):
            username = st.text_input(
                "Username",
                placeholder="Masukkan username admin",
            )

            password = st.text_input(
                "Password",
                placeholder="Masukkan password admin",
                type="password",
            )

            submitted = st.form_submit_button(
                "Login Admin",
                use_container_width=True,
            )

        if submitted:
            process_login(username=username, password=password)


def render_login_hero() -> None:
    st.markdown(
        """
        <div class="login-hero">
            <div class="login-hero-badge">Admin Page</div>
            <h1>Login Admin</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_login_support_cards() -> None:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="login-mini-card">
                <h3>Kelola Dataset</h3>
                <p>Admin dapat mengupload, memvalidasi, mengaktifkan, dan mempublish dataset.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="login-mini-card">
                <h3>Training Model</h3>
                <p>Admin dapat menjalankan training model LSTM berdasarkan dataset aktif.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="login-mini-card">
                <h3>Publish Hasil</h3>
                <p>Admin dapat mempublish hasil evaluasi dan prediksi agar tampil di halaman user.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_logged_in_view() -> None:
    admin_name = get_logged_admin_name()

    st.markdown(
        f"""
        <div class="login-hero">
            <div class="login-hero-badge">Admin Aktif</div>
            <h1>Anda Sudah Login</h1>
            <p>
                Saat ini Anda login sebagai <b>{admin_name}</b>.
                Anda dapat masuk ke dashboard admin atau keluar dari sesi login.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Buka Dashboard Admin", use_container_width=True):
            st.query_params["page"] = "admin-dashboard"
            st.rerun()

    with col2:
        if st.button("Logout", use_container_width=True):
            logout_admin_session()
            st.query_params["page"] = "home"
            st.rerun()


def process_login(username: str, password: str) -> None:
    username = username.strip() if username else ""

    if not username:
        st.error("Username tidak boleh kosong.")
        return

    if not password:
        st.error("Password tidak boleh kosong.")
        return

    admin_data = authenticate_admin(
        username=username,
        password=password,
    )

    if not admin_data:
        st.error("Username atau password salah.")
        return

    login_admin_session(admin_data)

    st.session_state["admin_logged_in"] = True
    st.session_state["is_admin_logged_in"] = True
    st.session_state["admin_data"] = admin_data
    st.session_state["admin"] = admin_data
    st.session_state["current_admin"] = admin_data
    st.session_state["logged_in_admin"] = admin_data

    # Paksa halaman berpindah setelah rerun
    st.session_state["force_page"] = "admin-dashboard"

    try:
        st.query_params.clear()
    except Exception:
        pass

    st.query_params["page"] = "admin-dashboard"
    st.rerun()