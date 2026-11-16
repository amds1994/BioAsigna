"""Copia el motor y los escenarios a docs/ (la carpeta que publica GitHub Pages).

La web carga core/*.py por red y los ejecuta con Pyodide, así que el motor debe estar
dentro de la carpeta publicada. Ejecutar tras cambiar core/ o los escenarios:

    python build_web.py
    python -m http.server --directory docs 8000     # y abrir http://localhost:8000
"""
import os
import shutil

RAIZ = os.path.dirname(os.path.abspath(__file__))
destino = os.path.join(RAIZ, "docs", "core")
os.makedirs(destino, exist_ok=True)
for nombre in os.listdir(os.path.join(RAIZ, "core")):
    if nombre.endswith(".py"):
        shutil.copy2(os.path.join(RAIZ, "core", nombre), os.path.join(destino, nombre))
shutil.copy2(os.path.join(RAIZ, "data", "scenarios.json"), os.path.join(RAIZ, "docs", "scenarios.json"))
print("docs/ actualizado con core/*.py y scenarios.json")
