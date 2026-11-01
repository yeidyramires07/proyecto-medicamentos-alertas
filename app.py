import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import unicodedata
import os
import time
import hmac
from datetime import datetime
from enviar_telegram import enviar_telegram

st.set_page_config(page_title="Alertas de medicamentos", page_icon="\U0001F48A", layout="wide")

COORD = {
    "Amazonas": (-4.215, -69.94), "Antioquia": (6.244, -75.574), "Arauca": (7.09, -70.76),
    "Atlantico": (10.964, -74.796), "Bolivar": (10.391, -75.479), "Boyaca": (5.535, -73.367),
    "Caldas": (5.07, -75.517), "Caqueta": (1.614, -75.606), "Casanare": (5.337, -72.396),
    "Cauca": (2.444, -76.614), "Cesar": (10.463, -73.253), "Choco": (5.695, -76.661),
    "Cordoba": (8.75, -75.881), "Cundinamarca": (4.86, -74.03), "Distrito Capital de Bogota": (4.711, -74.072),
    "Guainia": (3.865, -67.924), "Guaviare": (2.57, -72.64), "Huila": (2.927, -75.282),
    "La Guajira": (11.544, -72.907), "Magdalena": (11.241, -74.199), "Meta": (4.142, -73.627),
    "Narino": (1.214, -77.281), "Norte de Santander": (7.894, -72.507), "Putumayo": (1.15, -76.647),
    "Quindio": (4.534, -75.681), "Risaralda": (4.813, -75.696),
    "San Andres, Providencia y Santa Catalina": (12.585, -81.701), "Santander": (7.119, -73.122),
    "Sucre": (9.304, -75.397), "Tolima": (4.438, -75.232), "Valle del Cauca": (3.452, -76.532),
    "Vaupes": (1.253, -70.234), "Vichada": (6.189, -67.485),
}

ICONOS = {
    "Medicamentos": "\U0001F48A",
    "Vacunas": "\U0001F489",
    "Laboratorio y reactivos": "\U0001F9EA",
    "Dispositivos e insumos medicos": "\U0001FA7A",
    "Otros insumos de salud": "\U0001F4E6",
}

try:
    os.environ["TELEGRAM_TOKEN"] = st.secrets["TELEGRAM_TOKEN"]
except Exception:
    pass

def cargar_suscriptores():
    try:
        return [dict(s) for s in st.secrets["suscriptores"]]
    except Exception:
        return []

def sin_tilde(t):
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c))

@st.cache_data
def cargar():
    return pd.read_csv("contratos_publicar.csv", encoding="utf-8-sig", low_memory=False)

df = cargar()

st.markdown(
    "<div style='background:linear-gradient(90deg,#0f766e,#0891b2);padding:22px 28px;border-radius:14px;color:white;'>"
    "<h1 style='margin:0;color:white;'>\U0001F48A Alertas de contratos de medicamentos</h1>"
    "<p style='margin:6px 0 0 0;'>Colombia | ODS 3: Salud y bienestar | Procesamiento paralelo y distribuido, red y visualizacion de datos</p>"
    "</div>",
    unsafe_allow_html=True,
)
st.write("")

st.sidebar.header("Filtros")
deptos = st.sidebar.multiselect("Departamento", sorted(df["departamento"].unique()))
cats = st.sidebar.multiselect("Categoria", sorted(df["categoria"].unique()))
niveles = st.sidebar.multiselect("Nivel de alerta", ["Alta", "Media", "Baja", "Sin alerta"])

d = df.copy()
if deptos:
    d = d[d["departamento"].isin(deptos)]
if cats:
    d = d[d["categoria"].isin(cats)]
if niveles:
    d = d[d["nivel_alerta"].isin(niveles)]

st.sidebar.caption("Contratos en la base: " + f"{len(df):,}" + " | con los filtros: " + f"{len(d):,}")

tab_res, tab_mapa, tab_cont, tab_alert, tab_rend, tab_red = st.tabs(["Resumen", "Mapa", "Contratos", "Alertas", "Rendimiento", "Red"])

