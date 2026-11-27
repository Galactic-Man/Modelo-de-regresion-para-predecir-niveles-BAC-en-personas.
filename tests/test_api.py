"""Pruebas de la API llamando a los handlers directamente (sin httpx/TestClient,
para no agregar dependencias fuera de fastapi y uvicorn)."""

import time

import pytest
from pydantic import ValidationError

from app.main import EstimateRequest, config, estimate

BASE = {"sexo": "F", "edad": 22, "estatura_cm": 160, "peso_kg": 55, "nivel_entrenamiento": 0, "horas_consumo": 1.0}


def test_config():
    data = config()
    assert len(data["bebidas"]) == 5 and len(data["etapas"]) == 6
    assert "perfiles" not in data
    assert data["mae"] == 17.82
    assert all("gramos" in b for b in data["bebidas"])


def test_estimate_five_beers_profile_a():
    body = estimate(EstimateRequest(**BASE, tragos={"cerveza": 5}))
    assert abs(body["bac"]["bac"] - 115.4) < 1.0
    assert body["etapa"] == "borracho" and body["mezcla"] is False


def test_estimate_mix_and_out_of_limits():
    assert estimate(EstimateRequest(**BASE, tragos={"cerveza": 1, "ron": 1}))["mezcla"] is True
    r = estimate(EstimateRequest(**BASE, tragos={"cerveza": 22}))
    assert r["bac"]["estado"] == "fuera_de_limite"


@pytest.mark.parametrize("override", [{"horas_consumo": 1.2}, {"edad": 17}, {"peso_kg": 150}, {"tragos": {"tequila": 1}}, {"sexo": "X"}])
def test_validation(override):
    with pytest.raises(ValidationError):
        EstimateRequest(**{**BASE, **override})


def test_latency_under_one_second():
    estimate(EstimateRequest(**BASE, tragos={"cerveza": 2}))
    t = time.perf_counter()
    estimate(EstimateRequest(**BASE, tragos={"cerveza": 3, "aguardiente": 2}))
    assert time.perf_counter() - t < 1.0


def test_training_level_is_optional_and_defaults_to_zero():
    body = {k: v for k, v in BASE.items() if k != "nivel_entrenamiento"}
    req = EstimateRequest(**body, tragos={"cerveza": 5})
    assert req.nivel_entrenamiento == 0
    assert estimate(req)["bac"] == estimate(EstimateRequest(**BASE, tragos={"cerveza": 5}))["bac"]


def test_driving_notices_by_stage():
    avisos = {e["id"]: e["aviso"] for e in config()["etapas"]}
    assert avisos["sobrio"] is None
    assert avisos["relajado"] == "Desde aquí no manejes."
    assert all(avisos[k] == "Recuerda no manejar." for k in ("prendido", "borracho", "muy_borracho", "peligro"))
