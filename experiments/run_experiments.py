"""Experimentos reales: AG frente a tres referencias, 30 semillas por escenario.

Genera en evidencias/: resultados_por_semilla.csv, resumen.csv, resumen.md,
metadatos.json y las figuras en evidencias/figuras/. Todo sale de ejecuciones reales;
nada se escribe a mano. Ejecutar desde la raíz del proyecto:

    python experiments/run_experiments.py            # 30 semillas
    python experiments/run_experiments.py --semillas 5   # prueba rápida
"""
import argparse
import csv
import hashlib
import json
import math
import os
import platform
import statistics
import sys
import time
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from core.baselines import aleatorio_factible, busqueda_local, optimo_exacto, voraz  # noqa: E402
from core.escenarios import aplicar_cambios, reasignadas  # noqa: E402
from core.genetic_algorithm import ejecutar_ag  # noqa: E402
from core.model import Instancia  # noqa: E402

TOL = 1e-9
ALGS = ("ag", "local", "aleatorio")
NOMBRES = {"ag": "Algoritmo genético", "local": "Búsqueda local", "aleatorio": "Aleatorio factible",
           "voraz": "Voraz", "exacto": "Óptimo exacto"}


def cuantiles(xs):
    if len(xs) == 1:
        return xs[0], xs[0], xs[0]
    q1, q2, q3 = statistics.quantiles(xs, n=4, method="inclusive")
    return q1, q2, q3


def prueba_signos(difs):
    """Prueba de signos exacta (bilateral) sobre diferencias; los empates se excluyen."""
    a = sum(1 for d in difs if d < -TOL)   # AG mejor (menor J)
    b = sum(1 for d in difs if d > TOL)
    n = a + b
    if n == 0:
        return a, len(difs), b, 1.0
    k = min(a, b)
    p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return a, len(difs) - n, b, min(1.0, p)


