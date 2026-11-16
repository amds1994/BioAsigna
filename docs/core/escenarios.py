"""Cambios de entorno sobre una instancia (ausencia, menos capacidad, solicitudes nuevas)."""
import copy

from .model import ErrorValidacion, Instancia


def aplicar_cambio(instancia, cambio):
    """Devuelve una instancia nueva (dict) con el cambio aplicado, ya validada.

    Tipos de cambio:
      {"tipo": "deshabilitar_funcionario", "funcionario": "F2"}
      {"tipo": "reducir_capacidad", "funcionario": "F4", "factor": 0.7}
      {"tipo": "agregar_solicitud", "solicitud": {"id", "tematica", "esfuerzo", "prioridad"}}
    """
    nueva = copy.deepcopy(instancia)
    tipo = cambio.get("tipo")
    if tipo in ("deshabilitar_funcionario", "reducir_capacidad"):
        fid = cambio.get("funcionario")
        f = next((x for x in nueva["funcionarios"] if x["id"] == fid), None)
        if f is None:
            raise ErrorValidacion(["No existe el funcionario %s." % fid])
        if tipo == "deshabilitar_funcionario":
            f["capacidad"] = 0
        else:
            factor = cambio.get("factor")
            if not isinstance(factor, (int, float)) or isinstance(factor, bool) or not 0 <= factor <= 1:
                raise ErrorValidacion(["El factor de reducción debe estar entre 0 y 1."])
            f["capacidad"] = round(f["capacidad"] * factor, 2)
    elif tipo == "agregar_solicitud":
        sol = dict(cambio.get("solicitud") or {})
        sol.setdefault("prioridad", "Media")
        if not sol.get("id"):
            sol["id"] = "S%03d" % (len(nueva["solicitudes"]) + 1)
        nueva["solicitudes"].append(sol)
    else:
        raise ErrorValidacion(["Tipo de cambio desconocido: %s." % tipo])
    Instancia.desde_dict(nueva)  # valida el resultado (ids duplicados, números, etc.)
    return nueva


def aplicar_cambios(instancia, cambios):
    for c in cambios:
        instancia = aplicar_cambio(instancia, c)
    return instancia


def reasignadas(asignacion_antes, asignacion_despues):
    """Solicitudes presentes en ambos repartos cuyo responsable cambió."""
    if not asignacion_antes or not asignacion_despues:
        return []
    return sorted(s for s, f in asignacion_antes.items()
                  if s in asignacion_despues and asignacion_despues[s] != f)
