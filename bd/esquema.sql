CREATE TABLE departamento (
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
