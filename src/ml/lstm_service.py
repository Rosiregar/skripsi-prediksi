from __future__ import annotations

import os

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import joblib
import keras
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler

from src.config.settings import (
    BATCH_SIZE,
    CORRELATION_THRESHOLD,
    DROPOUT_RATE,
    EARLY_STOPPING_PATIENCE,
    EPOCHS,
    FEATURES_FILE_NAME,
    FUTURE_YEARS_DEFAULT,
    LSTM_UNITS,
    MODEL_DIR,
    MODEL_FILE_NAME,
    SCALER_FILE_NAME,
    TARGET_COLUMN,
    TRAIN_RATIO,
    TRAINING_CONFIG_FILE_NAME,
    VALIDATION_SPLIT,
    WINDOW_SIZE,
    YEAR_COLUMN,
)
from src.utils.file_validator import standardize_dataset, validate_dataset


EarlyStopping = keras.callbacks.EarlyStopping
LSTM = keras.layers.LSTM
Dense = keras.layers.Dense
Dropout = keras.layers.Dropout
load_model = keras.models.load_model


@dataclass
class LSTMTrainingResult:
    model: Any
    scaler: MinMaxScaler

    cleaned_dataframe: pd.DataFrame
    scaled_dataframe: pd.DataFrame

    selected_features: list[str]
    model_columns: list[str]

    correlation_values: dict
    correlation_matrix: pd.DataFrame

    train_years: np.ndarray
    test_years: np.ndarray

    y_train_scaled: np.ndarray
    y_test_scaled: np.ndarray

    y_test_actual: np.ndarray
    y_test_predicted: np.ndarray

    metrics: dict
    test_predictions: pd.DataFrame
    future_predictions: pd.DataFrame

    history: dict
    config: dict


def set_random_seed(seed: int = 42) -> None:
    np.random.seed(seed)
    tf.random.set_seed(seed)


