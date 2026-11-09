import os
import time
import hashlib
import hmac

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pymysql
import streamlit as st

from enviar_telegram import enviar_telegram

st.set_page_config(page_title="Alertas de medicamentos", layout="wide")


# ----- Claves y base de datos -----

def leer_secreto(nombre):
    try:
        return str(st.secrets[nombre])
    except Exception:
        return os.environ.get(nombre)


token_telegram = leer_secreto("TELEGRAM_TOKEN")
if token_telegram:
    os.environ["TELEGRAM_TOKEN"] = token_telegram


def conectar():
    return pymysql.connect(
        host=leer_secreto("MYSQL_HOST"),
        port=int(leer_secreto("MYSQL_PORT")),
        user=leer_secreto("MYSQL_USER"),
        password=leer_secreto("MYSQL_PASSWORD"),
        database=leer_secreto("MYSQL_DB"),
        ssl={"ca": leer_secreto("MYSQL_CA")},
        charset="utf8mb4",
        connect_timeout=8,
    )


CONSULTA = """
SELECT c.id_contrato, e.nombre AS nombre_entidad, d.nombre AS departamento,
       k.nombre AS categoria, c.valor_contrato AS valor_del_contrato,
       c.saldo_pendiente, c.nivel_alerta, c.estado_contrato,
       c.objeto AS objeto_del_contrato
FROM contrato c
JOIN entidad e ON c.id_entidad = e.id_entidad
JOIN departamento d ON e.id_departamento = d.id_departamento
JOIN categoria k ON c.id_categoria = k.id_categoria
"""


@st.cache_data(ttl=600)
def cargar_contratos():
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute(CONSULTA)
        filas = cursor.fetchall()
        nombres = [columna[0] for columna in cursor.description]
        conexion.close()
        datos = pd.DataFrame(filas, columns=nombres)
        datos["valor_del_contrato"] = datos["valor_del_contrato"].astype(float)
        datos["saldo_pendiente"] = datos["saldo_pendiente"].astype(float)
        return datos, "base de datos MySQL"
    except Exception:
        datos = pd.read_csv("contratos_publicar.csv", encoding="utf-8-sig", low_memory=False)
        return datos, "archivo CSV de respaldo"


# ----- Ingreso -----

def clave_correcta(clave_escrita, huella_guardada):
    try:
        _, vueltas, sal, huella = huella_guardada.split("$")
        huella_nueva = hashlib.pbkdf2_hmac("sha256", clave_escrita.encode("utf-8"), bytes.fromhex(sal), int(vueltas)).hex()
        return hmac.compare_digest(huella_nueva, huella)
    except Exception:
        return False


def iniciar_sesion(usuario, clave):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT u.nombre, u.password_hash, r.nombre, d.nombre "
            "FROM usuario u "
            "JOIN rol r ON u.id_rol = r.id_rol "
            "LEFT JOIN departamento d ON u.id_departamento = d.id_departamento "
            "WHERE u.login = %s AND u.activo = TRUE",
            (usuario,),
        )
        fila = cursor.fetchone()
        conexion.close()
    except Exception:
        return "sin_base", None

    if fila is None or not clave_correcta(clave, fila[1]):
        return "incorrecto", None
    return "ok", {"nombre": fila[0], "rol": fila[2], "departamento": fila[3]}


st.title("Alertas de contratos de medicamentos en Colombia")
st.caption("Proyecto Medicamentos | Salud y bienestar")

if "sesion" not in st.session_state:
    st.subheader("Ingreso")
    usuario_escrito = st.text_input("Usuario")
    clave_escrita = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        resultado, datos_usuario = iniciar_sesion(usuario_escrito.strip().lower(), clave_escrita)
        if resultado == "ok":
            st.session_state["sesion"] = datos_usuario
            st.rerun()
        elif resultado == "sin_base":
            st.warning("La base de datos no está disponible en este momento. Puedes entrar como invitado")
        else:
            st.error("Usuario o contraseña incorrectos")

    st.write("Ingresar sin cuenta:")
    if st.button("Entrar como invitado"):
        st.session_state["sesion"] = {"nombre": "Invitado", "rol": "Invitado", "departamento": None}
        st.rerun()

    st.stop()


# ----- Datos según el rol -----

sesion = st.session_state["sesion"]
rol = sesion["rol"]
es_admin = rol == "Administrador"

contratos, fuente = cargar_contratos()

if sesion["departamento"] and rol in ["Comprador", "EPS", "Farmacia o distribuidor"]:
    contratos = contratos[contratos["departamento"] == sesion["departamento"]]

st.sidebar.write("Sesión: " + sesion["nombre"] + " (" + rol + ")")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.clear()
    st.rerun()

st.sidebar.header("Filtros")
departamentos = st.sidebar.multiselect("Departamento", sorted(contratos["departamento"].unique()))
categorias = st.sidebar.multiselect("Categoría", sorted(contratos["categoria"].unique()))
niveles = st.sidebar.multiselect("Nivel de alerta", ["Alta", "Media", "Baja", "Sin alerta"])

