"""Motor de inferencia de «Drunk enough?» (Sprint 3).

- Carga ``models/rf_bac_model.joblib`` UNA sola vez (caché en memoria).
- ``predict_bac``: BAC central + banda ± MAE de test, o estado fuera de límite.
- ``calcular_margen``: barrido 0–220 g (paso 1 g) en UNA sola llamada
  vectorizada a ``model.predict`` para hallar el cruce de 120 mg/100 mL.
- ``floor_half``: redondeo piso en medios (2.8 → 2.5, 2.3 → 2).
- ``simular``: todo lo que necesita la interfaz con una sola llamada al modelo.
"""

from __future__ import annotations

import math
import warnings
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.constants import BAC_THRESHOLD_MG_100ML, FEATURE_COLUMNS
from src.drinks import DRINK_CATALOG
from src.stages import STAGES, stage_for

MODEL_PATH: Path = Path(__file__).resolve().parent.parent / "models" / "rf_bac_model.joblib"
MAX_SIMULATION_GRAMS: float = 220.0
MODEL_MAE: float = 17.82  # MAE en Test del Sprint 2 (notebook, sección de métricas)
MODEL_MAE_MG_100ML: float = MODEL_MAE  # alias con el nombre del documento de requerimientos
SWEEP_STEP_G: float = 1.0
SWEEP_GRAMS: np.ndarray = np.arange(0.0, MAX_SIMULATION_GRAMS + SWEEP_STEP_G / 2, SWEEP_STEP_G)

PERFIL_KEYS = ("sexo", "edad", "estatura_cm", "peso_kg", "nivel_entrenamiento")


class ModelVersionWarningError(RuntimeError):
    """El modelo cargó con advertencias (p. ej. versión distinta de scikit-learn)."""


