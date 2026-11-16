'use strict';
/* Interfaz del agente bioinspirado. El motor es Python (core/) ejecutado con Pyodide. */

const PYODIDE_VERSION = 'v0.26.4';
const PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/' + PYODIDE_VERSION + '/full/pyodide.js';
const CORE_FILES = ['__init__.py', 'model.py', 'constructivo.py', 'genetic_algorithm.py',
  'baselines.py', 'escenarios.py', 'api.py'];
const ASSET_V = '1.0.0';
const PARAMS_BASE = { semilla: 42, poblacion: 50, generaciones: 100, p_cruce: 0.8,
  p_mutacion: 0.05, torneo: 3, elitismo: 2 };
const ETIQUETA_ESTADO = { factible: 'Factible', sin_solucion_encontrada: 'Sin solución encontrada',
  infactible_demostrada: 'Infactible demostrada' };

const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;',
  '"': '&quot;', "'": '&#39;' }[c]));
const fmt = (x, d = 4) => (x == null ? '—' : Number(x).toFixed(d));
const clon = o => JSON.parse(JSON.stringify(o));
const pausa = () => new Promise(r => setTimeout(r, 30));

const estado = { escenarios: [], esc: null, base: null, actual: null, cambios: [],
  previo: null, resultado: null, api: null, ocupado: false, textoMotor: '' };

/* ---------- Motor Python ---------- */

function cargarScript(url, ms) {
  return new Promise((ok, mal) => {
    const s = document.createElement('script');
    s.src = url;
    const t = setTimeout(() => mal(new Error('se agotó el tiempo de espera')), ms);
    s.onload = () => { clearTimeout(t); ok(); };
    s.onerror = () => { clearTimeout(t); mal(new Error('no se pudo descargar Pyodide')); };
    document.head.appendChild(s);
  });
}

async function iniciarMotor() {
  const t0 = performance.now();
  await cargarScript(PYODIDE_URL, 60000);
  const py = await loadPyodide();
  py.runPython("import sys\nsys.path.insert(0, '/home/pyodide')");
  try { py.FS.mkdirTree('/home/pyodide/core'); } catch (e) { /* ya existe */ }
  for (const f of CORE_FILES) {
    const r = await fetch('core/' + f + '?v=' + ASSET_V);
    if (!r.ok) throw new Error('no se pudo leer core/' + f);
    py.FS.writeFile('/home/pyodide/core/' + f, await r.text());
  }
  estado.api = py.pyimport('core.api');
  return (performance.now() - t0) / 1000;
}

function llamar(nombre, ...args) {
  return JSON.parse(estado.api[nombre](...args));
}

/* ---------- Arranque ---------- */

async function init() {
  try {
    const r = await fetch('scenarios.json?v=' + ASSET_V);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    estado.escenarios = (await r.json()).escenarios;
  } catch (e) {
    $('estadoMotor').textContent = 'No se pudieron leer los escenarios. Si abriste el archivo con doble clic, ' +
      'sírvelo con un servidor local (python -m http.server) o usa la URL publicada.';
    return;
  }
  const sel = $('escenario');
  sel.innerHTML = estado.escenarios.map(e => '<option value="' + esc(e.id) + '">' + esc(e.nombre) + '</option>').join('');
  enlazar();
  seleccionarEscenario(estado.escenarios[0].id);
  try {
    const seg = await iniciarMotor();
    estado.textoMotor = 'Motor Python listo (' + seg.toFixed(1) + ' s de carga).';
    $('estadoMotor').textContent = estado.textoMotor;
    ocupar(false);
    await ejecutar();
  } catch (e) {
    $('estadoMotor').textContent = 'No se pudo iniciar el motor Python: ' + e.message +
      '. Revisa tu conexión (Pyodide se descarga de un CDN) y recarga la página.';
  }
}

