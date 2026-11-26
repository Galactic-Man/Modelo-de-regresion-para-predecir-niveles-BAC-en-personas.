# Especificación de Requerimientos — Sprint 3: Simulador Web «¿Existen los mala copas?»

## 1. Objetivo del Sprint

Construir una aplicación web ligera e interactiva que conecte el modelo de Machine Learning ya entrenado en el Sprint 2 (`RandomForestRegressor`) con una interfaz sencilla para el usuario final.

La aplicación permite ingresar un perfil físico básico y la duración de una salida, simular combinaciones de tragos en vivo y visualizar el BAC estimado (con su banda de incertidumbre biológica) y cuánto margen queda antes de alcanzar el umbral de embriaguez de **120 mg/100 mL** (0.12% BAC).

> **Nota de enfoque:** El peso académico y estadístico del proyecto está en la demostración del mito dentro del notebook del Sprint 2. En este sprint priorizamos una aplicación **funcional, fiel a las limitaciones del modelo, clara y fácil de desplegar**, sin sobreingeniería.

## 2. Insumos que ya tienes listos en el repositorio

No necesitas volver a generar datos ni reentrenar el modelo. Vas a trabajar directamente sobre estos archivos:

* `models/rf_bac_model.joblib`: `Pipeline` de `scikit-learn` ya entrenado (incluye el preprocesamiento de `sexo` y el `RandomForestRegressor`).
* `src/constants.py`: Constantes oficiales del proyecto (umbral de BAC, tabla de bebidas y niveles de entrenamiento). **Importa siempre los valores desde aquí** para no duplicar números.
* `notebooks/analisis_malacopa.ipynb`: De aquí debes tomar el valor del **MAE en Test** (error medio absoluto en mg/100 mL) para configurar la banda de incertidumbre de la app.
* `requirements.txt`: Dependencias base del entorno.

### Contrato de entrada del modelo (obligatorio)

Para hacer una predicción con `model.predict(df)`, el modelo espera un `DataFrame` de pandas con **exactamente estas 8 columnas y nombres**:

| Columna | Tipo | Valores válidos / Rango de entrenamiento |
| :--- | :--- | :--- |
| `sexo` | `str` | `"M"` o `"F"` |
| `edad` | `int` | `18` a `65` |
| `estatura_cm` | `float` | `145` a `200` |
| `peso_kg` | `float` | `40` a `140` |
| `nivel_entrenamiento` | `int` | `0`, `1`, `2` o `3` |
| `horas_consumo` | `float` | `0.5` a `6.0` |
| `gramos_alcohol` | `float` | `0.0` a `220.0` |
| `velocidad_consumo_g_h` | `float` | `gramos_alcohol / horas_consumo` |

### Tablas de referencia (definidas en `src/constants.py`)

**Bebidas estándar:**

| Bebida | Volumen | Alcohol (ABV) | Gramos de alcohol puro |
| :--- | :---: | :---: | :---: |
| Cerveza | 330 mL | 4% | 10.41 g |
| Shot de licor | 30 mL | 28% | 6.63 g |
| Whiskey | 45 mL | 43% | 15.27 g |

**Niveles de entrenamiento (desplegable):**

* `0`: No entrena
* `1`: Menos de 6 meses
* `2`: Entre 6 meses y 2 años
* `3`: Más de 2 años

## 3. Requerimientos Funcionales (Qué debe hacer la app)

### RF-01: Formulario de perfil y ventana de tiempo

La interfaz debe permitir configurar:

* **Edad** (campo numérico o deslizador, `18` a `65` años).
* **Sexo biológico** (selector obligatorio: Masculino / Femenino, mapeado a `"M"` / `"F"`).
* **Estatura aproximada** en centímetros (`145` a `200` cm).
* **Peso aproximado** en kilogramos (`40` a `140` kg).
* **¿Entrenas actualmente?** Selector desplegable con las 4 opciones escalonadas (`0` a `3`).
* **Duración de la salida:** *"¿Durante cuántas horas vas a estar tomando?"* — deslizador o selector desde **`0.5` horas (30 minutos) hasta `6.0` horas**, con incrementos de **`0.5` horas** (`0.5, 1.0, 1.5, ..., 6.0`).

### RF-02: Botones de perfiles precargados (obligatorio)

Para agilizar las pruebas y la demostración en vivo, la interfaz debe incluir botones rápidos que rellenen automáticamente los campos del formulario con perfiles predefinidos (tomados directamente del experimento del Sprint 2):

* **Perfil A (Ligero, sin entreno):** Mujer, 22 años, 160 cm, 55 kg, No entrena (`0`).
* **Perfil B (Medio, entrenado):** Mujer, 26 años, 166 cm, 66 kg, Más de 2 años (`3`).
* **Perfil C (Promedio, iniciando):** Hombre, 25 años, 174 cm, 74 kg, Menos de 6 meses (`1`).
* **Perfil D (Pesado, muy entrenado):** Hombre, 27 años, 180 cm, 92 kg, Más de 2 años (`3`).

