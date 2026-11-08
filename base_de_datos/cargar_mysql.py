import os
import pymysql
import pandas as pd

conexion = pymysql.connect(host=os.environ["MYSQL_HOST"], port=int(os.environ["MYSQL_PORT"]), user=os.environ["MYSQL_USER"], password=os.environ["MYSQL_PASSWORD"], database=os.environ["MYSQL_DB"], ssl={"ca": os.environ["MYSQL_CA"]}, charset="utf8mb4")
cur = conexion.cursor()
print("Conexion exitosa")

cur.execute("SHOW TABLES LIKE 'contrato'")
if cur.fetchone():
    print("La base ya tiene las tablas. No se modifico nada.")
    conexion.close()
    raise SystemExit

sql = open("bd/esquema_mysql.sql", encoding="utf-8").read()
for sentencia in sql.split(";"):
    if sentencia.strip():
        cur.execute(sentencia)
print("Tablas creadas")

for tabla in ["departamento", "categoria", "entidad", "contrato"]:
    d = pd.read_csv("bd/" + tabla + ".csv", encoding="utf-8")
    d = d.astype(object).where(d.notna(), None)
    filas = [tuple(f) for f in d.itertuples(index=False, name=None)]
    columnas = ", ".join(d.columns)
    marcas = ", ".join(["%s"] * len(d.columns))
    cur.executemany("INSERT INTO " + tabla + " (" + columnas + ") VALUES (" + marcas + ")", filas)
    print(tabla + ":", len(filas), "filas cargadas")

cur.executemany("INSERT INTO rol (nombre) VALUES (%s)", [("Comprador",), ("EPS",), ("Farmacia o distribuidor",), ("Auditor",)])
conexion.commit()

cur.execute("SELECT d.nombre, COUNT(*) AS contratos FROM contrato c JOIN entidad e ON c.id_entidad = e.id_entidad JOIN departamento d ON e.id_departamento = d.id_departamento GROUP BY d.nombre ORDER BY contratos DESC LIMIT 3")
print("Top 3 departamentos:", cur.fetchall())
conexion.close()