"""
Koneksi database aplikasi Prediksi Jumlah Pengangguran Sulawesi Utara.

File ini bertanggung jawab untuk:
- membuat koneksi database,
- membuat session database,
- menyediakan Base untuk model/tabel SQLAlchemy,
- menyediakan helper untuk test koneksi database,
- menyediakan helper untuk membuat tabel database.

Pada mode development, aplikasi dapat menggunakan SQLite.
Pada mode production, aplikasi dapat menggunakan PostgreSQL melalui DATABASE_URL.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from src.config.settings import APP_ENV, DATABASE_URL, create_required_directories


# ============================================================
# SQLALCHEMY BASE
# ============================================================

Base = declarative_base()


# ============================================================
# INTERNAL ENGINE AND SESSION FACTORY
# ============================================================

_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


# ============================================================
# DATABASE ENGINE
# ============================================================

def is_sqlite_database(database_url: str) -> bool:
    """
    Mengecek apakah database yang digunakan adalah SQLite.
    """

    return database_url.startswith("sqlite")


def get_engine() -> Engine:
    """
    Membuat dan mengembalikan SQLAlchemy engine.

    Engine dibuat satu kali saja, lalu digunakan ulang.
    Pada SQLite digunakan check_same_thread=False.
    Pada PostgreSQL digunakan pool_pre_ping agar koneksi mati dapat dicek ulang.
    """

    global _engine

    if _engine is None:
        create_required_directories()

        if is_sqlite_database(DATABASE_URL):
            _engine = create_engine(
                DATABASE_URL,
                connect_args={"check_same_thread": False},
                future=True,
            )
        else:
            _engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                pool_recycle=1800,
                future=True,
            )

    return _engine


# ============================================================
# DATABASE SESSION
# ============================================================

def get_session_factory() -> sessionmaker:
    """
    Membuat dan mengembalikan session factory database.
    """

    global _SessionLocal

    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            future=True,
        )

    return _SessionLocal


def get_session() -> Session:
    """
    Membuat session database baru.

    Session ini bisa digunakan untuk query, insert, update, dan delete data.
    Session harus ditutup setelah digunakan.
    """

    session_factory = get_session_factory()
    return session_factory()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context manager untuk session database.

    Dengan fungsi ini, commit dan rollback ditangani otomatis.

    Contoh:
        with db_session() as session:
            session.add(data_baru)
    """

    session = get_session()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ============================================================
# DATABASE UTILITIES
# ============================================================

def test_database_connection() -> bool:
    """
    Mengecek apakah koneksi database berhasil.
    """

    engine = get_engine()

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True


def create_tables() -> None:
    """
    Membuat seluruh tabel database berdasarkan model SQLAlchemy.

    Fungsi ini dipanggil saat aplikasi berjalan.
    Jika tabel sudah ada, SQLAlchemy tidak akan membuat ulang tabel yang sama.
    """

    from src.database import models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())


def drop_tables(confirm: bool = False) -> None:
    """
    Menghapus seluruh tabel database.

    Fungsi ini berbahaya dan hanya boleh dipakai saat development.
    Pada mode production, fungsi ini diblokir.
    """

    if APP_ENV == "production":
        raise RuntimeError(
            "drop_tables() tidak boleh dijalankan pada mode production."
        )

    if not confirm:
        raise ValueError(
            "drop_tables() membutuhkan confirm=True agar tabel dapat dihapus."
        )

    Base.metadata.drop_all(bind=get_engine())