function enlazar() {
  $('escenario').addEventListener('change', async e => {
    seleccionarEscenario(e.target.value);
    await ejecutar();
  });
  $('btnEjecutar').addEventListener('click', ejecutar);
  $('btnRestablecer').addEventListener('click', () => {
    $('p_semilla').value = PARAMS_BASE.semilla; $('p_poblacion').value = PARAMS_BASE.poblacion;
    $('p_generaciones').value = PARAMS_BASE.generaciones; $('p_cruce').value = PARAMS_BASE.p_cruce;
    $('p_mutacion').value = PARAMS_BASE.p_mutacion; $('p_torneo').value = PARAMS_BASE.torneo;
    $('p_elitismo').value = PARAMS_BASE.elitismo;
  });
  $('tipoCambio').addEventListener('change', mostrarCamposCambio);
  $('btnCambio').addEventListener('click', () => {
    const [cambio, texto] = cambioDesdeUI();
    aplicarCambios([cambio], [texto]);
  });
  $('btnCambiosEscenario').addEventListener('click', () => {
    const cs = estado.esc.cambios;
    aplicarCambios(cs, cs.map(textoCambio));
  });
  $('btnDeshacer').addEventListener('click', async () => {
    estado.actual = clon(estado.base); estado.cambios = []; estado.previo = null; estado.resultado = null;
    renderDatos(); renderCambios(); poblarSelectsCambio();
    $('resultados').hidden = true;
    await ejecutar();
  });
  $('btnExportar').addEventListener('click', exportar);
  mostrarCamposCambio();
}

function ocupar(si) {
  ['escenario', 'btnEjecutar', 'btnRestablecer', 'tipoCambio', 'btnCambio', 'btnCambiosEscenario', 'btnDeshacer']
    .forEach(id => { $(id).disabled = si; });
  if (si) $('estadoMotor').textContent = estado.api ? 'Optimizando…' : $('estadoMotor').textContent;
  else if (estado.textoMotor) $('estadoMotor').textContent = estado.textoMotor;
}

function mostrarErrores(lista) {
  const p = $('errores');
  p.hidden = false;
  p.innerHTML = lista.map(esc).join('<br>');
}

function ocultarErrores() { $('errores').hidden = true; }

/* ---------- Parámetros, escenarios y cambios ---------- */

function leerParametros() {
  const n = id => { const v = $(id).value; return v === '' ? NaN : Number(v); };
  return { semilla: n('p_semilla'), poblacion: n('p_poblacion'), generaciones: n('p_generaciones'),
    p_cruce: n('p_cruce'), p_mutacion: n('p_mutacion'), torneo: n('p_torneo'), elitismo: n('p_elitismo') };
}

function seleccionarEscenario(id) {
  const e = estado.escenarios.find(x => x.id === id);
  estado.esc = e; estado.base = clon(e.instancia); estado.actual = clon(e.instancia);
  estado.cambios = []; estado.previo = null; estado.resultado = null;
  $('escenario').value = id;
  $('descEscenario').textContent = e.descripcion;
  $('btnCambiosEscenario').hidden = !(e.cambios && e.cambios.length);
  $('resultados').hidden = true;
  ocultarErrores(); renderDatos(); renderCambios(); poblarSelectsCambio();
}

function poblarSelectsCambio() {
  const inst = estado.actual;
  $('cambioFuncionario').innerHTML = inst.funcionarios
    .map(f => '<option value="' + esc(f.id) + '">' + esc(f.id) + '</option>').join('');
  const temas = new Set();
  inst.funcionarios.forEach(f => f.competencias.forEach(t => temas.add(t)));
  inst.solicitudes.forEach(s => temas.add(s.tematica));
  $('cambioTema').innerHTML = [...temas].sort().map(t => '<option>' + esc(t) + '</option>').join('');
}

function mostrarCamposCambio() {
  const t = $('tipoCambio').value;
  $('campoFuncionario').hidden = t === 'agregar_solicitud';
  $('campoFactor').hidden = t !== 'reducir_capacidad';
  ['campoTema', 'campoEsfuerzo', 'campoPrioridad'].forEach(id => { $(id).hidden = t !== 'agregar_solicitud'; });
}

function siguienteId() {
  const ids = new Set(estado.actual.solicitudes.map(s => s.id));
  let k = estado.actual.solicitudes.length + 1;
  while (ids.has('S' + String(k).padStart(3, '0'))) k++;
  return 'S' + String(k).padStart(3, '0');
}

function textoCambio(c) {
  if (c.tipo === 'deshabilitar_funcionario') return c.funcionario + ' ausente (capacidad 0)';
  if (c.tipo === 'reducir_capacidad') return c.funcionario + ' con ' + Math.round(c.factor * 100) + ' % de su capacidad';
  const s = c.solicitud;
  return 'Nueva solicitud ' + s.id + ' (' + s.tematica + ', ' + s.esfuerzo + ' h)';
}

