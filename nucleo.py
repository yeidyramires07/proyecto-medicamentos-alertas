import os
import time
import hashlib
from datetime import datetime
import pymysql
from enviar_telegram import enviar_telegram

ROLES_DESTINO = ("Comprador", "EPS", "Farmacia o distribuidor")
PREFIJOS = {"Comprador": "Aviso para comprador", "EPS": "Aviso para EPS", "Farmacia o distribuidor": "Aviso para farmacia o distribuidor"}

def conectar():
    return pymysql.connect(host=os.environ["MYSQL_HOST"], port=int(os.environ["MYSQL_PORT"]), user=os.environ["MYSQL_USER"], password=os.environ["MYSQL_PASSWORD"], database=os.environ["MYSQL_DB"], ssl={"ca": os.environ["MYSQL_CA"]}, charset="utf8mb4", connect_timeout=10)

def consultar(sql, params=()):
    conexion = conectar()
    cur = conexion.cursor()
    cur.execute(sql, params)
    columnas = [c[0] for c in cur.description]
    filas = [dict(zip(columnas, f)) for f in cur.fetchall()]
    conexion.close()
    return filas

def ejecutar(sql, params=()):
    conexion = conectar()
    cur = conexion.cursor()
    cur.execute(sql, params)
    nuevo_id = cur.lastrowid
    conexion.commit()
    conexion.close()
    return nuevo_id

def cargar_contratos():
    filas = consultar("SELECT c.id_contrato, e.nombre AS nombre_entidad, d.nombre AS departamento, k.nombre AS categoria, c.valor_contrato AS valor_del_contrato, c.saldo_pendiente, c.nivel_alerta, c.estado_contrato FROM contrato c JOIN entidad e ON c.id_entidad = e.id_entidad JOIN departamento d ON e.id_departamento = d.id_departamento JOIN categoria k ON c.id_categoria = k.id_categoria")
    for f in filas:
        f["valor_del_contrato"] = float(f["valor_del_contrato"])
        f["saldo_pendiente"] = float(f["saldo_pendiente"] or 0)
    return filas

def cargar_riesgo():
    riesgo = {}
    if os.path.exists("riesgo_contratos.csv"):
        import csv
        with open("riesgo_contratos.csv", encoding="utf-8-sig") as f:
            for fila in csv.DictReader(f):
                riesgo[fila["id_contrato"]] = (float(fila["puntaje_riesgo"]), fila["nivel_riesgo"])
    return riesgo

def destinatarios(rol=None):
    sql = "SELECT u.login, u.nombre, r.nombre AS rol, d.nombre AS departamento, u.telegram_chat_id AS chat_id FROM usuario u JOIN rol r ON u.id_rol = r.id_rol LEFT JOIN departamento d ON u.id_departamento = d.id_departamento WHERE u.activo = TRUE AND u.telegram_chat_id IS NOT NULL AND u.telegram_chat_id <> '' AND r.nombre IN ('Comprador', 'EPS', 'Farmacia o distribuidor')"
    params = ()
    if rol:
        sql += " AND r.nombre = %s"
        params = (rol,)
    sql += " ORDER BY u.id_usuario"
    return consultar(sql, params)

def ya_enviados(nombre):
    filas = consultar("SELECT DISTINCT id_contrato FROM alerta_enviada WHERE destinatario = %s AND estado = 'enviado' AND id_contrato IS NOT NULL", (nombre,))
    return set(f["id_contrato"] for f in filas)

def elegir_contratos(dest, contratos, cantidad, excluir=(), riesgo=None):
    riesgo = riesgo or {}
    candidatos = []
    for c in contratos:
        if c["id_contrato"] in excluir:
            continue
        if dest["departamento"] and c["departamento"] != dest["departamento"]:
            continue
        r = riesgo.get(c["id_contrato"])
        if c["nivel_alerta"] == "Alta" or (r is not None and r[1] == "Alto"):
            candidatos.append(c)
    candidatos.sort(key=lambda c: (riesgo.get(c["id_contrato"], (0, ""))[0], c["saldo_pendiente"]), reverse=True)
    return candidatos[:cantidad]

