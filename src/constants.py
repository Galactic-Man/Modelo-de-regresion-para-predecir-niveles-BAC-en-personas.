"""Constantes de dominio y esquema compartidas para los 3 sprints del proyecto."""

BAC_THRESHOLD_MG_100ML: float = 120.0
ETHANOL_DENSITY_G_ML: float = 0.789

DRINKS: dict[str, dict[str, float | int | str]] = {
    "cerveza": {
        "nombre": "Cerveza",
        "volumen_ml": 330,
        "abv": 0.04,
        "gramos_alcohol": round(330 * 0.04 * ETHANOL_DENSITY_G_ML, 5),
    },
    "shot_licor": {
        "nombre": "Shot de licor",
        "volumen_ml": 30,
        "abv": 0.28,
        "gramos_alcohol": round(30 * 0.28 * ETHANOL_DENSITY_G_ML, 5),
    },
    "whiskey": {
        "nombre": "Whiskey",
        "volumen_ml": 45,
        "abv": 0.43,
        "gramos_alcohol": round(45 * 0.43 * ETHANOL_DENSITY_G_ML, 5),
    },
}

TRAINING_LEVELS: dict[int, dict[str, float | str]] = {
    0: {"label": "No entrena", "multiplier": 1.00},
    1: {"label": "Menos de 6 meses", "multiplier": 1.02},
    2: {"label": "Entre 6 meses y 2 años", "multiplier": 1.06},
    3: {"label": "Más de 2 años", "multiplier": 1.11},
}

FEATURE_COLUMNS: list[str] = [
    "sexo",
    "edad",
    "estatura_cm",
    "peso_kg",
    "nivel_entrenamiento",
    "horas_consumo",
    "gramos_alcohol",
    "velocidad_consumo_g_h",
]
TARGET_COLUMN: str = "bac_mg_100ml"
LATENT_COLUMNS: list[str] = [
    "latent_tbw_adj",
    "latent_beta_eliminacion",
    "latent_f_abs",
]
DATASET_COLUMNS: list[str] = FEATURE_COLUMNS + [TARGET_COLUMN] + LATENT_COLUMNS
