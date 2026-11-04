import os
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Riesgo con IA", page_icon="\U0001F50D", layout="wide")
st.title("Riesgo de contratos con inteligencia artificial")

if "usuario" not in st.session_state:
    st.warning("Primero inicia sesion en la pagina principal (menu lateral).")
    st.stop()
usuario = st.session_state["usuario"]
rol = usuario["rol"]

if not os.path.exists("riesgo_contratos.csv"):
    st.info("Aun no se han generado los resultados. Ejecuta riesgo_ia.py y sube los archivos CSV al repositorio.")
    st.stop()

contratos = pd.read_csv("contratos_publicar.csv", encoding="utf-8-sig", low_memory=False)
riesgo = pd.read_csv("riesgo_contratos.csv", encoding="utf-8-sig")
datos = contratos.merge(riesgo, on="id_contrato", how="inner")
if usuario["departamento"] and rol in ("Comprador", "EPS", "Farmacia o distribuidor"):
    datos = datos[datos["departamento"] == usuario["departamento"]]
    st.caption("Vista limitada a: " + usuario["departamento"])

c1, c2, c3 = st.columns(3)
c1.metric("Contratos analizados", f"{len(datos):,}")
c2.metric("Riesgo alto", f"{(datos['nivel_riesgo'] == 'Alto').sum():,}")
c3.metric("Puntaje promedio", f"{datos['puntaje_riesgo'].mean():.1f}" if len(datos) else "0")

st.subheader("Distribucion del puntaje de riesgo (0 a 100)")
st.plotly_chart(px.histogram(datos, x="puntaje_riesgo", nbins=30, color="nivel_riesgo", category_orders={"nivel_riesgo": ["Bajo", "Medio", "Alto"]}), width="stretch")

st.subheader("Los 20 contratos con mayor riesgo")
columnas = ["id_contrato", "nombre_entidad", "departamento", "categoria", "valor_del_contrato", "saldo_pendiente", "puntaje_riesgo", "nivel_riesgo", "motivo_riesgo"]
st.dataframe(datos.sort_values("puntaje_riesgo", ascending=False).head(20)[columnas], width="stretch", hide_index=True)

st.subheader("Ley de Benford sobre el valor de los contratos")
if os.path.exists("benford_global.csv"):
    benford = pd.read_csv("benford_global.csv")
    largo = benford.melt(id_vars="digito", value_vars=["esperado", "observado"], var_name="serie", value_name="proporcion")
    st.plotly_chart(px.bar(largo, x="digito", y="proporcion", color="serie", barmode="group", title="Primer digito: esperado vs observado"), width="stretch")
if os.path.exists("benford_departamentos.csv"):
    st.dataframe(pd.read_csv("benford_departamentos.csv"), width="stretch", hide_index=True)
st.caption("Una desviacion de la Ley de Benford es una senal para revisar, no una prueba de fraude: en contratacion de salud muchos valores son montos fijos o redondeados, y con pocos contratos por departamento la medida es inestable.")

with st.expander("Como se calcula el puntaje"):
    st.write("Puntaje = 60% patron atipico (Isolation Forest sobre valor, saldo, porcentaje pendiente, porcentaje facturado, duracion y posicion dentro de su categoria) + 25% atraso de pago (saldo pendiente en contratos vencidos) + 15% valor alto frente a su categoria. Alto: 75 o mas. Medio: de 50 a 75. Bajo: menos de 50.")