Al hacer clic en cualquiera de estos botones, los campos del perfil se actualizan de inmediato y la predicción se recalcula en vivo (permitiendo igualmente que el usuario edite cualquier valor después).

### RF-03: Simulador interactivo de tragos en vivo

* Contadores independientes (`0, 1, 2...`) para seleccionar cuántas unidades ya tomó o planea tomar de cada bebida:
  * Cervezas (330 mL, 4%)
  * Shots de licor (30 mL, 28%)
  * Whiskeys (45 mL, 43%)
* Botón rápido para reiniciar los tragos a cero sin borrar el perfil físico.
* Cada cambio en el perfil, las horas o los tragos debe recalcular los resultados automáticamente en vivo.

### RF-04: Indicador de BAC estimado con banda de incertidumbre

Como el modelo no conoce el metabolismo hepático exacto del usuario, la app **no debe presentar la predicción como un número exacto único**, sino con su rango de variabilidad:

* Mostrar el **BAC estimado central** en mg/100 mL acompañado de su **banda de incertidumbre** basada en el MAE del conjunto de prueba obtenido en el Sprint 2:
  $$\text{Rango estimado} = \left[\max(0,\; \text{BAC}_{\text{pred}} - \text{MAE}),\; \text{BAC}_{\text{pred}} + \text{MAE}\right]$$
* Mostrar visualmente el formato `XX.X` $\pm$ `MAE` mg/100 mL (o el intervalo mínimo–máximo estimado) con una nota breve explicando que ese margen refleja la variabilidad metabólica individual.
* Incluir una barra de progreso respecto al umbral de **120 mg/100 mL** con código de color semafórico:
  * **Verde:** menor a 60 mg/100 mL (margen amplio).
  * **Amarillo / Naranja:** entre 60 y 119.9 mg/100 mL (acercándose al límite).
  * **Rojo:** mayor o igual a 120 mg/100 mL (umbral de embriaguez alcanzado o superado).

### RF-05: Cálculo de margen restante, redondeo en mitades y control de límites de simulación

A partir del consumo marcado en el simulador, la app debe calcular cuánto margen queda antes de tocar los **120 mg/100 mL** siguiendo estas tres reglas estrictas:

1. **Búsqueda segura del límite máximo (barrido de 1 a 2 g):**
   * En lugar de usar búsqueda binaria simple (que puede fallar ante pequeños escalones del Random Forest), evaluar al modelo haciendo un barrido en pasos de `1` o `2` gramos desde `0 g` hasta `220 g` para ese perfil y duración, detectando el primer punto donde el BAC predicho alcanza o supera `120.0 mg/100 mL`.
2. **Parada por fuera de límites de la simulación (tope de 220 g):**
   * El modelo solo fue entrenado hasta **`220.0` gramos de alcohol puro** y un Random Forest no extrapola fuera de ese dominio.
   * **Caso A (Consumo actual excede el tope):** Si la suma de los tragos marcados por el usuario supera los `220.0 g`, **detener la simulación**, no mostrar una predicción engañosa y desplegar un aviso claro indicando que el consumo ingresado se encuentra **fuera de los límites de la simulación**.
   * **Caso B (El perfil no alcanza 120 mg/100 mL dentro de los 220 g):** Si al terminar el barrido en `220.0 g` (por ejemplo, un perfil muy pesado en 6 horas) la predicción aún no cruza los `120.0 mg/100 mL`, detener el cálculo en `220 g` y avisar claramente que el límite real de ese perfil supera el rango máximo del simulador (indicando el margen calculado hasta el tope de simulación).
3. **Redondeo piso en mitades (`0.5`):**
   * Al convertir los gramos restantes a unidades de cada bebida (cervezas, shots o whiskeys por separado), aplicar **función piso en pasos de `0.5`**:
     $$u_{\text{mostrado}} = \frac{\lfloor 2 \cdot u_{\text{exacto}} \rfloor}{2}$$
   * **Ejemplos obligatorios de comportamiento:**
     * `2.8` cervezas $\rightarrow$ mostrar **`2.5 cervezas`**
     * `2.3` cervezas $\rightarrow$ mostrar **`2 cervezas`** (sin `.0` innecesario)
     * `3.5` cervezas $\rightarrow$ mostrar **`3.5 cervezas`**
     * Si el usuario ya alcanzó o superó los `120 mg/100 mL` $\rightarrow$ mostrar **`0`** en todas las bebidas y un aviso claro de límite superado.

### RF-06: Distribución sugerida en el tiempo

* Indicar un ritmo de referencia para la ventana elegida (por ejemplo: *"En una salida de 3 horas, tu margen total equivale a un ritmo máximo aproximado de..."*), reforzando que espaciar el consumo en más horas cambia la tolerancia total.

### RF-07: Aviso educativo y de responsabilidad

