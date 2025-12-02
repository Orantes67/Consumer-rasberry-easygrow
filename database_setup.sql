-- ============================================================
-- Script de Base de Datos para EasyGrow Consumer
-- Base de Datos: PostgreSQL
-- Descripción: Crea la estructura completa de la BD
-- ============================================================

-- 1. CREAR LA BASE DE DATOS (ejecutar como superusuario)
-- Descomenta si necesitas crear la BD desde cero:
-- CREATE DATABASE easygrow_db;

-- 2. CONECTARSE A LA BASE DE DATOS
-- \c easygrow_db

-- ============================================================
-- TABLAS PRINCIPALES
-- ============================================================

-- Tabla de Dispositivos
CREATE TABLE IF NOT EXISTS dispositivos (
    id_dispositivo SERIAL PRIMARY KEY,
    mac_address VARCHAR(17) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    ubicacion VARCHAR(255),
    tipo VARCHAR(50) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de Sensores
CREATE TABLE IF NOT EXISTS sensores (
    id_sensor SERIAL PRIMARY KEY,
    id_dispositivo INTEGER NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    unidad_medida VARCHAR(20),
    valor_minimo FLOAT,
    valor_maximo FLOAT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_dispositivo FOREIGN KEY (id_dispositivo) 
        REFERENCES dispositivos(id_dispositivo) ON DELETE CASCADE
);

-- Tabla de Datos de Sensores
CREATE TABLE IF NOT EXISTS datos_sensores (
    id_dato SERIAL PRIMARY KEY,
    id_sensor INTEGER NOT NULL,
    mac_address VARCHAR(17) NOT NULL,
    valor FLOAT NOT NULL,
    fecha TIMESTAMP NOT NULL,
    CONSTRAINT fk_sensor FOREIGN KEY (id_sensor) 
        REFERENCES sensores(id_sensor) ON DELETE CASCADE,
    CONSTRAINT fk_dispositivo_sensor FOREIGN KEY (mac_address) 
        REFERENCES dispositivos(mac_address) ON DELETE CASCADE
);

-- Tabla de Eventos de Bombas
CREATE TABLE IF NOT EXISTS eventos_bomba (
    id_evento SERIAL PRIMARY KEY,
    id_sensor INTEGER NOT NULL,
    mac_address VARCHAR(17) NOT NULL,
    evento VARCHAR(100) NOT NULL,
    valor_humedad FLOAT NOT NULL,
    tiempo_encendida_seg INTEGER,
    fecha TIMESTAMP NOT NULL,
    CONSTRAINT fk_sensor_bomba FOREIGN KEY (id_sensor) 
        REFERENCES sensores(id_sensor) ON DELETE CASCADE,
    CONSTRAINT fk_dispositivo_bomba FOREIGN KEY (mac_address) 
        REFERENCES dispositivos(mac_address) ON DELETE CASCADE
);

-- ============================================================
-- ÍNDICES PARA OPTIMIZAR CONSULTAS
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_datos_sensores_id_sensor ON datos_sensores(id_sensor);
CREATE INDEX IF NOT EXISTS idx_datos_sensores_mac_address ON datos_sensores(mac_address);
CREATE INDEX IF NOT EXISTS idx_datos_sensores_fecha ON datos_sensores(fecha);
CREATE INDEX IF NOT EXISTS idx_sensores_id_dispositivo ON sensores(id_dispositivo);
CREATE INDEX IF NOT EXISTS idx_eventos_bomba_id_sensor ON eventos_bomba(id_sensor);
CREATE INDEX IF NOT EXISTS idx_eventos_bomba_mac_address ON eventos_bomba(mac_address);
CREATE INDEX IF NOT EXISTS idx_eventos_bomba_fecha ON eventos_bomba(fecha);

-- ============================================================
-- DATOS DE PRUEBA (COMENTADOS)
-- ============================================================

-- Insertar dispositivo de ejemplo
-- INSERT INTO dispositivos (mac_address, nombre, ubicacion, tipo)
-- VALUES ('AA:BB:CC:DD:EE:FF', 'Sensor Raspberry 1', 'Invernadero A', 'Sensor de Humedad');

-- Insertar sensor de ejemplo
-- INSERT INTO sensores (id_dispositivo, descripcion, tipo, unidad_medida, valor_minimo, valor_maximo)
-- VALUES (1, 'Sensor de Humedad del Suelo', 'Humedad', '%', 0, 100);

-- ============================================================
-- VISTAS ÚTILES
-- ============================================================

-- Vista para ver últimos datos de sensores
CREATE OR REPLACE VIEW v_ultimos_datos_sensores AS
SELECT 
    d.mac_address,
    d.nombre as dispositivo,
    s.descripcion as sensor,
    s.tipo,
    s.unidad_medida,
    ds.valor,
    ds.fecha,
    ROW_NUMBER() OVER (PARTITION BY ds.id_sensor ORDER BY ds.fecha DESC) as rn
FROM datos_sensores ds
JOIN sensores s ON ds.id_sensor = s.id_sensor
JOIN dispositivos d ON s.id_dispositivo = d.id_dispositivo;

-- Vista para ver últimos eventos de bombas
CREATE OR REPLACE VIEW v_ultimos_eventos_bomba AS
SELECT 
    d.mac_address,
    d.nombre as dispositivo,
    s.descripcion as sensor,
    eb.evento,
    eb.valor_humedad,
    eb.tiempo_encendida_seg,
    eb.fecha,
    ROW_NUMBER() OVER (PARTITION BY eb.id_sensor ORDER BY eb.fecha DESC) as rn
FROM eventos_bomba eb
JOIN sensores s ON eb.id_sensor = s.id_sensor
JOIN dispositivos d ON s.id_dispositivo = d.id_dispositivo;

-- ============================================================
-- FIN DEL SCRIPT
-- ============================================================
