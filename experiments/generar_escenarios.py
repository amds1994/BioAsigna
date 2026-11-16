"""Genera data/scenarios.json con escenarios SINTÉTICOS y reproducibles.

Todos los datos son ficticios. Las instancias aleatorias usan semillas fijas, de modo
que el archivo generado es siempre el mismo. Ejecutar desde la raíz del proyecto:

    python experiments/generar_escenarios.py
"""
import json
import os
import random

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def solicitudes_aleatorias(rng, n, temas, esfuerzos, pesos_tema=None):
    out = []
    for i in range(n):
        tema = rng.choices(temas, weights=pesos_tema)[0] if pesos_tema else rng.choice(temas)
        out.append({
            "id": "S%03d" % (i + 1),
            "tematica": tema,
            "esfuerzo": rng.choice(esfuerzos),
            "prioridad": rng.choices(["Alta", "Media", "Baja"], weights=[2, 5, 3])[0],
        })
    return out


def funcionarios(caps, pends, comps):
    return [{"id": "F%d" % (j + 1), "competencias": comps[j],
             "capacidad": caps[j], "pendiente": pends[j]} for j in range(len(caps))]


def construir():
    esf = [1, 1.5, 2, 2.5, 3, 3.5, 4, 5]
    escenarios = []

    # 1. Base 6x3. RECONSTRUCCIÓN del ejemplo manual de la Actividad 1: tiene totales
    # 6/5/4 h (desequilibrado) y 5/5/5 h (equilibrado). Los datos exactos del documento
    # original no se usan aquí: este es un ejemplo propio que reproduce esos totales.
    base = {
        "funcionarios": funcionarios([10, 10, 10], [0, 0, 0],
                                     [["T1", "T2"], ["T2", "T3"], ["T1", "T3"]]),
        "solicitudes": [
            {"id": "S001", "tematica": "T1", "esfuerzo": 3, "prioridad": "Alta"},
            {"id": "S002", "tematica": "T2", "esfuerzo": 2, "prioridad": "Media"},
            {"id": "S003", "tematica": "T3", "esfuerzo": 3, "prioridad": "Media"},
            {"id": "S004", "tematica": "T1", "esfuerzo": 2, "prioridad": "Baja"},
            {"id": "S005", "tematica": "T2", "esfuerzo": 2, "prioridad": "Alta"},
            {"id": "S006", "tematica": "T3", "esfuerzo": 3, "prioridad": "Baja"},
        ],
    }
    escenarios.append({
        "id": "base_6x3", "nombre": "Base: 6 solicitudes, 3 funcionarios",
        "descripcion": "Reconstrucción propia del ejemplo manual de la Actividad 1 (cargas 6/5/4 h "
                       "frente a 5/5/5 h). Existe un reparto perfectamente equilibrado.",
        "instancia": base})

    # 2. Carga moderada 20x5
    rng = random.Random(2026)
    moderada = {
        "funcionarios": funcionarios(
            [40, 40, 35, 45, 30], [10, 6, 12, 8, 4],
            [["T1", "T2"], ["T2", "T3"], ["T3", "T4"], ["T4", "T1"], ["T1", "T2", "T3", "T4"]]),
        "solicitudes": solicitudes_aleatorias(rng, 20, ["T1", "T2", "T3", "T4"], esf),
    }
    escenarios.append({
        "id": "carga_moderada_20x5", "nombre": "Carga moderada: 20 solicitudes, 5 funcionarios",
        "descripcion": "Capacidades y cargas pendientes distintas; un funcionario generalista.",
        "instancia": moderada})

    # 3. Heterogeneidad 30x6 con temáticas atendidas por muy pocas personas
    rng = random.Random(3030)
    heter = {
        "funcionarios": funcionarios(
            [60, 50, 40, 30, 24, 20], [20, 10, 15, 5, 18, 4],
            [["T1", "T2", "T3"], ["T2", "T4"], ["T3", "T5"], ["T1", "T5"], ["T4"], ["T2", "T5"]]),
        "solicitudes": solicitudes_aleatorias(rng, 30, ["T1", "T2", "T3", "T4", "T5"], esf,
                                              [3, 3, 3, 2, 2]),
    }
    escenarios.append({
        "id": "heterogeneidad_30x6", "nombre": "Heterogeneidad: 30 solicitudes, 6 funcionarios",
        "descripcion": "Capacidades muy distintas; T4 solo la atienden 2 personas y T5 solo 3.",
        "instancia": heter})

    # 4. Escala 150x12
    rng = random.Random(1500)
    temas6 = ["T1", "T2", "T3", "T4", "T5", "T6"]
    comps = []
    for j in range(12):
        c = [temas6[j % 6], temas6[(j + 1) % 6]]
        if j % 2 == 0:
            c.append(temas6[(j + 3) % 6])
        comps.append(c)
    caps = [rng.choice([40, 50, 60, 70, 80]) for _ in range(12)]
    pends = [rng.choice([0, 5, 10, 20, 30]) for _ in range(12)]
    escala = {"funcionarios": funcionarios(caps, pends, comps),
              "solicitudes": solicitudes_aleatorias(rng, 150, temas6, esf)}
    escenarios.append({
        "id": "escala_150x12", "nombre": "Escala: 150 solicitudes, 12 funcionarios",
        "descripcion": "Instancia grande, donde la diferencia entre algoritmos podría notarse.",
        "instancia": escala})

    # 5. Cambio de entorno: la carga moderada y tres cambios
    escenarios.append({
        "id": "cambio_entorno", "nombre": "Cambio de entorno (sobre la carga moderada)",
        "descripcion": "F2 se ausenta, F4 pierde 30 % de capacidad y llegan 3 solicitudes nuevas.",
        "instancia": moderada,
        "cambios": [
            {"tipo": "deshabilitar_funcionario", "funcionario": "F2"},
            {"tipo": "reducir_capacidad", "funcionario": "F4", "factor": 0.7},
            {"tipo": "agregar_solicitud", "solicitud": {"id": "S021", "tematica": "T2", "esfuerzo": 3, "prioridad": "Alta"}},
            {"tipo": "agregar_solicitud", "solicitud": {"id": "S022", "tematica": "T3", "esfuerzo": 2.5, "prioridad": "Media"}},
            {"tipo": "agregar_solicitud", "solicitud": {"id": "S023", "tematica": "T1", "esfuerzo": 4, "prioridad": "Baja"}},
        ]})

    # 6. Sobrecarga previa: F1 ya tiene más pendiente que capacidad
    escenarios.append({
        "id": "sobrecarga_previa", "nombre": "Sobrecarga previa",
        "descripcion": "F1 ya tiene 30 h pendientes con capacidad de 25 h: no recibe nada nuevo.",
        "instancia": {
            "funcionarios": funcionarios([25, 40, 40], [30, 10, 5],
                                         [["T1", "T2"], ["T1", "T2"], ["T1", "T2"]]),
            "solicitudes": [
                {"id": "S%03d" % (i + 1), "tematica": ["T1", "T2"][i % 2],
                 "esfuerzo": [2, 3, 1.5, 4, 2.5, 3.5, 1, 2][i], "prioridad": "Media"}
                for i in range(8)],
        }})

    # 7. Saturación: la demanda supera la capacidad (infactible demostrable)
    escenarios.append({
        "id": "saturacion", "nombre": "Saturación (infactible demostrable)",
        "descripcion": "La demanda total (40 h) supera la capacidad residual (30 h).",
        "instancia": {
            "funcionarios": funcionarios([10, 10, 10], [0, 0, 0],
                                         [["T1", "T2"], ["T1", "T2"], ["T1", "T2"]]),
            "solicitudes": [
                {"id": "S%03d" % (i + 1), "tematica": ["T1", "T2"][i % 2], "esfuerzo": 5,
                 "prioridad": "Media"} for i in range(8)],
        }})

    # 8. Sin competente
    escenarios.append({
        "id": "sin_competente", "nombre": "Solicitud sin funcionario competente",
        "descripcion": "La temática T9 no la atiende nadie: el estado debe decirlo.",
        "instancia": {
            "funcionarios": funcionarios([20, 20], [0, 0], [["T1"], ["T1", "T2"]]),
            "solicitudes": [
                {"id": "S001", "tematica": "T1", "esfuerzo": 2, "prioridad": "Media"},
                {"id": "S002", "tematica": "T9", "esfuerzo": 2, "prioridad": "Alta"},
            ],
        }})

    # 9. Empaquetado difícil: pasa las pruebas simples pero es infactible
    escenarios.append({
        "id": "empaquetado_dificil", "nombre": "Empaquetado imposible no detectado por pruebas simples",
        "descripcion": "3 solicitudes de 3 h y 2 funcionarios de 5 h: la suma cabe (9 de 10 h) pero "
                       "no cada pieza. El sistema no demuestra imposibilidad: informa que no encontró reparto.",
        "instancia": {
            "funcionarios": funcionarios([5, 5], [0, 0], [["T1"], ["T1"]]),
            "solicitudes": [{"id": "S%03d" % (i + 1), "tematica": "T1", "esfuerzo": 3,
                             "prioridad": "Media"} for i in range(3)],
        }})
    return escenarios


def main():
    destino = os.path.join(RAIZ, "data", "scenarios.json")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as fh:
        json.dump({"escenarios": construir()}, fh, ensure_ascii=False, indent=1)
    print("Escrito", destino)


if __name__ == "__main__":
    main()
