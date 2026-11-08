CREATE TABLE departamento (
    id_departamento INT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE categoria (
    id_categoria INT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE entidad (
    id_entidad INT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL UNIQUE,
    id_departamento INT NOT NULL,
    ciudad VARCHAR(100),
    orden VARCHAR(50),
    rama VARCHAR(50),
    FOREIGN KEY (id_departamento) REFERENCES departamento(id_departamento)
);

CREATE TABLE contrato (
    id_contrato VARCHAR(40) PRIMARY KEY,
    id_entidad INT NOT NULL,
    id_categoria INT NOT NULL,
    tipo_de_contrato VARCHAR(100),
    fecha_firma DATE,
    fecha_inicio DATE,
    fecha_fin DATE,
    valor_contrato DECIMAL(18,2) NOT NULL CHECK (valor_contrato > 0),
    valor_facturado DECIMAL(18,2),
    valor_pagado DECIMAL(18,2),
    saldo_pendiente DECIMAL(18,2) CHECK (saldo_pendiente >= 0),
    nivel_alerta VARCHAR(20) CHECK (nivel_alerta IN ('Alta', 'Media', 'Baja', 'Sin alerta')),
    estado_contrato VARCHAR(20),
    es_pyme VARCHAR(10),
    origen_recursos VARCHAR(100),
    destino_gasto VARCHAR(100),
    objeto TEXT,
    FOREIGN KEY (id_entidad) REFERENCES entidad(id_entidad),
    FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria)
);

CREATE INDEX idx_contrato_entidad ON contrato(id_entidad);
CREATE INDEX idx_contrato_categoria ON contrato(id_categoria);
CREATE INDEX idx_contrato_alerta ON contrato(nivel_alerta);

CREATE TABLE rol (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    id_rol INT NOT NULL,
    id_departamento INT NULL,
    telegram_chat_id VARCHAR(30),
    password_hash VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id_rol) REFERENCES rol(id_rol),
    FOREIGN KEY (id_departamento) REFERENCES departamento(id_departamento)
);

CREATE TABLE alerta_enviada (
    id_alerta INT AUTO_INCREMENT PRIMARY KEY,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_usuario INT,
    id_contrato VARCHAR(40),
    estado VARCHAR(20),
    hash_anterior CHAR(64),
    hash_actual CHAR(64),
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario),
    FOREIGN KEY (id_contrato) REFERENCES contrato(id_contrato)
);