function cambioDesdeUI() {
  const t = $('tipoCambio').value;
  let c;
  if (t === 'deshabilitar_funcionario') c = { tipo: t, funcionario: $('cambioFuncionario').value };
  else if (t === 'reducir_capacidad') {
    c = { tipo: t, funcionario: $('cambioFuncionario').value, factor: Number($('cambioFactor').value) / 100 };
  } else {
    c = { tipo: t, solicitud: { id: siguienteId(), tematica: $('cambioTema').value,
      esfuerzo: Number($('cambioEsfuerzo').value), prioridad: $('cambioPrioridad').value } };
  }
  return [c, textoCambio(c)];
}

async function aplicarCambios(lista, textos) {
  if (estado.ocupado || !estado.api) return;
  ocultarErrores();
  if (!estado.resultado) await ejecutar();          // asegura el resultado "antes"
  if (!estado.resultado) return;
  const antes = { ag: estado.resultado.ag, instancia: clon(estado.actual) };
  let inst = clon(estado.actual);
  for (const c of lista) {
    const r = llamar('cambiar', JSON.stringify(inst), JSON.stringify(c));
    if (r.error) { mostrarErrores(r.error); return; }
    inst = r.instancia;
  }
  estado.actual = inst; estado.cambios.push(...textos); estado.previo = antes;
  renderDatos(); renderCambios(); poblarSelectsCambio();
  await ejecutar();
}

/* ---------- Ejecución ---------- */

async function ejecutar() {
  if (estado.ocupado || !estado.api) return;
  estado.ocupado = true; ocupar(true); ocultarErrores();
  await pausa();
  try {
    const sal = llamar('ejecutar', JSON.stringify({ instancia: estado.actual, parametros: leerParametros(), extras: false }));
    if (sal.error) mostrarErrores(sal.error);
    else { estado.resultado = sal; render(); }
  } catch (e) {
    mostrarErrores(['Error del motor: ' + e.message]);
  } finally {
    estado.ocupado = false; ocupar(false);
  }
}

/* ---------- Render ---------- */

function renderCambios() {
  $('listaCambios').innerHTML = estado.cambios.map(c => '<li>' + esc(c) + '</li>').join('');
}

function tabla(el, cabeceras, filas, numericas) {
  const th = cabeceras.map(h => '<th>' + esc(h) + '</th>').join('');
  const tr = filas.map(f => {
    const clase = f.clase ? ' class="' + f.clase + '"' : '';
    return '<tr' + clase + '>' + f.celdas.map((c, i) =>
      '<td' + (numericas && numericas.includes(i) ? ' class="num"' : '') + '>' + c + '</td>').join('') + '</tr>';
  }).join('');
  el.innerHTML = '<thead><tr>' + th + '</tr></thead><tbody>' + tr + '</tbody>';
}

function renderDatos() {
  const inst = estado.actual;
  tabla($('tablaFuncionarios'), ['ID', 'Competencias', 'Capacidad (h)', 'Pendiente (h)', 'Residual (h)'],
    inst.funcionarios.map(f => ({ celdas: [esc(f.id), esc(f.competencias.join(', ')), fmt(f.capacidad, 1),
      fmt(f.pendiente, 1), fmt(Math.max(0, f.capacidad - f.pendiente), 1)] })), [2, 3, 4]);
  tabla($('tablaSolicitudes'), ['ID', 'Temática', 'Esfuerzo (h)', 'Prioridad'],
    inst.solicitudes.map(s => ({ celdas: [esc(s.id), esc(s.tematica), fmt(s.esfuerzo, 1), esc(s.prioridad || 'Media')] })), [2]);
}

function render() {
  const { ag, voraz } = estado.resultado;
  $('resultados').hidden = false;
  renderEstado(ag);
  renderKpis(ag);
  renderComparacion(ag, voraz);
  renderAntesDespues(ag);
  renderGraficos(ag, voraz);
  renderAsignacion(ag);
}

