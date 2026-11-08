# filtrar_paralelo.py
# Computacion Paralela: aqui se usa multiprocessing.
#
# Idea: son 100.000 contratos. Revisar uno por uno tarda. Entonces:
#   1. Se hace la revision "en serie" (un solo proceso) y se mide el tiempo.
#   2. Se parte la lista en pedazos y cada proceso revisa un pedazo al mismo tiempo.
#   3. Se comparan los tiempos (speedup y eficiencia).
#   4. Con el resultado se guarda contratos_medicamentos.csv, que usa el resto del proyecto.
#
# Se ejecuta desde la carpeta principal:  python procesamiento\filtrar_paralelo.py

import time
import pandas as pd
from multiprocessing import Pool
from reglas import es_de_medicamentos, categoria_del_contrato


def revisar_pedazo(textos):
    # Recibe una lista de textos y devuelve una lista de True/False.
    resultados = []
    for texto in textos:
        resultados.append(es_de_medicamentos(texto))
    return resultados


def partir_en_pedazos(lista, cantidad):
    # Parte una lista en 'cantidad' pedazos casi iguales.
    tamano = len(lista) // cantidad + 1
    pedazos = []
    for inicio in range(0, len(lista), tamano):
        pedazos.append(lista[inicio:inicio + tamano])
    return pedazos


# Este "if" es obligatorio en Windows cuando se usa multiprocessing.
if __name__ == "__main__":
    datos = pd.read_csv("datos_limpios.csv", encoding="utf-8-sig", low_memory=False)
    textos = datos["objeto_del_contrato"].fillna("").tolist()
    print("Contratos a revisar:", len(textos))

    # 1) En serie: un solo proceso revisa todo.
    inicio = time.time()
    marcas_serie = revisar_pedazo(textos)
    tiempo_serie = time.time() - inicio
    print("En serie: %.2f segundos" % tiempo_serie)

    # Aqui vamos anotando las mediciones para guardarlas al final.
    mediciones = [{"procesos": 1, "tiempo_segundos": round(tiempo_serie, 2), "speedup": 1.0, "eficiencia": 1.0}]

    # 2) En paralelo: probamos con 2 y con 4 procesos.
    marcas_paralelo = []
    for procesos in [2, 4]:
        pedazos = partir_en_pedazos(textos, procesos)

        inicio = time.time()
        with Pool(procesos) as grupo:
            respuestas = grupo.map(revisar_pedazo, pedazos)
        tiempo = time.time() - inicio

        # Juntamos las respuestas de todos los procesos en una sola lista.
        marcas_paralelo = []
        for respuesta in respuestas:
            marcas_paralelo.extend(respuesta)

        speedup = tiempo_serie / tiempo
        eficiencia = speedup / procesos
        print("Con %d procesos: %.2f segundos | speedup %.2f | eficiencia %.2f" % (procesos, tiempo, speedup, eficiencia))
        mediciones.append({"procesos": procesos, "tiempo_segundos": round(tiempo, 2), "speedup": round(speedup, 2), "eficiencia": round(eficiencia, 2)})

    # 3) Comprobamos que serie y paralelo dan exactamente lo mismo.
    print("Resultados iguales:", marcas_serie == marcas_paralelo)

    # Guardamos las mediciones: la app las muestra en la pestana Rendimiento.
    pd.DataFrame(mediciones).to_csv("rendimiento_multiprocessing.csv", index=False)

    # 4) Guardamos solo los contratos de medicamentos.
    datos["es_medicamento"] = marcas_paralelo
    medicamentos = datos[datos["es_medicamento"] == True].copy()
    medicamentos = medicamentos.drop(columns=["es_medicamento"])

    # Quitamos valores absurdos (cero o mas de 100 mil millones).
    medicamentos = medicamentos[medicamentos["valor_del_contrato"] > 0]
    medicamentos = medicamentos[medicamentos["valor_del_contrato"] < 100000000000]

    # Le ponemos a cada contrato su categoria.
    categorias = []
    for texto in medicamentos["objeto_del_contrato"]:
        categorias.append(categoria_del_contrato(texto))
    medicamentos["categoria"] = categorias

    medicamentos.to_csv("contratos_medicamentos.csv", index=False, encoding="utf-8-sig")
    print("Contratos de medicamentos guardados:", len(medicamentos))
