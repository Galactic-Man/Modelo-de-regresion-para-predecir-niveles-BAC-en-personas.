// «Drunk enough?» — lógica de la interfaz. Toda la estimación la hace el backend.
import { getConfig, estimate } from "./api.js";
import { glass, face, logo, miniGlass } from "./art.js";
import { num, plain, units, hours, grams, abv } from "./format.js";

const $ = (id) => document.getElementById(id);
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const STORAGE_KEY = "drunk-enough:v2";
const OLD_KEYS = ["drunk-enough:v1"]; // guardaba perfiles A–D y entrenamiento: se borra
const METER_MAX = 160; // escala de la barra semafórica (120 queda al 75 %)
const BEER = { bottom: 162, full: 22, wave: 8 }; // vaso del panel: lleno a 120 mg/100 mL
const SEMAFORO = [
  { max: 60, cls: "is-green", text: "Margen amplio respecto a 120 mg/100 mL." },
  { max: 120, cls: "is-amber", text: "Te acercas al umbral de 120 mg/100 mL." },
  { max: Infinity, cls: "is-red", text: "Umbral de embriaguez (120 mg/100 mL) alcanzado o superado." },
];

const state = {
  cfg: null,
  perfil: { sexo: "F", edad: 22, estatura_cm: 160, peso_kg: 55 },
  horas: 3,
  tragos: {},
  lastDrink: null,
  stageId: null,
  shownBac: 0,
  seq: 0,
  controller: null,
};

/* ---------- Persistencia (solo comodidad local) ---------- */
function save() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      perfil: state.perfil, horas: state.horas, tragos: state.tragos, lastDrink: state.lastDrink,
    }));
  } catch (_) { /* almacenamiento no disponible */ }
}
function load() {
  try {
    for (const k of OLD_KEYS) localStorage.removeItem(k);
    const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    if (raw && raw.perfil) {
      const { sexo, edad, estatura_cm, peso_kg } = raw.perfil;
      Object.assign(state.perfil, { sexo, edad, estatura_cm, peso_kg });
      state.horas = raw.horas ?? state.horas;
      state.tragos = raw.tragos || {};
      state.lastDrink = raw.lastDrink || null;
    }
  } catch (_) { /* ignorar */ }
}

/* ---------- Límites desde /api/config ---------- */
function clampTo(key, v) {
  const [min, max, step] = state.cfg.rangos[key];
  const n = Math.round(Number(v) / step) * step;
  return Math.min(max, Math.max(min, Number.isFinite(n) ? n : min));
}
function sanitize() {
  const p = state.perfil;
  p.sexo = p.sexo === "M" ? "M" : "F";
  p.edad = clampTo("edad", p.edad);
  p.estatura_cm = clampTo("estatura_cm", p.estatura_cm);
  p.peso_kg = clampTo("peso_kg", p.peso_kg);
  state.horas = clampTo("horas_consumo", state.horas);
  const ids = new Set(state.cfg.bebidas.map((b) => b.id));
  for (const k of Object.keys(state.tragos)) {
    if (!ids.has(k)) delete state.tragos[k];
    else state.tragos[k] = Math.min(200, Math.max(0, Math.round(state.tragos[k]) || 0));
  }
  if (!ids.has(state.lastDrink)) state.lastDrink = null;
}

/* ---------- Construcción del formulario ---------- */
const RANGE_FIELDS = {
  edad: (v) => `${v} años`,
  estatura_cm: (v) => `${v} cm`,
  peso_kg: (v) => `${v} kg`,
  horas_consumo: (v) => hours(v),
};

