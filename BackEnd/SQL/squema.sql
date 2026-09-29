CREATE DATABASE IF NOT EXISTS huellapet_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE huellapet_db;

-- ========================================================
-- 1. MÓDULO DE USUARIOS, ROLES Y CLÍNICAS
-- ========================================================

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255)
) ENGINE=InnoDB;

INSERT INTO roles (nombre, descripcion) VALUES 
('tutor', 'Dueño de la mascota'),
('veterinario', 'Médico veterinario verificado'),
('admin', 'Administrador de la plataforma');

CREATE TABLE usuarios (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    rol_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    rut_dni VARCHAR(20) UNIQUE,
    direccion VARCHAR(255),
    es_veterinario_verificado BOOLEAN DEFAULT FALSE,
    numero_colegiado VARCHAR(50) DEFAULT NULL,
    estado ENUM('activo', 'inactivo', 'suspendido') DEFAULT 'activo',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE RESTRICT,
    INDEX idx_usuarios_email (email),
    INDEX idx_usuarios_rol (rol_id)
) ENGINE=InnoDB;

CREATE TABLE veterinarias (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    direccion VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(150),
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE veterinario_clinica (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    veterinario_id BIGINT NOT NULL,
    veterinaria_id BIGINT NOT NULL,
    FOREIGN KEY (veterinario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (veterinaria_id) REFERENCES veterinarias(id) ON DELETE CASCADE,
    UNIQUE KEY uq_vet_clinica (veterinario_id, veterinaria_id)
) ENGINE=InnoDB;

-- ========================================================
-- 2. MÓDULO DE PLANES, SUSCRIPCIONES Y PAGOS (FREEMIUM)
-- ========================================================

CREATE TABLE planes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE, -- 'Gratis', 'Premium'
    precio_mensual DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    limite_mascotas INT DEFAULT 1,
    permite_chat_vet BOOLEAN DEFAULT FALSE,
    permite_recordatorios BOOLEAN DEFAULT FALSE,
    almacenamiento_ilimitado BOOLEAN DEFAULT FALSE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO planes (nombre, precio_mensual, limite_mascotas, permite_chat_vet, permite_recordatorios, almacenamiento_ilimitado) VALUES 
('Gratis', 0.00, 1, FALSE, FALSE, FALSE),
('Premium', 4990.00, 999, TRUE, TRUE, TRUE);

CREATE TABLE suscripciones (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id BIGINT NOT NULL,
    plan_id INT NOT NULL,
    estado ENUM('activo', 'cancelado', 'moroso', 'prueba') DEFAULT 'activo',
    fecha_inicio DATETIME NOT NULL,
    fecha_fin_periodo DATETIME NOT NULL,
    fecha_cancelacion DATETIME DEFAULT NULL,
    renovacion_automatica BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES planes(id) ON DELETE RESTRICT,
    INDEX idx_suscripciones_usuario (usuario_id),
    INDEX idx_suscripciones_estado (estado)
) ENGINE=InnoDB;

CREATE TABLE metodos_pago (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id BIGINT NOT NULL,
    proveedor VARCHAR(50) NOT NULL, -- ej. 'stripe', 'transbank', 'mercado_pago'
    token_tarjeta VARCHAR(255) NOT NULL,
    ultimos_4_digitos VARCHAR(4) NOT NULL,
    marca_tarjeta VARCHAR(20),
    es_predeterminado BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE pagos (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    suscripcion_id BIGINT NOT NULL,
    metodo_pago_id BIGINT DEFAULT NULL,
    monto DECIMAL(10, 2) NOT NULL,
    moneda VARCHAR(3) DEFAULT 'CLP',
    estado ENUM('completado', 'fallido', 'pendiente', 'reembolsado') DEFAULT 'pendiente',
    id_transaccion_pasarela VARCHAR(255),
    fecha_pago DATETIME NOT NULL,
    url_factura VARCHAR(255) DEFAULT NULL,
    FOREIGN KEY (suscripcion_id) REFERENCES suscripciones(id) ON DELETE CASCADE,
    FOREIGN KEY (metodo_pago_id) REFERENCES metodos_pago(id) ON DELETE SET NULL,
    INDEX idx_pagos_suscripcion (suscripcion_id)
) ENGINE=InnoDB;

-- ========================================================
-- 3. MÓDULO DE MASCOTAS Y DISPOSITIVOS NFC/QR
-- ========================================================

CREATE TABLE mascotas (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tutor_id BIGINT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    especie VARCHAR(50) NOT NULL,
    raza VARCHAR(100),
    fecha_nacimiento DATE,
    sexo ENUM('Macho', 'Hembra', 'Desconocido') NOT NULL,
    esterilizado BOOLEAN DEFAULT FALSE,
    peso_kg DECIMAL(5, 2),
    num_microchip_oficial VARCHAR(50) DEFAULT NULL,
    foto_url VARCHAR(255),
    contacto_emergencia_alt VARCHAR(100),
    telefono_emergencia_alt VARCHAR(20),
    notas_emergencia TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (tutor_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_mascotas_tutor (tutor_id)
) ENGINE=InnoDB;

CREATE TABLE dispositivos_nfc (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    codigo_uid VARCHAR(100) NOT NULL UNIQUE, -- Código del chip NFC
    token_qr VARCHAR(255) NOT NULL UNIQUE,  -- Hash para la URL del QR
    mascota_id BIGINT DEFAULT NULL,
    estado ENUM('no_asignado', 'activo', 'bloqueado', 'perdido') DEFAULT 'no_asignado',
    fecha_vinculacion DATETIME DEFAULT NULL,
    FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE SET NULL,
    INDEX idx_nfc_codigo (codigo_uid),
    INDEX idx_nfc_token (token_qr)
) ENGINE=InnoDB;

-- ========================================================
-- 4. MÓDULO DE HISTORIAL MÉDICO (ACCESO RESTRINGIDO A VETS)
-- ========================================================

CREATE TABLE historial_clinico (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    mascota_id BIGINT NOT NULL,
    veterinario_id BIGINT NOT NULL,
    veterinaria_id BIGINT DEFAULT NULL,
    fecha_consulta DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    motivo VARCHAR(255) NOT NULL,
    sintomas TEXT,
    diagnostico TEXT NOT NULL,
    tratamiento TEXT,
    notas_privadas TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE CASCADE,
    FOREIGN KEY (veterinario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    FOREIGN KEY (veterinaria_id) REFERENCES veterinarias(id) ON DELETE SET NULL,
    INDEX idx_historial_mascota (mascota_id)
) ENGINE=InnoDB;

CREATE TABLE vacunas (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    mascota_id BIGINT NOT NULL,
    veterinario_id BIGINT NOT NULL,
    nombre_vacuna VARCHAR(100) NOT NULL,
    lote VARCHAR(50),
    fecha_aplicacion DATE NOT NULL,
    fecha_proxima_dosis DATE,
    FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE CASCADE,
    FOREIGN KEY (veterinario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    INDEX idx_vacunas_mascota (mascota_id)
) ENGINE=InnoDB;

CREATE TABLE desparasitaciones (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    mascota_id BIGINT NOT NULL,
    veterinario_id BIGINT NOT NULL,
    producto VARCHAR(100) NOT NULL,
    tipo ENUM('interna', 'externa', 'ambas') NOT NULL,
    dosis VARCHAR(50),
    fecha_aplicacion DATE NOT NULL,
    fecha_proxima_dosis DATE,
    FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE CASCADE,
    FOREIGN KEY (veterinario_id) REFERENCES usuarios(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE alergias_condiciones (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    mascota_id BIGINT NOT NULL,
    veterinario_id BIGINT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    tipo ENUM('alergia', 'enfermedad_cronica', 'condicion_especial') NOT NULL,
    gravedad ENUM('leve', 'moderada', 'critica') NOT NULL,
    observaciones TEXT,
    FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE CASCADE,
    FOREIGN KEY (veterinario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    INDEX idx_alergias_mascota (mascota_id)
) ENGINE=InnoDB;

-- ========================================================
-- 5. MÓDULO DE INTERACCIÓN, CITAS Y CHAT
-- ========================================================

CREATE TABLE citas (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    mascota_id BIGINT NOT NULL,
    tutor_id BIGINT NOT NULL,
    veterinario_id BIGINT DEFAULT NULL,
    veterinaria_id BIGINT DEFAULT NULL,
    fecha_hora DATETIME NOT NULL,
    motivo VARCHAR(255) NOT NULL,
    estado ENUM('pendiente', 'confirmada', 'cancelada', 'completada') DEFAULT 'pendiente',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE CASCADE,
    FOREIGN KEY (tutor_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (veterinario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    FOREIGN KEY (veterinaria_id) REFERENCES veterinarias(id) ON DELETE SET NULL,
    INDEX idx_citas_fecha (fecha_hora)
) ENGINE=InnoDB;

CREATE TABLE chatbot_consultas (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id BIGINT NOT NULL,
    pregunta TEXT NOT NULL,
    respuesta TEXT NOT NULL,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE chat_veterinario_mensajes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tutor_id BIGINT NOT NULL,
    veterinario_id BIGINT NOT NULL,
    mascota_id BIGINT NOT NULL,
    remitente_tipo ENUM('tutor', 'veterinario') NOT NULL,
    mensaje TEXT NOT NULL,
    leido BOOLEAN DEFAULT FALSE,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tutor_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (veterinario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE recordatorios (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    mascota_id BIGINT NOT NULL,
    usuario_id BIGINT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT,
    fecha_programada DATETIME NOT NULL,
    tipo ENUM('vacuna', 'desparasitacion', 'cita', 'medicamento') NOT NULL,
    enviado BOOLEAN DEFAULT FALSE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_recordatorios_envio (fecha_programada, enviado)
) ENGINE=InnoDB;