function renderEstado(ag) {
  let h = '';
  if (ag.estado === 'factible') {
    h = '<span class="estado ok">Reparto factible</span> <span class="nota">Cumple competencias, capacidad residual y una sola persona responsable por solicitud.</span>';
  } else if (ag.estado === 'sin_solucion_encontrada') {
    h = '<span class="estado aviso-e">No se encontró un reparto válido</span>' +
      '<p class="nota">La búsqueda no halló un reparto que respete las restricciones. Esto <strong>no prueba</strong> que sea imposible. ' +
      'El mejor intento excede la capacidad en ' + fmt(ag.exceso, 2) + ' h y no se presenta como asignación.</p>';
  } else {
    h = '<span class="estado mal">Infactible demostrada</span><ul class="razones">' +
      ag.razones.map(r => '<li>' + esc(r) + '</li>').join('') + '</ul>';
  }
  $('estadoResultado').innerHTML = h;
  $('advertencias').innerHTML = (ag.advertencias || []).map(a => '<li>' + esc(a) + '</li>').join('');
}

function kpi(v, e) { return '<div class="kpi"><div class="v">' + v + '</div><div class="e">' + e + '</div></div>'; }

function renderKpis(ag) {
  let h = '';
  if (ag.estado === 'factible') {
    h += kpi(fmt(ag.J), 'J final (menor es mejor)') + kpi(fmt(ag.max_u), 'Ocupación máxima (max u)') +
      kpi(fmt(ag.sigma_u), 'Desviación σ de la ocupación');
  }
  h += kpi(ag.evaluaciones, 'Evaluaciones') + kpi(ag.reparaciones, 'Movimientos de reparación') +
    kpi((ag.tiempo_s * 1000).toFixed(0) + ' ms', 'Tiempo de cómputo') + kpi(ag.semilla, 'Semilla');
  if (ag.sobrecarga_previa > 0) h += kpi(fmt(ag.sobrecarga_previa, 1) + ' h', 'Sobrecarga previa (aparte)');
  $('kpis').innerHTML = h;
}

function filaAlg(nombre, r) {
  const ok = r.estado === 'factible';
  return { celdas: [nombre, esc(ETIQUETA_ESTADO[r.estado] || r.estado), ok ? fmt(r.J) : '—', ok ? fmt(r.max_u) : '—',
    ok ? fmt(r.sigma_u) : '—', r.evaluaciones, (r.tiempo_s * 1000).toFixed(1)] };
}

function renderComparacion(ag, voraz) {
  const filas = [filaAlg('Algoritmo genético', ag), filaAlg('Voraz (referencia)', voraz)];
  const a = ag.estado === 'factible', v = voraz.estado === 'factible';
  if (a && v) {
    if (ag.J < voraz.J - 1e-9) filas[0].clase = 'mejor';
    else if (voraz.J < ag.J - 1e-9) filas[1].clase = 'mejor';
  }
  tabla($('tablaComparacion'), ['Algoritmo', 'Estado', 'J', 'max u', 'σ', 'Evaluaciones', 'Tiempo (ms)'], filas, [2, 3, 4, 5, 6]);
  let t = '';
  if (a && v) {
    const d = ag.J - voraz.J;
    if (Math.abs(d) <= 1e-9) t = 'El algoritmo genético iguala a la voraz en esta ejecución (ΔJ = 0).';
    else if (d < 0) t = 'El algoritmo genético obtuvo un J menor que la voraz (ΔJ = ' + d.toFixed(4) + ').';
    else t = 'En esta ejecución la voraz obtuvo un J menor que el algoritmo genético (ΔJ = +' + d.toFixed(4) +
      '). El AG no siempre gana; prueba otra semilla o más generaciones.';
    t += ' Una sola ejecución no basta para concluir: el informe usa 30 semillas.';
  } else if (!a) {
    t = 'Sin comparación de calidad: el algoritmo genético no entregó un reparto válido.';
  }
  $('textoComparacion').textContent = t;
}

function renderAntesDespues(ag) {
  const bloque = $('bloqueAntesDespues');
  if (!estado.previo) { bloque.hidden = true; return; }
  bloque.hidden = false;
  const a = estado.previo.ag, d = ag;
  const f = (x, r) => (r.estado === 'factible' ? fmt(r[x]) : '—');
  tabla($('tablaAntesDespues'), ['Indicador', 'Antes', 'Después'], [
    { celdas: ['Estado', esc(ETIQUETA_ESTADO[a.estado]), esc(ETIQUETA_ESTADO[d.estado])] },
    { celdas: ['J', f('J', a), f('J', d)] },
    { celdas: ['max u', f('max_u', a), f('max_u', d)] },
    { celdas: ['σ', f('sigma_u', a), f('sigma_u', d)] },
    { celdas: ['Solicitudes', estado.previo.instancia.solicitudes.length, estado.actual.solicitudes.length] },
  ], [1, 2]);
  const t = $('textoReasignadas');
  if (a.asignacion && d.asignacion) {
    const r = llamar('comparar_repartos', JSON.stringify(a.asignacion), JSON.stringify(d.asignacion)).reasignadas;
    const lista = r.length > 20 ? r.slice(0, 20).join(', ') + '…' : r.join(', ');
    t.textContent = r.length + ' de las ' + Object.keys(a.asignacion).length +
      ' solicitudes que ya existían cambiaron de responsable' + (r.length ? ': ' + lista + '.' : '.') +
      ' Las filas resaltadas en la asignación muestran los cambios.';
  } else {
    t.textContent = 'No se pueden comparar los repartos porque alguno de los dos no es válido.';
  }
}