function buildForm() {
  const { cfg } = state;
  $("logo").innerHTML = logo;
  $("dock-glass").innerHTML = miniGlass;

  for (const [key, fmt] of Object.entries(RANGE_FIELDS)) {
    const input = $(key);
    const [min, max, step] = cfg.rangos[key];
    Object.assign(input, { min, max, step });
    input.addEventListener("input", () => {
      const v = Number(input.value);
      if (key === "horas_consumo") state.horas = v;
      else state.perfil[key] = v;
      paintRange(key, fmt);
      onChange();
    });
  }

  for (const r of document.querySelectorAll('input[name="sexo"]')) {
    r.addEventListener("change", () => { if (r.checked) { state.perfil.sexo = r.value; onChange(); } });
  }

  $("drinks").innerHTML = cfg.bebidas.map((d) => `
    <li class="drink" data-id="${d.id}" style="--fill:0">
      <div class="drink__art">${glass(d)}</div>
      <div class="drink__info">
        <p class="drink__name">${d.nombre}</p>
        <p class="drink__meta">${d.volumen_ml} mL · ${abv(d.abv)} · ${grams(d.gramos)}</p>
      </div>
      <div class="counter">
        <button type="button" class="counter__btn" data-step="-1" aria-label="Quitar ${d.singular}">
          <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="M5 10h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
        <output class="counter__n" id="n-${d.id}" aria-live="polite">0</output>
        <button type="button" class="counter__btn counter__btn--plus" data-step="1" aria-label="Agregar ${d.singular}">
          <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="M5 10h10M10 5v10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
      </div>
    </li>`).join("");
  $("drinks").addEventListener("click", (e) => {
    const btn = e.target.closest(".counter__btn");
    if (!btn || btn.disabled) return;
    const id = btn.closest(".drink").dataset.id;
    const step = Number(btn.dataset.step);
    state.tragos[id] = Math.min(200, Math.max(0, (state.tragos[id] || 0) + step));
    state.lastDrink = id;
    paintDrinks(id);
    if (step > 0) slosh(); // respuesta inmediata, antes de que llegue la API
    onChange();
  });

  $("reset").addEventListener("click", () => {
    state.tragos = {};
    paintDrinks(null); // null: anima la salida de los vasos de la mesa
    onChange();
  });

  $("mae").textContent = plain(cfg.mae);
  $("mix-text").textContent = cfg.textos.mezcla;
  $("disclaimer").textContent = cfg.textos.aviso;
  $("tips").innerHTML = cfg.textos.consejos.map((t) => `<li>${t}</li>`).join("");
  $("band-note").textContent =
    `El rango (± ${plain(cfg.mae)} mg/100 mL, el error medio del modelo en prueba) refleja que cada cuerpo procesa el alcohol distinto: metabolismo, comida, sueño.`;
}

function paintRange(key, fmt = RANGE_FIELDS[key]) {
  const input = $(key);
  const pct = ((input.value - input.min) / (input.max - input.min)) * 100;
  input.style.setProperty("--pct", `${pct}%`);
  const text = fmt(Number(input.value));
  $(`${key}-out`).textContent = text;
  input.setAttribute("aria-valuetext", text);
}

function syncForm() {
  const p = state.perfil;
  for (const r of document.querySelectorAll('input[name="sexo"]')) r.checked = r.value === p.sexo;
  for (const key of ["edad", "estatura_cm", "peso_kg"]) $(key).value = p[key];
  $("horas_consumo").value = state.horas;
  for (const key of Object.keys(RANGE_FIELDS)) paintRange(key);
}

function totalGrams() {
  return state.cfg.bebidas.reduce((s, d) => s + d.gramos * (state.tragos[d.id] || 0), 0);
}

function restart(el, cls) {
  if (reduceMotion.matches || !el) return;
  el.classList.remove(cls);
  void el.getBoundingClientRect(); // reinicia la animación
  el.classList.add(cls);
}

function paintDrinks(bumpId) {
  for (const d of state.cfg.bebidas) {
    const li = document.querySelector(`.drink[data-id="${d.id}"]`);
    const n = state.tragos[d.id] || 0;
    const out = $(`n-${d.id}`);
    out.textContent = n;
    out.setAttribute("aria-label", `${n} ${n === 1 ? d.singular : d.plural}`);
    li.style.setProperty("--fill", Math.min(1, n / 6).toFixed(3));
    li.classList.toggle("is-on", n > 0);
    li.querySelector('[data-step="-1"]').disabled = n === 0;
    li.querySelector('[data-step="1"]').disabled = n >= 200;
    if (d.id === bumpId) restart(li, "bump");
  }
  paintTable(bumpId !== undefined);
  const g = totalGrams();
  $("total-g").textContent = grams(g);
  const over = g > state.cfg.max_gramos;
  $("total-max").textContent = over ? `· pasa el tope de ${plain(state.cfg.max_gramos)} g` : `de ${plain(state.cfg.max_gramos)} g que cubre el simulador`;
  $("total-max").classList.toggle("is-over", over);
  $("reset").disabled = g === 0;
}

