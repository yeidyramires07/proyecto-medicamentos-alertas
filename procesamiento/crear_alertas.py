# crear_alertas.py
# Toma contratos_medicamentos.csv y le agrega:
#   - saldo_pendiente: cuanto falta por pagar
#   - nivel_alerta: Alta, Media, Baja o Sin alerta
#   - estado_contrato: Vencido o Vigente
# Quita la columna con los numeros de documento (dato personal) y guarda
# contratos_publicar.csv, que es el archivo que usa la app.
#
# Se ejecuta desde la carpeta principal:  python procesamiento\crear_alertas.py

import pandas as pd
from reglas import nivel_de_alerta

datos = pd.read_csv("contratos_medicamentos.csv", encoding="utf-8-sig", low_memory=False)

# Cuanto falta por pagar. Si el dato es negativo, lo dejamos en cero.
datos["saldo_pendiente"] = datos["valor_pendiente_de_pago"].clip(lower=0)

# Nivel de alerta segun el saldo (la regla esta en reglas.py).
niveles = []
for saldo in datos["saldo_pendiente"]:
    niveles.append(nivel_de_alerta(saldo))
datos["nivel_alerta"] = niveles

# Estado del contrato: vencido si su fecha de fin ya paso.
fechas_fin = pd.to_datetime(datos["fecha_de_fin_del_contrato"].str[:10], errors="coerce")
hoy = pd.Timestamp.today().normalize()
estados = []
for fecha in fechas_fin:
    if pd.notna(fecha) and fecha < hoy:
        estados.append("Vencido")
    else:
        estados.append("Vigente")
datos["estado_contrato"] = estados

# Quitamos el dato personal.
datos = datos.drop(columns=["n_mero_de_documento_ordenador_del_gasto"])

datos.to_csv("contratos_publicar.csv", index=False, encoding="utf-8-sig")
print("Contratos guardados:", len(datos))
print(datos["nivel_alerta"].value_counts())
