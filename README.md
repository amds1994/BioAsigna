# BioAsigna — Asignación de solicitudes mediante algoritmos genéticos

Asignatura: Computación Bioinspirada

Un **algoritmo genético** (inspirado en la selección natural) recomienda qué funcionario atiende cada solicitud ciudadana **sintética**. Respeta competencias y capacidad residual, asigna una sola persona por solicitud y **vuelve a optimizar cuando cambia el entorno** (ausencia, menos capacidad, solicitudes nuevas). El sistema solo recomienda: una persona decide.

- **Aplicación web:** https://amds1994.github.io/BioAsigna/ (requiere activar Pages; ver «Publicar»).
- Todos los datos son ficticios. No hay servidor, datos reales ni dependencias en el navegador salvo Pyodide (CDN).

## Qué hace

Minimiza `J = 0.6·max(u) + 0.4·σ(u)`, donde `u_j = (pendiente_j + nueva_j) / capacidad_j` solo para funcionarios activos. Restricción dura: `nueva_j ≤ max(0, capacidad_j − pendiente_j)`.

Estados honestos del resultado:

| Estado | Significado |
|---|---|
| `factible` | Reparto válido; se muestra la asignación y las colas por prioridad. |
| `infactible_demostrada` | Una condición necesaria falla (tema sin competentes, solicitud mayor que todo cupo, demanda > capacidad). Se explica el motivo. |
| `sin_solucion_encontrada` | La búsqueda no halló reparto válido; **no prueba** que no exista. Nunca se muestra como asignación. |

Referencias de comparación: voraz, aleatorio factible, búsqueda local (mismo presupuesto de evaluaciones) y óptimo exacto (solo si el espacio ≤ 500 000).

## Estructura

```
core/            Motor en Python puro (solo biblioteca estándar)
  model.py       Validación, evaluación de J, diagnóstico de infactibilidad
  constructivo.py  Construcción y reparación acotadas (sin bucles infinitos)
  genetic_algorithm.py  AG: torneo, cruce de un punto, mutación, elitismo
  baselines.py   Voraz, aleatorio, búsqueda local, óptimo exacto
  escenarios.py  Cambios de entorno
  api.py         Entrada/salida JSON (la usa la web)
data/scenarios.json   9 escenarios sintéticos con semillas fijas
experiments/     Generador de escenarios y experimentos (30 semillas)
tests/           43 pruebas (pytest)
evidencias/      CSV, resumen.md, figuras y capturas generadas por ejecución real
docs/            Sitio estático (GitHub Pages): index.html, app.js, styles.css + copia de core/
build_web.py     Copia core/ y scenarios.json a docs/
```

## Ejecutar

```bash
pip install -r requirements.txt
python -m pytest tests -q                       # 43 pruebas
python experiments/run_experiments.py --semillas 30   # regenera evidencias/
python build_web.py                             # sincroniza docs/ con core/
cd docs && python -m http.server 8000           # abrir http://localhost:8000
```

La web descarga Pyodide v0.26.4 desde jsDelivr, escribe `core/*.py` en su sistema de archivos virtual y ejecuta **el mismo código** que las pruebas. Se verificó que Pyodide y CPython dan resultados idénticos (J = 0.3 en el escenario base).

## Publicar en GitHub Pages

1. Crear un repositorio y subir esta carpeta.
2. Settings → Pages → *Deploy from a branch* → rama `main`, carpeta `/docs`.
3. Esperar el despliegue (1–2 min); la web queda en la URL indicada arriba.

## Resultados (30 semillas, ejecución real)

Resumen completo en `evidencias/resumen.md`. En resumen: el AG supera al voraz y a la búsqueda local en cargas moderadas y en heterogeneidad, y tras el cambio de entorno; **en el escenario de 150×12 es peor** que ambos (J mediana 0.531 frente a 0.519 y 0.518). Se reporta tal cual.

## Límites

- Datos sintéticos; el escenario `base_6x3` es una reconstrucción propia del ejemplo manual de la Actividad 1, no los datos originales.
- Las pruebas simples de infactibilidad no prueban factibilidad.
- Con 30 semillas la diferencia es estadística (prueba de signos), no una garantía general.
- Una versión de escritorio (Tkinter) que reutilice `core/` está pendiente.