/* ---------- «Tu mesa»: un vasito por trago (decorativa) ---------- */
const TABLE_MAX = 12;
let glassUid = 0;

/** Reparte hasta 12 vasos por turnos, para que ninguna bebida desaparezca de la mesa. */
function allocateGlasses(counts) {
  const shown = counts.map(() => 0);
  let left = TABLE_MAX;
  while (left > 0) {
    let placed = false;
    for (let i = 0; i < counts.length && left > 0; i++) {
      if (shown[i] < counts[i]) { shown[i]++; left--; placed = true; }
    }
    if (!placed) break;
  }
  return shown;
}

function leave(el, animate) {
  if (!animate || reduceMotion.matches) { el.remove(); return; }
  el.classList.add("is-leaving");
  const done = () => el.remove();
  el.addEventListener("animationend", done, { once: true });
  setTimeout(done, 500); // por si la animación no corre
}

function paintTable(animate) {
  const drinks = state.cfg.bebidas;
  const counts = drinks.map((d) => state.tragos[d.id] || 0);
  const shown = allocateGlasses(counts);
  const row = $("table-row");
  const more = $("table-more");
  const pop = animate && !reduceMotion.matches;

  drinks.forEach((d, i) => {
    let group = row.querySelector(`.tg[data-id="${d.id}"]:not(.is-leaving)`);
    if (counts[i] === 0) { if (group) leave(group, animate); return; }
    if (!group) {
      group = document.createElement("div");
      group.className = "tg";
      group.dataset.id = d.id;
      group.innerHTML = `<span class="tg__glasses"></span><span class="tg__n"></span>`;
      // mismo orden que el catálogo
      const next = drinks.slice(i + 1).map((x) => row.querySelector(`.tg[data-id="${x.id}"]:not(.is-leaving)`)).find(Boolean);
      row.insertBefore(group, next || more);
    }
    group.querySelector(".tg__n").textContent = `×${counts[i]}`;
    const box = group.querySelector(".tg__glasses");
    const live = [...box.querySelectorAll(".tg__glass:not(.is-leaving)")];
    for (let k = live.length; k < shown[i]; k++) {
      const el = document.createElement("span");
      el.className = pop ? "tg__glass is-entering" : "tg__glass";
      el.innerHTML = glass(d, `t${++glassUid}`);
      if (pop) el.addEventListener("animationend", () => el.classList.remove("is-entering"), { once: true });
      box.appendChild(el);
    }
    for (let k = live.length - 1; k >= shown[i]; k--) leave(live[k], animate);
  });

  const total = counts.reduce((a, b) => a + b, 0);
  const extra = total - shown.reduce((a, b) => a + b, 0);
  more.hidden = extra <= 0;
  more.textContent = `+${extra}`;
  $("table").classList.toggle("is-empty", total === 0);
}

/* ---------- Vaso del panel ---------- */
let fizzTimer = 0;
function slosh() {
  restart($("beer"), "slosh");
  restart($("dock-glass"), "slosh");
  if (reduceMotion.matches) return;
  $("beer").classList.add("is-fizz");
  clearTimeout(fizzTimer);
  fizzTimer = setTimeout(() => $("beer").classList.remove("is-fizz"), 1100);
}

/** Nivel 0–1 del vaso: lleno al llegar al umbral (120 mg/100 mL). */
function setBeer(bac) {
  const f = Math.max(0, Math.min(1, bac / state.cfg.umbral));
  // vacío: la ola queda por debajo del fondo para que no asome una línea de líquido
  const y = f === 0 ? BEER.bottom + BEER.wave : BEER.bottom - f * (BEER.bottom - BEER.full);
  const beer = $("beer");
  beer.style.setProperty("--level", `${(y - BEER.wave).toFixed(2)}px`);
  beer.style.setProperty("--rise", `${Math.max(0, BEER.bottom - y - 6).toFixed(2)}px`);
  beer.style.setProperty("--spd", (1 + f * 0.9).toFixed(2)); // las burbujas se aceleran al llenarse
  beer.classList.toggle("is-empty", f === 0);
  beer.classList.toggle("is-full", bac >= state.cfg.umbral);
  $("dock-glass").style.setProperty("--lvl", f.toFixed(3));
}

