"""Algoritmo genético para el reparto equilibrado de solicitudes.

Cromosoma: X[i] = índice del funcionario asignado a la solicitud i.
- Cada gen vive en su dominio (funcionarios habilitados), así la competencia se
  cumple siempre, también tras el cruce de un punto y la mutación.
- Solo la capacidad puede violarse. Un reparto factible siempre gana a uno
  infactible; entre factibles gana el menor J; entre infactibles, el menor exceso.
- Se repara de forma acotada y no se descarta nada: no hay bucles sin salida.
"""
import random
import time

from .constructivo import construir, reparar
from .model import construir_resultado, diagnosticar_infactibilidad, evaluar, validar_parametros


def ejecutar_ag(inst, parametros=None):
    t0 = time.perf_counter()
    params = validar_parametros(parametros)
    if diagnosticar_infactibilidad(inst):
        return construir_resultado(inst, "ag", None, params, [], 0, t0)

    rng = random.Random(params["semilla"])
    N, G = params["poblacion"], params["generaciones"]
    elit, pc, pm, k = params["elitismo"], params["p_cruce"], params["p_mutacion"], params["torneo"]
    estado = {"evals": 0, "reparaciones": 0}
    historial = []

    def evaluar_(X):
        estado["evals"] += 1
        return evaluar(inst, X)

    def con_reparacion(X, ev):
        if ev[0][0] == 0:
            return ev
        movs = reparar(inst, X, rng)
        if movs:
            estado["reparaciones"] += movs
            return evaluar_(X)
        return ev

    def mutar(X):
        for i in range(inst.n):
            dom = inst.dominio[i]
            if len(dom) > 1 and rng.random() < pm:
                X[i] = rng.choice([j for j in dom if j != X[i]])

    def registrar(gen, pob):
        factibles = [ind[1][1] for ind in pob if ind[1][0][0] == 0]
        mejor = min(pob, key=lambda ind: ind[1][0])
        feasible = mejor[1][0][0] == 0
        historial.append({
            "gen": gen,
            "mejor_J": round(mejor[1][1], 6) if feasible else None,
            "mejor_exceso": 0.0 if feasible else round(mejor[1][4], 6),
            "media_J": round(sum(factibles) / len(factibles), 6) if factibles else None,
            "factibles": len(factibles),
        })

    pob = []
    for _ in range(N):
        r = rng.random()
        if r < 0.30:
            X = [rng.choice(inst.dominio[i]) for i in range(inst.n)]
        elif r < 0.65:
            X = construir(inst, rng, "aleatorio", 0.5)
        else:
            X = construir(inst, rng, "esfuerzo", 0.5)
        pob.append((X, con_reparacion(X, evaluar_(X))))
    registrar(0, pob)

    for g in range(1, G + 1):
        pob.sort(key=lambda ind: ind[1][0])
        nueva = pob[:elit]
        while len(nueva) < N:
            i1 = min(rng.sample(range(N), k), key=lambda t: pob[t][1][0])
            i2 = min(rng.sample(range(N), k), key=lambda t: pob[t][1][0])
            p1, p2 = pob[i1][0], pob[i2][0]
            if inst.n >= 2 and rng.random() < pc:
                corte = rng.randint(1, inst.n - 1)
                h1, h2 = p1[:corte] + p2[corte:], p2[:corte] + p1[corte:]
            else:
                h1, h2 = list(p1), list(p2)
            for hijo in (h1, h2):
                if len(nueva) >= N:
                    break
                mutar(hijo)
                nueva.append((hijo, con_reparacion(hijo, evaluar_(hijo))))
        pob = nueva
        registrar(g, pob)

    mejor = min(pob, key=lambda ind: ind[1][0])
    return construir_resultado(inst, "ag", mejor[0], params, historial,
                               estado["evals"], t0, estado["reparaciones"])
