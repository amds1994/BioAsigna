import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import pytest

from core.model import Instancia


def cargar_escenarios():
    with open(os.path.join(RAIZ, "data", "scenarios.json"), encoding="utf-8") as fh:
        return {e["id"]: e for e in json.load(fh)["escenarios"]}


@pytest.fixture(scope="session")
def escenarios():
    return cargar_escenarios()


@pytest.fixture(scope="session")
def instancias(escenarios):
    return {k: Instancia.desde_dict(v["instancia"]) for k, v in escenarios.items()}


def verificar_reparto(instancia_dict, asignacion):
    """Verificador INDEPENDIENTE del motor: devuelve la lista de violaciones."""
    problemas = []
    funcs = {f["id"]: f for f in instancia_dict["funcionarios"]}
    sols = {s["id"]: s for s in instancia_dict["solicitudes"]}
    if set(asignacion) != set(sols):
        problemas.append("no hay exactamente un responsable por solicitud")
    carga = {fid: 0.0 for fid in funcs}
    for sid, fid in asignacion.items():
        if fid not in funcs:
            problemas.append("funcionario inexistente %s" % fid)
            continue
        if sols[sid]["tematica"] not in funcs[fid]["competencias"]:
            problemas.append("%s no es competente en %s" % (fid, sols[sid]["tematica"]))
        carga[fid] += sols[sid]["esfuerzo"]
    for fid, f in funcs.items():
        residual = max(0.0, f["capacidad"] - f["pendiente"])
        if carga[fid] > residual + 1e-9:
            problemas.append("%s excede su capacidad residual" % fid)
        if f["capacidad"] <= 0 and carga[fid] > 0:
            problemas.append("%s con capacidad 0 recibió trabajo" % fid)
    return problemas