/* ---------- Ciclo de estimación ---------- */
let timer = 0;
function onChange() {
  save();
  clearTimeout(timer);
  timer = setTimeout(run, 140);
}

async function run() {
  const seq = ++state.seq;
  state.controller?.abort();
  state.controller = new AbortController();
  $("resultado").setAttribute("aria-busy", "true");
  // nivel_entrenamiento se omite: la API lo toma como 0 por defecto.
  const body = { ...state.perfil, horas_consumo: state.horas, tragos: { ...state.tragos } };
  try {
    const res = await estimate(body, state.controller.signal);
    if (seq !== state.seq) return;
    $("error").hidden = true;
    render(res);
  } catch (err) {
    if (err.name === "AbortError" || seq !== state.seq) return;
    $("error").hidden = false;
    $("error").textContent = `No pudimos calcular: ${err.message}. Revisa tu conexión e inténtalo de nuevo.`;
  } finally {
    if (seq === state.seq) $("resultado").setAttribute("aria-busy", "false");
  }
}

/* ---------- Pintar resultado ---------- */
const drinkById = (id) => state.cfg.bebidas.find((d) => d.id === id);
const stageById = (id) => state.cfg.etapas.find((s) => s.id === id);
const mainDrink = () => drinkById(state.lastDrink) || state.cfg.bebidas[0];

function setStageColor(color) {
  document.documentElement.style.setProperty("--stage", color);
}

