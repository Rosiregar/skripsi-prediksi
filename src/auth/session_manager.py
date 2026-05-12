from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from src.config.settings import AUTH_COOKIE_NAME


try:
    from streamlit_cookies_controller import CookieController

    cookie_controller = CookieController()
except Exception:
    cookie_controller = None


# ============================================================
# SESSION KEYS
# ============================================================

ADMIN_SESSION_KEYS = [
    "admin",
    "current_admin",
    "admin_data",
    "logged_in_admin",
    "admin_id",
    "admin_name",
    "admin_full_name",
    "username",
    "is_admin_logged_in",
    "admin_logged_in",
    "auth_token",
    "token",
    "access_token",
    AUTH_COOKIE_NAME,
]


# ============================================================
# SESSION INITIALIZATION
# ============================================================

def initialize_session_state() -> None:
    """
    Inisialisasi session state admin.
    Fungsi ini dipanggil saat aplikasi dimulai.
    """

    st.session_state.setdefault("admin_logged_in", False)
    st.session_state.setdefault("is_admin_logged_in", False)
    st.session_state.setdefault("admin_data", None)


# ============================================================
# INTERNAL HELPERS
# ============================================================

def get_current_admin_data() -> Optional[dict[str, Any]]:
    """
    Mengambil data admin aktif dari session state.
    """

    admin_data = (
        st.session_state.get("admin_data")
        or st.session_state.get("admin")
        or st.session_state.get("current_admin")
        or st.session_state.get("logged_in_admin")
    )

    if isinstance(admin_data, dict) and admin_data:
        return admin_data

    return None


def clear_query_params() -> None:
    """
    Membersihkan query parameter dengan aman.
    """

    try:
        st.query_params.clear()
    except Exception:
        pass


# ============================================================
# LOGIN / LOGOUT
# ============================================================

def login_admin_session(admin_data: dict[str, Any]) -> None:
    """
    Menyimpan data login admin ke session state.

    Session dibuat konsisten agar app.py, halaman admin,
    dan komponen sidebar membaca status login dari key yang sama.
    """

    if not admin_data:
        return

    admin_id = admin_data.get("id")
    admin_username = admin_data.get("username", "admin")
    admin_full_name = (
        admin_data.get("full_name")
        or admin_data.get("name")
        or admin_username
        or "Administrator"
    )

    st.session_state["admin_logged_in"] = True
    st.session_state["is_admin_logged_in"] = True

    st.session_state["admin_data"] = admin_data
    st.session_state["admin"] = admin_data
    st.session_state["current_admin"] = admin_data
    st.session_state["logged_in_admin"] = admin_data

    st.session_state["admin_id"] = admin_id
    st.session_state["admin_name"] = admin_full_name
    st.session_state["admin_full_name"] = admin_full_name
    st.session_state["username"] = admin_username

    try:
        if cookie_controller is not None:
            cookie_controller.set(
                AUTH_COOKIE_NAME,
                str(admin_id or admin_username),
            )
    except Exception:
        pass


def logout_admin_session() -> None:
    """
    Logout admin secara aman.

    Fungsi ini:
    - menghapus seluruh session admin,
    - menghapus cookie auth jika tersedia,
    - tidak error jika cookie tidak ditemukan.
    """

    for key in ADMIN_SESSION_KEYS:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state["admin_logged_in"] = False
    st.session_state["is_admin_logged_in"] = False
    st.session_state["admin_data"] = None

    try:
        if cookie_controller is not None:
            cookie_controller.remove(AUTH_COOKIE_NAME)
    except KeyError:
        pass
    except Exception:
        pass


# ============================================================
# LOGIN CHECK
# ============================================================

def is_admin_logged_in() -> bool:
    """
    Mengecek apakah admin sedang login.
    """

    if st.session_state.get("admin_logged_in") is True:
        return True

    if st.session_state.get("is_admin_logged_in") is True:
        return True

    admin_data = get_current_admin_data()

    if admin_data is not None:
        return True

    return False


def require_admin_login() -> bool:
    """
    Guard untuk halaman admin.

    Jika belum login, user diarahkan ke halaman login.
    """

    if is_admin_logged_in():
        return True

    st.warning("Silakan login sebagai admin terlebih dahulu.")

    clear_query_params()
    st.query_params["page"] = "login"
    st.rerun()

    return False


# ============================================================
# CURRENT ADMIN DATA
# ============================================================

def get_current_admin_id() -> int | None:
    """
    Mengambil ID admin yang sedang login.
    """

    admin_data = get_current_admin_data()

    if admin_data is not None:
        admin_id = admin_data.get("id")

        if admin_id is not None:
            try:
                return int(admin_id)
            except Exception:
                return None

    admin_id = st.session_state.get("admin_id")

    if admin_id is not None:
        try:
            return int(admin_id)
        except Exception:
            return None

    return None


def get_current_admin_name() -> str:
    """
    Mengambil nama admin yang sedang login.
    """

    admin_data = get_current_admin_data()

    if admin_data is not None:
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


def get_admin_display_name() -> str:
    """
    Alias untuk menampilkan nama admin di sidebar.
    """

    return get_current_admin_name()