import pandas as pd
import numpy as np

df = pd.read_csv("contratos_medicamentos.csv", encoding="utf-8-sig", low_memory=False)

df["fecha_fin"] = pd.to_datetime(df["fecha_de_fin_del_contrato"].str[:10], errors="coerce")
hoy = pd.Timestamp.today().normalize()
df["dias_desde_fin"] = (hoy - df["fecha_fin"]).dt.days
df["estado_contrato"] = np.where(df["dias_desde_fin"] > 0, "Vencido", "Vigente")

df["saldo_pendiente"] = df["valor_pendiente_de_pago"].clip(lower=0)
df["pct_pendiente"] = (df["saldo_pendiente"] / df["valor_del_contrato"]).round(3)

df["nivel_alerta"] = np.select(
[df["saldo_pendiente"] >= 100e6, df["saldo_pendiente"] >= 20e6, df["saldo_pendiente"] > 0],
["Alta", "Media", "Baja"],
default="Sin alerta"
)

df["mensaje_alerta"] = "ALERTA " + df["nivel_alerta"] + ": " + df["nombre_entidad"].str.title() + " (" + df["departamento"] + ") tiene un contrato de " + df["categoria"].str.lower() + " con saldo pendiente de $" + (df["saldo_pendiente"] / 1e6).round(1).astype(str) + " millones."

df.to_csv("contratos_alertas.csv", index=False, encoding="utf-8-sig")

print("Contratos:", len(df))
print(df["nivel_alerta"].value_counts())
print(df["estado_contrato"].value_counts())
print(df["mensaje_alerta"].iloc[0])