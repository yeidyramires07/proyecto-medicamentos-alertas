import os
import pymysql

conexion = pymysql.connect(host=os.environ["MYSQL_HOST"], port=int(os.environ["MYSQL_PORT"]), user=os.environ["MYSQL_USER"], password=os.environ["MYSQL_PASSWORD"], database=os.environ["MYSQL_DB"], ssl={"ca": os.environ["MYSQL_CA"]}, charset="utf8mb4")
cur = conexion.cursor()
print("Conexion exitosa")

columnas = [
    ("remitente", "VARCHAR(50)"),
    ("destinatario", "VARCHAR(100)"),
    ("rol_destino", "VARCHAR(50)"),
    ("fecha_texto", "VARCHAR(19)"),
    ("mensaje", "TEXT"),
]
for nombre, tipo in columnas:
    cur.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'alerta_enviada' AND column_name = %s", (nombre,))
    if cur.fetchone()[0] == 0:
        cur.execute("ALTER TABLE alerta_enviada ADD COLUMN " + nombre + " " + tipo)
        print("Columna agregada:", nombre)
    else:
        print("Columna ya existe:", nombre)
conexion.commit()

cur.execute("SELECT COUNT(*) FROM alerta_enviada")
print("Registros actuales en la auditoria:", cur.fetchone()[0])
conexion.close()