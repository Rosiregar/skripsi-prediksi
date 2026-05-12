from pathlib import Path
import sys

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


def main() -> None:
    output_dir = PROJECT_DIR / "storage" / "temp"
    output_dir.mkdir(parents=True, exist_ok=True)

    tahun = list(range(2008, 2026))

    np.random.seed(42)

    jumlah_penduduk = np.linspace(2200000, 2700000, len(tahun)).astype(int)
    tpak = np.round(np.linspace(60, 66, len(tahun)) + np.random.normal(0, 0.5, len(tahun)), 2)
    pdrb = np.round(np.linspace(45000, 78000, len(tahun)) + np.random.normal(0, 1500, len(tahun)), 2)
    inflasi = np.round(np.random.uniform(1.5, 6.0, len(tahun)), 2)

    total_pengangguran = (
        85000
        + np.linspace(8000, -12000, len(tahun))
        - (tpak - 60) * 1200
        + np.random.normal(0, 2500, len(tahun))
    ).astype(int)

    df = pd.DataFrame(
        {
            "Tahun": tahun,
            "Total_Pengangguran": total_pengangguran,
            "Jumlah_Penduduk": jumlah_penduduk,
            "TPAK": tpak,
            "PDRB": pdrb,
            "Inflasi": inflasi,
        }
    )

    output_path = output_dir / "dataset_contoh_pengangguran_sulut.xlsx"
    df.to_excel(output_path, index=False)

    print(f"Dataset contoh berhasil dibuat:")
    print(output_path)


if __name__ == "__main__":
    main()