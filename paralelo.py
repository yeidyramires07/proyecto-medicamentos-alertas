import pandas as pd
import time
import re
import unicodedata
from multiprocessing import Pool, cpu_count

POS = re.compile(r"medicament|farmaco|farmaceutic|suministro de insumos|dispositivos medicos|material medico|insumos medico|vacuna|reactivo")
NEG = re.compile(r"regente|quimico|prestar servicios|prestacion de servicios|apoyo|profesional|auxiliar|tecnolog")

def normalizar(texto):
    t = unicodedata.normalize("NFKD", str(texto).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", t)

def es_medicamento(texto):
    t = normalizar(texto)
    return bool(POS.search(t)) and not NEG.search(t)

def procesar(trozo):
    marca = trozo["objeto_del_contrato"].apply(es_medicamento)
    return trozo[marca]

if __name__ == "__main__":
    df = pd.read_csv("datos_limpios.csv", encoding="utf-8-sig", low_memory=False)
    print("Nucleos de tu computador:", cpu_count())
    print("Filas:", len(df))

    t0 = time.time()
    res_serial = procesar(df)
    t_serial = time.time() - t0
    print("Serial: %.2f s, contratos: %d" % (t_serial, len(res_serial)))

    for n in [2, 4, 8]:
        paso = -(-len(df) // n)
        trozos = [df.iloc[i:i + paso] for i in range(0, len(df), paso)]
        t0 = time.time()
        with Pool(n) as p:
            partes = p.map(procesar, trozos)
        t = time.time() - t0
        total = sum(len(x) for x in partes)
        sp = t_serial / t
        print("Procesos %d: %.2f s, speedup %.2f, eficiencia %.2f, contratos %d" % (n, t, sp, sp / n, total))