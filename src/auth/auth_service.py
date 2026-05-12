"""
Service autentikasi admin.

File ini bertanggung jawab untuk:
- hash password admin,
- verifikasi password admin,
- membuat admin default dari konfigurasi .env,
- autentikasi login admin,
- mencatat aktivitas login admin.

Password admin tidak boleh disimpan dalam bentuk teks biasa.
Password disimpan dalam bentuk hash menggunakan bcrypt.

Pada mode production, konfigurasi admin default wajib diganti
melalui file .env dan tidak boleh memakai password bawaan yang lemah.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config.settings import (
    APP_ENV,
    DEFAULT_ADMIN_FULL_NAME,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
)
from src.database.connection import db_session
from src.database.models import Admin, AdminActivityLog


# ============================================================
# PASSWORD UTILITIES
# ============================================================

def hash_password(password: str) -> str:
    """
    Membuat hash password menggunakan bcrypt.
    """

    if not password:
        raise ValueError("Password tidak boleh kosong.")

    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)

    return hashed_password.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Mengecek apakah password asli cocok dengan password hash.
    """

    if not password or not password_hash:
        return False

    try:
        password_bytes = password.encode("utf-8")
        password_hash_bytes = password_hash.encode("utf-8")

        return bcrypt.checkpw(password_bytes, password_hash_bytes)

    except Exception:
        return False


def validate_password_strength(password: str) -> None:
    """
    Validasi sederhana kekuatan password untuk production.
    """

    if not password:
        raise ValueError("Password tidak boleh kosong.")

    if len(password) < 8:
        raise ValueError("Password minimal harus memiliki 8 karakter.")

    weak_passwords = {
        "admin",
        "admin123",
        "password",
        "password123",
        "123456",
        "12345678",
        "qwerty",
    }

    if password.lower() in weak_passwords:
        raise ValueError(
            "Password terlalu lemah. Gunakan password yang lebih kuat."
        )


def validate_default_admin_config() -> None:
    """
    Memastikan konfigurasi admin default aman.

    Pada production:
    - username tidak boleh kosong,
    - password tidak boleh kosong,
    - password tidak boleh memakai nilai default lemah.
    """

    if not DEFAULT_ADMIN_USERNAME:
        raise ValueError("DEFAULT_ADMIN_USERNAME tidak boleh kosong.")

    if not DEFAULT_ADMIN_PASSWORD:
        raise ValueError("DEFAULT_ADMIN_PASSWORD tidak boleh kosong.")

    if APP_ENV == "production":
        validate_password_strength(DEFAULT_ADMIN_PASSWORD)


# ============================================================
# ADMIN HELPERS
# ============================================================

def admin_to_dict(admin: Admin) -> dict:
    """
    Mengubah object Admin menjadi dictionary.

    Ini berguna agar data admin aman digunakan setelah session database ditutup.
    Password hash tidak ikut dikembalikan.
    """

    return {
        "id": admin.id,
        "username": admin.username,
        "full_name": admin.full_name,
        "role": admin.role,
        "is_active": admin.is_active,
        "created_at": admin.created_at,
        "last_login": admin.last_login,
    }


def get_admin_by_username(session: Session, username: str) -> Optional[Admin]:
    """
    Mengambil data admin berdasarkan username.
    """

    if not username:
        return None

    statement = select(Admin).where(Admin.username == username)
    return session.execute(statement).scalar_one_or_none()


def create_admin(
    session: Session,
    username: str,
    password: str,
    full_name: Optional[str] = None,
    role: str = "admin",
    is_active: bool = True,
) -> Admin:
    """
    Membuat admin baru.

    Password asli akan di-hash sebelum disimpan ke database.
    """

    if not username:
        raise ValueError("Username tidak boleh kosong.")

    if not password:
        raise ValueError("Password tidak boleh kosong.")

    if APP_ENV == "production":
        validate_password_strength(password)

    existing_admin = get_admin_by_username(session, username)

    if existing_admin:
        raise ValueError(f"Username '{username}' sudah digunakan.")

    admin = Admin(
        username=username,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=is_active,
    )

    session.add(admin)
    session.flush()

    return admin


def log_admin_activity(
    session: Session,
    admin_id: Optional[int],
    activity_type: str,
    description: Optional[str] = None,
) -> AdminActivityLog:
    """
    Mencatat aktivitas admin ke tabel admin_activity_logs.
    """

    activity_log = AdminActivityLog(
        admin_id=admin_id,
        activity_type=activity_type,
        description=description,
    )

    session.add(activity_log)
    session.flush()

    return activity_log


# ============================================================
# DEFAULT ADMIN
# ============================================================

def ensure_default_admin() -> dict:
    """
    Membuat admin default jika belum ada.

    Data admin default diambil dari konfigurasi .env:
    - DEFAULT_ADMIN_USERNAME
    - DEFAULT_ADMIN_PASSWORD
    - DEFAULT_ADMIN_FULL_NAME

    Pada mode production, password default wajib kuat.
    """

    validate_default_admin_config()

    with db_session() as session:
        existing_admin = get_admin_by_username(session, DEFAULT_ADMIN_USERNAME)

        if existing_admin:
            return admin_to_dict(existing_admin)

        admin = create_admin(
            session=session,
            username=DEFAULT_ADMIN_USERNAME,
            password=DEFAULT_ADMIN_PASSWORD,
            full_name=DEFAULT_ADMIN_FULL_NAME,
            role="admin",
            is_active=True,
        )

        log_admin_activity(
            session=session,
            admin_id=admin.id,
            activity_type="CREATE_DEFAULT_ADMIN",
            description="Admin default berhasil dibuat dari konfigurasi environment.",
        )

        return admin_to_dict(admin)


# ============================================================
# AUTHENTICATION
# ============================================================

def authenticate_admin(username: str, password: str) -> Optional[dict]:
    """
    Autentikasi login admin.

    Return:
    - dict data admin jika berhasil,
    - None jika gagal.
    """

    if not username or not password:
        return None

    username = username.strip()

    with db_session() as session:
        admin = get_admin_by_username(session, username)

        if not admin:
            return None

        if not admin.is_active:
            return None

        is_valid_password = verify_password(password, admin.password_hash)

        if not is_valid_password:
            return None

        admin.last_login = datetime.utcnow()

        log_admin_activity(
            session=session,
            admin_id=admin.id,
            activity_type="LOGIN",
            description=f"Admin '{admin.username}' berhasil login.",
        )

        return admin_to_dict(admin)


def change_admin_password(
    session: Session,
    admin_id: int,
    new_password: str,
) -> Admin:
    """
    Mengubah password admin.
    """

    if not new_password:
        raise ValueError("Password baru tidak boleh kosong.")

    if APP_ENV == "production":
        validate_password_strength(new_password)

    admin = session.get(Admin, admin_id)

    if not admin:
        raise ValueError("Admin tidak ditemukan.")

    admin.password_hash = hash_password(new_password)

    log_admin_activity(
        session=session,
        admin_id=admin.id,
        activity_type="CHANGE_PASSWORD",
        description=f"Password admin '{admin.username}' berhasil diubah.",
    )

    session.flush()

    return admin