with tab_res:
    c1, c2, c3 = st.columns(3)
    c1.metric("Contratos", f"{len(d):,}")
    c2.metric("Saldo pendiente (millones COP)", f"{d['saldo_pendiente'].sum() / 1e6:,.0f}")
    c3.metric("Alertas altas", f"{(d['nivel_alerta'] == 'Alta').sum():,}")

    st.subheader("Por categoria")
    resumen_cat = d.groupby("categoria").agg(contratos=("id_contrato", "count"), saldo=("saldo_pendiente", "sum"))
    cols_cat = st.columns(len(ICONOS))
    for col, (nombre, icono) in zip(cols_cat, ICONOS.items()):
        n = int(resumen_cat["contratos"].get(nombre, 0))
        saldo = float(resumen_cat["saldo"].get(nombre, 0)) / 1e6
        with col:
            with st.container(border=True):
                st.markdown("## " + icono)
                st.caption(nombre)
                st.metric("Contratos", f"{n:,}")
                st.caption("Saldo: $" + f"{saldo:,.0f}" + " millones")

    g1, g2 = st.columns(2)
    g = d.groupby("departamento").size().reset_index(name="contratos").sort_values("contratos", ascending=False)
    fig_dep = px.bar(g, x="departamento", y="contratos", title="Contratos por departamento")
    g1.plotly_chart(fig_dep, width="stretch")

    top = d.groupby("nombre_entidad")["saldo_pendiente"].sum().sort_values(ascending=False).head(10).reset_index()
    top["saldo_millones"] = (top["saldo_pendiente"] / 1e6).round(1)
    fig_top = px.bar(top, x="saldo_millones", y="nombre_entidad", orientation="h", title="Top 10 entidades por saldo pendiente (millones)")
    fig_top.update_layout(yaxis=dict(autorange="reversed"))
    g2.plotly_chart(fig_top, width="stretch")

    niv = d["nivel_alerta"].value_counts().reindex(["Alta", "Media", "Baja", "Sin alerta"]).fillna(0).reset_index()
    niv.columns = ["nivel", "contratos"]
    fig_niv = px.bar(niv, x="nivel", y="contratos", title="Contratos por nivel de alerta")
    st.plotly_chart(fig_niv, width="stretch")

with tab_mapa:
    st.subheader("Mapa de contratos por departamento")
    m = d.groupby("departamento").agg(contratos=("id_contrato", "count"), saldo=("saldo_pendiente", "sum")).reset_index()
    m["clave"] = m["departamento"].apply(sin_tilde)
    m["lat"] = m["clave"].map(lambda k: COORD.get(k, (None, None))[0])
    m["lon"] = m["clave"].map(lambda k: COORD.get(k, (None, None))[1])
    m = m.dropna(subset=["lat"])

    if len(m) == 0:
        st.info("No hay contratos con departamento ubicable en el mapa.")
    else:
        centro = COORD["Distrito Capital de Bogota"]
        mx = m["contratos"].max()
        fig2 = go.Figure()
        for _, r in m.iterrows():
            if r["clave"] != "Distrito Capital de Bogota":
                fig2.add_trace(go.Scattermap(lat=[centro[0], r["lat"]], lon=[centro[1], r["lon"]], mode="lines", line=dict(width=1 + 5 * r["contratos"] / mx, color="rgba(80,80,200,0.5)"), hoverinfo="skip", showlegend=False))
        fig2.add_trace(go.Scattermap(lat=m["lat"], lon=m["lon"], mode="markers", marker=dict(size=10 + 30 * m["contratos"] / mx, color=m["saldo"] / 1e6, colorscale="YlOrRd", showscale=True, colorbar=dict(title="Saldo (millones)")), text=m["departamento"] + ": " + m["contratos"].astype(str) + " contratos", hoverinfo="text", showlegend=False))
        fig2.update_layout(map=dict(style="open-street-map", center=dict(lat=4.6, lon=-73.5), zoom=4.3), height=600, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig2, width="stretch")
        st.caption("El tamano del circulo indica la cantidad de contratos y el color el saldo pendiente. Las lineas conectan cada departamento con Bogota (el grosor depende de los contratos). Los contratos con departamento 'No Definido' no se ubican en el mapa.")

with tab_cont:
    st.subheader("Contratos filtrados")
    cols = ["nombre_entidad", "departamento", "categoria", "valor_del_contrato", "saldo_pendiente", "nivel_alerta", "estado_contrato", "objeto_del_contrato"]
    tabla = d[cols].sort_values("saldo_pendiente", ascending=False)
    st.dataframe(tabla, width="stretch")
    st.download_button("Descargar tabla filtrada (CSV)", tabla.to_csv(index=False).encode("utf-8-sig"), "contratos_filtrados.csv", "text/csv")

