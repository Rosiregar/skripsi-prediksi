"""
Training Service final.

File ini bertanggung jawab untuk:
- mengambil dataset aktif dari database,
- menjalankan pipeline training LSTM,
- menyimpan artifact model ke storage,
- menyimpan metadata training ke database,
- menyimpan hasil evaluasi MAE, RMSE, MAPE,
- menyimpan hasil prediksi test,
- menyimpan hasil prediksi masa depan,
- mengatur status training,
- mempublish model/prediksi resmi untuk user.

Service ini menjadi jembatan antara:
- dataset_service.py
- lstm_service.py
- database models

Pada production, artifact model disimpan ke MODEL_DIR yang dapat diarahkan
ke persistent storage melalui konfigurasi STORAGE_DIR di file .env.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

import pandas as pd
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.config.settings import (
    BATCH_SIZE,
    CORRELATION_THRESHOLD,
    DROPOUT_RATE,
    EARLY_STOPPING_PATIENCE,
    EPOCHS,
    FUTURE_YEARS_DEFAULT,
    LSTM_UNITS,
    MODEL_DIR,
    TARGET_COLUMN,
    TRAIN_RATIO,
    VALIDATION_SPLIT,
    WINDOW_SIZE,
)
from src.database.connection import db_session
from src.database.models import (
    AdminActivityLog,
    FuturePrediction,
    ModelArtifact,
    ModelEvaluation,
    ModelTraining,
    TestPrediction,
)
from src.ml.lstm_service import (
    LSTMTrainingResult,
    save_training_artifacts,
    train_lstm_pipeline,
)
from src.services.dataset_service import (
    get_active_dataset,
    load_dataset_file_as_dataframe,
)
from src.utils.logger import get_logger


logger = get_logger(__name__)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def generate_model_version() -> str:
    """
    Membuat versi model unik.

    Contoh:
        LSTM-SULUT-20260507-093012-a1b2c3
    """

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_id = uuid.uuid4().hex[:6]

    return f"LSTM-SULUT-{timestamp}-{unique_id}"


def training_to_dict(training: ModelTraining) -> dict:
    """
    Mengubah object ModelTraining menjadi dictionary.
    """

    return {
        "id": training.id,
        "dataset_id": training.dataset_id,
        "model_version": training.model_version,
        "algorithm": training.algorithm,
        "window_size": training.window_size,
        "train_ratio": training.train_ratio,
        "epochs": training.epochs,
        "batch_size": training.batch_size,
        "validation_split": training.validation_split,
        "lstm_units": training.lstm_units,
        "dropout_rate": training.dropout_rate,
        "early_stopping_patience": training.early_stopping_patience,
        "correlation_threshold": training.correlation_threshold,
        "selected_features_json": training.selected_features_json,
        "status": training.status,
        "error_message": training.error_message,
        "is_published": training.is_published,
        "started_at": training.started_at,
        "finished_at": training.finished_at,
        "created_at": training.created_at,
    }


def evaluation_to_dict(evaluation: Optional[ModelEvaluation]) -> Optional[dict]:
    """
    Mengubah object ModelEvaluation menjadi dictionary.
    """

    if evaluation is None:
        return None

    return {
        "id": evaluation.id,
        "training_id": evaluation.training_id,
        "mae": evaluation.mae,
        "rmse": evaluation.rmse,
        "mape": evaluation.mape,
        "test_start_year": evaluation.test_start_year,
        "test_end_year": evaluation.test_end_year,
        "created_at": evaluation.created_at,
    }


def artifact_to_dict(artifact: ModelArtifact) -> dict:
    """
    Mengubah object ModelArtifact menjadi dictionary.
    """

    return {
        "id": artifact.id,
        "training_id": artifact.training_id,
        "artifact_type": artifact.artifact_type,
        "file_name": artifact.file_name,
        "file_path": artifact.file_path,
        "checksum": artifact.checksum,
        "created_at": artifact.created_at,
    }


def log_admin_activity(
    session: Session,
    admin_id: Optional[int],
    activity_type: str,
    description: Optional[str] = None,
) -> None:
    """
    Mencatat aktivitas admin.
    """

    activity_log = AdminActivityLog(
        admin_id=admin_id,
        activity_type=activity_type,
        description=description,
    )

    session.add(activity_log)


# ============================================================
# DATABASE INSERT HELPERS
# ============================================================

def create_training_record(
    session: Session,
    dataset_id: int,
    model_version: str,
    future_years: int,
    window_size: int,
    train_ratio: float,
    epochs: int,
    batch_size: int,
    validation_split: float,
    lstm_units: int,
    dropout_rate: float,
    early_stopping_patience: int,
    correlation_threshold: float,
) -> ModelTraining:
    """
    Membuat record awal training dengan status running.
    """

    training = ModelTraining(
        dataset_id=dataset_id,
        model_version=model_version,
        algorithm="LSTM",
        window_size=window_size,
        train_ratio=train_ratio,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=validation_split,
        lstm_units=lstm_units,
        dropout_rate=dropout_rate,
        early_stopping_patience=early_stopping_patience,
        correlation_threshold=correlation_threshold,
        selected_features_json=None,
        status="running",
        error_message=None,
        is_published=False,
        started_at=datetime.utcnow(),
        finished_at=None,
    )

    session.add(training)
    session.flush()

    return training


def save_artifact_records(
    session: Session,
    training_id: int,
    artifact_paths: dict,
) -> list[ModelArtifact]:
    """
    Menyimpan daftar artifact hasil training ke database.
    """

    artifacts = []

    for artifact_type, file_path in artifact_paths.items():
        if artifact_type == "artifact_dir":
            continue

        path = Path(file_path)

        artifact = ModelArtifact(
            training_id=training_id,
            artifact_type=artifact_type,
            file_name=path.name,
            file_path=str(path),
            checksum=None,
        )

        session.add(artifact)
        artifacts.append(artifact)

    session.flush()

    return artifacts


def save_evaluation_record(
    session: Session,
    training_id: int,
    result: LSTMTrainingResult,
) -> ModelEvaluation:
    """
    Menyimpan hasil evaluasi model ke database.
    """

    test_start_year = None
    test_end_year = None

    if len(result.test_predictions) > 0:
        test_start_year = int(result.test_predictions["Tahun"].min())
        test_end_year = int(result.test_predictions["Tahun"].max())

    evaluation = ModelEvaluation(
        training_id=training_id,
        mae=float(result.metrics["MAE"]),
        rmse=float(result.metrics["RMSE"]),
        mape=float(result.metrics["MAPE"]),
        test_start_year=test_start_year,
        test_end_year=test_end_year,
    )

    session.add(evaluation)
    session.flush()

    return evaluation


def save_test_prediction_records(
    session: Session,
    training_id: int,
    test_predictions: pd.DataFrame,
) -> None:
    """
    Menyimpan hasil prediksi data test ke database.
    """

    for _, row in test_predictions.iterrows():
        test_prediction = TestPrediction(
            training_id=training_id,
            tahun=int(row["Tahun"]),
            actual_value=float(row["Aktual"]),
            predicted_value=float(row["Prediksi"]),
        )

        session.add(test_prediction)


def save_future_prediction_records(
    session: Session,
    training_id: int,
    future_predictions: pd.DataFrame,
    publish: bool = False,
) -> None:
    """
    Menyimpan hasil prediksi masa depan ke database.
    """

    published_at = datetime.utcnow() if publish else None

    for _, row in future_predictions.iterrows():
        future_prediction = FuturePrediction(
            training_id=training_id,
            tahun=int(row["Tahun"]),
            predicted_value=float(row["Prediksi"]),
            is_published=publish,
            published_at=published_at,
        )

        session.add(future_prediction)


# ============================================================
# MAIN TRAINING SERVICE
# ============================================================

def train_active_dataset_model(
    admin_id: Optional[int] = None,
    future_years: int = FUTURE_YEARS_DEFAULT,
    publish_after_training: bool = False,
    window_size: int = WINDOW_SIZE,
    train_ratio: float = TRAIN_RATIO,
    correlation_threshold: float = CORRELATION_THRESHOLD,
    lstm_units: int = LSTM_UNITS,
    dropout_rate: float = DROPOUT_RATE,
    epochs: int = EPOCHS,
    batch_size: int = BATCH_SIZE,
    validation_split: float = VALIDATION_SPLIT,
    early_stopping_patience: int = EARLY_STOPPING_PATIENCE,
    verbose: int = 0,
) -> dict:
    """
    Melatih model LSTM menggunakan dataset aktif.

    Fungsi ini dipakai oleh halaman Admin Training.
    """

    active_dataset = get_active_dataset()

    if not active_dataset:
        raise ValueError(
            "Belum ada dataset aktif. Upload dan aktifkan dataset terlebih dahulu."
        )

    dataset_id = int(active_dataset["id"])
    model_version = generate_model_version()

    with db_session() as session:
        training = create_training_record(
            session=session,
            dataset_id=dataset_id,
            model_version=model_version,
            future_years=future_years,
            window_size=window_size,
            train_ratio=train_ratio,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            lstm_units=lstm_units,
            dropout_rate=dropout_rate,
            early_stopping_patience=early_stopping_patience,
            correlation_threshold=correlation_threshold,
        )

        log_admin_activity(
            session=session,
            admin_id=admin_id,
            activity_type="START_TRAINING",
            description=(
                f"Training model '{model_version}' dimulai "
                f"menggunakan dataset ID {dataset_id}."
            ),
        )

        training_id = training.id

    try:
        df = load_dataset_file_as_dataframe(dataset_id)

        result = train_lstm_pipeline(
            df=df,
            future_years=future_years,
            target_column=TARGET_COLUMN,
            window_size=window_size,
            train_ratio=train_ratio,
            correlation_threshold=correlation_threshold,
            lstm_units=lstm_units,
            dropout_rate=dropout_rate,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            patience=early_stopping_patience,
            verbose=verbose,
        )

        artifact_paths = save_training_artifacts(
            result=result,
            model_version=model_version,
            artifact_root=MODEL_DIR,
        )

        with db_session() as session:
            training = session.get(ModelTraining, training_id)

            if training is None:
                raise ValueError("Record training tidak ditemukan.")

            if publish_after_training:
                unpublish_all_trainings_and_predictions(session)

            training.selected_features_json = {
                "selected_features": result.selected_features,
                "model_columns": result.model_columns,
                "correlation_values": result.correlation_values,
            }
            training.status = "completed"
            training.error_message = None
            training.finished_at = datetime.utcnow()
            training.is_published = publish_after_training

            artifacts = save_artifact_records(
                session=session,
                training_id=training.id,
                artifact_paths=artifact_paths,
            )

            evaluation = save_evaluation_record(
                session=session,
                training_id=training.id,
                result=result,
            )

            save_test_prediction_records(
                session=session,
                training_id=training.id,
                test_predictions=result.test_predictions,
            )

            save_future_prediction_records(
                session=session,
                training_id=training.id,
                future_predictions=result.future_predictions,
                publish=publish_after_training,
            )

            log_admin_activity(
                session=session,
                admin_id=admin_id,
                activity_type="FINISH_TRAINING",
                description=(
                    f"Training model '{model_version}' selesai. "
                    f"MAE={result.metrics['MAE']:.4f}, "
                    f"RMSE={result.metrics['RMSE']:.4f}, "
                    f"MAPE={result.metrics['MAPE']:.4f}%."
                ),
            )

            if publish_after_training:
                log_admin_activity(
                    session=session,
                    admin_id=admin_id,
                    activity_type="PUBLISH_MODEL",
                    description=(
                        f"Model '{model_version}' langsung dipublish "
                        "setelah training."
                    ),
                )

            session.flush()

            training_data = training_to_dict(training)
            evaluation_data = evaluation_to_dict(evaluation)
            artifact_data = [artifact_to_dict(item) for item in artifacts]

        return {
            "training": training_data,
            "evaluation": evaluation_data,
            "artifacts": artifact_data,
            "artifact_paths": artifact_paths,
            "metrics": result.metrics,
            "selected_features": result.selected_features,
            "model_columns": result.model_columns,
            "test_predictions": result.test_predictions,
            "future_predictions": result.future_predictions,
        }

    except Exception as exc:
        logger.exception("Training model gagal dijalankan.")

        with db_session() as session:
            training = session.get(ModelTraining, training_id)

            if training is not None:
                training.status = "failed"
                training.error_message = str(exc)
                training.finished_at = datetime.utcnow()

            log_admin_activity(
                session=session,
                admin_id=admin_id,
                activity_type="FAILED_TRAINING",
                description=(
                    f"Training model '{model_version}' gagal. Error: {exc}"
                ),
            )

        raise


# ============================================================
# PUBLISH SERVICE
# ============================================================

def unpublish_all_trainings_and_predictions(session: Session) -> None:
    """
    Menghapus status publish dari seluruh model dan prediksi.
    """

    trainings = session.execute(select(ModelTraining)).scalars().all()

    for training in trainings:
        training.is_published = False

    future_predictions = session.execute(select(FuturePrediction)).scalars().all()

    for prediction in future_predictions:
        prediction.is_published = False
        prediction.published_at = None


def publish_training_result(
    training_id: int,
    admin_id: Optional[int] = None,
) -> dict:
    """
    Mempublish model dan hasil prediksi masa depan tertentu ke sisi user.

    Hanya satu model yang boleh published dalam satu waktu.
    """

    with db_session() as session:
        training = session.get(ModelTraining, training_id)

        if not training:
            raise ValueError("Training tidak ditemukan.")

        if training.status != "completed":
            raise ValueError(
                "Hanya training dengan status completed yang dapat dipublish."
            )

        unpublish_all_trainings_and_predictions(session)

        training.is_published = True

        statement = select(FuturePrediction).where(
            FuturePrediction.training_id == training_id
        )

        predictions = session.execute(statement).scalars().all()

        now = datetime.utcnow()

        for prediction in predictions:
            prediction.is_published = True
            prediction.published_at = now

        log_admin_activity(
            session=session,
            admin_id=admin_id,
            activity_type="PUBLISH_MODEL",
            description=f"Model '{training.model_version}' berhasil dipublish.",
        )

        session.flush()

        return training_to_dict(training)


def unpublish_training_result(
    training_id: int,
    admin_id: Optional[int] = None,
) -> dict:
    """
    Mengubah model dan prediksi masa depan menjadi tidak published.
    """

    with db_session() as session:
        training = session.get(ModelTraining, training_id)

        if not training:
            raise ValueError("Training tidak ditemukan.")

        training.is_published = False

        statement = select(FuturePrediction).where(
            FuturePrediction.training_id == training_id
        )

        predictions = session.execute(statement).scalars().all()

        for prediction in predictions:
            prediction.is_published = False
            prediction.published_at = None

        log_admin_activity(
            session=session,
            admin_id=admin_id,
            activity_type="UNPUBLISH_MODEL",
            description=(
                f"Model '{training.model_version}' tidak lagi dipublish."
            ),
        )

        session.flush()

        return training_to_dict(training)


# ============================================================
# QUERY SERVICE
# ============================================================

def list_training_results(limit: int = 50) -> list[dict]:
    """
    Mengambil daftar riwayat training terbaru.
    """

    with db_session() as session:
        statement = (
            select(ModelTraining)
            .order_by(desc(ModelTraining.created_at))
            .limit(limit)
        )

        trainings = session.execute(statement).scalars().all()

        return [training_to_dict(training) for training in trainings]


def get_training_by_id(training_id: int) -> Optional[dict]:
    """
    Mengambil data training berdasarkan ID.
    """

    with db_session() as session:
        training = session.get(ModelTraining, training_id)

        if not training:
            return None

        return training_to_dict(training)


def get_published_training() -> Optional[dict]:
    """
    Mengambil model training yang sedang dipublish.
    """

    with db_session() as session:
        statement = (
            select(ModelTraining)
            .where(ModelTraining.is_published.is_(True))
            .where(ModelTraining.status == "completed")
            .order_by(desc(ModelTraining.finished_at))
        )

        training = session.execute(statement).scalars().first()

        if not training:
            return None

        return training_to_dict(training)


def get_training_evaluation(training_id: int) -> Optional[dict]:
    """
    Mengambil evaluasi model berdasarkan training_id.
    """

    with db_session() as session:
        statement = select(ModelEvaluation).where(
            ModelEvaluation.training_id == training_id
        )

        evaluation = session.execute(statement).scalars().first()

        return evaluation_to_dict(evaluation)


def get_training_artifacts(training_id: int) -> list[dict]:
    """
    Mengambil daftar artifact dari sebuah training.
    """

    with db_session() as session:
        statement = select(ModelArtifact).where(
            ModelArtifact.training_id == training_id
        )

        artifacts = session.execute(statement).scalars().all()

        return [artifact_to_dict(artifact) for artifact in artifacts]


def get_artifact_dir(training_id: int) -> Optional[str]:
    """
    Mengambil folder artifact model dari training tertentu.
    """

    artifacts = get_training_artifacts(training_id)

    if not artifacts:
        return None

    for artifact in artifacts:
        file_path = Path(artifact["file_path"])

        if file_path.exists():
            return str(file_path.parent)

    return None


def get_test_predictions_dataframe(training_id: int) -> pd.DataFrame:
    """
    Mengambil hasil prediksi test sebagai dataframe.
    """

    with db_session() as session:
        statement = (
            select(TestPrediction)
            .where(TestPrediction.training_id == training_id)
            .order_by(TestPrediction.tahun)
        )

        rows = session.execute(statement).scalars().all()

        data = [
            {
                "Tahun": row.tahun,
                "Aktual": row.actual_value,
                "Prediksi": row.predicted_value,
            }
            for row in rows
        ]

    return pd.DataFrame(data)


def get_future_predictions_dataframe(
    training_id: Optional[int] = None,
    only_published: bool = False,
) -> pd.DataFrame:
    """
    Mengambil hasil prediksi masa depan sebagai dataframe.

    Jika only_published=True, hanya prediksi yang dipublish yang diambil.
    """

    with db_session() as session:
        statement = select(FuturePrediction)

        if training_id is not None:
            statement = statement.where(FuturePrediction.training_id == training_id)

        if only_published:
            statement = statement.where(FuturePrediction.is_published.is_(True))

        statement = statement.order_by(FuturePrediction.tahun)

        rows = session.execute(statement).scalars().all()

        data = [
            {
                "Tahun": row.tahun,
                "Prediksi": row.predicted_value,
                "training_id": row.training_id,
                "is_published": row.is_published,
                "published_at": row.published_at,
            }
            for row in rows
        ]

    return pd.DataFrame(data)


def get_published_prediction_summary() -> Optional[dict]:
    """
    Mengambil ringkasan model dan prediksi yang sedang dipublish.

    Fungsi ini dipakai pada sisi user.
    """

    training = get_published_training()

    if not training:
        return None

    evaluation = get_training_evaluation(training["id"])
    future_predictions = get_future_predictions_dataframe(
        training_id=training["id"],
        only_published=True,
    )
    test_predictions = get_test_predictions_dataframe(training["id"])

    return {
        "training": training,
        "evaluation": evaluation,
        "future_predictions": future_predictions,
        "test_predictions": test_predictions,
    }