def hash_codigo():
    h = hashlib.sha256()
    carpeta = os.path.join(RAIZ, "core")
    for nombre in sorted(os.listdir(carpeta)):
        if nombre.endswith(".py"):
            with open(os.path.join(carpeta, nombre), "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--semillas", type=int, default=30)
    args = ap.parse_args()
    semillas = list(range(1, args.semillas + 1))

    with open(os.path.join(RAIZ, "data", "scenarios.json"), encoding="utf-8") as fh:
        crudo = fh.read()
    escenarios = {e["id"]: e for e in json.loads(crudo)["escenarios"]}

    # Conjunto de instancias a evaluar. El cambio de entorno se evalúa antes y después.
    casos = {}
    for sid, e in escenarios.items():
        if sid == "cambio_entorno":
            casos["cambio_entorno_antes"] = e["instancia"]
            casos["cambio_entorno_despues"] = aplicar_cambios(e["instancia"], e["cambios"])
        else:
            casos[sid] = e["instancia"]

    filas, historias, asign_ag, asign_voraz, exactos = [], {}, {}, {}, {}
    t_ini = time.time()
    for cid, d in casos.items():
        inst = Instancia.desde_dict(d)
        v = voraz(inst)
        asign_voraz[cid] = v["asignacion"]
        ex = optimo_exacto(inst)
        if ex is not None and ex["estado"] == "factible":
            exactos[cid] = ex
            filas.append(fila(cid, "exacto", 0, ex))
        filas.append(fila(cid, "voraz", 0, v))
        historias[cid] = []
        for s in semillas:
            ag = ejecutar_ag(inst, {"semilla": s})
            filas.append(fila(cid, "ag", s, ag))
            historias[cid].append([h["mejor_J"] for h in ag["historial"]])
            asign_ag[(cid, s)] = ag["asignacion"]
            filas.append(fila(cid, "local", s, busqueda_local(inst, s, max(ag["evaluaciones"], 1))))
            filas.append(fila(cid, "aleatorio", s, aleatorio_factible(inst, s)))
        print("  listo:", cid, "(%.1f s acumulados)" % (time.time() - t_ini), flush=True)

    out = os.path.join(RAIZ, "evidencias")
    os.makedirs(os.path.join(out, "figuras"), exist_ok=True)
    escribir_csv_semillas(filas, os.path.join(out, "resultados_por_semilla.csv"))
    resumen = resumir(filas, exactos, casos, asign_ag, asign_voraz, semillas)
    escribir_resumen(resumen, out)
    figuras(casos, filas, historias, exactos, asign_ag, asign_voraz, semillas, out)
    meta = {
        "fecha_ejecucion": datetime.now().isoformat(timespec="seconds"),
        "python": platform.python_version(), "plataforma": platform.platform(),
        "semillas": [semillas[0], semillas[-1]], "n_semillas": len(semillas),
        "parametros_ag": {"poblacion": 50, "generaciones": 100, "p_cruce": 0.8, "p_mutacion": 0.05,
                          "torneo": 3, "elitismo": 2},
        "pesos_J": {"max": 0.6, "sigma": 0.4},
        "presupuesto_local": "igual a las evaluaciones del AG con la misma semilla",
        "huella_codigo_core": hash_codigo(),
        "huella_escenarios": hashlib.sha256(crudo.encode("utf-8")).hexdigest()[:16],
        "segundos_totales": round(time.time() - t_ini, 1),
    }
    with open(os.path.join(out, "metadatos.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)
    print("Evidencias escritas en", out)


def fila(cid, alg, semilla, r):
    return {"escenario": cid, "algoritmo": alg, "semilla": semilla, "estado": r["estado"],
            "J": r["J"], "max_u": r["max_u"], "sigma_u": r["sigma_u"], "exceso": r["exceso"],
            "evaluaciones": r["evaluaciones"], "tiempo_ms": round(r["tiempo_s"] * 1000, 2)}


def escribir_csv_semillas(filas, ruta):
    with open(ruta, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)


def resumir(filas, exactos, casos, asign_ag, asign_voraz, semillas):
    res = {"por_algoritmo": [], "comparaciones": [], "adaptacion": None}
    for cid in casos:
        voraz_j = next((f["J"] for f in filas if f["escenario"] == cid and f["algoritmo"] == "voraz"), None)
        for alg in ("exacto", "voraz") + ALGS:
            fs = [f for f in filas if f["escenario"] == cid and f["algoritmo"] == alg]
            if not fs:
                continue
            fact = [f for f in fs if f["estado"] == "factible"]
            estados = sorted({f["estado"] for f in fs})
            fila_res = {"escenario": cid, "algoritmo": NOMBRES[alg], "corridas": len(fs),
                        "factibles": len(fact), "estado": "/".join(estados)}
            if fact:
                js = [f["J"] for f in fact]
                q1, med, q3 = cuantiles(js)
                fila_res.update(J_mediana=round(med, 4), J_q1=round(q1, 4), J_q3=round(q3, 4),
                                J_min=round(min(js), 4), J_max=round(max(js), 4),
                                maxu_mediana=round(statistics.median(f["max_u"] for f in fact), 4),
                                sigma_mediana=round(statistics.median(f["sigma_u"] for f in fact), 4))
            fila_res["tiempo_ms_mediana"] = round(statistics.median(f["tiempo_ms"] for f in fs), 2)
            fila_res["evaluaciones_mediana"] = statistics.median(f["evaluaciones"] for f in fs)
            res["por_algoritmo"].append(fila_res)
        # AG frente a cada referencia
        ag = {f["semilla"]: f for f in filas if f["escenario"] == cid and f["algoritmo"] == "ag"}
        if not any(f["estado"] == "factible" for f in ag.values()):
            continue
        for ref in ("voraz", "local", "aleatorio"):
            if ref == "voraz":
                if voraz_j is None:
                    continue
                difs = [ag[s]["J"] - voraz_j for s in semillas if ag[s]["J"] is not None]
            else:
                rf = {f["semilla"]: f for f in filas if f["escenario"] == cid and f["algoritmo"] == ref}
                difs = [ag[s]["J"] - rf[s]["J"] for s in semillas
                        if ag[s]["J"] is not None and rf[s]["J"] is not None]
            if not difs:
                continue
            mejor, empate, peor, p = prueba_signos(difs)
            res["comparaciones"].append({
                "escenario": cid, "referencia": NOMBRES[ref], "pares": len(difs),
                "AG_mejor": mejor, "empate": empate, "AG_peor": peor,
                "mediana_dif_J": round(statistics.median(difs), 4), "p_signos": round(p, 4)})
    # Adaptación: solicitudes reasignadas tras el cambio de entorno
    mov_ag = []
    for s in semillas:
        a, b = asign_ag.get(("cambio_entorno_antes", s)), asign_ag.get(("cambio_entorno_despues", s))
        if a and b:
            mov_ag.append(len(reasignadas(a, b)))
    mov_v = len(reasignadas(asign_voraz.get("cambio_entorno_antes"), asign_voraz.get("cambio_entorno_despues")))
    if mov_ag:
        q1, med, q3 = cuantiles(mov_ag)
        res["adaptacion"] = {"AG_mediana": med, "AG_q1": q1, "AG_q3": q3, "AG_min": min(mov_ag),
                             "AG_max": max(mov_ag), "voraz": mov_v,
                             "total_solicitudes_antes": len(casos["cambio_entorno_antes"]["solicitudes"])}
    return res


def escribir_resumen(res, out):
    campos = ["escenario", "algoritmo", "corridas", "factibles", "estado", "J_mediana", "J_q1", "J_q3",
              "J_min", "J_max", "maxu_mediana", "sigma_mediana", "tiempo_ms_mediana", "evaluaciones_mediana"]
    with open(os.path.join(out, "resumen.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(res["por_algoritmo"])
    L = ["# Resumen de experimentos (ejecución real)\n",
         "Cada fila resume las corridas de un algoritmo en un escenario. J: menor es mejor. "
         "`factibles` = corridas con reparto válido. Los algoritmos estocásticos usan las mismas semillas.\n",
         "## Calidad por algoritmo\n",
         "| Escenario | Algoritmo | Factibles | J mediana | J Q1–Q3 | J mín–máx | max u (med.) | σ (med.) | Tiempo ms (med.) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for f in res["por_algoritmo"]:
        if "J_mediana" in f:
            L.append("| %s | %s | %d/%d | %.4f | %.4f–%.4f | %.4f–%.4f | %.4f | %.4f | %.1f |" % (
                f["escenario"], f["algoritmo"], f["factibles"], f["corridas"], f["J_mediana"], f["J_q1"],
                f["J_q3"], f["J_min"], f["J_max"], f["maxu_mediana"], f["sigma_mediana"], f["tiempo_ms_mediana"]))
        else:
            L.append("| %s | %s | %d/%d | — (%s) | — | — | — | — | %.1f |" % (
                f["escenario"], f["algoritmo"], f["factibles"], f["corridas"], f["estado"], f["tiempo_ms_mediana"]))
    L += ["", "## AG frente a cada referencia (mismas semillas)\n",
          "`AG mejor` = corridas donde el AG obtuvo menor J. La diferencia es J(AG) − J(referencia): "
          "negativa favorece al AG. `p` es de una prueba de signos exacta bilateral (empates excluidos).\n",
          "| Escenario | Referencia | Pares | AG mejor | Empate | AG peor | Mediana ΔJ | p |",
          "|---|---|---|---|---|---|---|---|"]
    for c in res["comparaciones"]:
        p = "%.4f" % c["p_signos"] if c["p_signos"] >= 0.0001 else "<0.0001"
        L.append("| %s | %s | %d | %d | %d | %d | %+.4f | %s |" % (
            c["escenario"], c["referencia"], c["pares"], c["AG_mejor"], c["empate"], c["AG_peor"],
            c["mediana_dif_J"], p))
    a = res["adaptacion"]
    if a:
        L += ["", "## Adaptación: solicitudes reasignadas tras el cambio de entorno\n",
              "Cambio: F2 se ausenta, F4 pierde 30 %% de capacidad y llegan 3 solicitudes. "
              "De las %d solicitudes originales, cuántas cambiaron de responsable.\n" % a["total_solicitudes_antes"],
              "| Algoritmo | Reasignadas |", "|---|---|",
              "| AG (30 semillas, mediana [Q1–Q3], mín–máx) | %g [%g–%g], %d–%d |" % (
                  a["AG_mediana"], a["AG_q1"], a["AG_q3"], a["AG_min"], a["AG_max"]),
              "| Voraz (determinista) | %d |" % a["voraz"]]
    with open(os.path.join(out, "resumen.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def figuras(casos, filas, historias, exactos, asign_ag, asign_voraz, semillas, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    carpeta = os.path.join(out, "figuras")
    azul, gris, naranja = "#1f5fa8", "#6b7280", "#c2570c"

    # Convergencia: mediana y rango intercuartil del mejor J por generación
    for cid in ("carga_moderada_20x5", "heterogeneidad_30x6", "escala_150x12"):
        H = historias[cid]
        gens = range(len(H[0]))
        med, lo, hi, xs = [], [], [], []
        for g in gens:
            vals = [h[g] for h in H if h[g] is not None]
            if len(vals) >= max(2, len(H) // 2):
                q1, m, q3 = cuantiles(vals)
                xs.append(g)
                med.append(m); lo.append(q1); hi.append(q3)
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.fill_between(xs, lo, hi, color=azul, alpha=0.2, label="AG: rango intercuartil")
        ax.plot(xs, med, color=azul, lw=2, label="AG: mediana de %d semillas" % len(H))
        vj = next(f["J"] for f in filas if f["escenario"] == cid and f["algoritmo"] == "voraz")
        ax.axhline(vj, color=naranja, ls="--", lw=1.5, label="Voraz (J = %.4f)" % vj)
        if cid in exactos:
            ax.axhline(exactos[cid]["J"], color=gris, ls=":", lw=1.5, label="Óptimo exacto")
        ax.set_xlabel("Generación"); ax.set_ylabel("Mejor J (menor es mejor)")
        ax.set_title("Convergencia del AG: %s" % cid)
        ax.grid(alpha=0.3); ax.legend(frameon=False)
        fig.tight_layout(); fig.savefig(os.path.join(carpeta, "convergencia_%s.png" % cid), dpi=150)
        plt.close(fig)

    # Cajas de J por algoritmo
    mostrar = ["carga_moderada_20x5", "heterogeneidad_30x6", "escala_150x12", "cambio_entorno_despues"]
    fig, axs = plt.subplots(1, len(mostrar), figsize=(13, 4))
    for ax, cid in zip(axs, mostrar):
        datos, etiquetas = [], []
        for alg in ALGS:
            js = [f["J"] for f in filas if f["escenario"] == cid and f["algoritmo"] == alg
                  and f["estado"] == "factible"]
            if js:
                datos.append(js); etiquetas.append({"ag": "AG", "local": "Local", "aleatorio": "Azar"}[alg])
        ax.boxplot(datos, patch_artist=True,
                   boxprops=dict(facecolor="#cfe0f5", color=azul), medianprops=dict(color=azul, lw=2))
        ax.set_xticks(range(1, len(etiquetas) + 1))
        ax.set_xticklabels(etiquetas)
        vj = next(f["J"] for f in filas if f["escenario"] == cid and f["algoritmo"] == "voraz")
        ax.axhline(vj, color=naranja, ls="--", lw=1.5, label="Voraz")
        titulos = {"carga_moderada_20x5": "Carga moderada (20 solicitudes, 5 funcionarios)",
                   "heterogeneidad_30x6": "Heterogeneidad (30 solicitudes, 6 funcionarios)",
                   "escala_150x12": "Escala (150 solicitudes, 12 funcionarios)",
                   "cambio_entorno_despues": "Después del cambio de entorno"}
        ax.set_title(titulos[cid], fontsize=9); ax.grid(alpha=0.3, axis="y")
    axs[0].set_ylabel("J (menor es mejor)"); axs[0].legend(frameon=False)
    fig.suptitle("Distribución de J en %d semillas" % len(semillas))
    fig.tight_layout(); fig.savefig(os.path.join(carpeta, "cajas_J.png"), dpi=150); plt.close(fig)

    # Ocupación antes / después del cambio de entorno (semilla 1)
    fig, axs = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, cid, titulo in ((axs[0], "cambio_entorno_antes", "Antes del cambio"),
                            (axs[1], "cambio_entorno_despues", "Después del cambio")):
        inst = Instancia.desde_dict(casos[cid])
        r = ejecutar_ag(inst, {"semilla": 1})
        ids = [c["id"] for c in r["cargas"]]
        pend = [c["pendiente"] / c["capacidad"] * 100 if c["capacidad"] > 0 else 0 for c in r["cargas"]]
        nueva = [(c["nueva"] / c["capacidad"] * 100) if c["capacidad"] > 0 else 0 for c in r["cargas"]]
        ax.bar(ids, pend, color=gris, label="Pendiente previa")
        ax.bar(ids, nueva, bottom=pend, color=azul, label="Asignación nueva")
        ax.axhline(100, color=naranja, ls="--", lw=1.5, label="Capacidad (100 %)")
        for i, c in enumerate(r["cargas"]):
            if not c["activo"]:
                ax.text(i, 3, "ausente", ha="center", fontsize=9, color=naranja)
        ax.set_title(titulo); ax.grid(alpha=0.3, axis="y")
    axs[0].set_ylabel("Ocupación (% de la capacidad)")
    manijas, rotulos = axs[0].get_legend_handles_labels()
    fig.legend(manijas, rotulos, loc="lower center", ncol=3, frameon=False)
    fig.suptitle("Ocupación por funcionario con AG (semilla 1)")
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.savefig(os.path.join(carpeta, "ocupacion_cambio_entorno.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