filtrado = contratos
if departamentos:
    filtrado = filtrado[filtrado["departamento"].isin(departamentos)]
if categorias:
    filtrado = filtrado[filtrado["categoria"].isin(categorias)]
if niveles:
    filtrado = filtrado[filtrado["nivel_alerta"].isin(niveles)]

st.sidebar.write("Datos tomados de: " + fuente)
st.sidebar.write("Contratos: " + str(len(filtrado)) + " de " + str(len(contratos)))

tab_resumen, tab_mapa, tab_contratos, tab_alertas, tab_rendimiento, tab_red = st.tabs(
    ["Resumen", "Mapa", "Contratos", "Alertas", "Rendimiento", "Red"]
)


# ----- Resumen -----

with tab_resumen:
    columna1, columna2, columna3 = st.columns(3)
    columna1.metric("Contratos", len(filtrado))
    columna2.metric("Saldo pendiente (millones de pesos)", round(filtrado["saldo_pendiente"].sum() / 1000000))
    columna3.metric("Alertas altas", int((filtrado["nivel_alerta"] == "Alta").sum()))

    st.subheader("Por categoría")
    por_categoria = filtrado.groupby("categoria").agg(
        contratos=("id_contrato", "count"),
        saldo_millones=("saldo_pendiente", "sum"),
    ).reset_index()
    por_categoria["saldo_millones"] = (por_categoria["saldo_millones"] / 1000000).round()
    st.dataframe(por_categoria, hide_index=True, width="stretch")

    st.subheader("Por departamento")
    por_departamento = filtrado.groupby("departamento").size().reset_index(name="contratos")
    por_departamento = por_departamento.sort_values("contratos", ascending=False)
    st.plotly_chart(px.bar(por_departamento, x="departamento", y="contratos"), width="stretch")


# ----- Mapa -----

COORDENADAS = {
    "Amazonas": (-4.215, -69.94), "Antioquia": (6.244, -75.574), "Arauca": (7.09, -70.76),
    "Atlántico": (10.964, -74.796), "Bolívar": (10.391, -75.479), "Boyacá": (5.535, -73.367),
    "Caldas": (5.07, -75.517), "Caquetá": (1.614, -75.606), "Casanare": (5.337, -72.396),
    "Cauca": (2.444, -76.614), "Cesar": (10.463, -73.253), "Chocó": (5.695, -76.661),
    "Córdoba": (8.75, -75.881), "Cundinamarca": (4.86, -74.03), "Distrito Capital de Bogotá": (4.711, -74.072),
    "Guainía": (3.865, -67.924), "Guaviare": (2.57, -72.64), "Huila": (2.927, -75.282),
    "La Guajira": (11.544, -72.907), "Magdalena": (11.241, -74.199), "Meta": (4.142, -73.627),
    "Nariño": (1.214, -77.281), "Norte de Santander": (7.894, -72.507), "Putumayo": (1.15, -76.647),
    "Quindío": (4.534, -75.681), "Risaralda": (4.813, -75.696), "Santander": (7.119, -73.122),
    "Sucre": (9.304, -75.397), "Tolima": (4.438, -75.232), "Valle del Cauca": (3.452, -76.532),
    "Vaupés": (1.253, -70.234), "Vichada": (6.189, -67.485),
}

with tab_mapa:
    st.subheader("Contratos por departamento")

    por_depto = filtrado.groupby("departamento").agg(
        contratos=("id_contrato", "count"),
        saldo=("saldo_pendiente", "sum"),
    ).reset_index()

    latitudes = []
    longitudes = []
    for nombre in por_depto["departamento"]:
        if nombre in COORDENADAS:
            latitudes.append(COORDENADAS[nombre][0])
            longitudes.append(COORDENADAS[nombre][1])
        else:
            latitudes.append(None)
            longitudes.append(None)
    por_depto["latitud"] = latitudes
    por_depto["longitud"] = longitudes
    por_depto = por_depto.dropna(subset=["latitud"])

    if len(por_depto) == 0:
        st.info("No hay contratos con departamento ubicable en el mapa")
    else:
        textos = []
        for _, fila in por_depto.iterrows():
            textos.append(fila["departamento"] + ": " + str(fila["contratos"]) + " contratos")

        mapa = go.Figure(go.Scattermap(
            lat=por_depto["latitud"],
            lon=por_depto["longitud"],
            mode="markers",
            marker=dict(
                size=10 + 30 * por_depto["contratos"] / por_depto["contratos"].max(),
                color=por_depto["saldo"] / 1000000,
                colorscale="YlOrRd",
                showscale=True,
                colorbar=dict(title="Saldo (millones)"),
            ),
            text=textos,
            hoverinfo="text",
        ))
        mapa.update_layout(
            map=dict(style="open-street-map", center=dict(lat=4.6, lon=-73.5), zoom=4.3),
            height=600,
            margin=dict(l=0, r=0, t=0, b=0),
        )
        st.plotly_chart(mapa, width="stretch")
        st.caption("El tamaño del círculo es la cantidad de contratos y el color es el saldo pendiente")


