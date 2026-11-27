"""API y servidor estático de «Drunk enough?».

Arranque:  uvicorn app.main:app   (desde la raíz del proyecto)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from src.constants import BAC_THRESHOLD_MG_100ML, TRAINING_LEVELS
from src.drinks import DRINK_CATALOG, DRINKS_BY_ID
from src.predictor import MAX_SIMULATION_GRAMS, MODEL_MAE, load_model, simular
from src.stages import DISCLAIMER, MIX_NOTE, STAGES, TIPS

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    load_model()  # carga única al iniciar (RNF-02)
    yield


app = FastAPI(title="Drunk enough?", lifespan=lifespan)


class EstimateRequest(BaseModel):
    sexo: Literal["M", "F"]
    edad: int = Field(ge=18, le=65)
    estatura_cm: float = Field(ge=145, le=200)
    peso_kg: float = Field(ge=40, le=140)
    nivel_entrenamiento: int = Field(default=0, ge=0, le=3)  # opcional: la interfaz no lo pide
    horas_consumo: float = Field(ge=0.5, le=6.0)
    tragos: dict[str, int] = Field(default_factory=dict)

    @field_validator("horas_consumo")
    @classmethod
    def _media_hora(cls, v: float) -> float:
        if abs(v * 2 - round(v * 2)) > 1e-9:
            raise ValueError("horas_consumo debe ir en pasos de 0.5")
        return v

    @field_validator("tragos")
    @classmethod
    def _tragos(cls, v: dict[str, int]) -> dict[str, int]:
        for key, n in v.items():
            if key not in DRINKS_BY_ID:
                raise ValueError(f"bebida desconocida: {key}")
            if n < 0 or n > 200:
                raise ValueError(f"cantidad inválida para {key}")
        return v


@app.get("/api/config")
def config() -> dict:
    return {
        "bebidas": DRINK_CATALOG,
        "niveles_entrenamiento": [{"valor": k, "etiqueta": v["label"]} for k, v in TRAINING_LEVELS.items()],
        "etapas": STAGES,
        "umbral": BAC_THRESHOLD_MG_100ML,
        "mae": MODEL_MAE,
        "max_gramos": MAX_SIMULATION_GRAMS,
        "rangos": {
            "edad": [18, 65, 1],
            "estatura_cm": [145, 200, 1],
            "peso_kg": [40, 140, 1],
            "horas_consumo": [0.5, 6.0, 0.5],
        },
        "textos": {"mezcla": MIX_NOTE, "aviso": DISCLAIMER, "consejos": TIPS},
    }


@app.post("/api/estimate")
def estimate(req: EstimateRequest) -> dict:
    perfil = req.model_dump(include={"sexo", "edad", "estatura_cm", "peso_kg", "nivel_entrenamiento"})
    gramos = sum(DRINKS_BY_ID[k]["gramos"] * n for k, n in req.tragos.items())
    tipos = sum(1 for n in req.tragos.values() if n > 0)
    try:
        resultado = simular(perfil, req.horas_consumo, round(gramos, 5))
    except Exception as exc:  # pragma: no cover - defensa ante errores del modelo
        raise HTTPException(status_code=500, detail=f"Error del modelo: {exc}") from exc
    resultado["mezcla"] = tipos >= 2
    return resultado


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
