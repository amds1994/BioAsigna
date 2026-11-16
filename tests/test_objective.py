"""Función objetivo J, determinismo, elitismo y validación de entradas."""
import math

import pytest

from core.genetic_algorithm import ejecutar_ag
from core.model import ErrorValidacion, Instancia, evaluar, validar_parametros


def test_j_del_ejemplo_equilibrado(instancias):
    inst = instancias["base_6x3"]
    # S001..S006 con esfuerzos 3,2,3,2,2,3 -> F1: S001+S002, F2: S003+S005, F3: S004+S006 (5/5/5)
    ids = {fid: j for j, fid in enumerate(inst.ids_f)}
    X = [ids["F1"], ids["F1"], ids["F2"], ids["F3"], ids["F2"], ids["F3"]]
    clave, J, maxu, sigma, exceso, a = evaluar(inst, X)
    assert a == [5.0, 5.0, 5.0] and exceso == 0
    assert maxu == pytest.approx(0.5) and sigma == pytest.approx(0.0)
    assert J == pytest.approx(0.3)


def test_j_del_ejemplo_desequilibrado(instancias):
    import itertools
    inst = instancias["base_6x3"]
    # Busca un reparto factible con cargas 6/5/4 h (existe en este escenario).
    X = next(list(c) for c in itertools.product(*inst.dominio)
             if sorted(evaluar(inst, list(c))[5]) == [4.0, 5.0, 6.0])
    clave, J, maxu, sigma, exceso, a = evaluar(inst, X)
    assert exceso == 0 and sorted(a) == [4.0, 5.0, 6.0]
    # Capacidad 10 y sin pendiente: u = (0.6, 0.5, 0.4); sigma = sqrt(0.02 / 3)
    esperado_sigma = math.sqrt(0.02 / 3)
    assert maxu == pytest.approx(0.6) and sigma == pytest.approx(esperado_sigma)
    assert J == pytest.approx(0.6 * 0.6 + 0.4 * esperado_sigma)   # 0.39266
    assert J > 0.3   # peor que el reparto 5/5/5


def test_j_incluye_la_carga_pendiente():
    d = {"funcionarios": [
            {"id": "A", "competencias": ["T"], "capacidad": 10, "pendiente": 5},
            {"id": "B", "competencias": ["T"], "capacidad": 20, "pendiente": 0}],
         "solicitudes": [{"id": "S1", "tematica": "T", "esfuerzo": 2}]}
    inst = Instancia.desde_dict(d)
    _, J, maxu, sigma, exceso, a = evaluar(inst, [0])   # A: u=(5+2)/10=0.7 ; B: u=0
    assert maxu == pytest.approx(0.7) and sigma == pytest.approx(0.35)
    assert J == pytest.approx(0.6 * 0.7 + 0.4 * 0.35)


def test_misma_semilla_mismo_resultado(instancias):
    a = ejecutar_ag(instancias["carga_moderada_20x5"], {"semilla": 11})
    b = ejecutar_ag(instancias["carga_moderada_20x5"], {"semilla": 11})
    assert a["asignacion"] == b["asignacion"] and a["historial"] == b["historial"]
    assert a["J"] == b["J"] and a["evaluaciones"] == b["evaluaciones"]


def test_semillas_distintas_pueden_dar_trayectorias_distintas(instancias):
    a = ejecutar_ag(instancias["carga_moderada_20x5"], {"semilla": 1})
    b = ejecutar_ag(instancias["carga_moderada_20x5"], {"semilla": 2})
    assert a["historial"] != b["historial"]


def test_el_elitismo_hace_que_el_mejor_j_no_empeore(instancias):
    h = ejecutar_ag(instancias["heterogeneidad_30x6"], {"semilla": 5})["historial"]
    mejores = [x["mejor_J"] for x in h if x["mejor_J"] is not None]
    assert len(mejores) >= 2
    assert all(b <= a + 1e-12 for a, b in zip(mejores, mejores[1:]))


def test_el_ag_mejora_o_iguala_su_poblacion_inicial(instancias):
    h = ejecutar_ag(instancias["carga_moderada_20x5"], {"semilla": 3})["historial"]
    assert h[-1]["mejor_J"] <= h[0]["mejor_J"] + 1e-12


def test_validacion_de_parametros():
    assert validar_parametros({})["poblacion"] == 50
    for malo in ({"p_cruce": 1.5}, {"p_mutacion": -0.1}, {"poblacion": 1}, {"generaciones": 0},
                 {"torneo": 99}, {"elitismo": 50}, {"poblacion": 2.5}):
        with pytest.raises(ErrorValidacion):
            validar_parametros(malo)


def test_validacion_de_instancia():
    base = {"funcionarios": [{"id": "A", "competencias": ["T"], "capacidad": 10, "pendiente": 0}],
            "solicitudes": [{"id": "S", "tematica": "T", "esfuerzo": 1}]}
    Instancia.desde_dict(base)
    import copy
    casos = []
    c = copy.deepcopy(base); c["funcionarios"].append(dict(c["funcionarios"][0])); casos.append(c)      # id duplicado
    c = copy.deepcopy(base); c["solicitudes"].append(dict(c["solicitudes"][0])); casos.append(c)        # id duplicado
    c = copy.deepcopy(base); c["solicitudes"][0]["esfuerzo"] = -2; casos.append(c)                       # negativo
    c = copy.deepcopy(base); c["funcionarios"][0]["capacidad"] = "40"; casos.append(c)                   # no numérico
    c = copy.deepcopy(base); c["funcionarios"][0]["pendiente"] = -1; casos.append(c)
    c = copy.deepcopy(base); c["solicitudes"][0]["tematica"] = ""; casos.append(c)
    c = copy.deepcopy(base); c["solicitudes"][0]["prioridad"] = "Urgente"; casos.append(c)
    c = copy.deepcopy(base); c["funcionarios"] = []; casos.append(c)
    for malo in casos:
        with pytest.raises(ErrorValidacion):
            Instancia.desde_dict(malo)
