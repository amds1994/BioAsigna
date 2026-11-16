"""Construcción y reparación de repartos (compartido por el AG y las referencias).

Ningún bucle es no acotado: la construcción es una sola pasada y la reparación
tiene un número máximo de pasadas, de modo que nunca hay ciclos sin solución.
"""
from .model import EPS, cargas_nuevas


def construir(inst, rng, orden="aleatorio", p_voraz=0.5):
    """Reparto por una sola pasada. Cada gen se elige dentro de su dominio.

    Con probabilidad p_voraz elige, entre los funcionarios con cupo, el de menor
    ocupación resultante; si no, uno al azar con cupo. Si nadie tiene cupo, elige el
    de mayor holgura (menor exceso) y el reparto resultará infactible.
    """
    idx = list(range(inst.n))
    if orden == "esfuerzo":
        idx.sort(key=lambda i: -inst.e[i] + rng.random() * 0.5)
    else:
        rng.shuffle(idx)
    a = [0.0] * inst.m
    X = [0] * inst.n
    for i in idx:
        dom = inst.dominio[i]
        con_cupo = [j for j in dom if a[j] + inst.e[i] <= inst.r[j] + EPS]
        if con_cupo:
            if rng.random() < p_voraz:
                j = min(con_cupo, key=lambda k: ((inst.h[k] + a[k] + inst.e[i]) / inst.c[k], k))
            else:
                j = rng.choice(con_cupo)
        else:
            j = max(dom, key=lambda k: (inst.r[k] - a[k], -k))
        X[i] = j
        a[j] += inst.e[i]
    return X


def reparar(inst, X, rng, max_pasadas=3):
    """Mueve solicitudes de funcionarios excedidos a otros habilitados con holgura.

    Modifica X en lugar. Devuelve el número de movimientos. Acotada por max_pasadas.
    """
    a = cargas_nuevas(inst, X)
    movimientos = 0
    for _ in range(max_pasadas):
        excedidos = [j for j in range(inst.m) if a[j] > inst.r[j] + EPS]
        if not excedidos:
            break
        rng.shuffle(excedidos)
        movido = False
        for j in excedidos:
            propias = [i for i in range(inst.n) if X[i] == j]
            propias.sort(key=lambda i: -inst.e[i] + rng.random() * 0.01)
            for i in propias:
                if a[j] <= inst.r[j] + EPS:
                    break
                destinos = [k for k in inst.dominio[i]
                            if k != j and a[k] + inst.e[i] <= inst.r[k] + EPS]
                if destinos:
                    k = max(destinos, key=lambda d: (inst.r[d] - a[d], -d))
                    X[i] = k
                    a[j] -= inst.e[i]
                    a[k] += inst.e[i]
                    movimientos += 1
                    movido = True
        if not movido:
            break
    return movimientos
