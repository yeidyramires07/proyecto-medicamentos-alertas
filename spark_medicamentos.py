import os
import sys
import time
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

POS = "medicament|farmaco|farmaceutic|suministro de insumos|dispositivos medicos|material medico|insumos medico|vacuna|reactivo"
NEG = "regente|quimico|prestar servicios|prestacion de servicios|apoyo|profesional|auxiliar|tecnolog"

def ejecutar(n):
    spark = SparkSession.builder.master("local[%d]" % n).appName("contratos").config("spark.ui.showConsoleProgress", "false").config("spark.sql.shuffle.partitions", "8").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    t0 = time.time()
    df = spark.read.csv("datos_limpios.csv", header=True, inferSchema=True, multiLine=True, escape='"')
    obj = F.translate(F.lower(F.col("objeto_del_contrato")), "\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1", "aeioun")
    med = df.filter(obj.rlike(POS) & ~obj.rlike(NEG))
    resumen = med.groupBy("departamento").agg(F.count("*").alias("contratos"), F.round(F.sum("valor_del_contrato") / 1e6, 1).alias("valor_millones")).orderBy(F.desc("contratos"))
    filas = resumen.collect()
    t = time.time() - t0
    total_med = sum(f["contratos"] for f in filas)
    spark.stop()
    return t, total_med, filas

if __name__ == "__main__":
    print("Calentando Spark...")
    ejecutar(1)
    tiempos = {}
    for n in [1, 2, 4]:
        t, total, filas = ejecutar(n)
        tiempos[n] = t
        print("Spark con %d nucleo(s): %.2f s, contratos de medicamentos: %d" % (n, t, total))
    for n in [2, 4]:
        sp = tiempos[1] / tiempos[n]
        print("Nucleos %d: speedup %.2f, eficiencia %.2f" % (n, sp, sp / n))
    print("Top departamentos:")
    for f in filas[:8]:
        print(f["departamento"], f["contratos"], f["valor_millones"])