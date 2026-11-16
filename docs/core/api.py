"""Puerta de entrada JSON para la web (Pyodide) y para otras interfaces.

Todas las funciones reciben y devuelven texto JSON; los errores de validación se
devuelven como {"error": [...]} en lugar de lanzar excepciones al navegador.
"""
import json

from .baselines import aleatorio_factible, busqueda_local, voraz
from .escenarios import aplicar_cambio, reasignadas
from .genetic_algorithm import ejecutar_ag
from .model import ErrorValidacion, Instancia, validar_parametros


def _error(mensajes):
    return json.dumps({"error": list(mensajes)})


def ejecutar(entrada_json):
    """Entrada: {"instancia": {...}, "parametros": {...}, "extras": bool}.

    Salida: {"ag": resultado, "voraz": resultado[, "aleatorio": ..., "local": ...]}.
    """
    try:
        d = json.loads(entrada_json)
        inst = Instancia.desde_dict(d.get("instancia"))
        params = validar_parametros(d.get("parametros"))
        ag = ejecutar_ag(inst, params)
        salida = {"ag": ag, "voraz": voraz(inst)}
        if d.get("extras"):
            salida["aleatorio"] = aleatorio_factible(inst, params["semilla"])
            salida["local"] = busqueda_local(inst, params["semilla"], max(ag["evaluaciones"], 1))
        return json.dumps(salida)
    except ErrorValidacion as e:
        return _error(e.errores)
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        return _error(["Entrada inválida: %s" % e])


def cambiar(instancia_json, cambio_json):
    """Aplica un cambio de entorno y devuelve la instancia nueva como JSON."""
    try:
        nueva = aplicar_cambio(json.loads(instancia_json), json.loads(cambio_json))
        return json.dumps({"instancia": nueva})
    except ErrorValidacion as e:
        return _error(e.errores)
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        return _error(["Cambio inválido: %s" % e])


def comparar_repartos(antes_json, despues_json):
    """Solicitudes reasignadas entre dos asignaciones {solicitud: funcionario}."""
    antes, despues = json.loads(antes_json), json.loads(despues_json)
    return json.dumps({"reasignadas": reasignadas(antes, despues)})
