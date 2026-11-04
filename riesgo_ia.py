import numpy as np
import pandas as pd
from scipy.stats import chisquare
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

REFERENCIA = pd.Timestamp("2026-11-01")

df = pd.read_csv("contratos_publicar.csv", encoding="utf-8-sig", low_memory=False)
firma = pd.to_datetime(df["fecha_de_firma"], errors="coerce")
inicio = pd.to_datetime(df["fecha_de_inicio_del_contrato"], errors="coerce")
fin = pd.to_datetime(df["fecha_de_fin_del_contrato"], errors="coerce")

valor = df["valor_del_contrato"].astype(float)
saldo = df["saldo_pendiente"].astype(float).clip(lower=0)
caract = pd.DataFrame(index=df.index)
caract["log_valor"] = np.log1p(valor)
caract["log_saldo"] = np.log1p(saldo)
caract["pct_pendiente"] = (saldo / valor).clip(0, 1)
caract["pct_facturado"] = (df["valor_facturado"].astype(float) / valor).clip(0, 1.5)
duracion = (fin - inicio).dt.days.clip(0, 3650)
caract["duracion"] = duracion.fillna(duracion.median())
media_cat = caract.groupby(df["categoria"])["log_valor"].transform("mean")
desv_cat = caract.groupby(df["categoria"])["log_valor"].transform("std").replace(0, 1).fillna(1)
caract["z_categoria"] = (caract["log_valor"] - media_cat) / desv_cat

X = StandardScaler().fit_transform(caract.fillna(0))
modelo = IsolationForest(n_estimators=200, contamination="auto", random_state=42)
modelo.fit(X)
anomalia = -modelo.decision_function(X)
puntaje_ia = pd.Series(anomalia).rank(pct=True).to_numpy() * 100

dias_vencido = (REFERENCIA - fin).dt.days.clip(lower=0).fillna(0)
retraso = (caract["pct_pendiente"] * np.minimum(1, dias_vencido / 730) * 100).to_numpy()
valor_relativo = valor.groupby(df["categoria"]).rank(pct=True).to_numpy() * 100

puntaje = 0.60 * puntaje_ia + 0.25 * retraso + 0.15 * valor_relativo
componentes = np.vstack([0.60 * puntaje_ia, 0.25 * retraso, 0.15 * valor_relativo]).T
nombres = np.array(["patron atipico detectado por IA", "pago pendiente y contrato vencido", "valor alto para su categoria"])
motivo = nombres[componentes.argmax(axis=1)]
nivel = np.where(puntaje >= 75, "Alto", np.where(puntaje >= 50, "Medio", "Bajo"))

salida = pd.DataFrame({"id_contrato": df["id_contrato"], "puntaje_riesgo": np.round(puntaje, 1), "nivel_riesgo": nivel, "motivo_riesgo": motivo})
salida.to_csv("riesgo_contratos.csv", index=False, encoding="utf-8")

esperado = np.log10(1 + 1 / np.arange(1, 10))
def primer_digito(serie):
    return serie[serie > 0].astype(float).apply(lambda v: int(str(f"{v:.6e}")[0]))

digitos = primer_digito(valor)
observado = digitos.value_counts(normalize=True).reindex(range(1, 10)).fillna(0).to_numpy()
conteo = digitos.value_counts().reindex(range(1, 10)).fillna(0).to_numpy()
chi = chisquare(conteo, f_exp=esperado * conteo.sum())
pd.DataFrame({"digito": range(1, 10), "esperado": np.round(esperado, 4), "observado": np.round(observado, 4)}).to_csv("benford_global.csv", index=False, encoding="utf-8")

filas = []
for dep, grupo in df.groupby("departamento"):
    d = primer_digito(grupo["valor_del_contrato"])
    if len(d) < 50:
        continue
    obs = d.value_counts(normalize=True).reindex(range(1, 10)).fillna(0).to_numpy()
    mad = float(np.mean(np.abs(obs - esperado)))
    if mad < 0.006:
        conf = "Cercana"
    elif mad < 0.012:
        conf = "Aceptable"
    elif mad < 0.015:
        conf = "Marginal"
    else:
        conf = "No conforme"
    filas.append({"departamento": dep, "contratos": len(d), "mad": round(mad, 4), "conformidad": conf})
pd.DataFrame(filas).sort_values("mad", ascending=False).to_csv("benford_departamentos.csv", index=False, encoding="utf-8")

print("Contratos analizados:", len(salida))
print(salida["nivel_riesgo"].value_counts().to_string())
print("Benford global: chi2 =", round(float(chi.statistic), 1), "| p =", float(chi.pvalue))
print("Listo: riesgo_contratos.csv, benford_global.csv y benford_departamentos.csv")