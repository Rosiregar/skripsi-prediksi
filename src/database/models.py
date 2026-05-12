"""
Model/tabel database aplikasi Prediksi Jumlah Pengangguran Sulawesi Utara.

File ini berisi struktur tabel:
- admins
- datasets
- dataset_rows
- model_trainings
- model_artifacts
- model_evaluations
- test_predictions
- future_predictions
- user_prediction_jobs
- user_prediction_details
- admin_activity_logs

Database default saat development adalah SQLite.
Saat production, struktur ini tetap bisa digunakan dengan PostgreSQL.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from src.database.connection import Base


# ============================================================
# ADMIN TABLE
# ============================================================

class Admin(Base):
    """
    Tabel untuk menyimpan data admin.
    Password tidak boleh disimpan dalam bentuk asli.
    Password harus disimpan dalam bentuk hash.
    """

    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=True)
    role = Column(String(50), nullable=False, default="admin")
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_login = Column(DateTime, nullable=True)

    datasets = relationship("Dataset", back_populates="uploader")
    activity_logs = relationship("AdminActivityLog", back_populates="admin")

    def __repr__(self) -> str:
        return f"<Admin(username='{self.username}', role='{self.role}')>"


# ============================================================
# DATASET TABLES
# ============================================================

class Dataset(Base):
    """
    Tabel metadata dataset.

    File dataset asli disimpan di folder storage/datasets.
    Tabel ini hanya menyimpan informasi penting tentang file dataset tersebut.
    """

    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)

    dataset_name = Column(String(200), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    storage_path = Column(Text, nullable=False)

    uploaded_by = Column(Integer, ForeignKey("admins.id"), nullable=True)

    row_count = Column(Integer, nullable=False, default=0)
    column_count = Column(Integer, nullable=False, default=0)

    year_column = Column(String(100), nullable=False, default="Tahun")
    target_column = Column(String(100), nullable=False, default="Total_Pengangguran")

    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)

    is_active = Column(Boolean, nullable=False, default=False)
    is_published = Column(Boolean, nullable=False, default=False)

    uploaded_at = Column(DateTime, nullable=False, server_default=func.now())

    uploader = relationship("Admin", back_populates="datasets")

    rows = relationship(
        "DatasetRow",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )

    trainings = relationship(
        "ModelTraining",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Dataset(name='{self.dataset_name}', file='{self.original_filename}')>"


class DatasetRow(Base):
    """
    Tabel detail isi dataset.

    Karena struktur kolom dataset bisa berubah, isi baris disimpan dalam bentuk JSON.
    Ini membuat database lebih fleksibel untuk dataset penelitian.
    """

    __tablename__ = "dataset_rows"

    id = Column(Integer, primary_key=True, index=True)

    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    tahun = Column(Integer, nullable=False, index=True)

    values_json = Column(JSON, nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    dataset = relationship("Dataset", back_populates="rows")

    __table_args__ = (
        UniqueConstraint(
            "dataset_id",
            "tahun",
            name="uq_dataset_rows_dataset_id_tahun",
        ),
    )

    def __repr__(self) -> str:
        return f"<DatasetRow(dataset_id={self.dataset_id}, tahun={self.tahun})>"


# ============================================================
# MODEL TRAINING TABLES
# ============================================================

class ModelTraining(Base):
    """
    Tabel riwayat training model LSTM.

    Setiap kali admin melakukan training, satu data baru akan disimpan di tabel ini.
    """

    __tablename__ = "model_trainings"

    id = Column(Integer, primary_key=True, index=True)

    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)

    model_version = Column(String(100), unique=True, nullable=False, index=True)
    algorithm = Column(String(50), nullable=False, default="LSTM")

    window_size = Column(Integer, nullable=False, default=5)
    train_ratio = Column(Float, nullable=False, default=0.8)

    epochs = Column(Integer, nullable=False, default=300)
    batch_size = Column(Integer, nullable=False, default=4)
    validation_split = Column(Float, nullable=False, default=0.2)

    lstm_units = Column(Integer, nullable=False, default=32)
    dropout_rate = Column(Float, nullable=False, default=0.2)
    early_stopping_patience = Column(Integer, nullable=False, default=30)

    correlation_threshold = Column(Float, nullable=False, default=0.3)
    selected_features_json = Column(JSON, nullable=True)

    status = Column(String(50), nullable=False, default="created")
    error_message = Column(Text, nullable=True)

    is_published = Column(Boolean, nullable=False, default=False)

    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    dataset = relationship("Dataset", back_populates="trainings")

    artifacts = relationship(
        "ModelArtifact",
        back_populates="training",
        cascade="all, delete-orphan",
    )

    evaluation = relationship(
        "ModelEvaluation",
        back_populates="training",
        uselist=False,
        cascade="all, delete-orphan",
    )

    test_predictions = relationship(
        "TestPrediction",
        back_populates="training",
        cascade="all, delete-orphan",
    )

    future_predictions = relationship(
        "FuturePrediction",
        back_populates="training",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<ModelTraining(version='{self.model_version}', "
            f"algorithm='{self.algorithm}', status='{self.status}')>"
        )


class ModelArtifact(Base):
    """
    Tabel lokasi file artifact hasil training.

    Contoh artifact:
    - model.keras
    - scaler.joblib
    - features.json
    - metrics.json
    - training_config.json
    - report.pdf
    """

    __tablename__ = "model_artifacts"

    id = Column(Integer, primary_key=True, index=True)

    training_id = Column(Integer, ForeignKey("model_trainings.id"), nullable=False)

    artifact_type = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    checksum = Column(String(128), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    training = relationship("ModelTraining", back_populates="artifacts")

    __table_args__ = (
        Index("ix_model_artifacts_training_type", "training_id", "artifact_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<ModelArtifact(training_id={self.training_id}, "
            f"type='{self.artifact_type}')>"
        )


class ModelEvaluation(Base):
    """
    Tabel hasil evaluasi model.

    MAE, RMSE, dan MAPE dihitung dari data test historis,
    bukan dari prediksi masa depan.
    """

    __tablename__ = "model_evaluations"

    id = Column(Integer, primary_key=True, index=True)

    training_id = Column(
        Integer,
        ForeignKey("model_trainings.id"),
        unique=True,
        nullable=False,
    )

    mae = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    mape = Column(Float, nullable=False)

    test_start_year = Column(Integer, nullable=True)
    test_end_year = Column(Integer, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    training = relationship("ModelTraining", back_populates="evaluation")

    def __repr__(self) -> str:
        return (
            f"<ModelEvaluation(training_id={self.training_id}, "
            f"mae={self.mae}, rmse={self.rmse}, mape={self.mape})>"
        )


class TestPrediction(Base):
    """
    Tabel hasil prediksi pada data test.

    Tabel ini menyimpan perbandingan nilai aktual dan nilai prediksi.
    """

    __tablename__ = "test_predictions"

    id = Column(Integer, primary_key=True, index=True)

    training_id = Column(Integer, ForeignKey("model_trainings.id"), nullable=False)

    tahun = Column(Integer, nullable=False, index=True)
    actual_value = Column(Float, nullable=False)
    predicted_value = Column(Float, nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    training = relationship("ModelTraining", back_populates="test_predictions")

    __table_args__ = (
        UniqueConstraint(
            "training_id",
            "tahun",
            name="uq_test_predictions_training_id_tahun",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<TestPrediction(training_id={self.training_id}, "
            f"tahun={self.tahun})>"
        )


class FuturePrediction(Base):
    """
    Tabel hasil prediksi masa depan.

    Hasil prediksi ini bisa dipublish oleh admin agar tampil di sisi user.
    """

    __tablename__ = "future_predictions"

    id = Column(Integer, primary_key=True, index=True)

    training_id = Column(Integer, ForeignKey("model_trainings.id"), nullable=False)

    tahun = Column(Integer, nullable=False, index=True)
    predicted_value = Column(Float, nullable=False)

    is_published = Column(Boolean, nullable=False, default=False)
    published_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    training = relationship("ModelTraining", back_populates="future_predictions")

    __table_args__ = (
        UniqueConstraint(
            "training_id",
            "tahun",
            name="uq_future_predictions_training_id_tahun",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<FuturePrediction(training_id={self.training_id}, "
            f"tahun={self.tahun}, predicted_value={self.predicted_value})>"
        )


# ============================================================
# USER PREDICTION TABLES
# ============================================================

class UserPredictionJob(Base):
    """
    Tabel riwayat prediksi/simulasi yang dilakukan user.

    Prediksi user tidak mengganti model resmi admin.
    """

    __tablename__ = "user_prediction_jobs"

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(String(255), nullable=True, index=True)
    uploaded_filename = Column(String(255), nullable=True)

    prediction_start_year = Column(Integer, nullable=True)
    prediction_end_year = Column(Integer, nullable=True)
    prediction_horizon = Column(Integer, nullable=True)

    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    mape = Column(Float, nullable=True)

    status = Column(String(50), nullable=False, default="created")
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    details = relationship(
        "UserPredictionDetail",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<UserPredictionJob(id={self.id}, "
            f"status='{self.status}', horizon={self.prediction_horizon})>"
        )


class UserPredictionDetail(Base):
    """
    Tabel detail hasil prediksi user.
    """

    __tablename__ = "user_prediction_details"

    id = Column(Integer, primary_key=True, index=True)

    user_prediction_job_id = Column(
        Integer,
        ForeignKey("user_prediction_jobs.id"),
        nullable=False,
    )

    tahun = Column(Integer, nullable=False, index=True)
    predicted_value = Column(Float, nullable=False)
    actual_value = Column(Float, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    job = relationship("UserPredictionJob", back_populates="details")

    __table_args__ = (
        UniqueConstraint(
            "user_prediction_job_id",
            "tahun",
            name="uq_user_prediction_details_job_id_tahun",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<UserPredictionDetail(job_id={self.user_prediction_job_id}, "
            f"tahun={self.tahun})>"
        )


# ============================================================
# ADMIN ACTIVITY LOG TABLE
# ============================================================

class AdminActivityLog(Base):
    """
    Tabel log aktivitas admin.

    Contoh aktivitas:
    - LOGIN
    - UPLOAD_DATASET
    - TRAIN_MODEL
    - PUBLISH_PREDICTION
    - EXPORT_REPORT
    """

    __tablename__ = "admin_activity_logs"

    id = Column(Integer, primary_key=True, index=True)

    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)

    activity_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    admin = relationship("Admin", back_populates="activity_logs")

    def __repr__(self) -> str:
        return (
            f"<AdminActivityLog(admin_id={self.admin_id}, "
            f"activity_type='{self.activity_type}')>"
        )