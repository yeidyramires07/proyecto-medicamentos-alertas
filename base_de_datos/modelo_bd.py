import os
import pandas as pd

os.makedirs("bd", exist_ok=True)
df = pd.read_csv("contratos_publicar.csv", encoding="utf-8-sig", low_memory=False)

dep = df[["departamento"]].drop_duplicates().sort_values("departamento").reset_index(drop=True)
dep.insert(0, "id_departamento", dep.index + 1)
dep = dep.rename(columns={"departamento": "nombre"})

cat = df[["categoria"]].drop_duplicates().sort_values("categoria").reset_index(drop=True)
cat.insert(0, "id_categoria", cat.index + 1)
cat = cat.rename(columns={"categoria": "nombre"})

ent = df[["nombre_entidad", "departamento", "ciudad", "orden", "rama"]].drop_duplicates("nombre_entidad").sort_values("nombre_entidad").reset_index(drop=True)
ent.insert(0, "id_entidad", ent.index + 1)
ent = ent.merge(dep.rename(columns={"nombre": "departamento"}), on="departamento", how="left")
ent_map = ent[["id_entidad", "nombre_entidad"]]
ent = ent.rename(columns={"nombre_entidad": "nombre"})[["id_entidad", "nombre", "id_departamento", "ciudad", "orden", "rama"]]

con = df.drop(columns=["fecha_fin"]).merge(ent_map, on="nombre_entidad", how="left").merge(cat.rename(columns={"nombre": "categoria"}), on="categoria", how="left")
con = con.rename(columns={"fecha_de_firma": "fecha_firma", "fecha_de_inicio_del_contrato": "fecha_inicio", "fecha_de_fin_del_contrato": "fecha_fin", "valor_del_contrato": "valor_contrato", "origen_de_los_recursos": "origen_recursos", "objeto_del_contrato": "objeto"})
columnas = ["id_contrato", "id_entidad", "id_categoria", "tipo_de_contrato", "fecha_firma", "fecha_inicio", "fecha_fin", "valor_contrato", "valor_facturado", "valor_pagado", "saldo_pendiente", "nivel_alerta", "estado_contrato", "es_pyme", "origen_recursos", "destino_gasto", "objeto"]
con = con[columnas]
for c in ["fecha_firma", "fecha_inicio", "fecha_fin"]:
    con[c] = pd.to_datetime(con[c], errors="coerce").dt.strftime("%Y-%m-%d")

dep.to_csv("bd/departamento.csv", index=False, encoding="utf-8")
cat.to_csv("bd/categoria.csv", index=False, encoding="utf-8")
ent.to_csv("bd/entidad.csv", index=False, encoding="utf-8")
con.to_csv("bd/contrato.csv", index=False, encoding="utf-8")

esquema = """CREATE TABLE departamento (
    id_departamento INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE categoria (
    id_categoria INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE entidad (
    id_entidad INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    id_departamento INTEGER NOT NULL REFERENCES departamento(id_departamento),
    ciudad TEXT,
    orden TEXT,
    rama TEXT
);

CREATE TABLE contrato (
    id_contrato TEXT PRIMARY KEY,
    id_entidad INTEGER NOT NULL REFERENCES entidad(id_entidad),
    id_categoria INTEGER NOT NULL REFERENCES categoria(id_categoria),
    tipo_de_contrato TEXT,
    fecha_firma DATE,
    fecha_inicio DATE,
    fecha_fin DATE,
    valor_contrato NUMERIC(18,2) NOT NULL CHECK (valor_contrato > 0),
    valor_facturado NUMERIC(18,2),
    valor_pagado NUMERIC(18,2),
    saldo_pendiente NUMERIC(18,2) CHECK (saldo_pendiente >= 0),
    nivel_alerta TEXT CHECK (nivel_alerta IN ('Alta', 'Media', 'Baja', 'Sin alerta')),
    estado_contrato TEXT,
    es_pyme TEXT,
    origen_recursos TEXT,
    destino_gasto TEXT,
    objeto TEXT
);

CREATE INDEX idx_contrato_entidad ON contrato(id_entidad);
CREATE INDEX idx_contrato_categoria ON contrato(id_categoria);
CREATE INDEX idx_contrato_alerta ON contrato(nivel_alerta);
CREATE INDEX idx_entidad_departamento ON entidad(id_departamento);

CREATE TABLE rol (
    id_rol SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE usuario (
    id_usuario SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    id_rol INTEGER NOT NULL REFERENCES rol(id_rol),
    id_departamento INTEGER REFERENCES departamento(id_departamento),
    telegram_chat_id TEXT,
    password_hash TEXT,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE alerta_enviada (
    id_alerta SERIAL PRIMARY KEY,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_usuario INTEGER REFERENCES usuario(id_usuario),
    id_contrato TEXT REFERENCES contrato(id_contrato),
    estado TEXT,
    hash_anterior TEXT,
    hash_actual TEXT
);
"""
with open("bd/esquema.sql", "w", encoding="utf-8") as f:
    f.write(esquema)

print("departamento:", len(dep), "| categoria:", len(cat), "| entidad:", len(ent), "| contrato:", len(con))
print("Contratos sin entidad:", int(con["id_entidad"].isna().sum()), "| sin categoria:", int(con["id_categoria"].isna().sum()))
print("Listo: archivos creados en la carpeta bd")