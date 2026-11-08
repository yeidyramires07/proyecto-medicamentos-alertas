import os
import hashlib
import getpass
import pymysql

conexion = pymysql.connect(host=os.environ["MYSQL_HOST"], port=int(os.environ["MYSQL_PORT"]), user=os.environ["MYSQL_USER"], password=os.environ["MYSQL_PASSWORD"], database=os.environ["MYSQL_DB"], ssl={"ca": os.environ["MYSQL_CA"]}, charset="utf8mb4")
cur = conexion.cursor()
print("Conexion exitosa")

cur.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'usuario' AND column_name = 'login'")
if cur.fetchone()[0] == 0:
    cur.execute("ALTER TABLE usuario ADD COLUMN login VARCHAR(50) UNIQUE")
    print("Columna login agregada a la tabla usuario")

cur.execute("SELECT id_rol FROM rol WHERE nombre = %s", ("Administrador",))
if cur.fetchone() is None:
    cur.execute("INSERT INTO rol (nombre) VALUES (%s)", ("Administrador",))
    print("Rol Administrador creado")
conexion.commit()

cur.execute("SELECT id_rol, nombre FROM rol ORDER BY id_rol")
roles = cur.fetchall()
cur.execute("SELECT id_departamento, nombre FROM departamento ORDER BY nombre")
deps = cur.fetchall()

def calcular_hash(clave):
    sal = os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), bytes.fromhex(sal), 200000).hex()
    return "pbkdf2_sha256$200000$" + sal + "$" + h

while True:
    print("")
    nombre = input("Nombre completo: ").strip()
    login = input("Usuario para iniciar sesion (sin espacios, minusculas): ").strip().lower()
    print("Roles:")
    for i, r in enumerate(roles, start=1):
        print(" ", i, "-", r[1])
    try:
        id_rol = roles[int(input("Numero del rol: ")) - 1][0]
    except Exception:
        print("Rol no valido. Se cancela este usuario.")
        continue
    print("Departamentos:")
    for i, dp in enumerate(deps, start=1):
        print(" ", i, "-", dp[1])
    entrada = input("Numero del departamento (Enter si no aplica): ").strip()
    id_dep = None
    if entrada != "":
        try:
            id_dep = deps[int(entrada) - 1][0]
        except Exception:
            print("Departamento no valido. Se cancela este usuario.")
            continue
    chat = input("chat_id de Telegram (Enter si no tiene): ").strip()
    clave = getpass.getpass("Contrasena de al menos 8 caracteres (no se ve al escribir): ")
    clave2 = getpass.getpass("Repite la contrasena: ")
    if len(clave) < 8 or clave != clave2:
        print("La contrasena es muy corta o no coincide. Se cancela este usuario.")
        continue
    if nombre == "" or login == "" or " " in login:
        print("Nombre o usuario no validos. Se cancela este usuario.")
        continue
    cur.execute("SELECT id_usuario FROM usuario WHERE login = %s", (login,))
    if cur.fetchone() is not None:
        print("Ese usuario ya existe. Se cancela.")
        continue
    cur.execute("INSERT INTO usuario (nombre, login, id_rol, id_departamento, telegram_chat_id, password_hash) VALUES (%s, %s, %s, %s, %s, %s)", (nombre, login, id_rol, id_dep, chat if chat != "" else None, calcular_hash(clave)))
    conexion.commit()
    print("Usuario creado:", login)
    if input("Crear otro usuario? (s/n): ").strip().lower() != "s":
        break

cur.execute("SELECT u.login, u.nombre, r.nombre FROM usuario u JOIN rol r ON u.id_rol = r.id_rol ORDER BY u.id_usuario")
print("")
print("Usuarios en la base:")
for f in cur.fetchall():
    print(" ", f[0], "|", f[1], "|", f[2])
conexion.close()