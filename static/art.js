// Ilustraciones SVG en línea: vasos (por bebida) y caras (por etapa).
// Todo es decorativo (aria-hidden); el texto siempre dice lo mismo que el dibujo.

const GLASSES = {
  // Vaso de cerveza: trapecio alto.
  cerveza: { outline: "M9 5 H35 L31.5 45 H12.5 Z", top: 5, bottom: 45 },
  // Vaso de shot: bajo, con base gruesa.
  shot: { outline: "M11 17 H33 L30.5 41 H13.5 Z", top: 17, bottom: 41, base: "M13.3 41 H30.7 L30.3 45 H13.7 Z" },
};

/**
 * Vaso cuyo líquido sube con la variable CSS --fill (0–1) del elemento padre.
 * @param {{id:string, vaso:string, color_liquido:string}} drink
 */
export function glass(drink, uid = "") {
  const g = GLASSES[drink.vaso] || GLASSES.shot;
  const clip = `clip-${drink.id}${uid ? `-${uid}` : ""}`; // id único si hay varios vasos iguales
  const h = g.bottom - g.top;
  const foam = drink.vaso === "cerveza"
    ? `<rect class="glass__foam" x="0" y="${g.top - 3}" width="44" height="4" rx="2"/>`
    : "";
  return `
<svg class="glass" viewBox="0 0 44 50" aria-hidden="true" focusable="false">
  <defs><clipPath id="${clip}"><path d="${g.outline}"/></clipPath></defs>
  <g clip-path="url(#${clip})">
    <g class="glass__liquid" style="--liquid:${drink.color_liquido}">
      <rect x="0" y="${g.top}" width="44" height="${h}" />
      ${foam}
    </g>
  </g>
  <path class="glass__outline" d="${g.outline}"/>
  ${g.base ? `<path class="glass__base" d="${g.base}"/>` : ""}
  <path class="glass__shine" d="M${drink.vaso === "cerveza" ? "13 10 L15.4 38" : "15 21 L16.2 36"}"/>
</svg>`;
}

const EYES = {
  dot: `<circle cx="23" cy="27" r="2.6" class="f"/><circle cx="41" cy="27" r="2.6" class="f"/>`,
  happy: `<path d="M19 28 q4 -5 8 0"/><path d="M37 28 q4 -5 8 0"/>`,
  wink: `<path d="M19 27 q4 -4 8 0"/><path d="M37 26 h8"/>`,
  sleepy: `<path d="M19 27 h8"/><path d="M37 28 h8"/>`,
  spiral: `<path d="M23 27 m-4 0 a4 4 0 1 0 4 -4 a2.4 2.4 0 1 0 2.4 2.4"/><path d="M41 27 m-4 0 a4 4 0 1 0 4 -4 a2.4 2.4 0 1 0 2.4 2.4"/>`,
  cross: `<path d="M19.5 23.5 l7 7 M26.5 23.5 l-7 7"/><path d="M37.5 23.5 l7 7 M44.5 23.5 l-7 7"/>`,
};

const MOUTHS = {
  calm: `<path d="M25 41 q7 4 14 0"/>`,
  smile: `<path d="M23 39 q9 8 18 0"/>`,
  grin: `<path d="M22 38 q10 11 20 0 z" class="f"/>`,
  wavy: `<path d="M22 42 q3 -3 6 0 t6 0 t6 0"/>`,
  queasy: `<path d="M23 43 q4 -4 9 -1 t9 0"/>`,
  flat: `<path d="M24 42 h16"/>`,
};

const FACES = {
  sobrio: { eyes: "dot", mouth: "calm", cheeks: false },
  relajado: { eyes: "happy", mouth: "smile", cheeks: false },
  prendido: { eyes: "happy", mouth: "grin", cheeks: true },
  borracho: { eyes: "wink", mouth: "wavy", cheeks: true },
  muy_borracho: { eyes: "spiral", mouth: "queasy", cheeks: true },
  peligro: { eyes: "cross", mouth: "flat", cheeks: false },
};

/** Cara de la etapa; el color sale de la variable CSS --stage. */
export function face(cara) {
  const f = FACES[cara] || FACES.sobrio;
  const cheeks = f.cheeks
    ? `<circle class="face__cheek" cx="18" cy="35" r="3.6"/><circle class="face__cheek" cx="46" cy="35" r="3.6"/>`
    : "";
  return `
<svg class="face" viewBox="0 0 64 64" aria-hidden="true" focusable="false" data-cara="${cara}">
  <circle class="face__disc" cx="32" cy="32" r="28"/>
  ${cheeks}
  <g class="face__lines">${EYES[f.eyes]}${MOUTHS[f.mouth]}</g>
</svg>`;
}

/** Vaso pequeño para la barra móvil; el líquido sube con la variable CSS --lvl (0–1). */
export const miniGlass = `
<svg viewBox="0 0 24 30" aria-hidden="true" focusable="false">
  <defs><clipPath id="mini-clip"><path d="M3 3 H21 L19 26 Q18.8 28 17 28 H7 Q5.2 28 5 26 Z"/></clipPath></defs>
  <g clip-path="url(#mini-clip)">
    <rect class="mini__liquid" x="0" y="3" width="24" height="25"/>
  </g>
  <path class="mini__outline" d="M3 3 H21 L19 26 Q18.8 28 17 28 H7 Q5.2 28 5 26 Z"/>
</svg>`;

/** Marca de la app: copa simple. */
export const logo = `
<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">
  <path d="M8 5 H24 L22 17 Q16 22 10 17 Z" fill="currentColor" opacity=".9"/>
  <path d="M16 20 V27 M11 27 H21" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" fill="none"/>
  <circle cx="21" cy="9" r="1.6" fill="var(--bg)"/>
</svg>`;