def armar_mensaje(rol, c, riesgo=None):
    texto = PREFIJOS[rol] + " | " + c["nivel_alerta"] + ": " + c["nombre_entidad"].title() + " (" + c["departamento"] + ") - contrato de " + c["categoria"].lower() + " por $" + str(round(c["valor_del_contrato"] / 1e6, 1)) + " millones, saldo pendiente $" + str(round(c["saldo_pendiente"] / 1e6, 1)) + " millones."
    r = (riesgo or {}).get(c["id_contrato"])
    if r is not None:
        texto += " Riesgo IA: " + str(int(round(r[0]))) + "/100 (" + r[1] + ")."
    return texto

def calcular_hash_alerta(anterior, fecha_texto, remitente, destinatario, id_contrato, estado, mensaje):
    base = "|".join([str(anterior), str(fecha_texto), str(remitente), str(destinatario), str(id_contrato), str(estado), str(mensaje)])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

def registrar_alertas(registros):
    try:
        conexion = conectar()
        cur = conexion.cursor()
        cur.execute("SELECT hash_actual FROM alerta_enviada ORDER BY id_alerta DESC LIMIT 1 FOR UPDATE")
        fila = cur.fetchone()
        anterior = fila[0] if fila and fila[0] else "0" * 64
        for r in registros:
            fecha_texto = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            h = calcular_hash_alerta(anterior, fecha_texto, r["remitente"], r["destinatario"], r["id_contrato"], r["estado"], r["mensaje"])
            cur.execute("INSERT INTO alerta_enviada (id_contrato, estado, hash_anterior, hash_actual, remitente, destinatario, rol_destino, fecha_texto, mensaje) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (r["id_contrato"], r["estado"], anterior, h, r["remitente"], r["destinatario"], r["rol_destino"], fecha_texto, r["mensaje"]))
            anterior = h
        conexion.commit()
        conexion.close()
        return True
    except Exception:
        return False

def verificar_cadena():
    filas = consultar("SELECT id_alerta, hash_anterior, hash_actual, fecha_texto, remitente, destinatario, id_contrato, estado, mensaje FROM alerta_enviada ORDER BY id_alerta")
    anterior = "0" * 64
    for f in filas:
        if f["hash_anterior"] != anterior:
            return False, f["id_alerta"], "se rompio el enlace con el registro anterior (falta o se cambio un registro)"
        if calcular_hash_alerta(f["hash_anterior"], f["fecha_texto"], f["remitente"], f["destinatario"], f["id_contrato"], f["estado"], f["mensaje"]) != f["hash_actual"]:
            return False, f["id_alerta"], "el contenido del registro fue alterado"
        anterior = f["hash_actual"]
    return True, len(filas), anterior

def leer_auditoria():
    return consultar("SELECT id_alerta, fecha_texto AS fecha, remitente, destinatario, rol_destino AS rol, id_contrato, estado, LEFT(hash_actual, 12) AS huella FROM alerta_enviada ORDER BY id_alerta DESC LIMIT 100")

def enviar_lote(rol, cantidad, remitente, evitar_repetidos=True):
    contratos = cargar_contratos()
    riesgo = cargar_riesgo()
    resumen = []
    registros = []
    for dest in destinatarios(rol):
        excluir = ya_enviados(dest["nombre"]) if evitar_repetidos else set()
        elegidos = elegir_contratos(dest, contratos, cantidad, excluir, riesgo)
        enviados = 0
        errores = 0
        for c in elegidos:
            texto = "Hola " + dest["nombre"] + ". " + armar_mensaje(dest["rol"], c, riesgo)
            try:
                resp = enviar_telegram(str(dest["chat_id"]), texto)
                estado = "enviado" if resp.get("ok") else "error"
            except Exception:
                estado = "error"
            registros.append({"remitente": remitente, "destinatario": dest["nombre"], "rol_destino": dest["rol"], "id_contrato": c["id_contrato"], "estado": estado, "mensaje": texto})
            if estado == "enviado":
                enviados += 1
            else:
                errores += 1
            time.sleep(0.4)
        resumen.append({"destinatario": dest["nombre"], "rol": dest["rol"], "departamento": dest["departamento"] or "Todos", "contratos_elegidos": len(elegidos), "enviados": enviados, "errores": errores})
    registrado = registrar_alertas(registros) if registros else True
    return resumen, registrado

def crear_solicitud(tipo, login, nombre, rol, departamento, categoria, descripcion, cantidad, precio, urgencia):
    fila = consultar("SELECT id_departamento FROM departamento WHERE nombre = %s", (departamento,))
    id_dep = fila[0]["id_departamento"] if fila else None
    fecha_texto = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return ejecutar("INSERT INTO solicitud (tipo, publicado_por, nombre_publicador, rol, id_departamento, categoria, descripcion, cantidad, precio_unitario, urgencia, estado, fecha_texto) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'abierta', %s)", (tipo, login, nombre, rol, id_dep, categoria, descripcion, cantidad, precio, urgencia, fecha_texto))

def listar_solicitudes(tipo, departamento=None):
    sql = "SELECT s.id_solicitud, s.fecha_texto AS fecha, s.nombre_publicador AS publicado_por, s.publicado_por AS login, s.rol, d.nombre AS departamento, s.categoria, s.descripcion, s.cantidad, s.precio_unitario, s.urgencia FROM solicitud s LEFT JOIN departamento d ON s.id_departamento = d.id_departamento WHERE s.tipo = %s AND s.estado = 'abierta'"
    params = [tipo]
    if departamento:
        sql += " AND d.nombre = %s"
        params.append(departamento)
    sql += " ORDER BY s.id_solicitud DESC LIMIT 50"
    filas = consultar(sql, tuple(params))
    for f in filas:
        if f["precio_unitario"] is not None:
            f["precio_unitario"] = float(f["precio_unitario"])
    return filas

def cerrar_solicitud(id_solicitud):
    ejecutar("UPDATE solicitud SET estado = 'cerrada' WHERE id_solicitud = %s", (id_solicitud,))

def mensaje_solicitud(tipo, nombre, departamento, categoria, descripcion, cantidad, precio, urgencia):
    if tipo == "necesidad":
        return "NECESIDAD (urgencia " + str(urgencia) + ") | " + nombre + " (" + departamento + ") necesita " + str(cantidad) + " unidades de " + categoria.lower() + ": " + descripcion + "."
    return "DISPONIBILIDAD | " + nombre + " (" + departamento + ") ofrece " + str(cantidad) + " unidades de " + categoria.lower() + ": " + descripcion + " a $" + str(int(precio or 0)) + " c/u."

def notificar_solicitud(tipo, login, nombre, departamento, categoria, descripcion, cantidad, precio, urgencia):
    roles = ("Farmacia o distribuidor", "EPS") if tipo == "necesidad" else ("Comprador", "EPS")
    texto_base = mensaje_solicitud(tipo, nombre, departamento, categoria, descripcion, cantidad, precio, urgencia)
    resumen = []
    registros = []
    for dest in destinatarios():
        if dest["rol"] not in roles or dest["login"] == login:
            continue
        if dest["departamento"] and dest["departamento"] != departamento:
            continue
        texto = "Hola " + dest["nombre"] + ". " + texto_base
        try:
            resp = enviar_telegram(str(dest["chat_id"]), texto)
            estado = "enviado" if resp.get("ok") else "error"
        except Exception:
            estado = "error"
        registros.append({"remitente": login, "destinatario": dest["nombre"], "rol_destino": dest["rol"], "id_contrato": None, "estado": estado, "mensaje": texto})
        resumen.append({"destinatario": dest["nombre"], "rol": dest["rol"], "estado": estado})
        time.sleep(0.4)
    registrado = registrar_alertas(registros) if registros else True
    return resumen, registrado