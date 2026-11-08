# spark_resumen.py
# Computacion Distribuida: aqui se usa Apache Spark.
#
# Spark reparte el trabajo entre varios "nucleos" (en tu computador, uno por cada nucleo).
# El programa hace lo mismo que filtrar_paralelo.py (buscar los contratos de medicamentos),
# pero con Spark, y cuenta cuantos contratos hay por departamento.
# Lo corremos con 1, 2 y 4 nucleos para ver como cambia el tiempo.
#
# Se ejecuta desde la carpeta principal:  python procesamiento\spark_resumen.py
# (Necesita Java instalado. Tarda unos minutos.)

import os
import sys
import time
import pandas as pd

# Le decimos a Spark que use el mismo Python de este proyecto.
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Las mismas palabras que en reglas.py
PALABRAS_SI = ["medicament", "farmaco", "farmaceutic", "suministro de insumos",
               "dispositivos medicos", "material medico", "insumos medico", "vacuna", "reactivo"]
PALABRAS_NO = ["regente", "quimico", "prestar servicios", "prestacion de servicios",
               "apoyo", "profesional", "auxiliar", "tecnologo", "tecnologa",
               "direccion de medicamentos", "acompanamiento juridico"]


def contar_con_spark(nucleos):
    # Abrimos Spark usando 'nucleos' nucleos.
    spark = SparkSession.builder.master("local[" + str(nucleos) + "]").appName("contratos").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    inicio = time.time()

    # Leemos el CSV de 100.000 contratos.
    datos = spark.read.csv("datos_limpios.csv", header=True, inferSchema=True, multiLine=True, escape='"')

    # Texto en minuscula y sin tildes (los \u00e1 son las letras con tilde y la n con tilde).
    texto = F.translate(F.lower(F.col("objeto_del_contrato")), "\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1", "aeioun")

    # Condicion: tiene alguna palabra de PALABRAS_SI ...
    tiene_si = F.lit(False)
    for palabra in PALABRAS_SI:
        tiene_si = tiene_si | texto.contains(palabra)

    # ... y no tiene ninguna de PALABRAS_NO.
    tiene_no = F.lit(False)
    for palabra in PALABRAS_NO:
        tiene_no = tiene_no | texto.contains(palabra)

    medicamentos = datos.filter(tiene_si & (~tiene_no))

    # Contamos contratos por departamento.
    por_departamento = medicamentos.groupBy("departamento").count().orderBy(F.desc("count"))
    filas = por_departamento.collect()

    tiempo = time.time() - inicio
    total = 0
    for fila in filas:
        total = total + fila["count"]

    spark.stop()
    return tiempo, total, filas


if __name__ == "__main__":
    print("Calentando Spark (esta primera vuelta no se cuenta)...")
    contar_con_spark(1)

    tiempos = {}
    for nucleos in [1, 2, 4]:
        tiempo, total, filas = contar_con_spark(nucleos)
        tiempos[nucleos] = tiempo
        print("Con %d nucleo(s): %.2f segundos | contratos de medicamentos: %d" % (nucleos, tiempo, total))

    # Anotamos las mediciones para guardarlas: la app las muestra en la pestana Rendimiento.
    mediciones = [{"nucleos": 1, "tiempo_segundos": round(tiempos[1], 2), "speedup": 1.0, "eficiencia": 1.0}]
    for nucleos in [2, 4]:
        speedup = tiempos[1] / tiempos[nucleos]
        eficiencia = speedup / nucleos
        print("Con %d nucleos: speedup %.2f | eficiencia %.2f" % (nucleos, speedup, eficiencia))
        mediciones.append({"nucleos": nucleos, "tiempo_segundos": round(tiempos[nucleos], 2), "speedup": round(speedup, 2), "eficiencia": round(eficiencia, 2)})
    pd.DataFrame(mediciones).to_csv("rendimiento_spark.csv", index=False)

    print("Los 5 departamentos con mas contratos de medicamentos:")
    for fila in filas[:5]:
        print(" ", fila["departamento"], fila["count"])
