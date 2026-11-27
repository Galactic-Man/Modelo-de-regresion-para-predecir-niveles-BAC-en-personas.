"""Catálogo de bebidas de la app «Drunk enough?».

ÚNICO lugar donde se definen las bebidas. Para agregar una nueva basta con
añadir una entrada a ``DRINK_CATALOG``: la API (/api/config), la interfaz y el
predictor la toman automáticamente. Los gramos NO se escriben a mano: se
calculan con la fórmula oficial del repo (volumen_ml × abv × densidad etanol).

Campos:
    id         identificador único (sin espacios; se usa en la API)
    nombre     nombre visible
    singular / plural  cómo se cuenta en frases ("1 cerveza", "2.5 cervezas")
    volumen_ml volumen de una unidad
    abv        fracción de alcohol por volumen (0.04 = 4 %)
    vaso       ilustración que usa la interfaz: "cerveza" | "shot"
    color_liquido  color del líquido en la ilustración (solo estético)

SUPUESTOS A VERIFICAR: los ABV de Ron (35 %), Smirnoff/vodka (37.5 %) y
Bacardí (35 %) son valores típicos de etiqueta, no medidos; revísalos contra la
botella real. Cerveza (330 mL, 4 %) y Aguardiente (= "shot de licor" del repo,
30 mL, 28 %) vienen de src/constants.py.
"""

from __future__ import annotations

from src.constants import DRINKS as REPO_DRINKS
from src.constants import ETHANOL_DENSITY_G_ML


def alcohol_grams(volumen_ml: float, abv: float) -> float:
    """Gramos de etanol puro de una unidad (fórmula del repo)."""
    return round(volumen_ml * abv * ETHANOL_DENSITY_G_ML, 5)


_BEER = REPO_DRINKS["cerveza"]
_SHOT = REPO_DRINKS["shot_licor"]

DRINK_CATALOG: list[dict] = [
    {
        "id": "cerveza",
        "nombre": "Cerveza",
        "singular": "cerveza",
        "plural": "cervezas",
        "volumen_ml": _BEER["volumen_ml"],
        "abv": _BEER["abv"],
        "vaso": "cerveza",
        "color_liquido": "#F5B83D",
    },
    {
        "id": "aguardiente",
        "nombre": "Aguardiente",
        "singular": "shot de aguardiente",
        "plural": "shots de aguardiente",
        "volumen_ml": _SHOT["volumen_ml"],
        "abv": _SHOT["abv"],
        "vaso": "shot",
        "color_liquido": "#D6EEF5",
    },
    {
        "id": "ron",
        "nombre": "Ron",
        "singular": "shot de ron",
        "plural": "shots de ron",
        "volumen_ml": 30,
        "abv": 0.35,  # supuesto a verificar
        "vaso": "shot",
        "color_liquido": "#C9822B",
    },
    {
        "id": "smirnoff",
        "nombre": "Smirnoff (vodka)",
        "singular": "shot de Smirnoff",
        "plural": "shots de Smirnoff",
        "volumen_ml": 30,
        "abv": 0.375,  # supuesto a verificar
        "vaso": "shot",
        "color_liquido": "#E3F1F7",
    },
    {
        "id": "bacardi",
        "nombre": "Bacardí",
        "singular": "shot de Bacardí",
        "plural": "shots de Bacardí",
        "volumen_ml": 30,
        "abv": 0.35,  # supuesto a verificar
        "vaso": "shot",
        "color_liquido": "#E0A24A",
    },
]

# Gramos calculados (nunca escritos a mano).
for _d in DRINK_CATALOG:
    _d["gramos"] = alcohol_grams(_d["volumen_ml"], _d["abv"])

DRINKS_BY_ID: dict[str, dict] = {d["id"]: d for d in DRINK_CATALOG}
