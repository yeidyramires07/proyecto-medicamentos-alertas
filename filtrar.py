import pandas as pd
import numpy as np

df = pd.read_csv("datos_limpios.csv", encoding="utf-8-sig", low_memory=False)
obj = df["objeto_del_contrato"].str.lower().fillna("")

positivo = obj.str.contains(r"medicament|f[aá]rmaco|farmac[eé]utic|suministro de insumos|dispositivos m[eé]dicos|material m[eé]dico|insumos m[eé]dico|vacuna|reactivo", regex=True)
negativo = obj.str.contains(r"regente|qu[ií]mico|prestar servicios|prestaci[oó]n de servicios|apoyo|profesional|auxiliar|tecn[oó]log", regex=True)

med = df[positivo & ~negativo].copy()
obj_med = med["objeto_del_contrato"].str.lower()

med["categoria"] = np.select(
[
obj_med.str.contains("vacuna"),
obj_med.str.contains("reactivo|laboratorio"),
obj_med.str.contains("dispositivos m|material m|insumos m|odontol"),
obj_med.str.contains("medicament|f[aá]rmaco|farmac")
],
["Vacunas", "Laboratorio y reactivos", "Dispositivos e insumos medicos", "Medicamentos"],
default="Otros insumos de salud"
)

med = med[(med["valor_del_contrato"] > 0) & (med["valor_del_contrato"] < 1e11)]
med.to_csv("contratos_medicamentos.csv", index=False, encoding="utf-8-sig")

print("Contratos filtrados:", len(med))
print(med["categoria"].value_counts())
print(med["departamento"].value_counts().head(8))