# ----- Contratos -----

with tab_contratos:
    st.subheader("Contratos")
    columnas = ["nombre_entidad", "departamento", "categoria", "valor_del_contrato",
                "saldo_pendiente", "nivel_alerta", "estado_contrato", "objeto_del_contrato"]
    tabla = filtrado[columnas].sort_values("saldo_pendiente", ascending=False)
    st.dataframe(tabla, width="stretch")
    st.download_button("Descargar esta tabla (CSV)", tabla.to_csv(index=False).encode("utf-8-sig"), "contratos.csv", "text/csv")


# ----- Alertas -----

def armar_mensaje(contrato):
    valor = round(contrato["valor_del_contrato"] / 1000000, 1)
    saldo = round(contrato["saldo_pendiente"] / 1000000, 1)
    return ("Alerta " + contrato["nivel_alerta"] + ": " + contrato["nombre_entidad"].title()
            + " (" + contrato["departamento"] + ") tiene un contrato de " + contrato["categoria"].lower()
            + " por $" + str(valor) + " millones, con saldo pendiente de $" + str(saldo) + " millones.")


def leer_suscriptores():
    try:
        return [dict(persona) for persona in st.secrets["suscriptores"]]
    except Exception:
        return []


with tab_alertas:
    st.subheader("Alertas activas")
    st.caption("Contratos con saldo pendiente alto o medio")
    activas = filtrado[filtrado["nivel_alerta"].isin(["Alta", "Media"])]
    activas = activas.sort_values("saldo_pendiente", ascending=False).head(20)
    st.dataframe(activas[["nombre_entidad", "departamento", "categoria", "nivel_alerta", "saldo_pendiente"]],
                 hide_index=True, width="stretch")

    st.subheader("Enviar alertas por Telegram")
    if not es_admin:
        st.info("Solo el Administrador puede enviar alertas. Tu rol es: " + rol + ".")
    else:
        tipo = st.selectbox("Enviar a", ["Comprador", "EPS", "Farmacia o distribuidor"])
        cantidad = st.slider("Cantidad de alertas por persona", 1, 10, 3)

        destinatarios = []
        for persona in leer_suscriptores():
            if persona.get("rol") == tipo:
                destinatarios.append(persona)
        st.write("Personas que las recibirán: " + str(len(destinatarios)))

        elegidos = filtrado[filtrado["nivel_alerta"] != "Sin alerta"]
        elegidos = elegidos.sort_values("saldo_pendiente", ascending=False).head(cantidad)
        st.dataframe(elegidos[["nombre_entidad", "departamento", "nivel_alerta", "saldo_pendiente"]],
                     hide_index=True, width="stretch")

        if st.button("Enviar alertas"):
            if len(destinatarios) == 0 or len(elegidos) == 0:
                st.warning("No hay personas con ese rol o no hay contratos con alertas")
            else:
                enviadas = 0
                total = 0
                for persona in destinatarios:
                    for _, contrato in elegidos.iterrows():
                        texto = "Hola " + persona["nombre"] + ". " + armar_mensaje(contrato)
                        try:
                            respuesta = enviar_telegram(str(persona["chat_id"]), texto)
                            if respuesta.get("ok"):
                                enviadas = enviadas + 1
                        except Exception:
                            pass
                        total = total + 1
                        time.sleep(0.4)
                st.success("Alertas enviadas: " + str(enviadas) + " de " + str(total))


# ----- Rendimiento -----

with tab_rendimiento:
    st.subheader("Rendimiento del procesamiento paralelo y distribuido")

    if os.path.exists("rendimiento_multiprocessing.csv"):
        st.markdown("**Multiprocessing de Python**")
        medidas = pd.read_csv("rendimiento_multiprocessing.csv")
        st.dataframe(medidas, hide_index=True, width="stretch")
        st.plotly_chart(px.bar(medidas, x="procesos", y="speedup"), width="stretch")
    else:
        st.write("Todavía no hay mediciones. Ejecuta: python procesamiento\\filtrar_paralelo.py")

    if os.path.exists("rendimiento_spark.csv"):
        st.markdown("**Apache Spark**")
        medidas_spark = pd.read_csv("rendimiento_spark.csv")
        st.dataframe(medidas_spark, hide_index=True, width="stretch")
        st.plotly_chart(px.bar(medidas_spark, x="nucleos", y="speedup"), width="stretch")
    else:
        st.write("Todavía no hay mediciones de Spark. Ejecuta: python procesamiento\\spark_resumen.py")


# ----- Red -----

with tab_red:
    st.subheader("Infraestructura de red")
    if os.path.exists("topologia_red.png"):
        st.image("topologia_red.png", caption="Topología de red diseñada en Cisco Packet Tracer")
    else:
        st.write("Aquí irá el diagrama de la red (archivo topologia_red.png).")
