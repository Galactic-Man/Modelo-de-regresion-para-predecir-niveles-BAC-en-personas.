"""Etapas, mensajes y textos de la app «Drunk enough?» (archivo editable).

Todo el texto de "cómo te vas a sentir" vive aquí. Son SUPUESTOS GENERALES
orientativos (no salen del modelo): la respuesta real al alcohol varía mucho
entre personas. Tono: cercano, humor suave, nunca como reto ni meta.

Cada etapa: ``min`` (inclusive) y ``max`` (exclusivo, None = sin tope) en
mg/100 mL, ``color`` de acento para la interfaz, y ``cara`` (expresión que
dibuja el frontend: sobrio, relajado, prendido, borracho, muy_borracho, peligro).
"""

from __future__ import annotations

STAGES: list[dict] = [
    {
        "id": "sobrio",
        "min": 0.0,
        "max": 20.0,
        "nombre": "Sobrio",
        "titulo": "Sobrio o apenas un cosquilleo",
        "mensaje": "Todo en orden por acá. Si acaso, un calorcito en la cara.",
        "consejo": "Arrancaste bien: come algo antes y ten agua a la mano.",
        "aviso": None,
        "color": "#16A34A",
        "cara": "sobrio",
    },
    {
        "id": "relajado",
        "min": 20.0,
        "max": 50.0,
        "nombre": "Relajado",
        "titulo": "Relajado y más hablador",
        "mensaje": "Te sueltas, cuentas más chistes y la charla fluye solita.",
        "consejo": "Un vaso de agua entre trago y trago te mantiene en este punto.",
        "aviso": "Desde aquí no manejes.",
        "color": "#0EA5E9",
        "cara": "relajado",
    },
    {
        "id": "prendido",
        "min": 50.0,
        "max": 80.0,
        "nombre": "Prendido",
        "titulo": "Prendido",
        "mensaje": "Risa fácil y buena vibra, pero los reflejos ya van más lentos.",
        "consejo": "Buen momento para bajar el ritmo y picar algo.",
        "aviso": "Recuerda no manejar.",
        "color": "#F59E0B",
        "cara": "prendido",
    },
    {
        "id": "borracho",
        "min": 80.0,
        "max": 120.0,
        "nombre": "Borracho",
        "titulo": "Borracho",
        "mensaje": "La coordinación y el habla se afectan. Ojo con las decisiones (y con los mensajes al ex).",
        "consejo": "Pásate al agua, quédate con tu gente y no te vayas solo.",
        "aviso": "Recuerda no manejar.",
        "color": "#EA580C",
        "cara": "borracho",
    },
    {
        "id": "muy_borracho",
        "min": 120.0,
        "max": 200.0,
        "nombre": "Muy borracho",
        "titulo": "Muy borracho",
        "mensaje": "Tropiezos, náuseas y posibles lagunas. La noche ya no está sumando.",
        "consejo": "Para de tomar, toma agua, siéntate y que alguien de confianza te acompañe a casa.",
        "aviso": "Recuerda no manejar.",
        "color": "#DC2626",
        "cara": "muy_borracho",
    },
    {
        "id": "peligro",
        "min": 200.0,
        "max": None,
        "nombre": "Zona de peligro",
        "titulo": "Zona de peligro",
        "mensaje": "Riesgo real para la salud. Esto ya no es chiste.",
        "consejo": "Agua, no estés solo y busca ayuda médica (línea 123 en Colombia) si la persona no responde o vomita sin parar.",
        "aviso": "Recuerda no manejar.",
        "color": "#9F1239",
        "cara": "peligro",
    },
]

MIX_NOTE: str = (
    "Estás mezclando bebidas. El modelo solo cuenta gramos de etanol, pero en la vida "
    "real mezclar cambia el ritmo al que tomas, enmascara el sabor del alcohol y suele "
    "empeorar el guayabo. Esta nota es cualitativa: no la calcula el modelo."
)

DISCLAIMER: str = (
    "Modelo educativo entrenado con datos sintéticos. Hay variabilidad individual real "
    "(metabolismo, comida, medicamentos, sueño). No es consejo médico ni te habilita para conducir."
)

TIPS: list[str] = [
    "Come antes y durante la salida.",
    "Alterna cada trago con un vaso de agua.",
    "No te quedes solo y cuida a tus amigos.",
    "Planea cómo vuelves a casa sin manejar.",
]


def stage_for(bac: float) -> dict:
    """Etapa que corresponde a un BAC en mg/100 mL."""
    for stage in STAGES:
        if stage["max"] is None or bac < stage["max"]:
            if bac >= stage["min"]:
                return stage
    return STAGES[-1]
