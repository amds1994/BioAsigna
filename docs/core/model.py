"""Modelo de datos, validación y evaluación del reparto de solicitudes.

Definiciones (Actividad 1, con las precisiones de la Actividad 2):

    a_j  = suma de esfuerzos de las solicitudes asignadas a j
    r_j  = max(0, c_j - h_j)             capacidad residual para trabajo nuevo
    u_j  = (h_j + a_j) / c_j             solo para funcionarios activos (c_j > 0)
    J(X) = 0.6 * max_j u_j + 0.4 * sigma(u)   (sigma poblacional sobre activos)

Restricción dura: a_j <= r_j. J solo se compara entre repartos factibles.
Los repartos infactibles se comparan por su exceso total de capacidad.
"""
import math
import time

EPS = 1e-9
PESO_MAX = 0.6
PESO_SIGMA = 0.4
PRIORIDADES = ("Alta", "Media", "Baja")

PARAMETROS_BASE = {
    "poblacion": 50,
    "generaciones": 100,
    "p_cruce": 0.8,
    "p_mutacion": 0.05,
    "torneo": 3,
    "elitismo": 2,
    "semilla": 42,
}


class ErrorValidacion(ValueError):
    """Entrada inválida. `errores` lista todos los problemas encontrados."""

    def __init__(self, errores):
        self.errores = list(errores)
        super().__init__("; ".join(self.errores))


