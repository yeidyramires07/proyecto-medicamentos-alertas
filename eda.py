import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

os.makedirs("graficos", exist_ok=True)
sns.set_theme(style="whitegrid")

df = pd.read_csv("contratos_publicar.csv", encoding="utf-8-sig", low_memory=False)
df["valor_millones"] = df["valor_del_contrato"] / 1e6
df["saldo_millones"] = df["saldo_pendiente"] / 1e6
df["anio_firma"] = pd.to_datetime(df["fecha_de_firma"], errors="coerce").dt.year

def guardar(nombre):
    plt.tight_layout()
    plt.savefig("graficos/" + nombre + ".png", dpi=150)
    plt.close()

plt.figure(figsize=(8, 5))
sns.histplot(df["valor_millones"], bins=40, log_scale=True)
plt.title("1. Distribucion del valor de los contratos (escala logaritmica)")
plt.xlabel("Valor del contrato (millones COP)")
plt.ylabel("Cantidad de contratos")
guardar("01_histograma_valor")

plt.figure(figsize=(9, 5))
sns.boxplot(data=df, x="categoria", y="valor_millones")
plt.yscale("log")
plt.title("2. Valor del contrato por categoria")
plt.xlabel("Categoria")
plt.ylabel("Valor (millones COP, escala log)")
plt.xticks(rotation=20, ha="right")
guardar("02_boxplot_categoria")

plt.figure(figsize=(9, 5))
orden = df["departamento"].value_counts().head(10).index
sns.countplot(data=df, y="departamento", order=orden)
plt.title("3. Top 10 departamentos por cantidad de contratos")
plt.xlabel("Cantidad de contratos")
plt.ylabel("Departamento")
guardar("03_barras_departamentos")

plt.figure(figsize=(8, 5))
tabla = pd.crosstab(df["categoria"], df["nivel_alerta"])
tabla = tabla.reindex(columns=[c for c in ["Alta", "Media", "Baja", "Sin alerta"] if c in tabla.columns])
sns.heatmap(tabla, annot=True, fmt="d", cmap="YlOrRd")
plt.title("4. Contratos por categoria y nivel de alerta")
plt.xlabel("Nivel de alerta")
plt.ylabel("Categoria")
guardar("04_heatmap_categoria_alerta")

plt.figure(figsize=(8, 6))
con_saldo = df[(df["valor_millones"] > 0) & (df["saldo_millones"] > 0)]
sns.scatterplot(data=con_saldo, x="valor_millones", y="saldo_millones", hue="categoria", alpha=0.6)
plt.xscale("log")
plt.yscale("log")
plt.title("5. Valor del contrato vs saldo pendiente")
plt.xlabel("Valor (millones COP, escala log)")
plt.ylabel("Saldo pendiente (millones COP, escala log)")
guardar("05_dispersion_valor_saldo")

plt.figure(figsize=(8, 5))
por_anio = df.dropna(subset=["anio_firma"]).groupby("anio_firma").size().reset_index(name="contratos")
sns.lineplot(data=por_anio, x="anio_firma", y="contratos", marker="o")
plt.title("6. Contratos firmados por anio")
plt.xlabel("Anio de firma")
plt.ylabel("Cantidad de contratos")
guardar("06_linea_contratos_por_anio")

print("Listo: 6 graficos guardados en la carpeta graficos")