/* ---------- Gráficas SVG ---------- */

function svgOcupacion(cargas, techo) {
  const W = 520, H = 270, ml = 44, mr = 12, mt = 14, mb = 38;
  const n = cargas.length, paso = (W - ml - mr) / n, bw = Math.min(48, paso * 0.62);
  const y = v => mt + (H - mt - mb) * (1 - v / techo);
  let s = '<svg class="grafico" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Ocupación por funcionario como porcentaje de su capacidad">';
  for (let t = 0; t <= techo; t += 25) {
    s += '<line class="rejilla" x1="' + ml + '" x2="' + (W - mr) + '" y1="' + y(t) + '" y2="' + y(t) + '"/>' +
      '<text class="txt-gris" x="' + (ml - 6) + '" y="' + (y(t) + 4) + '" text-anchor="end">' + t + ' %</text>';
  }
  cargas.forEach((c, i) => {
    const cx = ml + paso * (i + 0.5);
    s += '<text x="' + cx + '" y="' + (H - mb + 16) + '" text-anchor="middle">' + esc(c.id) + '</text>';
    if (!c.activo) {
      s += '<text x="' + cx + '" y="' + (y(0) - 6) + '" text-anchor="middle" style="fill:var(--naranja)">ausente</text>';
      return;
    }
    const pend = Math.min(techo, c.pendiente / c.capacidad * 100);
    const nueva = Math.min(techo - pend, (c.nueva || 0) / c.capacidad * 100);
    s += '<rect class="bar-pend" x="' + (cx - bw / 2) + '" y="' + y(pend) + '" width="' + bw + '" height="' + (y(0) - y(pend)) + '"/>' +
      '<rect class="bar-new" x="' + (cx - bw / 2) + '" y="' + y(pend + nueva) + '" width="' + bw + '" height="' + (y(pend) - y(pend + nueva)) + '"/>' +
      '<text x="' + cx + '" y="' + (y(pend + nueva) - 4) + '" text-anchor="middle">' + Math.round(c.ocupacion * 100) + ' %</text>';
  });
  s += '<line class="eje" x1="' + ml + '" x2="' + (W - mr) + '" y1="' + y(0) + '" y2="' + y(0) + '"/>' +
    '<line class="cap-line" x1="' + ml + '" x2="' + (W - mr) + '" y1="' + y(100) + '" y2="' + y(100) + '"/></svg>';
  return s;
}

