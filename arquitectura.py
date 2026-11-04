import os
import time
import numpy as np
import pandas as pd

filas = []

def agregar(seccion, metrica, valor):
    filas.append({"seccion": seccion, "metrica": metrica, "valor": valor})

agregar("Equipo de pruebas", "Nucleos logicos de la CPU", os.cpu_count())

medidas = {"Multiprocessing": (8.39, {2: 6.66, 4: 6.22, 8: 9.42}), "Spark": (9.19, {2: 6.35, 4: 6.53})}
for nombre, (serial, tiempos) in medidas.items():
    fracciones = []
    for p, t in tiempos.items():
        s = serial / t
        agregar("Ley de Amdahl: " + nombre, "Speedup con " + str(p) + " procesos o nucleos", round(s, 2))
        if p <= 4 and s > 1:
            fracciones.append((1 / s - 1 / p) / (1 - 1 / p))
    f = float(np.mean(fracciones))
    agregar("Ley de Amdahl: " + nombre, "Fraccion serial estimada (p=2 y p=4)", round(f, 2))
    agregar("Ley de Amdahl: " + nombre, "Speedup maximo teorico (1 / fraccion serial)", round(1 / f, 2))

def promedio_lectura(funcion, veces=3):
    tiempos = []
    for _ in range(veces):
        t0 = time.time()
        funcion()
        tiempos.append(time.time() - t0)
    return sum(tiempos) / len(tiempos)

df = pd.read_csv("datos_limpios.csv", encoding="utf-8-sig", low_memory=False)
agregar("Formato de archivo (100.000 contratos)", "CSV: tamano en disco (MB)", round(os.path.getsize("datos_limpios.csv") / 1e6, 1))
agregar("Formato de archivo (100.000 contratos)", "CSV: tiempo de lectura (s)", round(promedio_lectura(lambda: pd.read_csv("datos_limpios.csv", encoding="utf-8-sig", low_memory=False)), 2))
try:
    df.to_parquet("temporal_prueba.parquet")
    agregar("Formato de archivo (100.000 contratos)", "Parquet: tamano en disco (MB)", round(os.path.getsize("temporal_prueba.parquet") / 1e6, 1))
    agregar("Formato de archivo (100.000 contratos)", "Parquet: tiempo de lectura (s)", round(promedio_lectura(lambda: pd.read_parquet("temporal_prueba.parquet")), 2))
except Exception:
    agregar("Formato de archivo (100.000 contratos)", "Parquet", "no disponible (falta instalar pyarrow)")
if os.path.exists("temporal_prueba.parquet"):
    os.remove("temporal_prueba.parquet")

memoria_antes = df.memory_usage(deep=True).sum() / 1e6
optimizado = df.copy()
for columna in optimizado.columns:
    if (optimizado[columna].dtype == object or pd.api.types.is_string_dtype(optimizado[columna])) and optimizado[columna].nunique() / len(optimizado) < 0.5:
        optimizado[columna] = optimizado[columna].astype("category")
memoria_despues = optimizado.memory_usage(deep=True).sum() / 1e6
agregar("Memoria del DataFrame", "Antes de optimizar tipos (MB)", round(memoria_antes, 1))
agregar("Memoria del DataFrame", "Despues de usar tipo category (MB)", round(memoria_despues, 1))
agregar("Memoria del DataFrame", "Reduccion (%)", round(100 * (1 - memoria_despues / memoria_antes), 1))

valores = np.tile(df["valor_del_contrato"].dropna().to_numpy(dtype=float), 50)
lista = valores.tolist()
t0 = time.time()
total = 0.0
for v in lista:
    total += v
t_bucle = time.time() - t0
t0 = time.time()
total_np = valores.sum()
t_numpy = time.time() - t0
agregar("Vectorizacion y memoria contigua (" + str(len(valores)) + " valores)", "Suma con bucle de Python (s)", round(t_bucle, 3))
agregar("Vectorizacion y memoria contigua (" + str(len(valores)) + " valores)", "Suma con arreglo NumPy contiguo (s)", round(t_numpy, 4))
agregar("Vectorizacion y memoria contigua (" + str(len(valores)) + " valores)", "NumPy es mas rapido (veces)", round(t_bucle / max(t_numpy, 1e-9), 1))

resultado = pd.DataFrame(filas)
resultado["valor"] = resultado["valor"].astype(str)
resultado.to_csv("arquitectura_resultados.csv", index=False, encoding="utf-8")
print(resultado.to_string(index=False))
print("Listo: arquitectura_resultados.csv")