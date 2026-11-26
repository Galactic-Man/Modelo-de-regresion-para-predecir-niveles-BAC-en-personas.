# Validación Biológica del Mito «¿Existen los Mala Copas?»

Proyecto de Ciencia de Datos y Machine Learning orientado a evaluar científicamente el mito popular de salud **«¿Existen los mala copas?»**, demostrando con fundamentos fisiológicos y farmacocinéticos reales (sin manipulación artificial de datos) cómo la composición corporal, el sexo biológico, el entrenamiento físico y la variabilidad metabólica hepática determinan la **concentración de alcohol en sangre (BAC)**.

El umbral de referencia de embriaguez marcada utilizado en todo el proyecto es **`120.0 mg/100 mL`** (equivalente a `120 mg/dL` o `0.12% BAC`).

---

## Estado del proyecto (Roadmap por Sprints)

| Sprint | Alcance | Estado |
| :--- | :--- | :--- |
| **Sprint 1** | Estructura del repositorio, constantes compartidas (`src/constants.py`) y generador reproducible de 15,000 sesiones (`src/generate_data.py` -> `data/synthetic_bac_dataset.csv`). | **Completado** |
| **Sprint 2** | Notebook autónomo (`notebooks/analisis_malacopa.ipynb`) con EDA fisiológico, `RandomForestRegressor` sin *data leakage*, auditoría biológica de residuales, demostración del mito y exportación del modelo (`models/rf_bac_model.joblib`). | **Completado** |
| **Sprint 3** | Motor de inferencia (`src/predictor.py`) y simulador web interactivo en Streamlit (`app.py`) para estimar tragos combinados y margen restante en vivo según horas de fiesta. | **Pendiente** |

---

## Estructura actual del repositorio

```text
proyecto_malacopa/
├── data/
│   └── synthetic_bac_dataset.csv      # 15,000 sesiones sintéticas (12 columnas, 0 nulos)
├── models/
│   └── rf_bac_model.joblib            # Pipeline entrenado y comprimido (9.10 MB)
├── notebooks/
│   └── analisis_malacopa.ipynb        # Notebook completo ejecutado (7 secciones, 10 gráficas)
├── src/
│   ├── __init__.py
│   ├── constants.py                   # Constantes de dominio, bebidas y esquema
│   └── generate_data.py               # Simulación farmacocinética reproducible (SEED = 42)
├── README.md
└── requirements.txt
```

---

## Base biológica y prevención de fuga de datos (*Data Leakage*)

### 1. Simulación farmacocinética (`src/generate_data.py`)
El generador simula `15,000` sesiones de consumo (`SEED = 42`) separando estrictamente **8 variables observables** de **3 variables latentes internas**:

- **Observables (`FEATURE_COLS`)**: `sexo`, `edad`, `estatura_cm`, `peso_kg`, `nivel_entrenamiento`, `horas_consumo`, `gramos_alcohol`, `velocidad_consumo_g_h`.
- **Objetivo (`TARGET_COL`)**: `bac_mg_100ml` (calculado con el modelo de Widmark-Watson, truncado en `>= 0.0`).
- **Latentes (`LATENT_COLS`, prefijo `latent_`)**:
  - `latent_tbw_adj`: Agua Corporal Total base por ecuaciones de Watson multiplicada por el impacto escalonado del entrenamiento (`1.00`, `1.02`, `1.06`, `1.11`) y variabilidad individual de composición corporal ($\eta_{\text{agua}} \sim \mathcal{N}(1.0, 0.05)$ acotado en $[0.85, 1.15]$).
  - `latent_beta_eliminacion`: tasa individual de depuración hepática (enzimas ADH/ALDH), $\sim \mathcal{N}(15.0, 3.5)$ acotada en $[10.0, 24.0]$ mg/100 mL/h.
  - `latent_f_abs`: eficiencia de absorción gástrica, $\sim \mathcal{N}(0.92, 0.06)$ acotada en $[0.78, 1.00]$.

### 2. Bebidas estándar y niveles de entrenamiento (`src/constants.py`)
Con densidad del etanol `0.789 g/mL`:
- **Cerveza**: `330 mL` al `4% ABV` -> `10.4148 g` de alcohol puro.
- **Shot de licor**: `30 mL` al `28% ABV` -> `6.6276 g` de alcohol puro.
- **Whiskey**: `45 mL` al `43% ABV` -> `15.26715 g` de alcohol puro.