function svgConvergencia(hist, jVoraz) {
  const pts = hist.filter(h => h.mejor_J != null);
  if (!pts.length) return '<p class="nota">La población no contiene ningún reparto válido: no hay curva de J.</p>';
  const W = 520, H = 270, ml = 56, mr = 14, mt = 14, mb = 38;
  const G = hist[hist.length - 1].gen || 1;
  const ys = pts.map(p => p.mejor_J);
  let lo = Math.min(...ys, jVoraz == null ? Infinity : jVoraz), hi = Math.max(...ys, jVoraz == null ? -Infinity : jVoraz);
  if (hi - lo < 1e-6) { lo -= 0.005; hi += 0.005; } else { const p = (hi - lo) * 0.1; lo -= p; hi += p; }
  const x = g => ml + (W - ml - mr) * g / G;
  const y = v => mt + (H - mt - mb) * (1 - (v - lo) / (hi - lo));
  let s = '<svg class="grafico" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Mejor J del algoritmo genético por generación">';
  for (let i = 0; i <= 4; i++) {
    const v = lo + (hi - lo) * i / 4;
    s += '<line class="rejilla" x1="' + ml + '" x2="' + (W - mr) + '" y1="' + y(v) + '" y2="' + y(v) + '"/>' +
      '<text class="txt-gris" x="' + (ml - 6) + '" y="' + (y(v) + 4) + '" text-anchor="end">' + v.toFixed(3) + '</text>';
    const g = Math.round(G * i / 4);
    s += '<text class="txt-gris" x="' + x(g) + '" y="' + (H - mb + 16) + '" text-anchor="middle">' + g + '</text>';
  }
  s += '<text class="txt-gris" x="' + (ml + (W - ml - mr) / 2) + '" y="' + (H - 6) + '" text-anchor="middle">Generación</text>';
  if (jVoraz != null) s += '<line class="linea-voraz" x1="' + ml + '" x2="' + (W - mr) + '" y1="' + y(jVoraz) + '" y2="' + y(jVoraz) + '"/>';
  s += '<path class="linea-ag" d="' + pts.map((p, i) => (i ? 'L' : 'M') + x(p.gen).toFixed(1) + ' ' + y(p.mejor_J).toFixed(1)).join('') + '"/>';
  const lx = W - mr - 170;
  s += '<line class="linea-ag" x1="' + lx + '" x2="' + (lx + 24) + '" y1="' + (mt + 10) + '" y2="' + (mt + 10) + '"/>' +
    '<text x="' + (lx + 30) + '" y="' + (mt + 14) + '">AG: mejor J</text>';
  if (jVoraz != null) {
    s += '<line class="linea-voraz" x1="' + lx + '" x2="' + (lx + 24) + '" y1="' + (mt + 28) + '" y2="' + (mt + 28) + '"/>' +
      '<text x="' + (lx + 30) + '" y="' + (mt + 32) + '">Voraz: J = ' + jVoraz.toFixed(4) + '</text>';
  }
  return s + '</svg>';
}

function renderGraficos(ag, voraz) {
  const conjuntos = [];
  if (estado.previo && estado.previo.ag.cargas) conjuntos.push(['Antes del cambio', estado.previo.ag.cargas]);
  conjuntos.push([estado.previo ? 'Después del cambio' : 'Reparto del AG', ag.cargas]);
  const pico = Math.max(100, ...conjuntos.flatMap(([, cs]) => cs.filter(c => c.activo)
    .map(c => (c.ocupacion == null ? 0 : c.ocupacion) * 100)));
  const techo = Math.ceil((pico + 12) / 25) * 25;
  $('graficoOcupacion').innerHTML = conjuntos.map(([titulo, cs]) =>
    '<figure><figcaption>' + esc(titulo) + '</figcaption>' + svgOcupacion(cs, techo) + '</figure>').join('');
  $('graficoConvergencia').innerHTML = '<figure><figcaption>Mejor J por generación (menor es mejor)</figcaption>' +
    svgConvergencia(ag.historial || [], voraz.estado === 'factible' ? voraz.J : null) + '</figure>';
}

function renderAsignacion(ag) {
  const t = $('tablaAsignacion');
  if (!ag.asignacion) {
    t.innerHTML = '<tbody><tr><td>No hay asignación válida que mostrar.</td></tr></tbody>';
    return;
  }
  const previa = estado.previo && estado.previo.ag.asignacion;
  const cab = ['Solicitud', 'Temática', 'Horas', 'Prioridad', 'Responsable (AG)'];
  if (previa) cab.push('Responsable antes');
  const filas = estado.actual.solicitudes.slice().sort((a, b) => a.id.localeCompare(b.id)).map(s => {
    const ahora = ag.asignacion[s.id];
    const celdas = [esc(s.id), esc(s.tematica), fmt(s.esfuerzo, 1), esc(s.prioridad || 'Media'), esc(ahora)];
    let clase = '';
    if (previa) {
      const antes = previa[s.id];
      celdas.push(antes ? esc(antes) : 'nueva');
      if (!antes || antes !== ahora) clase = 'cambio';
    }
    return { celdas, clase };
  });
  tabla(t, cab, filas, [2]);
}

function exportar() {
  if (!estado.resultado) return;
  const datos = { escenario: estado.esc.id, cambios: estado.cambios, parametros: leerParametros(),
    instancia: estado.actual, resultado_ag: estado.resultado.ag, resultado_voraz: estado.resultado.voraz };
  const blob = new Blob([JSON.stringify(datos, null, 1)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'resultado_' + estado.esc.id + '.json';
  a.click();
  URL.revokeObjectURL(a.href);
}

ocupar(true);
init();
