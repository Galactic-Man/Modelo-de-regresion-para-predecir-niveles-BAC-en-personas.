// Formato de números y frases en español (Colombia).

const nf = (dec) => new Intl.NumberFormat("es-CO", { minimumFractionDigits: dec, maximumFractionDigits: dec });
const nfAuto = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 2 });

/** Número con decimales fijos: num(115.4, 1) → "115,4". */
export function num(value, dec = 1) {
  return nf(dec).format(value);
}

/** Número sin ceros sobrantes: 2 → "2", 2.5 → "2,5". */
export function plain(value) {
  return nfAuto.format(value);
}

/** "1 cerveza", "2,5 cervezas", "0,5 cervezas". */
export function units(n, drink) {
  return `${plain(n)} ${n === 1 ? drink.singular : drink.plural}`;
}

/** 0.5 → "30 min", 1 → "1 hora", 2.5 → "2,5 horas". */
export function hours(h) {
  if (h < 1) return `${Math.round(h * 60)} min`;
  return `${plain(h)} ${h === 1 ? "hora" : "horas"}`;
}

/** Gramos legibles: 10.414 → "10,4 g". */
export function grams(g) {
  return `${num(g, 1)} g`;
}

/** Porcentaje de alcohol de una bebida: 0.375 → "37,5 %". */
export function abv(x) {
  return `${plain(x * 100)} %`;
}