Niveles de entrenamiento (`TRAINING_LEVELS`):
- `0`: *No entrena* (`1.00`)
- `1`: *Menos de 6 meses* (`1.02`)
- `2`: *Entre 6 meses y 2 años* (`1.06`)
- `3`: *Más de 2 años* (`1.11`)

### 3. Regla anti-leakage en el modelado
Las variables `latent_*` **nunca** entran al modelo predictivo (`RandomForestRegressor`), ya que no son observables sin pruebas clínicas. Solo se utilizan en la Sección 4 del notebook para auditar biológicamente los residuales (`y_test - y_pred_test`).

---

## Resultados principales obtenidos (Sprints 1 y 2)

### Desempeño del modelo (`Pipeline`: `ColumnTransformer` + `RandomForestRegressor`)
Configuración: `n_estimators=150`, `max_depth=14`, `min_samples_leaf=4`, `random_state=42`, partición 80/20 (`12,000` Train / `3,000` Test).

| Conjunto | $R^2$ | MAE (mg/100 mL) | RMSE (mg/100 mL) |
| :--- | :---: | :---: | :---: |
| **Train (80%)** | `0.9870` | `10.96` | `15.89` |
| **5-Fold CV (Train)** | `0.9662 ± 0.0024` | `17.99 ± 0.43` | `25.66 ± 0.62` |
| **Test (20%)** | `0.9662` | `17.82` | `25.29` |

- Artefacto exportado: `models/rf_bac_model.joblib` (**`9.10 MB`**, por debajo del límite de `15 MB`).

### Importancia de variables por permutación (*Permutation Importance* en Test)
1. `gramos_alcohol`: **`107.69`** mg/100 mL (caída en MAE)
2. `sexo`: **`16.83`** mg/100 mL
3. `velocidad_consumo_g_h`: **`15.32`** mg/100 mL
4. `peso_kg`: **`13.53`** mg/100 mL
5. `nivel_entrenamiento`: **`1.28`** mg/100 mL
6. `estatura_cm`: **`0.79`** mg/100 mL
7. `horas_consumo`: **`0.25`** mg/100 mL
8. `edad`: **`0.20`** mg/100 mL

### Auditoría de residuales frente a biología oculta
Los errores residuales (`y_test - y_pred_test`) se correlacionan directamente con las variables latentes no observables:
- `latent_beta_eliminacion` (depuración hepática ADH/ALDH): **`r = -0.3650`**
- `latent_tbw_adj` (agua corporal total real): **`r = -0.1852`**
- `latent_f_abs` (absorción gástrica): **`r = 0.5317`**

### Experimento controlado (misma ingesta: `52.07 g` = 5 cervezas)
| Perfil | BAC predicho en `1.0 h` | BAC predicho en `2.0 h` |
| :--- | :---: | :---: |
| **Perfil A** (Mujer, 22 años, 160 cm, 55 kg, No entrena) | **`115.41 mg/100 mL`** | **`95.76 mg/100 mL`** |
| **Perfil B** (Mujer, 26 años, 166 cm, 66 kg, >2 años) | **`98.87 mg/100 mL`** | **`81.96 mg/100 mL`** |
| **Perfil C** (Hombre, 25 años, 174 cm, 74 kg, <6 meses) | **`74.18 mg/100 mL`** | **`54.70 mg/100 mL`** |
| **Perfil D** (Hombre, 27 años, 180 cm, 92 kg, >2 años) | **`67.25 mg/100 mL`** | **`43.45 mg/100 mL`** |

> **Veredicto científico:** El mito de los «mala copas» es **VERDADERO por fundamentos biológicos**. Aunque la dosis total y la velocidad de ingesta impulsan el ascenso del BAC, a igual consumo el volumen de dilución hídrica (sexo, peso, estatura y masa magra) y la variabilidad hepática individual (ADH/ALDH) generan brechas fisiológicas drásticas.

---

## Instalación y ejecución reproducible

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. (Opcional) Regenerar el dataset sintético y validar pruebas de sanidad
python src/generate_data.py

# 3. Ejecutar el notebook completo de análisis y entrenamiento
jupyter nbconvert --to notebook --execute --inplace notebooks/analisis_malacopa.ipynb
```
