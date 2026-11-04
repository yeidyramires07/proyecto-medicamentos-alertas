import os
import pymysql

conexion = pymysql.connect(host=os.environ["MYSQL_HOST"], port=int(os.environ["MYSQL_PORT"]), user=os.environ["MYSQL_USER"], password=os.environ["MYSQL_PASSWORD"], database=os.environ["MYSQL_DB"], ssl={"ca": os.environ["MYSQL_CA"]}, charset="utf8mb4")
cur = conexion.cursor()
print("Conexion exitosa")

cur.execute("""CREATE TABLE IF NOT EXISTS solicitud (
    id_solicitud INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(15) NOT NULL CHECK (tipo IN ('necesidad', 'oferta')),
    publicado_por VARCHAR(50) NOT NULL,
    nombre_publicador VARCHAR(100) NOT NULL,
    rol VARCHAR(50) NOT NULL,
    id_departamento INT NULL,
    categoria VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario DECIMAL(18,2) NULL,
    urgencia VARCHAR(10) NULL,
    estado VARCHAR(10) NOT NULL DEFAULT 'abierta' CHECK (estado IN ('abierta', 'cerrada')),
    fecha_texto VARCHAR(19) NOT NULL,
    FOREIGN KEY (id_departamento) REFERENCES departamento(id_departamento)
)""")
conexion.commit()
print("Tabla solicitud lista")
conexion.close()