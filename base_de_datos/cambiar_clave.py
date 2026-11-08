import os
import hashlib
import hmac
import getpass
import pymysql

conexion = pymysql.connect(host=os.environ["MYSQL_HOST"], port=int(os.environ["MYSQL_PORT"]), user=os.environ["MYSQL_USER"], password=os.environ["MYSQL_PASSWORD"], database=os.environ["MYSQL_DB"], ssl={"ca": os.environ["MYSQL_CA"]}, charset="utf8mb4")
cur = conexion.cursor()
print("Conexion exitosa")

cur.execute("SELECT u.login, u.nombre, u.password_hash, r.nombre FROM usuario u JOIN rol r ON u.id_rol = r.id_rol ORDER BY u.id_usuario")
usuarios = cur.fetchall()
print("")
print("Usuarios en la base:")
for u in usuarios:
    print(" ", u[0], "|", u[1], "|", u[3])

def calcular_hash(clave):
    sal = os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), bytes.fromhex(sal), 200000).hex()
    return "pbkdf2_sha256$200000$" + sal + "$" + h

def coincide(clave, guardado):
    try:
        esquema, iteraciones, sal, h = guardado.split("$")
        calculado = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), bytes.fromhex(sal), int(iteraciones)).hex()
        return hmac.compare_digest(calculado, h)
    except Exception:
        return False

while True:
    print("")
    login = input("Usuario al que le vas a cambiar la contrasena (Enter para terminar): ").strip().lower()
    if login == "":
        break
    if login not in [u[0] for u in usuarios]:
        print("Ese usuario no existe.")
        continue
    clave = getpass.getpass("Nueva contrasena de al menos 8 caracteres (no se ve al escribir): ")
    clave2 = getpass.getpass("Repite la nueva contrasena: ")
    if len(clave) < 8 or clave != clave2:
        print("La contrasena es muy corta o no coincide. No se cambio nada.")
        continue
    repetida = [u[0] for u in usuarios if u[0] != login and coincide(clave, u[2])]
    if repetida:
        print("Esa contrasena ya la usa otra cuenta. Elige una distinta. No se cambio nada.")
        continue
    nuevo = calcular_hash(clave)
    cur.execute("UPDATE usuario SET password_hash = %s WHERE login = %s", (nuevo, login))
    conexion.commit()
    usuarios = [(u[0], u[1], nuevo if u[0] == login else u[2], u[3]) for u in usuarios]
    print("Contrasena actualizada para", login)

print("Listo")
conexion.close()