def make_json_serializable(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): make_json_serializable(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [make_json_serializable(item) for item in value]

    if isinstance(value, tuple):
        return [make_json_serializable(item) for item in value]

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        if np.isnan(value):
            return None
        return float(value)

    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    try:
        if not isinstance(value, (list, tuple, dict)) and pd.isna(value):
            return None
    except Exception:
        pass

    return value


def save_json(data: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            make_json_serializable(data),
            file,
            indent=4,
            ensure_ascii=False,
        )


def load_json(input_path: Path) -> dict:
    with open(input_path, "r", encoding="utf-8") as file:
        return json.load(file)


def select_features_by_correlation(
    df: pd.DataFrame,
    target_column: str = TARGET_COLUMN,
    year_column: str = YEAR_COLUMN,
    threshold: float = CORRELATION_THRESHOLD,
) -> tuple[list[str], dict, pd.DataFrame]:
    if target_column not in df.columns:
        raise ValueError(f"Kolom target '{target_column}' tidak ditemukan.")

    numeric_df = df.drop(columns=[year_column], errors="ignore").copy()

    for column in numeric_df.columns:
        numeric_df[column] = pd.to_numeric(numeric_df[column], errors="coerce")

    if numeric_df.isna().any().any():
        raise ValueError(
            "Dataset memiliki nilai kosong atau nilai non-numerik."
        )

    correlation_matrix = numeric_df.corr()

    if target_column not in correlation_matrix.columns:
        raise ValueError(
            f"Kolom target '{target_column}' tidak tersedia dalam matriks korelasi."
        )

    corr_target = correlation_matrix[target_column].drop(target_column)

    selected_features = (
        corr_target[abs(corr_target) >= threshold]
        .index
        .tolist()
    )

    selected_features = [
        feature for feature in selected_features
        if feature != target_column
    ]

    correlation_values = {
        column: float(value)
        for column, value in corr_target.to_dict().items()
    }

    return selected_features, correlation_values, correlation_matrix


def scale_dataset(
    df: pd.DataFrame,
    model_columns: list[str],
) -> tuple[pd.DataFrame, MinMaxScaler]:
    missing_columns = [
        column for column in model_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Kolom model tidak ditemukan pada dataset: "
            + ", ".join(missing_columns)
        )

    scaler = MinMaxScaler()
    scaled_array = scaler.fit_transform(df[model_columns])

    scaled_df = pd.DataFrame(
        scaled_array,
        columns=model_columns,
        index=df.index,
    )

    return scaled_df, scaler


def transform_dataset_with_existing_scaler(
    df: pd.DataFrame,
    model_columns: list[str],
    scaler: MinMaxScaler,
) -> pd.DataFrame:
    missing_columns = [
        column for column in model_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Kolom dataset tidak sesuai dengan model. Kolom yang kurang: "
            + ", ".join(missing_columns)
        )

    scaled_array = scaler.transform(df[model_columns])

    return pd.DataFrame(
        scaled_array,
        columns=model_columns,
        index=df.index,
    )


def create_lstm_sequences(
    data: pd.DataFrame,
    target_column: str,
    window_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    if target_column not in data.columns:
        raise ValueError(f"Kolom target '{target_column}' tidak ditemukan.")

    if window_size <= 0:
        raise ValueError("Window size harus lebih dari 0.")

    if window_size >= len(data):
        raise ValueError("Window size terlalu besar dibandingkan jumlah data.")

    X = []
    y = []

    for index in range(len(data) - window_size):
        x_sequence = data.iloc[index:index + window_size].values
        y_value = data.iloc[index + window_size][target_column]

        X.append(x_sequence)
        y.append(y_value)

    return np.array(X), np.array(y).reshape(-1, 1)


def split_train_test(
    X: np.ndarray,
    y: np.ndarray,
    years: np.ndarray,
    train_ratio: float = TRAIN_RATIO,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if len(X) != len(y):
        raise ValueError("Jumlah X dan y tidak sama.")

    if len(X) != len(years):
        raise ValueError("Jumlah X dan years tidak sama.")

    if len(X) < 2:
        raise ValueError("Data sequence terlalu sedikit untuk train-test split.")

    train_size = int(len(X) * train_ratio)

    if train_size <= 0:
        train_size = 1

    if train_size >= len(X):
        train_size = len(X) - 1

    X_train = X[:train_size]
    X_test = X[train_size:]

    y_train = y[:train_size]
    y_test = y[train_size:]

    train_years = years[:train_size]
    test_years = years[train_size:]

    return X_train, X_test, y_train, y_test, train_years, test_years


def build_lstm_model(
    input_shape: tuple[int, int],
    lstm_units: int = LSTM_UNITS,
    dropout_rate: float = DROPOUT_RATE,
) -> Any:
    model = keras.models.Sequential()
    model.add(LSTM(lstm_units, input_shape=input_shape))
    model.add(Dropout(dropout_rate))
    model.add(Dense(1))

    model.compile(
        optimizer="adam",
        loss="mse",
    )

    return model


def train_model(
    model: Any,
    X_train: np.ndarray,
    y_train: np.ndarray,
    epochs: int = EPOCHS,
    batch_size: int = BATCH_SIZE,
    validation_split: float = VALIDATION_SPLIT,
    patience: int = EARLY_STOPPING_PATIENCE,
    verbose: int = 0,
):
    effective_validation_split = validation_split

    if len(X_train) < 5:
        effective_validation_split = 0.0

    monitor_metric = "val_loss" if effective_validation_split > 0 else "loss"

    early_stop = EarlyStopping(
        monitor=monitor_metric,
        patience=patience,
        restore_best_weights=True,
    )

    history = model.fit(
        X_train,
        y_train,
        epochs=epochs,
        batch_size=batch_size,
        verbose=verbose,
        validation_split=effective_validation_split,
        callbacks=[early_stop],
    )

    return history


def inverse_scale_target(
    scaler: MinMaxScaler,
    y_scaled: np.ndarray,
    target_index: int,
) -> np.ndarray:
    y_scaled = np.array(y_scaled).reshape(-1, 1)

    dummy = np.zeros((len(y_scaled), scaler.n_features_in_))
    dummy[:, target_index] = y_scaled.ravel()

    inversed = scaler.inverse_transform(dummy)

    return inversed[:, target_index]


def mean_absolute_percentage_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> float:
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    if np.any(y_true == 0):
        raise ValueError(
            "MAPE tidak dapat dihitung karena terdapat nilai aktual 0."
        )

    return float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = mean_absolute_percentage_error(y_true, y_pred)

    return {
        "MAE": float(mae),
        "RMSE": float(rmse),
        "MAPE": float(mape),
    }


def build_test_prediction_dataframe(
    years: np.ndarray,
    y_actual: np.ndarray,
    y_predicted: np.ndarray,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            YEAR_COLUMN: years.astype(int),
            "Aktual": y_actual.astype(float),
            "Prediksi": y_predicted.astype(float),
        }
    )


def predict_future_scaled_values(
    model: Any,
    scaled_df: pd.DataFrame,
    target_column: str = TARGET_COLUMN,
    window_size: int = WINDOW_SIZE,
    future_years: int = FUTURE_YEARS_DEFAULT,
) -> list[float]:
    if future_years <= 0:
        raise ValueError("Jumlah tahun prediksi harus lebih dari 0.")

    if len(scaled_df) < window_size:
        raise ValueError(
            "Jumlah data lebih kecil dari window size untuk prediksi masa depan."
        )

    if target_column not in scaled_df.columns:
        raise ValueError(f"Kolom target '{target_column}' tidak ditemukan.")

    target_index = scaled_df.columns.get_loc(target_column)

    last_window = scaled_df.values[-window_size:]
    current_window = last_window.copy()

    future_predictions = []

    for _ in range(future_years):
        pred_input = current_window.reshape(
            1,
            window_size,
            current_window.shape[1],
        )

        future_pred_scaled = model.predict(pred_input, verbose=0)[0][0]
        future_predictions.append(float(future_pred_scaled))

        next_row = current_window[-1].copy()
        next_row[target_index] = future_pred_scaled

        current_window = np.vstack([current_window[1:], next_row])

    return future_predictions


def predict_future(
    model: Any,
    scaler: MinMaxScaler,
    scaled_df: pd.DataFrame,
    original_df: pd.DataFrame,
    model_columns: list[str],
    target_column: str = TARGET_COLUMN,
    year_column: str = YEAR_COLUMN,
    window_size: int = WINDOW_SIZE,
    future_years: int = FUTURE_YEARS_DEFAULT,
) -> pd.DataFrame:
    future_predictions_scaled = predict_future_scaled_values(
        model=model,
        scaled_df=scaled_df,
        target_column=target_column,
        window_size=window_size,
        future_years=future_years,
    )

    target_index = model_columns.index(target_column)

    future_predictions_actual = inverse_scale_target(
        scaler=scaler,
        y_scaled=np.array(future_predictions_scaled).reshape(-1, 1),
        target_index=target_index,
    )

    last_year = int(original_df[year_column].max())

    future_year_labels = [
        last_year + index
        for index in range(1, future_years + 1)
    ]

    return pd.DataFrame(
        {
            year_column: future_year_labels,
            "Prediksi": future_predictions_actual.astype(float),
        }
    )


def train_lstm_pipeline(
    df: pd.DataFrame,
    future_years: int = FUTURE_YEARS_DEFAULT,
    target_column: str = TARGET_COLUMN,
    year_column: str = YEAR_COLUMN,
    window_size: int = WINDOW_SIZE,
    train_ratio: float = TRAIN_RATIO,
    correlation_threshold: float = CORRELATION_THRESHOLD,
    lstm_units: int = LSTM_UNITS,
    dropout_rate: float = DROPOUT_RATE,
    epochs: int = EPOCHS,
    batch_size: int = BATCH_SIZE,
    validation_split: float = VALIDATION_SPLIT,
    patience: int = EARLY_STOPPING_PATIENCE,
    random_seed: int = 42,
    verbose: int = 0,
) -> LSTMTrainingResult:
    set_random_seed(random_seed)

    validation_result = validate_dataset(
        df=df,
        year_column=year_column,
        target_column=target_column,
        window_size=window_size,
    )

    if not validation_result.is_valid:
        raise ValueError(
            "Dataset tidak valid: "
            + "; ".join(validation_result.errors)
        )

    cleaned_df = standardize_dataset(
        df=df,
        year_column=year_column,
        target_column=target_column,
    )

    selected_features, correlation_values, correlation_matrix = (
        select_features_by_correlation(
            df=cleaned_df,
            target_column=target_column,
            year_column=year_column,
            threshold=correlation_threshold,
        )
    )

    model_columns = selected_features + [target_column]

    if target_column not in model_columns:
        model_columns.append(target_column)

    scaled_df, scaler = scale_dataset(
        df=cleaned_df,
        model_columns=model_columns,
    )

    X, y = create_lstm_sequences(
        data=scaled_df,
        target_column=target_column,
        window_size=window_size,
    )

    target_years = cleaned_df[year_column].iloc[window_size:].values

    X_train, X_test, y_train, y_test, train_years, test_years = split_train_test(
        X=X,
        y=y,
        years=target_years,
        train_ratio=train_ratio,
    )

    model = build_lstm_model(
        input_shape=(X_train.shape[1], X_train.shape[2]),
        lstm_units=lstm_units,
        dropout_rate=dropout_rate,
    )

    history = train_model(
        model=model,
        X_train=X_train,
        y_train=y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=validation_split,
        patience=patience,
        verbose=verbose,
    )

    y_pred_scaled = model.predict(X_test, verbose=0)

    target_index = model_columns.index(target_column)

    y_test_actual = inverse_scale_target(
        scaler=scaler,
        y_scaled=y_test,
        target_index=target_index,
    )

    y_test_predicted = inverse_scale_target(
        scaler=scaler,
        y_scaled=y_pred_scaled,
        target_index=target_index,
    )

    metrics = calculate_metrics(
        y_true=y_test_actual,
        y_pred=y_test_predicted,
    )

    test_predictions = build_test_prediction_dataframe(
        years=test_years,
        y_actual=y_test_actual,
        y_predicted=y_test_predicted,
    )

    future_predictions = predict_future(
        model=model,
        scaler=scaler,
        scaled_df=scaled_df,
        original_df=cleaned_df,
        model_columns=model_columns,
        target_column=target_column,
        year_column=year_column,
        window_size=window_size,
        future_years=future_years,
    )

    config = {
        "target_column": target_column,
        "year_column": year_column,
        "window_size": window_size,
        "train_ratio": train_ratio,
        "correlation_threshold": correlation_threshold,
        "selected_features": selected_features,
        "model_columns": model_columns,
        "lstm_units": lstm_units,
        "dropout_rate": dropout_rate,
        "epochs": epochs,
        "batch_size": batch_size,
        "validation_split": validation_split,
        "early_stopping_patience": patience,
        "future_years": future_years,
        "random_seed": random_seed,
    }


    return LSTMTrainingResult(
        model=model,
        scaler=scaler,
        cleaned_dataframe=cleaned_df,
        scaled_dataframe=scaled_df,
        selected_features=selected_features,
        model_columns=model_columns,
        correlation_values=correlation_values,
        correlation_matrix=correlation_matrix,
        train_years=train_years,
        test_years=test_years,
        y_train_scaled=y_train,
        y_test_scaled=y_test,
        y_test_actual=y_test_actual,
        y_test_predicted=y_test_predicted,
        metrics=metrics,
        test_predictions=test_predictions,
        future_predictions=future_predictions,
        history=history.history,
        config=config,
    )


def save_training_artifacts(
    result: LSTMTrainingResult,
    model_version: str,
    artifact_root: Optional[Path] = None,
) -> dict:
    if artifact_root is None:
        artifact_root = MODEL_DIR

    artifact_dir = artifact_root / model_version
    artifact_dir.mkdir(parents=True, exist_ok=True)

    model_path = artifact_dir / MODEL_FILE_NAME
    scaler_path = artifact_dir / SCALER_FILE_NAME
    features_path = artifact_dir / FEATURES_FILE_NAME
    config_path = artifact_dir / TRAINING_CONFIG_FILE_NAME
    metrics_path = artifact_dir / "metrics.json"
    test_predictions_path = artifact_dir / "test_predictions.csv"
    future_predictions_path = artifact_dir / "future_predictions.csv"
    correlation_path = artifact_dir / "correlation_matrix.csv"

    result.model.save(model_path)
    joblib.dump(result.scaler, scaler_path)

    save_json(
        {
            "selected_features": result.selected_features,
            "model_columns": result.model_columns,
            "correlation_values": result.correlation_values,
        },
        features_path,
    )

    save_json(result.config, config_path)
    save_json(result.metrics, metrics_path)

    result.test_predictions.to_csv(test_predictions_path, index=False)
    result.future_predictions.to_csv(future_predictions_path, index=False)
    result.correlation_matrix.to_csv(correlation_path)

    return {
        "artifact_dir": str(artifact_dir),
        "model": str(model_path),
        "scaler": str(scaler_path),
        "features": str(features_path),
        "config": str(config_path),
        "metrics": str(metrics_path),
        "test_predictions": str(test_predictions_path),
        "future_predictions": str(future_predictions_path),
        "correlation_matrix": str(correlation_path),
    }


def load_training_artifacts(artifact_dir: str | Path) -> dict:
    artifact_dir = Path(artifact_dir)

    model_path = artifact_dir / MODEL_FILE_NAME
    scaler_path = artifact_dir / SCALER_FILE_NAME
    features_path = artifact_dir / FEATURES_FILE_NAME
    config_path = artifact_dir / TRAINING_CONFIG_FILE_NAME
    metrics_path = artifact_dir / "metrics.json"

    if not model_path.exists():
        raise FileNotFoundError(f"File model tidak ditemukan: {model_path}")

    if not scaler_path.exists():
        raise FileNotFoundError(f"File scaler tidak ditemukan: {scaler_path}")

    if not features_path.exists():
        raise FileNotFoundError(f"File features tidak ditemukan: {features_path}")

    model = load_model(model_path)
    scaler = joblib.load(scaler_path)
    features_data = load_json(features_path)

    config = load_json(config_path) if config_path.exists() else {}
    metrics = load_json(metrics_path) if metrics_path.exists() else {}

    return {
        "model": model,
        "scaler": scaler,
        "selected_features": features_data.get("selected_features", []),
        "model_columns": features_data.get("model_columns", []),
        "correlation_values": features_data.get("correlation_values", {}),
        "config": config,
        "metrics": metrics,
        "artifact_dir": str(artifact_dir),
    }


def predict_future_with_saved_model(
    df: pd.DataFrame,
    artifact_dir: str | Path,
    future_years: int = FUTURE_YEARS_DEFAULT,
) -> pd.DataFrame:
    artifacts = load_training_artifacts(artifact_dir)

    model = artifacts["model"]
    scaler = artifacts["scaler"]
    model_columns = artifacts["model_columns"]
    config = artifacts["config"]

    if not model_columns:
        raise ValueError("model_columns tidak ditemukan pada artifact model.")

    target_column = config.get("target_column", TARGET_COLUMN)
    year_column = config.get("year_column", YEAR_COLUMN)
    window_size = int(config.get("window_size", WINDOW_SIZE))

    cleaned_df = standardize_dataset(
        df=df,
        year_column=year_column,
        target_column=target_column,
    )

    scaled_df = transform_dataset_with_existing_scaler(
        df=cleaned_df,
        model_columns=model_columns,
        scaler=scaler,
    )

    return predict_future(
        model=model,
        scaler=scaler,
        scaled_df=scaled_df,
        original_df=cleaned_df,
        model_columns=model_columns,
        target_column=target_column,
        year_column=year_column,
        window_size=window_size,
        future_years=future_years,
    )