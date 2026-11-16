"""Estados de salida honestos, escenarios de cambio y la API JSON."""
import json

import pytest

from conftest import verificar_reparto
from core import api
from core.baselines import voraz
from core.escenarios import aplicar_cambio, aplicar_cambios, reasignadas
from core.genetic_algorithm import ejecutar_ag
from core.model import ErrorValidacion, Instancia


def test_todos_los_escenarios_son_validos(escenarios):
    assert len(escenarios) >= 9
    for e in escenarios.values():
        Instancia.desde_dict(e["instancia"])


def test_saturacion_es_infactible_demostrada(instancias):
    res = ejecutar_ag(instancias["saturacion"])
    assert res["estado"] == "infactible_demostrada"
    assert res["asignacion"] is None and res["razones"]
    assert any("demanda total" in r for r in res["razones"])
    assert voraz(instancias["saturacion"])["estado"] == "infactible_demostrada"


def test_solicitud_sin_competente_se_informa(instancias):
    res = ejecutar_ag(instancias["sin_competente"])
    assert res["estado"] == "infactible_demostrada"
    assert any("S002" in r and "competente" in r for r in res["razones"])


def test_empaquetado_dificil_no_se_declara_imposible_sin_prueba(instancias):
    """Pasa las condiciones necesarias simples pero no tiene reparto: el sistema NO afirma
    que sea imposible, dice que no encontró uno, y no entrega un reparto como válido."""
    res = ejecutar_ag(instancias["empaquetado_dificil"])
    assert res["estado"] == "sin_solucion_encontrada"
    assert res["asignacion"] is None
    assert res["mejor_intento"]["valido"] is False and res["exceso"] > 0


def test_cambios_de_entorno(escenarios):
    inst0 = escenarios["cambio_entorno"]["instancia"]
    antes = ejecutar_ag(Instancia.desde_dict(inst0), {"semilla": 4})
    despues_dict = aplicar_cambios(inst0, escenarios["cambio_entorno"]["cambios"])
    assert next(f for f in despues_dict["funcionarios"] if f["id"] == "F2")["capacidad"] == 0
    assert next(f for f in despues_dict["funcionarios"] if f["id"] == "F4")["capacidad"] == pytest.approx(31.5)
    assert len(despues_dict["solicitudes"]) == len(inst0["solicitudes"]) + 3
    assert len(inst0["solicitudes"]) == 20          # el original no se modifica
    despues = ejecutar_ag(Instancia.desde_dict(despues_dict), {"semilla": 4})
    assert antes["estado"] == despues["estado"] == "factible"
    assert "F2" not in despues["asignacion"].values()
    assert verificar_reparto(despues_dict, despues["asignacion"]) == []
    mover = reasignadas(antes["asignacion"], despues["asignacion"])
    # F2 atendía solicitudes antes: todas las suyas tuvieron que moverse
    de_f2 = [s for s, f in antes["asignacion"].items() if f == "F2"]
    assert de_f2 and set(de_f2) <= set(mover)


def test_cambios_invalidos():
    inst = {"funcionarios": [{"id": "A", "competencias": ["T"], "capacidad": 10, "pendiente": 0}],
            "solicitudes": []}
    for malo in ({"tipo": "deshabilitar_funcionario", "funcionario": "Z"},
                 {"tipo": "reducir_capacidad", "funcionario": "A", "factor": 2},
                 {"tipo": "inventado"},
                 {"tipo": "agregar_solicitud", "solicitud": {"id": "S", "tematica": "T", "esfuerzo": -1}}):
        with pytest.raises(ErrorValidacion):
            aplicar_cambio(inst, malo)


def test_api_json_ida_y_vuelta(escenarios):
    entrada = json.dumps({"instancia": escenarios["base_6x3"]["instancia"],
                          "parametros": {"semilla": 9}, "extras": True})
    salida = json.loads(api.ejecutar(entrada))
    assert salida["ag"]["estado"] == "factible" and salida["voraz"]["estado"] == "factible"
    assert {"aleatorio", "local"} <= set(salida)
    assert salida["ag"]["semilla"] == 9


def test_api_devuelve_errores_en_lugar_de_lanzar(escenarios):
    malo = json.loads(api.ejecutar(json.dumps({"instancia": {"funcionarios": [], "solicitudes": []}})))
    assert "error" in malo
    malo = json.loads(api.ejecutar(json.dumps({"instancia": escenarios["base_6x3"]["instancia"],
                                               "parametros": {"p_cruce": 3}})))
    assert "error" in malo
    assert "error" in json.loads(api.ejecutar("esto no es json"))
    cambio = json.loads(api.cambiar(json.dumps(escenarios["base_6x3"]["instancia"]),
                                    json.dumps({"tipo": "reducir_capacidad", "funcionario": "F1", "factor": 0.5})))
    assert cambio["instancia"]["funcionarios"][0]["capacidad"] == 5