@lru_cache(maxsize=1)
def load_model():
    """Carga el Pipeline una sola vez. Falla si scikit-learn emite advertencias de versión."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model = joblib.load(MODEL_PATH)
    relevant = [w for w in caught if "version" in str(w.message).lower() or "Inconsistent" in str(w.message)]
    if relevant:
        raise ModelVersionWarningError(
            "El modelo se cargó con advertencias de versión: "
            + "; ".join(str(w.message) for w in relevant)
            + ". Instala scikit-learn==1.9.1 (versión con la que se serializó)."
        )
    # Solo afecta la ejecución en memoria (no el archivo): para lotes pequeños
    # un hilo es más rápido que repartir 150 árboles entre todos los núcleos.
    regressor = model.named_steps.get("regressor")
    if regressor is not None and hasattr(regressor, "n_jobs"):
        regressor.n_jobs = 1
    return model


def floor_half(valor: float) -> int | float:
    """Piso en pasos de 0.5. Devuelve int si es entero (2, no 2.0)."""
    resultado = math.floor(valor * 2 + 1e-9) / 2
    if resultado < 0:
        resultado = 0.0
    return int(resultado) if float(resultado).is_integer() else resultado


def _frame(perfil: dict, horas_consumo: float, gramos: np.ndarray) -> pd.DataFrame:
    gramos = np.asarray(gramos, dtype=float)
    n = len(gramos)
    df = pd.DataFrame(
        {
            "sexo": [perfil["sexo"]] * n,
            "edad": np.full(n, int(perfil["edad"])),
            "estatura_cm": np.full(n, float(perfil["estatura_cm"])),
            "peso_kg": np.full(n, float(perfil["peso_kg"])),
            "nivel_entrenamiento": np.full(n, int(perfil["nivel_entrenamiento"])),
            "horas_consumo": np.full(n, float(horas_consumo)),
            "gramos_alcohol": gramos,
            "velocidad_consumo_g_h": gramos / float(horas_consumo),
        }
    )
    return df[FEATURE_COLUMNS]


def _predict(perfil: dict, horas_consumo: float, gramos: np.ndarray) -> np.ndarray:
    """Una única llamada vectorizada al modelo. 0 g → 0.0 exacto."""
    gramos = np.asarray(gramos, dtype=float)
    pred = load_model().predict(_frame(perfil, horas_consumo, gramos))
    pred = np.clip(pred, 0.0, None)
    pred[gramos == 0] = 0.0
    return pred


def _banda(bac: float) -> list[float]:
    return [round(max(0.0, bac - MODEL_MAE), 2), round(bac + MODEL_MAE, 2)]


def _resultado_bac(gramos: float, bac: float | None) -> dict:
    if gramos > MAX_SIMULATION_GRAMS:
        return {"estado": "fuera_de_limite", "bac": None, "banda": None, "gramos": round(gramos, 2)}
    return {"estado": "ok", "bac": round(float(bac), 2), "banda": _banda(float(bac)), "gramos": round(gramos, 2)}


def predict_bac(perfil: dict, gramos_alcohol: float, horas_consumo: float) -> dict:
    """BAC estimado con banda ± MAE. Si gramos > 220 → estado 'fuera_de_limite'."""
    if gramos_alcohol > MAX_SIMULATION_GRAMS:
        return _resultado_bac(gramos_alcohol, None)
    if gramos_alcohol == 0:
        return _resultado_bac(0.0, 0.0)
    bac = _predict(perfil, horas_consumo, np.array([gramos_alcohol]))[0]
    return _resultado_bac(gramos_alcohol, bac)


def _unidades(gramos: float, drinks: list[dict]) -> list[dict]:
    return [{"id": d["id"], "unidades": floor_half(max(gramos, 0.0) / d["gramos"])} for d in drinks]


def _primer_cruce(grid_pred: np.ndarray, desde_g: float, umbral: float) -> float | None:
    """Primer gramo del barrido > desde_g (o == 0) cuyo BAC alcanza el umbral."""
    mask = (grid_pred >= umbral) & (SWEEP_GRAMS >= desde_g)
    idx = np.flatnonzero(mask)
    return float(SWEEP_GRAMS[idx[0]]) if idx.size else None


def calcular_margen(
    perfil: dict,
    horas_consumo: float,
    gramos_actuales: float,
    drinks: list[dict] | None = None,
    grid_pred: np.ndarray | None = None,
    bac_actual: float | None = None,
) -> dict:
    """Margen hasta 120 mg/100 mL con barrido 0–220 g (una sola llamada a predict)."""
    drinks = drinks or DRINK_CATALOG
    if grid_pred is None:
        grid_pred = _predict(perfil, horas_consumo, SWEEP_GRAMS)
    if bac_actual is None:
        bac_actual = predict_bac(perfil, gramos_actuales, horas_consumo)["bac"]

    limite_g = _primer_cruce(grid_pred, 0.0, BAC_THRESHOLD_MG_100ML)
    alcanza_en_tope = limite_g is not None

    if bac_actual is not None and bac_actual >= BAC_THRESHOLD_MG_100ML:
        caso, restante = "limite_superado", 0.0
    else:
        cruce = _primer_cruce(grid_pred, gramos_actuales, BAC_THRESHOLD_MG_100ML)
        if cruce is None:
            caso, restante = "supera_tope_simulacion", MAX_SIMULATION_GRAMS - gramos_actuales
        else:
            caso, restante = "ok", cruce - gramos_actuales
    restante = max(0.0, restante)

    ritmo_total_g = limite_g if alcanza_en_tope else MAX_SIMULATION_GRAMS
    return {
        "caso": caso,
        "gramos_restantes": round(restante, 2),
        "unidades": _unidades(restante, drinks) if caso != "limite_superado" else [{"id": d["id"], "unidades": 0} for d in drinks],
        "gramos_limite_perfil": limite_g,
        "ritmo": {
            "horas": horas_consumo,
            "gramos_por_hora": round(ritmo_total_g / horas_consumo, 2),
            "supera_tope": not alcanza_en_tope,
            "unidades_por_hora": _unidades(ritmo_total_g / horas_consumo, drinks),
        },
    }


def proxima_etapa(grid_pred: np.ndarray, gramos_actuales: float, bac_actual: float, drinks: list[dict]) -> dict | None:
    """Siguiente etapa y cuántos tragos más (piso en 0.5) la alcanzan, según el barrido."""
    actual = stage_for(bac_actual)
    idx = STAGES.index(actual)
    if idx + 1 >= len(STAGES):
        return None
    siguiente = STAGES[idx + 1]
    cruce = _primer_cruce(grid_pred, gramos_actuales + 1e-9, siguiente["min"])
    if cruce is None:
        return {"id": siguiente["id"], "nombre": siguiente["nombre"], "fuera_de_simulacion": True, "gramos": None, "unidades": []}
    gramos = cruce - gramos_actuales
    return {
        "id": siguiente["id"],
        "nombre": siguiente["nombre"],
        "fuera_de_simulacion": False,
        "gramos": round(gramos, 2),
        "unidades": _unidades(gramos, drinks),
    }


def simular(perfil: dict, horas_consumo: float, gramos_actuales: float, drinks: list[dict] | None = None) -> dict:
    """Resultado completo para la interfaz con UNA sola llamada a ``model.predict``."""
    drinks = drinks or DRINK_CATALOG
    if gramos_actuales > MAX_SIMULATION_GRAMS:
        return {"bac": _resultado_bac(gramos_actuales, None), "etapa": None, "margen": None, "proxima_etapa": None}

    gramos_eval = np.concatenate([SWEEP_GRAMS, [gramos_actuales]])
    pred = _predict(perfil, horas_consumo, gramos_eval)
    grid_pred, bac_actual = pred[:-1], float(pred[-1])

    bac = _resultado_bac(gramos_actuales, bac_actual)
    return {
        "bac": bac,
        "etapa": stage_for(bac["bac"])["id"],
        "margen": calcular_margen(perfil, horas_consumo, gramos_actuales, drinks, grid_pred, bac["bac"]),
        "proxima_etapa": proxima_etapa(grid_pred, gramos_actuales, bac["bac"], drinks),
    }
