"""Generador reproducible de datos sintéticos con simulación farmacocinética real."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.constants import (  # noqa: E402
    BAC_THRESHOLD_MG_100ML,
    DATASET_COLUMNS,
    DRINKS,
    TRAINING_LEVELS,
)

SEED: int = 42
N_SAMPLES: int = 15_000
OUTPUT_PATH: Path = PROJECT_ROOT / "data" / "synthetic_bac_dataset.csv"


def compute_watson_tbw(
    sexo: np.ndarray | str,
    edad: np.ndarray | int | float,
    estatura_cm: np.ndarray | float,
    peso_kg: np.ndarray | float,
) -> np.ndarray | float:
    """Calcula el Agua Corporal Total base (TBW, litros) con las ecuaciones de Watson."""
    tbw_male = 2.447 - 0.09516 * edad + 0.1074 * estatura_cm + 0.3362 * peso_kg
    tbw_female = -2.097 + 0.1069 * estatura_cm + 0.2466 * peso_kg
    if isinstance(sexo, str):
        return float(tbw_male if sexo == "M" else tbw_female)
    return np.where(sexo == "M", tbw_male, tbw_female)


def compute_bac_mg_100ml(
    gramos_alcohol: np.ndarray | float,
    horas_consumo: np.ndarray | float,
    latent_tbw_adj: np.ndarray | float,
    latent_beta_eliminacion: np.ndarray | float,
    latent_f_abs: np.ndarray | float,
) -> np.ndarray | float:
    """Calcula el BAC (mg/100 mL) mediante modelo farmacocinético de Widmark-Watson."""
    raw_bac = (80.65 * gramos_alcohol * latent_f_abs) / latent_tbw_adj - (
        latent_beta_eliminacion * horas_consumo
    )
    return np.maximum(0.0, raw_bac)


def generate_synthetic_dataset(
    n_samples: int = N_SAMPLES,
    seed: int = SEED,
) -> pd.DataFrame:
    """Genera n_samples sesiones de consumo con variables observables, objetivo y latentes."""
    rng = np.random.default_rng(seed)

    # A. Variables observables
    sexo = rng.choice(["M", "F"], size=n_samples, p=[0.5, 0.5])
    edad = np.clip(
        np.rint(18 + rng.beta(1.5, 3.0, size=n_samples) * (65 - 18)),
        18,
        65,
    ).astype(int)

    estatura_m = np.clip(rng.normal(173.0, 7.0, size=n_samples), 155.0, 200.0)
    estatura_f = np.clip(rng.normal(160.0, 6.5, size=n_samples), 145.0, 185.0)
    estatura_cm = np.round(np.where(sexo == "M", estatura_m, estatura_f), 1)

    imc = np.clip(rng.normal(24.5, 4.0, size=n_samples), 17.0, 38.0)
    peso_kg = np.round(imc * (estatura_cm / 100.0) ** 2, 1)

    nivel_entrenamiento = rng.choice(
        [0, 1, 2, 3],
        size=n_samples,
        p=[0.40, 0.20, 0.25, 0.15],
    ).astype(int)

    horas_consumo = np.round(rng.uniform(0.5, 6.0, size=n_samples), 2)
    gramos_alcohol = np.round(rng.uniform(0.0, 220.0, size=n_samples), 2)
    velocidad_consumo_g_h = np.round(gramos_alcohol / horas_consumo, 2)

    # B. Simulación biológica real (variables latentes)
    tbw_base = compute_watson_tbw(sexo, edad, estatura_cm, peso_kg)
    k_entreno = np.array(
        [TRAINING_LEVELS[int(lvl)]["multiplier"] for lvl in nivel_entrenamiento],
        dtype=float,
    )
    eta_agua = np.clip(rng.normal(1.0, 0.05, size=n_samples), 0.85, 1.15)
    latent_tbw_adj = np.round(tbw_base * k_entreno * eta_agua, 4)

    latent_beta_eliminacion = np.round(
        np.clip(rng.normal(15.0, 3.5, size=n_samples), 10.0, 24.0),
        4,
    )
    latent_f_abs = np.round(
        np.clip(rng.normal(0.92, 0.06, size=n_samples), 0.78, 1.00),
        4,
    )

    bac_mg_100ml = np.round(
        compute_bac_mg_100ml(
            gramos_alcohol,
            horas_consumo,
            latent_tbw_adj,
            latent_beta_eliminacion,
            latent_f_abs,
        ),
        2,
    )

    df = pd.DataFrame(
        {
            "sexo": sexo,
            "edad": edad,
            "estatura_cm": estatura_cm,
            "peso_kg": peso_kg,
            "nivel_entrenamiento": nivel_entrenamiento,
            "horas_consumo": horas_consumo,
            "gramos_alcohol": gramos_alcohol,
            "velocidad_consumo_g_h": velocidad_consumo_g_h,
            "bac_mg_100ml": bac_mg_100ml,
            "latent_tbw_adj": latent_tbw_adj,
            "latent_beta_eliminacion": latent_beta_eliminacion,
            "latent_f_abs": latent_f_abs,
        }
    )
    return df[DATASET_COLUMNS]


def validate_dataset(df: pd.DataFrame) -> None:
    """Ejecuta aserciones de integridad estructural, rangos y sanidad biológica."""
    assert len(df) == N_SAMPLES, f"Se esperaban {N_SAMPLES} filas, hay {len(df)}"
    assert df.isna().sum().sum() == 0, "Se encontraron valores nulos en el dataset"
    assert list(df.columns) == DATASET_COLUMNS, "Orden o nombres de columnas incorrectos"
    assert (df["bac_mg_100ml"] >= 0.0).all(), "Existen valores negativos de BAC"

    assert set(df["sexo"].unique()) == {"M", "F"}, "Valores inválidos en sexo"
    assert df["edad"].between(18, 65).all(), "Edad fuera del rango [18, 65]"
    assert df.loc[df["sexo"] == "M", "estatura_cm"].between(155.0, 200.0).all()
    assert df.loc[df["sexo"] == "F", "estatura_cm"].between(145.0, 185.0).all()
    assert (df["peso_kg"] > 0.0).all(), "Peso debe ser positivo"
    assert set(df["nivel_entrenamiento"].unique()).issubset({0, 1, 2, 3})
    assert df["horas_consumo"].between(0.5, 6.0).all(), "Horas fuera de [0.5, 6.0]"
    assert df["gramos_alcohol"].between(0.0, 220.0).all(), "Gramos fuera de [0.0, 220.0]"
    assert (df["latent_tbw_adj"] > 0.0).all(), "TBW ajustada debe ser positiva"
    assert df["latent_beta_eliminacion"].between(10.0, 24.0).all()
    assert df["latent_f_abs"].between(0.78, 1.00).all()


def run_biological_coherence_check() -> tuple[float, float]:
    """Verifica perfiles de referencia con 5 cervezas (52.07 g) en 1 h y media metabólica."""
    gramos_5_cervezas = 5 * float(DRINKS["cerveza"]["gramos_alcohol"])
    horas = 1.0
    eta_agua_media = 1.0
    beta_media = 15.0
    f_abs_media = 0.92

    # Perfil A: Mujer, 22 años, 160 cm, 55 kg, no entrena (nivel=0)
    tbw_m = compute_watson_tbw("F", 22, 160.0, 55.0)
    tbw_m_adj = tbw_m * float(TRAINING_LEVELS[0]["multiplier"]) * eta_agua_media
    bac_mujer = float(
        compute_bac_mg_100ml(gramos_5_cervezas, horas, tbw_m_adj, beta_media, f_abs_media)
    )

    # Perfil B: Hombre, 25 años, 178 cm, 90 kg, >2 años entrenando (nivel=3)
    tbw_h = compute_watson_tbw("M", 25, 178.0, 90.0)
    tbw_h_adj = tbw_h * float(TRAINING_LEVELS[3]["multiplier"]) * eta_agua_media
    bac_hombre = float(
        compute_bac_mg_100ml(gramos_5_cervezas, horas, tbw_h_adj, beta_media, f_abs_media)
    )

    assert bac_mujer >= BAC_THRESHOLD_MG_100ML, (
        f"Se esperaba BAC mujer >= {BAC_THRESHOLD_MG_100ML}, obtenido {bac_mujer:.2f}"
    )
    assert bac_hombre < 70.0, (
        f"Se esperaba BAC hombre < 70.0, obtenido {bac_hombre:.2f}"
    )

    print("\n=== PRUEBA DE COHERENCIA BIOLÓGICA (5 cervezas = "
          f"{gramos_5_cervezas:.2f} g en 1.0 h, media metabólica) ===")
    print(
        f"Perfil A (Mujer, 22a, 160 cm, 55 kg, nivel=0): "
        f"TBW_base={tbw_m:.2f} L | TBW_adj={tbw_m_adj:.2f} L | "
        f"BAC={bac_mujer:.2f} mg/100 mL (>= {BAC_THRESHOLD_MG_100ML:.1f} OK)"
    )
    print(
        f"Perfil B (Hombre, 25a, 178 cm, 90 kg, nivel=3): "
        f"TBW_base={tbw_h:.2f} L | TBW_adj={tbw_h_adj:.2f} L | "
        f"BAC={bac_hombre:.2f} mg/100 mL (< 70.0 OK)"
    )
    return bac_mujer, bac_hombre


def main() -> None:
    """Orquesta la generación, validación, exportación y reporte del dataset sintético."""
    df = generate_synthetic_dataset(n_samples=N_SAMPLES, seed=SEED)
    validate_dataset(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    n_rows = len(df)
    n_nulls = int(df.isna().sum().sum())
    min_bac = float(df["bac_mg_100ml"].min())
    above_threshold = df["bac_mg_100ml"] >= BAC_THRESHOLD_MG_100ML
    n_above = int(above_threshold.sum())
    pct_above = float(above_threshold.mean() * 100.0)

    print("=== GENERACIÓN DE DATASET SINTÉTICO COMPLETADA ===")
    print(f"Archivo guardado: {OUTPUT_PATH}")
    print(f"Confirmación: {n_rows:,} filas | {n_nulls} valores nulos | min(bac_mg_100ml) = {min_bac:.2f} (>= 0 OK)")
    print(f"Registros con bac_mg_100ml >= {BAC_THRESHOLD_MG_100ML:.1f} mg/100 mL: {n_above:,} ({pct_above:.2f}%)")

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)
    print("\n=== RESUMEN ESTADÍSTICO (describe()) ===")
    print(df.describe().round(2))

    run_biological_coherence_check()
    print("\nTodas las aserciones de Sprint 1 pasaron correctamente.")


if __name__ == "__main__":
    main()
