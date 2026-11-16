"""Referencias de comparación para el algoritmo genético.

- voraz: esfuerzo descendente; cada solicitud va al funcionario habilitado con cupo
  que quede con menor ocupación. Determinista.
- aleatorio_factible: repartos aleatorios hasta hallar uno factible (con tope).
- busqueda_local: ascenso de colina con el mismo presupuesto de evaluaciones.
- optimo_exacto: enumeración completa, solo cuando el espacio es pequeño.
"""
import itertools
import random
import time

from .constructivo import construir
from .model import (EPS, construir_resultado, diagnosticar_infactibilidad, evaluar)


def _reparto_voraz(inst):
    orden = sorted(range(inst.n), key=lambda i: (-inst.e[i], inst.ids_s[i]))
    a = [0.0] * inst.m
    X = [0] * inst.n
    for i in orden:
        dom = inst.dominio[i]
        con_cupo = [j for j in dom if a[j] + inst.e[i] <= inst.r[j] + EPS]
        if con_cupo:
            j = min(con_cupo, key=lambda k: ((inst.h[k] + a[k] + inst.e[i]) / inst.c[k], k))
        else:
            j = max(dom, key=lambda k: (inst.r[k] - a[k], -k))
        X[i] = j
        a[j] += inst.e[i]
    return X


def voraz(inst):
    t0 = time.perf_counter()
    if diagnosticar_infactibilidad(inst):
        return construir_resultado(inst, "voraz", None, {}, [], 0, t0)
    X = _reparto_voraz(inst)
    return construir_resultado(inst, "voraz", X, {}, [], 1, t0)


def aleatorio_factible(inst, semilla=42, intentos=200):
    t0 = time.perf_counter()
    params = {"semilla": semilla}
    if diagnosticar_infactibilidad(inst):
        return construir_resultado(inst, "aleatorio", None, params, [], 0, t0)
    rng = random.Random(semilla)
    mejor, mejor_ev, usados = None, None, 0
    for _ in range(intentos):
        X = construir(inst, rng, "aleatorio", 0.0)
        ev = evaluar(inst, X)
        usados += 1
        if mejor is None or ev[0] < mejor_ev[0]:
            mejor, mejor_ev = X, ev
        if ev[0][0] == 0:
            break
    return construir_resultado(inst, "aleatorio", mejor, params, [], usados, t0)


def busqueda_local(inst, semilla=42, presupuesto=5000):
    """Ascenso de colina: cambia el responsable de una solicitud y acepta si no empeora."""
    t0 = time.perf_counter()
    params = {"semilla": semilla}
    if diagnosticar_infactibilidad(inst):
        return construir_resultado(inst, "local", None, params, [], 0, t0)
    rng = random.Random(semilla)
    X = construir(inst, rng, "aleatorio", 0.5)
    ev = evaluar(inst, X)
    usados = 1
    mutables = [i for i in range(inst.n) if len(inst.dominio[i]) > 1]
    while usados < presupuesto and mutables:
        i = rng.choice(mutables)
        anterior = X[i]
        X[i] = rng.choice([j for j in inst.dominio[i] if j != anterior])
        nuevo = evaluar(inst, X)
        usados += 1
        if nuevo[0] <= ev[0]:
            ev = nuevo
        else:
            X[i] = anterior
    return construir_resultado(inst, "local", X, params, [], usados, t0)


def optimo_exacto(inst, limite=500000):
    """Óptimo por enumeración, o None si el espacio supera `limite` combinaciones."""
    t0 = time.perf_counter()
    if diagnosticar_infactibilidad(inst):
        return construir_resultado(inst, "exacto", None, {}, [], 0, t0)
    espacio = 1
    for dom in inst.dominio:
        espacio *= len(dom)
        if espacio > limite:
            return None
    mejor, mejor_ev, usados = None, None, 0
    for combo in itertools.product(*inst.dominio):
        X = list(combo)
        ev = evaluar(inst, X)
        usados += 1
        if mejor is None or ev[0] < mejor_ev[0]:
            mejor, mejor_ev = X, ev
    return construir_resultado(inst, "exacto", mejor, {}, [], usados, t0)