with tab_alert:
    st.subheader("Alertas por Telegram")
    suscriptores = cargar_suscriptores()
    col_a, col_b = st.columns(2)
    tipo = col_a.selectbox("Enviar a", ["Comprador", "EPS", "Farmacia o distribuidor"])
    cuantas = col_b.slider("Cantidad de alertas por persona", 1, 10, 3)
    destinos = [s for s in suscriptores if s.get("rol") == tipo]
    if destinos:
        st.write("Destinatarios (" + str(len(destinos)) + "): " + ", ".join(s["nombre"] for s in destinos))
        chat_manual = ""
    else:
        st.info("No hay personas registradas con este rol. Puedes escribir un chat_id manualmente.")
        chat_manual = st.text_input("Chat de Telegram (chat_id)", value=os.environ.get("TELEGRAM_CHAT_ID", ""))

    prefijos = {"Comprador": "Aviso para comprador", "EPS": "Aviso para EPS", "Farmacia o distribuidor": "Aviso para farmacia o distribuidor"}
    cand = d[d["nivel_alerta"] != "Sin alerta"].sort_values("saldo_pendiente", ascending=False).head(cuantas).copy()
    cand["mensaje"] = prefijos[tipo] + " | " + cand["nivel_alerta"] + ": " + cand["nombre_entidad"].str.title() + " (" + cand["departamento"] + ") - contrato de " + cand["categoria"].str.lower() + " por $" + (cand["valor_del_contrato"] / 1e6).round(1).astype(str) + " millones, saldo pendiente $" + (cand["saldo_pendiente"] / 1e6).round(1).astype(str) + " millones."
    st.dataframe(cand[["departamento", "nivel_alerta", "mensaje"]], width="stretch")

    try:
        clave_correcta = str(st.secrets["CLAVE_ENVIO"])
    except Exception:
        clave_correcta = None
    clave = st.text_input("Clave de envio", type="password")

    if st.button("Enviar alertas por Telegram"):
        if clave_correcta is None:
            st.error("La clave de envio no esta configurada en los secretos de la app.")
        elif not hmac.compare_digest(clave.encode(), clave_correcta.encode()):
            st.error("Clave incorrecta. Pidela al equipo.")
        elif len(cand) == 0:
            st.warning("No hay contratos con alerta para los filtros elegidos.")
        elif len(destinos) == 0 and chat_manual.strip() == "":
            st.warning("Escribe un chat_id o registra personas con este rol.")
        else:
            lista = destinos if destinos else [{"nombre": "Manual", "rol": tipo, "chat_id": chat_manual.strip()}]
            filas = []
            for s in lista:
                for texto in cand["mensaje"]:
                    try:
                        resp = enviar_telegram(str(s["chat_id"]), "Hola " + s["nombre"] + ". " + texto)
                        estado = "enviado" if resp.get("ok") else "error"
                    except Exception:
                        estado = "error"
                    filas.append({"fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "destinatario": s["nombre"], "rol": tipo, "estado": estado})
                    time.sleep(0.4)
            st.session_state["registro"] = st.session_state.get("registro", []) + filas
            ok = sum(1 for f in filas if f["estado"] == "enviado")
            if ok == len(filas):
                st.success("Alertas enviadas: %d de %d." % (ok, len(filas)))
            else:
                st.warning("Alertas enviadas: %d de %d. Si hay errores, la persona debe abrir el bot y pulsar Iniciar." % (ok, len(filas)))

    if "registro" in st.session_state:
        st.caption("Alertas enviadas en esta sesion")
        st.dataframe(pd.DataFrame(st.session_state["registro"]).tail(15), width="stretch")

with tab_rend:
    st.subheader("Rendimiento del procesamiento paralelo y distribuido")
    st.caption("Mediciones sobre 100.000 contratos (54 MB), en un computador de 4 nucleos. Speedup = tiempo serial / tiempo paralelo. Eficiencia = speedup / numero de procesos.")
    mp = pd.DataFrame({"Procesos": [1, 2, 4, 8], "Tiempo (s)": [8.39, 6.66, 6.22, 9.42]})
    mp["Speedup"] = (8.39 / mp["Tiempo (s)"]).round(2)
    mp["Eficiencia"] = (mp["Speedup"] / mp["Procesos"]).round(2)
    sp = pd.DataFrame({"Nucleos": [1, 2, 4], "Tiempo (s)": [9.19, 6.35, 6.53]})
    sp["Speedup"] = (9.19 / sp["Tiempo (s)"]).round(2)
    sp["Eficiencia"] = (sp["Speedup"] / sp["Nucleos"]).round(2)
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("**Python multiprocessing**")
        st.dataframe(mp, width="stretch", hide_index=True)
        st.plotly_chart(px.bar(mp, x="Procesos", y="Speedup", title="Speedup con multiprocessing"), width="stretch")
    with r2:
        st.markdown("**Apache Spark (modo local)**")
        st.dataframe(sp, width="stretch", hide_index=True)
        st.plotly_chart(px.bar(sp, x="Nucleos", y="Speedup", title="Speedup con Spark"), width="stretch")
    st.info("El speedup crece al pasar de 1 a 2 procesos y se estanca con 4. Con 8 procesos en un equipo de 4 nucleos empeora, porque compiten por los mismos nucleos y el costo de repartir los datos supera la ganancia.")

with tab_red:
    st.subheader("Infraestructura de red")
    if os.path.exists("topologia_red.png"):
        st.image("topologia_red.png", caption="Topologia de red disenada en Cisco Packet Tracer")
    else:
        st.info("Aqui ira el diagrama de la red de Packet Tracer cuando el equipo de redes entregue la imagen (archivo topologia_red.png en el repositorio).")