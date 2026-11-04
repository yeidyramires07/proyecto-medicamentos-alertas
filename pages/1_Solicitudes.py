import os
import streamlit as st
import pandas as pd
import nucleo

for _clave in ["TELEGRAM_TOKEN", "MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DB", "MYSQL_CA"]:
    try:
        os.environ[_clave] = str(st.secrets[_clave])
    except Exception:
        pass

st.set_page_config(page_title="Solicitudes", page_icon="\U0001F4E6", layout="wide")
st.title("Necesidades y disponibilidades")

if "usuario" not in st.session_state:
    st.warning("Primero inicia sesion en la pagina principal (menu lateral).")
    st.stop()

usuario = st.session_state["usuario"]
rol = usuario["rol"]
if usuario.get("respaldo"):
    st.info("Modo respaldo: esta pagina requiere la base de datos.")
    st.stop()

CATEGORIAS = ["Medicamentos", "Vacunas", "Laboratorio y reactivos", "Dispositivos e insumos medicos", "Otros insumos de salud"]
puede_necesidad = rol in ("Comprador", "Administrador")
puede_oferta = rol in ("Farmacia o distribuidor", "Administrador")

try:
    deps = [f["nombre"] for f in nucleo.consultar("SELECT nombre FROM departamento ORDER BY nombre")]
except Exception:
    st.error("No se pudo conectar con la base de datos. Revisa que el servicio de Aiven este encendido.")
    st.stop()

if puede_necesidad or puede_oferta:
    opciones = []
    if puede_necesidad:
        opciones.append("Publicar una necesidad")
    if puede_oferta:
        opciones.append("Publicar una disponibilidad")
    accion = st.radio("Que quieres hacer", opciones, horizontal=True)
    tipo = "necesidad" if "necesidad" in accion else "oferta"
    if usuario["departamento"]:
        departamento = usuario["departamento"]
        st.caption("Departamento: " + departamento)
    else:
        departamento = st.selectbox("Departamento", deps)
    categoria = st.selectbox("Categoria", CATEGORIAS)
    descripcion = st.text_input("Descripcion (por ejemplo: Amoxicilina 500 mg)", max_chars=200)
    cantidad = st.number_input("Cantidad (unidades)", min_value=1, value=100, step=10)
    if tipo == "necesidad":
        urgencia = st.selectbox("Urgencia", ["Alta", "Media", "Baja"])
        precio = None
    else:
        urgencia = None
        precio = st.number_input("Precio por unidad (COP)", min_value=0, value=1000, step=100)
    if st.button("Publicar y avisar"):
        if descripcion.strip() == "":
            st.warning("Escribe una descripcion.")
        else:
            try:
                nucleo.crear_solicitud(tipo, usuario["login"], usuario["nombre"], rol, departamento, categoria, descripcion.strip(), int(cantidad), precio, urgencia)
                resumen, registrado = nucleo.notificar_solicitud(tipo, usuario["login"], usuario["nombre"], departamento, categoria, descripcion.strip(), int(cantidad), precio, urgencia)
                st.success("Publicado. Personas avisadas: " + str(sum(1 for r in resumen if r["estado"] == "enviado")) + " de " + str(len(resumen)) + ".")
                if resumen:
                    st.dataframe(pd.DataFrame(resumen), width="stretch", hide_index=True)
                if not registrado:
                    st.warning("Los avisos se enviaron, pero no se pudieron registrar en la auditoria.")
            except Exception:
                st.error("No se pudo publicar. Revisa la conexion con la base de datos.")
else:
    st.info("Tu rol (" + rol + ") puede consultar las solicitudes, pero no publicarlas.")

st.divider()
filtro_dep = usuario["departamento"] if usuario["departamento"] and rol in ("Comprador", "EPS", "Farmacia o distribuidor") else None
columnas = ["id_solicitud", "fecha", "publicado_por", "rol", "departamento", "categoria", "descripcion", "cantidad"]
try:
    necesidades = nucleo.listar_solicitudes("necesidad", filtro_dep)
    ofertas = nucleo.listar_solicitudes("oferta", filtro_dep)
except Exception:
    st.error("No se pudieron leer las solicitudes.")
    st.stop()

st.subheader("Necesidades abiertas")
if necesidades:
    st.dataframe(pd.DataFrame(necesidades)[columnas + ["urgencia"]], width="stretch", hide_index=True)
else:
    st.caption("No hay necesidades abiertas.")
st.subheader("Disponibilidades abiertas")
if ofertas:
    st.dataframe(pd.DataFrame(ofertas)[columnas + ["precio_unitario"]], width="stretch", hide_index=True)
else:
    st.caption("No hay disponibilidades abiertas.")

propias = [s for s in necesidades + ofertas if s["login"] == usuario["login"] or rol == "Administrador"]
if propias:
    st.subheader("Cerrar una solicitud")
    elegida = st.selectbox("Solicitud", [str(s["id_solicitud"]) + " - " + s["descripcion"] for s in propias])
    if st.button("Cerrar solicitud"):
        try:
            nucleo.cerrar_solicitud(int(elegida.split(" - ")[0]))
            st.success("Solicitud cerrada. Recarga la pagina para ver la lista actualizada.")
        except Exception:
            st.error("No se pudo cerrar la solicitud.")