def _es_numero(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


# ---------------------------------------------------------------------------
# Validación
# ---------------------------------------------------------------------------

def validar_parametros(parametros=None):
    """Devuelve los parámetros completos y válidos, o lanza ErrorValidacion."""
    out = dict(PARAMETROS_BASE)
    for k, v in (parametros or {}).items():
        if k in PARAMETROS_BASE:
            out[k] = v
    errores = []

    def entero(nombre, minimo):
        v = out[nombre]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or int(v) != v:
            errores.append("El parámetro '%s' debe ser un entero." % nombre)
            return False
        out[nombre] = int(v)
        if out[nombre] < minimo:
            errores.append("El parámetro '%s' debe ser al menos %d." % (nombre, minimo))
            return False
        return True

    ok_pob = entero("poblacion", 2)
    entero("generaciones", 1)
    ok_tor = entero("torneo", 1)
    ok_eli = entero("elitismo", 0)
    entero("semilla", -10 ** 12)
    for nombre in ("p_cruce", "p_mutacion"):
        v = out[nombre]
        if not _es_numero(v) or not 0 <= v <= 1:
            errores.append("El parámetro '%s' debe estar entre 0 y 1." % nombre)
    if ok_pob and ok_tor and out["torneo"] > out["poblacion"]:
        errores.append("El torneo no puede ser mayor que la población.")
    if ok_pob and ok_eli and out["elitismo"] >= out["poblacion"]:
        errores.append("El elitismo debe ser menor que la población.")
    if errores:
        raise ErrorValidacion(errores)
    return out


def _validar_instancia(d):
    errores = []
    if not isinstance(d, dict):
        raise ErrorValidacion(["La instancia debe ser un objeto con 'funcionarios' y 'solicitudes'."])
    fs, ss = d.get("funcionarios"), d.get("solicitudes")
    if not isinstance(fs, list) or not fs:
        errores.append("Debe haber al menos un funcionario.")
        fs = []
    if not isinstance(ss, list):
        errores.append("'solicitudes' debe ser una lista.")
        ss = []
    funcionarios, solicitudes, vistos = [], [], set()
    for k, f in enumerate(fs):
        if not isinstance(f, dict):
            errores.append("Funcionario #%d no es un objeto." % (k + 1))
            continue
        fid = f.get("id")
        if not isinstance(fid, str) or not fid.strip():
            errores.append("Funcionario #%d sin 'id' válido." % (k + 1))
            continue
        if fid in vistos:
            errores.append("Identificador de funcionario duplicado: %s." % fid)
        vistos.add(fid)
        comp = f.get("competencias", [])
        if not isinstance(comp, list) or any(not isinstance(t, str) or not t.strip() for t in comp):
            errores.append("%s: 'competencias' debe ser una lista de textos." % fid)
            comp = []
        cap, pen = f.get("capacidad"), f.get("pendiente", 0)
        if not _es_numero(cap) or cap < 0:
            errores.append("%s: 'capacidad' debe ser un número >= 0." % fid)
            cap = 0
        if not _es_numero(pen) or pen < 0:
            errores.append("%s: 'pendiente' debe ser un número >= 0." % fid)
            pen = 0
        funcionarios.append({"id": fid, "competencias": list(comp),
                             "capacidad": cap, "pendiente": pen})
    vistos = set()
    for k, s in enumerate(ss):
        if not isinstance(s, dict):
            errores.append("Solicitud #%d no es un objeto." % (k + 1))
            continue
        sid = s.get("id")
        if not isinstance(sid, str) or not sid.strip():
            errores.append("Solicitud #%d sin 'id' válido." % (k + 1))
            continue
        if sid in vistos:
            errores.append("Identificador de solicitud duplicado: %s." % sid)
        vistos.add(sid)
        tema = s.get("tematica")
        if not isinstance(tema, str) or not tema.strip():
            errores.append("%s: 'tematica' debe ser un texto." % sid)
            tema = ""
        esf = s.get("esfuerzo")
        if not _es_numero(esf) or esf < 0:
            errores.append("%s: 'esfuerzo' debe ser un número >= 0." % sid)
            esf = 0
        pr = s.get("prioridad", "Media")
        if pr not in PRIORIDADES:
            errores.append("%s: 'prioridad' debe ser Alta, Media o Baja." % sid)
            pr = "Media"
        solicitudes.append({"id": sid, "tematica": tema, "esfuerzo": esf, "prioridad": pr})
    if errores:
        raise ErrorValidacion(errores)
    return funcionarios, solicitudes


class Instancia:
    """Datos de un escenario ya validados, con índices precalculados."""

    def __init__(self, funcionarios, solicitudes):
        self.funcionarios = funcionarios
        self.solicitudes = solicitudes
        self.m = len(funcionarios)
        self.n = len(solicitudes)
        self.ids_f = [f["id"] for f in funcionarios]
        self.ids_s = [s["id"] for s in solicitudes]
        self.c = [float(f["capacidad"]) for f in funcionarios]
        self.h = [float(f["pendiente"]) for f in funcionarios]
        self.r = [max(0.0, c - h) for c, h in zip(self.c, self.h)]
        self.e = [float(s["esfuerzo"]) for s in solicitudes]
        self.activos = [j for j in range(self.m) if self.c[j] > 0]
        comp = [set(f["competencias"]) for f in funcionarios]
        # dominio[i]: funcionarios activos habilitados para la temática de la solicitud i
        self.dominio = [[j for j in self.activos if s["tematica"] in comp[j]]
                        for s in solicitudes]

    @classmethod
    def desde_dict(cls, d):
        funcionarios, solicitudes = _validar_instancia(d)
        return cls(funcionarios, solicitudes)

    def a_dict(self):
        return {"funcionarios": [dict(f) for f in self.funcionarios],
                "solicitudes": [dict(s) for s in self.solicitudes]}


# ---------------------------------------------------------------------------
# Evaluación
# ---------------------------------------------------------------------------

def cargas_nuevas(inst, X):
    a = [0.0] * inst.m
    for i, j in enumerate(X):
        a[j] += inst.e[i]
    return a


def evaluar(inst, X):
    """Evalúa un reparto X (X[i] = índice del funcionario de la solicitud i).

    Devuelve (clave, J, max_u, sigma_u, exceso, a). La clave ordena los repartos:
    (0, J) si es factible y (1, exceso) si no; menor es mejor.
    """
    a = cargas_nuevas(inst, X)
    exceso = 0.0
    for j in range(inst.m):
        d = a[j] - inst.r[j]
        if d > EPS:
            exceso += d
    u = [(inst.h[j] + a[j]) / inst.c[j] for j in inst.activos]
    if u:
        media = sum(u) / len(u)
        sigma = math.sqrt(sum((x - media) ** 2 for x in u) / len(u))
        maxu = max(u)
    else:
        sigma = maxu = 0.0
    J = PESO_MAX * maxu + PESO_SIGMA * sigma
    clave = (0, J) if exceso == 0.0 else (1, exceso)
    return clave, J, maxu, sigma, exceso, a


def sobrecarga_previa_total(inst):
    """Horas pendientes por encima de la capacidad, ANTES de asignar nada."""
    return sum(max(0.0, inst.h[j] - inst.c[j]) for j in range(inst.m))


def advertencias_instancia(inst):
    adv = []
    for j in range(inst.m):
        fid = inst.ids_f[j]
        if inst.c[j] <= 0:
            adv.append("%s tiene capacidad 0: no recibe nuevas solicitudes y no entra en el cálculo de J." % fid)
        elif inst.h[j] > inst.c[j]:
            adv.append("%s ya tenía sobrecarga previa (pendiente %.1f > capacidad %.1f): "
                       "no recibe nuevas solicitudes." % (fid, inst.h[j], inst.c[j]))
        elif inst.r[j] <= 0:
            adv.append("%s no tiene capacidad residual: no recibe nuevas solicitudes." % fid)
    return adv


def diagnosticar_infactibilidad(inst):
    """Condiciones NECESARIAS incumplidas (cada una prueba que no hay reparto válido).

    Lista vacía NO prueba factibilidad: solo significa que estas pruebas simples no
    descartan el caso (puede haber infactibilidad por empaquetado).
    """
    razones = []
    for i in range(inst.n):
        if not inst.dominio[i]:
            razones.append("La solicitud %s (temática %s) no tiene ningún funcionario activo competente."
                           % (inst.ids_s[i], inst.solicitudes[i]["tematica"]))
    if razones:
        return razones
    for i in range(inst.n):
        mayor = max(inst.r[j] for j in inst.dominio[i])
        if inst.e[i] > mayor + EPS:
            razones.append("La solicitud %s requiere %.1f h y la mayor capacidad residual entre "
                           "sus funcionarios habilitados es %.1f h." % (inst.ids_s[i], inst.e[i], mayor))
    por_tema = {}
    for i in range(inst.n):
        por_tema.setdefault(inst.solicitudes[i]["tematica"], []).append(i)
    for tema in sorted(por_tema):
        idxs = por_tema[tema]
        demanda = sum(inst.e[i] for i in idxs)
        capacidad = sum(inst.r[j] for j in inst.dominio[idxs[0]])
        if demanda > capacidad + EPS:
            razones.append("La temática %s demanda %.1f h y sus funcionarios habilitados solo tienen "
                           "%.1f h de capacidad residual." % (tema, demanda, capacidad))
    total = sum(inst.e)
    cap_total = sum(inst.r[j] for j in inst.activos)
    if total > cap_total + EPS:
        razones.append("La demanda total (%.1f h) supera la capacidad residual total (%.1f h)."
                       % (total, cap_total))
    return razones


# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------

def _r6(x):
    return None if x is None else round(x, 6)


def _cargas(inst, a):
    out = []
    for j in range(inst.m):
        activo = inst.c[j] > 0
        out.append({
            "id": inst.ids_f[j],
            "activo": activo,
            "capacidad": inst.c[j],
            "pendiente": inst.h[j],
            "residual": inst.r[j],
            "nueva": _r6(a[j]),
            "ocupacion": _r6((inst.h[j] + a[j]) / inst.c[j]) if activo else None,
        })
    return out


def _colas(inst, X):
    orden = {p: k for k, p in enumerate(PRIORIDADES)}
    colas = {fid: [] for fid in inst.ids_f}
    for i, j in enumerate(X):
        colas[inst.ids_f[j]].append(i)
    for fid in colas:
        colas[fid].sort(key=lambda i: (orden[inst.solicitudes[i]["prioridad"]], inst.ids_s[i]))
        colas[fid] = [inst.ids_s[i] for i in colas[fid]]
    return colas


def construir_resultado(inst, algoritmo, X, params, historial, evaluaciones, t0, reparaciones=0):
    """Resultado uniforme para el AG y las referencias.

    Estados: 'factible', 'sin_solucion_encontrada' (la búsqueda no halló un reparto
    válido; NO prueba imposibilidad) o 'infactible_demostrada' (una condición necesaria
    falla). Un reparto no válido nunca se presenta como asignación.
    """
    razones = diagnosticar_infactibilidad(inst)
    res = {
        "algoritmo": algoritmo,
        "semilla": (params or {}).get("semilla"),
        "advertencias": advertencias_instancia(inst),
        "sobrecarga_previa": _r6(sobrecarga_previa_total(inst)),
        "evaluaciones": evaluaciones,
        "reparaciones": reparaciones,
        "tiempo_s": round(time.perf_counter() - t0, 4),
        "historial": historial or [],
        "asignacion": None, "mejor_intento": None, "colas": None,
        "J": None, "max_u": None, "sigma_u": None, "max_u_receptores": None,
        "exceso": None, "razones": [],
    }
    if razones:
        res.update(estado="infactible_demostrada", razones=razones,
                   cargas=_cargas(inst, [0.0] * inst.m))
        return res
    clave, J, maxu, sigma, exceso, a = evaluar(inst, X)
    asign = {inst.ids_s[i]: inst.ids_f[X[i]] for i in range(inst.n)}
    res["cargas"] = _cargas(inst, a)
    if exceso == 0.0:
        receptores = [(inst.h[j] + a[j]) / inst.c[j] for j in inst.activos if a[j] > 0]
        res.update(estado="factible", asignacion=asign, colas=_colas(inst, X),
                   J=_r6(J), max_u=_r6(maxu), sigma_u=_r6(sigma), exceso=0.0,
                   max_u_receptores=_r6(max(receptores)) if receptores else None)
    else:
        res.update(estado="sin_solucion_encontrada", exceso=_r6(exceso),
                   mejor_intento={"asignacion": asign, "exceso": _r6(exceso),
                                  "valido": False})
    return res
