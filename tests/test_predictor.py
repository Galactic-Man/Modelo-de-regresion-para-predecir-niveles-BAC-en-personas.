import warnings

import pytest

from src.drinks import DRINK_CATALOG, DRINKS_BY_ID
from src.predictor import (
    MAX_SIMULATION_GRAMS,
    MODEL_MAE,
    SWEEP_GRAMS,
    calcular_margen,
    floor_half,
    load_model,
    predict_bac,
    simular,
)
from src.stages import STAGES, stage_for

# Perfiles del experimento controlado del Sprint 2 (antes en src/profiles.py; la interfaz ya no los usa).
P = {
    "A": {"sexo": "F", "edad": 22, "estatura_cm": 160, "peso_kg": 55, "nivel_entrenamiento": 0},
    "B": {"sexo": "F", "edad": 26, "estatura_cm": 166, "peso_kg": 66, "nivel_entrenamiento": 3},
    "C": {"sexo": "M", "edad": 25, "estatura_cm": 174, "peso_kg": 74, "nivel_entrenamiento": 1},
    "D": {"sexo": "M", "edad": 27, "estatura_cm": 180, "peso_kg": 92, "nivel_entrenamiento": 3},
}

# Tabla del README (experimento controlado, 52.07 g = 5 cervezas)
README = [("A", 1.0, 115.41), ("A", 2.0, 95.76), ("B", 1.0, 98.87), ("B", 2.0, 81.96),
          ("C", 1.0, 74.18), ("C", 2.0, 54.70), ("D", 1.0, 67.25), ("D", 2.0, 43.45)]


def test_model_loads_without_version_warnings():
    load_model.cache_clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        load_model()
    assert not [w for w in caught if "version" in str(w.message).lower()]


@pytest.mark.parametrize("perfil,horas,esperado", README)
def test_profiles_match_readme(perfil, horas, esperado):
    r = predict_bac(P[perfil], 52.07, horas)
    assert r["estado"] == "ok"
    assert r["bac"] == pytest.approx(esperado, abs=0.05)


def test_band_uses_test_mae():
    r = predict_bac(P["A"], 52.07, 1.0)
    assert MODEL_MAE == 17.82
    assert r["banda"] == [pytest.approx(r["bac"] - 17.82, abs=0.01), pytest.approx(r["bac"] + 17.82, abs=0.01)]
    low = predict_bac(P["D"], 5.0, 6.0)
    assert low["banda"][0] >= 0.0


def test_zero_grams_is_exact_zero():
    assert predict_bac(P["A"], 0, 3.0)["bac"] == 0.0


def test_out_of_limits():
    r = predict_bac(P["A"], 220.5, 3.0)
    assert r["estado"] == "fuera_de_limite" and r["bac"] is None
    assert simular(P["A"], 3.0, 230)["bac"]["estado"] == "fuera_de_limite"
    assert predict_bac(P["A"], MAX_SIMULATION_GRAMS, 3.0)["estado"] == "ok"


@pytest.mark.parametrize("valor,esperado", [(2.8, 2.5), (2.3, 2), (3.5, 3.5), (3.0, 3), (0.4, 0), (0.0, 0)])
def test_floor_half(valor, esperado):
    out = floor_half(valor)
    assert out == esperado
    if float(esperado).is_integer():
        assert isinstance(out, int)


def test_sweep_grid_1g_0_to_220():
    assert SWEEP_GRAMS[0] == 0 and SWEEP_GRAMS[-1] == 220 and len(SWEEP_GRAMS) == 221


def test_single_vectorized_predict_call(monkeypatch):
    model = load_model()
    calls = []
    original = model.predict
    monkeypatch.setattr(model, "predict", lambda df: calls.append(len(df)) or original(df))
    simular(P["C"], 2.0, 30.0)
    assert len(calls) == 1 and calls[0] == len(SWEEP_GRAMS) + 1


def test_margin_profile_a_one_hour():
    m = calcular_margen(P["A"], 1.0, 0.0)
    assert m["caso"] == "ok"
    assert 40 <= m["gramos_limite_perfil"] <= 60  # cruza 120 cerca de 5 cervezas
    beer = next(u for u in m["unidades"] if u["id"] == "cerveza")["unidades"]
    assert beer == floor_half(m["gramos_restantes"] / DRINKS_BY_ID["cerveza"]["gramos"])


def test_limit_reached_shows_zero():
    m = calcular_margen(P["A"], 1.0, 80.0)
    assert m["caso"] == "limite_superado"
    assert all(u["unidades"] == 0 for u in m["unidades"])


def test_heavy_profile_beyond_simulator():
    # Perfil D en 6 h: si no cruza 120 dentro de 220 g, se avisa el tope.
    m = calcular_margen(P["D"], 6.0, 0.0)
    if m["gramos_limite_perfil"] is None:
        assert m["caso"] == "supera_tope_simulacion"
        assert m["gramos_restantes"] == pytest.approx(220.0)
        assert m["ritmo"]["supera_tope"] is True


def test_next_stage_from_sweep():
    r = simular(P["A"], 1.0, DRINKS_BY_ID["cerveza"]["gramos"])
    nxt = r["proxima_etapa"]
    actual_idx = [s["id"] for s in STAGES].index(r["etapa"])
    assert nxt["id"] == STAGES[actual_idx + 1]["id"]
    assert all(isinstance(u["unidades"], (int, float)) for u in nxt["unidades"])


def test_stage_boundaries():
    assert stage_for(0)["id"] == "sobrio"
    assert stage_for(19.99)["id"] == "sobrio"
    assert stage_for(20)["id"] == "relajado"
    assert stage_for(119.9)["id"] == "borracho"
    assert stage_for(120)["id"] == "muy_borracho"
    assert stage_for(250)["id"] == "peligro"


def test_drink_grams_are_computed():
    for d in DRINK_CATALOG:
        assert d["gramos"] == pytest.approx(d["volumen_ml"] * d["abv"] * 0.789, abs=1e-4)
    assert DRINKS_BY_ID["cerveza"]["gramos"] == pytest.approx(10.4148, abs=1e-3)
