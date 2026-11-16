"""Invariantes: ningún reparto presentado como válido puede violar una restricción."""
import pytest

from conftest import verificar_reparto
from core.baselines import aleatorio_factible, busqueda_local, optimo_exacto, voraz
from core.genetic_algorithm import ejecutar_ag

FACTIBLES = ["base_6x3", "carga_moderada_20x5", "heterogeneidad_30x6",
             "escala_150x12", "sobrecarga_previa"]


@pytest.mark.parametrize("escenario", FACTIBLES)
@pytest.mark.parametrize("semilla", [1, 2, 3])
def test_ag_cumple_todas_las_restricciones(escenarios, instancias, escenario, semilla):
    res = ejecutar_ag(instancias[escenario], {"semilla": semilla})
    assert res["estado"] == "factible"
    assert verificar_reparto(escenarios[escenario]["instancia"], res["asignacion"]) == []


@pytest.mark.parametrize("escenario", FACTIBLES)
def test_voraz_cumple_las_restricciones(escenarios, instancias, escenario):
    res = voraz(instancias[escenario])
    assert res["estado"] == "factible"
    assert verificar_reparto(escenarios[escenario]["instancia"], res["asignacion"]) == []


@pytest.mark.parametrize("escenario", ["base_6x3", "carga_moderada_20x5"])
def test_aleatorio_y_local_cumplen_si_son_factibles(escenarios, instancias, escenario):
    for res in (aleatorio_factible(instancias[escenario], 7),
                busqueda_local(instancias[escenario], 7, 2000)):
        assert res["estado"] == "factible"
        assert verificar_reparto(escenarios[escenario]["instancia"], res["asignacion"]) == []


def test_sobrecarga_previa_no_recibe_trabajo_nuevo(escenarios, instancias):
    res = ejecutar_ag(instancias["sobrecarga_previa"])
    assert "F1" not in res["asignacion"].values()
    assert res["sobrecarga_previa"] == pytest.approx(5.0)  # 30 pendientes - 25 de capacidad
    assert any("F1" in a and "sobrecarga" in a for a in res["advertencias"])
    f1 = next(c for c in res["cargas"] if c["id"] == "F1")
    assert f1["nueva"] == 0 and f1["residual"] == 0


def test_capacidad_cero_queda_excluida_de_candidatos_y_de_j():
    from core.model import Instancia
    d = {"funcionarios": [
            {"id": "A", "competencias": ["T1"], "capacidad": 0, "pendiente": 0},
            {"id": "B", "competencias": ["T1"], "capacidad": 10, "pendiente": 0},
            {"id": "C", "competencias": ["T1"], "capacidad": 10, "pendiente": 0}],
         "solicitudes": [
            {"id": "S1", "tematica": "T1", "esfuerzo": 4}, {"id": "S2", "tematica": "T1", "esfuerzo": 4}]}
    inst = Instancia.desde_dict(d)
    res = ejecutar_ag(inst)
    assert res["estado"] == "factible"
    assert "A" not in res["asignacion"].values()
    # B y C con 4 h cada uno: u=0.4 y 0.4; sigma=0 sobre ACTIVOS (A no cuenta) -> J = 0.6*0.4
    assert res["J"] == pytest.approx(0.24)
    assert verificar_reparto(d, res["asignacion"]) == []


def test_el_exacto_confirma_el_optimo_del_ejemplo_base(instancias):
    exacto = optimo_exacto(instancias["base_6x3"])
    ag = ejecutar_ag(instancias["base_6x3"])
    assert exacto["J"] == pytest.approx(0.3)      # 5/5/5 h con capacidad 10 -> u=0.5
    assert ag["J"] == pytest.approx(exacto["J"], abs=1e-9)


def test_exacto_no_aplica_si_el_espacio_es_enorme(instancias):
    assert optimo_exacto(instancias["escala_150x12"]) is None
