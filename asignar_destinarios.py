import os
import pymysql

conexion = pymysql.connect(host=os.environ["MYSQL_HOST"], port=int(os.environ["MYSQL_PORT"]), user=os.environ["MYSQL_USER"], password=os.environ["MYSQL_PASSWORD"], database=os.environ["MYSQL_DB"], ssl={"ca": os.environ["MYSQL_CA"]}, charset="utf8mb4")
cur = conexion.cursor()
print("Conexion exitosa")

cur.execute("SELECT id_departamento, nombre FROM departamento ORDER BY nombre")
deps = cur.fetchall()

def mostrar():
    cur.execute("SELECT u.login, u.nombre, r.nombre, d.nombre, u.telegram_chat_id FROM usuario u JOIN rol r ON u.id_rol = r.id_rol LEFT JOIN departamento d ON u.id_departamento = d.id_departamento ORDER BY u.id_usuario")
    print("")
    print("usuario | nombre | rol | departamento | tiene chat_id")
    for f in cur.fetchall():
        print(" ", f[0], "|", f[1], "|", f[2], "|", f[3] if f[3] else "Todos", "|", "si" if f[4] else "no")

mostrar()
while True:
    print("")
    login = input("Usuario a modificar (Enter para terminar): ").strip().lower()
    if login == "":
        break
    cur.execute("SELECT id_usuario FROM usuario WHERE login = %s", (login,))
    fila = cur.fetchone()
    if fila is None:
        print("Ese usuario no existe.")
        continue
    chat = input("chat_id de Telegram (Enter para no cambiarlo, - para quitarlo): ").strip()
    if chat == "-":
        cur.execute("UPDATE usuario SET telegram_chat_id = NULL WHERE id_usuario = %s", (fila[0],))
    elif chat != "":
        cur.execute("UPDATE usuario SET telegram_chat_id = %s WHERE id_usuario = %s", (chat, fila[0]))
    print("Departamentos:")
    for i, dp in enumerate(deps, start=1):
        print(" ", i, "-", dp[1])
    entrada = input("Numero del departamento (Enter para no cambiarlo, 0 para dejarlo en Todos): ").strip()
    if entrada == "0":
        cur.execute("UPDATE usuario SET id_departamento = NULL WHERE id_usuario = %s", (fila[0],))
    elif entrada != "":
        try:
            cur.execute("UPDATE usuario SET id_departamento = %s WHERE id_usuario = %s", (deps[int(entrada) - 1][0], fila[0]))
        except Exception:
            print("Departamento no valido. No se cambio el departamento.")
    conexion.commit()
    print("Usuario actualizado:", login)

mostrar()
conexion.close()