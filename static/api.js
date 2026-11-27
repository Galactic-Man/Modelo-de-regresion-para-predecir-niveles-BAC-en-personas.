// Cliente mínimo de la API de «Drunk enough?» (app/main.py).

async function readError(res) {
  try {
    const body = await res.json();
    if (Array.isArray(body.detail)) return body.detail.map((d) => d.msg).join(" · ");
    if (body.detail) return String(body.detail);
  } catch (_) { /* cuerpo no JSON */ }
  return `Error ${res.status}`;
}

export async function getConfig() {
  const res = await fetch("/api/config", { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

/**
 * @param {{sexo:"M"|"F", edad:number, estatura_cm:number, peso_kg:number,
 *          nivel_entrenamiento?:number, horas_consumo:number, tragos:Record<string,number>}} body
 * @param {AbortSignal} [signal]
 */
export async function estimate(body, signal) {
  const res = await fetch("/api/estimate", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}