* Incluir en un lugar visible (pie de página o recuadro informativo) que los resultados provienen de un modelo educativo entrenado con datos sintéticos, que existe variabilidad metabólica real y que la herramienta **no es consejo médico ni habilita para conducir**.

## 4. Arquitectura y Libertad de Framework

Para mantener el código limpio y fácil de mantener, se recomienda separar la lógica de predicción de la capa visual:

1. **`src/predictor.py` (lógica de negocio e inferencia — obligatorio en Python):**
   * Cargar `models/rf_bac_model.joblib` una sola vez en memoria (caché).
   * Constantes auxiliares: `MAX_SIMULATION_GRAMS = 220.0` y `MODEL_MAE_MG_100ML` (valor exacto del Sprint 2).
   * Función `floor_half(valor)`: implementa `math.floor(valor * 2) / 2` y formatea enteros sin `.0` (`2`, `2.5`, `3`, `3.5`).
   * Función `predict_bac(perfil, gramos_alcohol, horas_consumo)`:
     * Si `gramos_alcohol == 0`, retorna `0.0` (evita ruido residual en cero).
     * Si `gramos_alcohol > 220.0`, retorna un estado indicando `"fuera_de_limite"` para que la interfaz detenga la simulación.
     * Devuelve el valor predicho y la banda `[max(0, pred - MAE), pred + MAE]`.
   * Función `calcular_margen(...)`:
     * Construye un único `DataFrame` vectorizado con `gramos_alcohol` de `0` a `220` en pasos de `1` o `2` g y ejecuta una sola llamada `model.predict(df_grid)` (tarda milisegundos).
     * Detecta si el perfil alcanza `120.0 mg/100 mL` dentro de `220 g` o si alcanza el tope del simulador.
     * Calcula el margen restante en gramos y devuelve las unidades disponibles de cada bebida aplicando `floor_half(...)`.

2. **Capa Web / Frontend (Framework libre):**
   * **Opción considerada y sugerida:** **Streamlit** (`app.py`), porque permite armar toda la interfaz en Python puro con poco esfuerzo y desplegar gratis en Streamlit Community Cloud.
   * **Nota importante:** **Streamlit NO es obligatorio.** Tienes total libertad para cambiarlo por cualquier otro framework web que prefieras o domines mejor (por ejemplo, **Flask**, **FastAPI + HTML/CSS/JS**, **Gradio**, **React + backend Python**, etc.), siempre y cuando consuma `models/rf_bac_model.joblib`, respete los requerimientos funcionales de la Sección 3 y cumpla con el acceso remoto de la Sección 5.

## 5. Requerimientos No Funcionales y Despliegue

* **RNF-01 (Acceso desde otros equipos):** La app debe poder abrirse desde otro computador o celular sin pagar servidor. Según el framework que elijas, cualquiera de estas opciones es válida:
  * **Nube gratuita:** Streamlit Community Cloud, Hugging Face Spaces o Render (plan gratuito).
  * **Servidor local expuesto:** Correr la app en tu equipo y compartir el acceso temporal mediante **Cloudflare Tunnel** (`cloudflared tunnel --url http://localhost:<puerto>`).
* **RNF-02 (Rendimiento):** El modelo debe cargarse una sola vez al iniciar la aplicación (no en cada interacción) para que el simulador responda en menos de 1 segundo.
* **RNF-03 (Documentación):** Actualizar `README.md` con el framework elegido, los comandos para instalar dependencias y las instrucciones exactas para ejecutar la app localmente.

## 6. Mejora Opcional (Solo si sobra tiempo)

* **Sugerencia de combo mixto:** Además de mostrar cuántas cervezas O shots O whiskeys caben por separado, sugerir 1 o 2 combinaciones mezcladas que queden justo debajo del umbral.

## 7. Criterios de Aceptación (Checklist para cerrar el Sprint 3)

* [ ] La app levanta sin errores siguiendo los pasos documentados en `README.md`.
* [ ] El selector de tiempo permite valores desde `0.5` hasta `6.0` horas en pasos de `0.5` horas.
* [ ] Los 4 botones de perfiles precargados rellenan automáticamente el formulario y recalculan en vivo.
* [ ] Con 0 tragos seleccionados, el BAC mostrado es `0.0 mg/100 mL`.
* [ ] La predicción muestra claramente la **banda de incertidumbre** ($\pm \text{MAE}$ del Sprint 2) y no solo un valor puntual.
* [ ] El margen restante se redondea con **función piso en mitades** (`2.8` $\rightarrow$ `2.5`, `2.3` $\rightarrow$ `2`).
* [ ] Si el usuario ingresa tragos que superan los `220 g` de alcohol (o si un perfil no alcanza `120 mg/100 mL` dentro de los `220 g`), la app detiene la extrapolación y muestra un aviso claro de **fuera de los límites de la simulación**.
* [ ] Se probó el acceso desde otro dispositivo distinto al que ejecuta el código (vía nube gratuita o túnel).