function countUp(to) {
  const els = [$("bac-num"), $("dock-bac")];
  const from = state.shownBac;
  state.shownBac = to;
  const paint = (v) => { for (const el of els) el.textContent = num(v, 1); };
  if (reduceMotion.matches || Math.abs(to - from) < 0.05) { paint(to); return; }
  const t0 = performance.now();
  const dur = 520;
  const tick = (t) => {
    if (state.shownBac !== to) return; // llegó un valor más nuevo
    const k = Math.min(1, (t - t0) / dur);
    paint(from + (to - from) * (1 - Math.pow(1 - k, 3)));
    if (k < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

/** Unidades de la bebida principal + alternativas en las demás. */
function unitsPhrase(list) {
  const main = mainDrink();
  const first = list.find((u) => u.id === main.id);
  const rest = list.filter((u) => u.id !== main.id && u.unidades > 0)
    .map((u) => units(u.unidades, drinkById(u.id)));
  return { main, mainUnits: first ? first.unidades : 0, rest };
}

function altList(rest) {
  if (!rest.length) return "";
  return `<ul class="alts">${rest.map((r) => `<li>o ${r}</li>`).join("")}</ul>`;
}

function renderNext(prox, stageIdx) {
  const el = $("next");
  if (!prox) {
    el.innerHTML = `<p class="info__k">Siguiente etapa</p>
      <p class="info__v">No hay más arriba. Para de tomar y busca compañía.</p>`;
    return;
  }
  const s = stageById(prox.id);
  const dot = `<span class="chip" style="--c:${s.color}">${prox.nombre}</span>`;
  if (prox.fuera_de_simulacion) {
    el.innerHTML = `<p class="info__k">Siguiente etapa ${dot}</p>
      <p class="info__v">Queda más allá de los ${plain(state.cfg.max_gramos)} g que cubre el simulador.</p>`;
    return;
  }
  const { main, mainUnits, rest } = unitsPhrase(prox.unidades);
  const lead = mainUnits > 0
    ? `Con <strong>${units(mainUnits, main)}</strong> más`
    : `Con <strong>menos de media unidad</strong> más`;
  const careful = stageIdx >= 2 ? " Es un aviso, no una meta." : "";
  el.innerHTML = `<p class="info__k">Siguiente etapa ${dot}</p>
    <p class="info__v">${lead} llegarías ahí (${grams(prox.gramos)} de alcohol).${careful}</p>
    ${mainUnits > 0 ? altList(rest) : ""}`;
}

function renderMargin(m) {
  const el = $("margin");
  const limit = plain(state.cfg.umbral);
  const r = m.ritmo;
  const main = mainDrink();
  const perHour = r.unidades_por_hora.find((u) => u.id === main.id)?.unidades ?? 0;
  const ritmo = `<p class="info__foot">En una salida de ${hours(r.horas)}, eso equivale a un ritmo máximo de unos ${num(r.gramos_por_hora, 1)} g por hora${perHour > 0 ? ` (≈ ${units(perHour, main)} por hora)` : ""}${r.supera_tope ? `, calculado hasta el tope de ${plain(state.cfg.max_gramos)} g` : ""}. Repartir en más horas cambia el total.</p>`;

  if (m.caso === "limite_superado") {
    el.innerHTML = `<p class="info__k">Margen hasta ${limit} mg/100 mL</p>
      <p class="info__v info__v--alert">Ya pasaste el umbral de embriaguez. Margen: <strong>0</strong> en todas las bebidas.</p>`;
    return;
  }
  const { mainUnits, rest } = unitsPhrase(m.unidades);
  if (m.caso === "supera_tope_simulacion") {
    el.innerHTML = `<p class="info__k">Margen hasta ${limit} mg/100 mL</p>
      <p class="info__v">Tu límite real supera el rango del simulador. Hasta el tope de ${plain(state.cfg.max_gramos)} g quedan ${grams(m.gramos_restantes)}: <strong>${units(mainUnits, main)}</strong>.</p>
      ${altList(rest)}${ritmo}`;
    return;
  }
  el.innerHTML = `<p class="info__k">Margen hasta ${limit} mg/100 mL</p>
    <p class="info__v">Te quedan ≈ <strong>${units(mainUnits, main)}</strong> (${grams(m.gramos_restantes)}).</p>
    ${altList(rest)}${ritmo}`;
}

/** Cara, color y aviso cuando cambia la etapa. */
function applyStage(id, cara, nombre, announce) {
  const changed = state.stageId !== null && state.stageId !== id;
  if (state.stageId !== id) {
    $("face").innerHTML = face(cara);
    $("dock-face").innerHTML = face(cara);
  }
  state.stageId = id;
  $("stage-name").textContent = nombre;
  $("dock-stage").textContent = nombre;
  if (changed) {
    restart($("face"), "pop");
    restart($("dock-face"), "pop");
    restart($("resultado"), "flash");
    if (announce) toast(announce);
  }
}

function render(res) {
  const { cfg } = state;
  const b = res.bac;
  $("mix").hidden = !res.mezcla;

  if (b.estado === "fuera_de_limite") {
    const peligro = stageById("peligro");
    $("ok").hidden = true;
    $("out").hidden = false;
    $("out-text").textContent =
      `Marcaste ${grams(b.gramos)} de alcohol puro y el modelo solo aprendió hasta ${plain(cfg.max_gramos)} g. No mostramos una cifra porque sería inventada. A ese nivel el riesgo para la salud es real: para de tomar y busca ayuda si alguien no responde.`;
    setStageColor(peligro.color);
    applyStage("fuera", peligro.cara, "Fuera de límites", {
      color: peligro.color, cara: peligro.cara, nombre: "Fuera de límites",
      mensaje: "Pasaste los 220 g que cubre el simulador.",
    });
    state.shownBac = NaN;
    $("bac-num").textContent = "—";
    document.querySelector(".bac__pm").hidden = true;
    $("dock-bac").textContent = "—";
    $("bac-pct").textContent = "";
    $("bac-range").textContent = "Sin estimación: consumo fuera de lo que el modelo conoce.";
    setBeer(cfg.umbral);
    paintMeter(null);
    return;
  }

  $("ok").hidden = false;
  $("out").hidden = true;
  document.querySelector(".bac__pm").hidden = false;
  if (Number.isNaN(state.shownBac)) state.shownBac = b.bac;

  const stage = stageById(res.etapa);
  const idx = cfg.etapas.indexOf(stage);
  setStageColor(stage.color);
  applyStage(stage.id, stage.cara, stage.nombre, stage);

  countUp(b.bac);
  setBeer(b.bac);
  $("bac-pct").textContent = `(≈ ${num(b.bac / 1000, 3)} % BAC)`;
  $("bac-range").innerHTML = b.bac === 0
    ? "Sin alcohol marcado, el estimado es cero."
    : `Rango probable: <strong>${num(b.banda[0], 1)} – ${num(b.banda[1], 1)}</strong>`;
  paintMeter(b);

  $("stage-title").textContent = stage.titulo;
  $("stage-msg").textContent = stage.mensaje;
  $("stage-tip").textContent = stage.consejo;
  $("stage-warn").hidden = !stage.aviso;
  $("stage-warn").textContent = stage.aviso || "";

  renderNext(res.proxima_etapa, idx);
  renderMargin(res.margen);
}

function paintMeter(b) {
  const { cfg } = state;
  const meter = $("meter");
  const bac = b ? b.bac : METER_MAX; // fuera de límites: barra llena y en rojo
  const sem = SEMAFORO.find((s) => bac < s.max) ?? SEMAFORO[SEMAFORO.length - 1];
  meter.classList.remove("is-green", "is-amber", "is-red");
  meter.classList.add(sem.cls);
  $("meter-fill").style.width = `${Math.min(100, (bac / METER_MAX) * 100)}%`;
  const lo = !b || b.bac === 0 ? 0 : Math.min(100, (b.banda[0] / METER_MAX) * 100);
  const hi = !b || b.bac === 0 ? 0 : Math.min(100, (b.banda[1] / METER_MAX) * 100);
  $("meter-band").style.left = `${lo}%`;
  $("meter-band").style.width = `${hi - lo}%`;
  const text = b ? sem.text : "Fuera de los límites de la simulación.";
  $("meter-status").textContent = text;
  meter.setAttribute("role", "img");
  meter.setAttribute("aria-label", b ? `${num(b.bac, 1)} de ${plain(cfg.umbral)} mg/100 mL. ${text}` : text);
}

/* ---------- Aviso de cambio de etapa (dentro del panel y en la barra móvil) ---------- */
let toastTimer = 0;
function toast(stage) {
  const box = $("toast");
  box.style.setProperty("--c", stage.color);
  $("toast-in").innerHTML = `<div class="stage-alert__box"><span class="stage-alert__face">${face(stage.cara)}</span>
    <span><strong>Cambiaste de etapa: ${stage.nombre}</strong><span class="stage-alert__msg">${stage.mensaje}</span></span></div>`;
  $("dock-msg").textContent = `Ahora: ${stage.nombre}`;
  box.classList.add("is-on");
  $("dock").classList.add("has-msg");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    box.classList.remove("is-on");
    $("dock").classList.remove("has-msg");
  }, 4500);
}

/* ---------- Barra móvil: visible solo si el panel no está en pantalla ---------- */
function watchDock() {
  const dock = $("dock");
  dock.hidden = false;
  if (!("IntersectionObserver" in window)) return;
  new IntersectionObserver(([entry]) => {
    dock.classList.toggle("is-on", !entry.isIntersecting);
  }, { threshold: 0.2 }).observe($("hero"));
  dock.addEventListener("click", (e) => {
    e.preventDefault();
    const target = $("resultado");
    target.scrollIntoView({ behavior: reduceMotion.matches ? "auto" : "smooth", block: "start" });
    target.focus({ preventScroll: true });
  });
}

/* ---------- Arranque ---------- */
async function init() {
  try {
    state.cfg = await getConfig();
  } catch (err) {
    $("error").hidden = false;
    $("error").textContent = `No se pudo cargar la configuración (${err.message}). ¿Está corriendo el servidor?`;
    $("ok").hidden = true;
    $("resultado").setAttribute("aria-busy", "false");
    return;
  }
  load();
  sanitize();
  buildForm();
  syncForm();
  paintDrinks();
  setBeer(0);
  watchDock();
  document.body.classList.add("is-ready");
  run();
}

init();
