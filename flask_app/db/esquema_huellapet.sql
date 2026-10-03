CREATE DATABASE IF NOT EXISTS huellapet_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE huellapet_db;

-- ========================================================
-- 1. TABLAS CATÁLOGO DE TIPOS Y ESTADOS (3NF)
-- ========================================================

CREATE TABLE tipo_usuario (
    id_tipo_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL UNIQUE,
    descripcion_tipo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE tipo_especie (
    id_tipo_especie INT AUTO_INCREMENT PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL UNIQUE,
    descripcion_tipo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE tipo_estado_dispositivo (
    id_tipo_estado_dispositivo INT AUTO_INCREMENT PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL UNIQUE,
    descripcion_tipo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE tipo_historial (
    id_tipo_historial INT AUTO_INCREMENT PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL UNIQUE,
    descripcion_tipo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE tipo_documento (
    id_tipo_documento INT AUTO_INCREMENT PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL UNIQUE,
    descripcion_tipo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE tipo_plan (
    id_tipo_plan INT AUTO_INCREMENT PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL UNIQUE,
    descripcion_tipo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE tipo_estado_suscripcion (
    id_tipo_estado_suscripcion INT AUTO_INCREMENT PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL UNIQUE,
    descripcion_tipo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE tipo_estado_pago (
    id_tipo_estado_pago INT AUTO_INCREMENT PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL UNIQUE,
    descripcion_tipo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ========================================================
-- 2. TABLAS PRINCIPALES DEL SISTEMA
-- ========================================================

CREATE TABLE usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    id_tipo_usuario INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    direccion VARCHAR(255),
    es_veterinario_verificado BOOLEAN DEFAULT FALSE,
    numero_colegiado VARCHAR(50) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_tipo_usuario) REFERENCES tipo_usuario(id_tipo_usuario) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE mascota (
    id_mascota INT AUTO_INCREMENT PRIMARY KEY,
    id_tutor INT NOT NULL,
    id_tipo_especie INT NOT NULL,
    codigo_huellapet VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    raza VARCHAR(100),
    fecha_nacimiento DATE,
    sexo VARCHAR(20) NOT NULL,
    peso_kg DECIMAL(5, 2),
    descripcion TEXT,
    foto_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_tutor) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_tipo_especie) REFERENCES tipo_especie(id_tipo_especie) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE dispositivo_nfc (
    id_dispositivo_nfc INT AUTO_INCREMENT PRIMARY KEY,
    id_mascota INT UNIQUE DEFAULT NULL,
    id_tipo_estado_dispositivo INT NOT NULL,
    codigo_uid VARCHAR(100) NOT NULL UNIQUE,
    token_qr VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_mascota) REFERENCES mascota(id_mascota) ON DELETE SET NULL,
    FOREIGN KEY (id_tipo_estado_dispositivo) REFERENCES tipo_estado_dispositivo(id_tipo_estado_dispositivo) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE historial_medico (
    id_historial_medico INT AUTO_INCREMENT PRIMARY KEY,
    id_mascota INT NOT NULL,
    id_veterinario INT DEFAULT NULL,
    id_tipo_historial INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT,
    fecha_atencion DATE NOT NULL,
    proxima_fecha DATE DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_mascota) REFERENCES mascota(id_mascota) ON DELETE CASCADE,
    FOREIGN KEY (id_veterinario) REFERENCES usuario(id_usuario) ON DELETE SET NULL,
    FOREIGN KEY (id_tipo_historial) REFERENCES tipo_historial(id_tipo_historial) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE documento (
    id_documento INT AUTO_INCREMENT PRIMARY KEY,
    id_mascota INT NOT NULL,
    id_tipo_documento INT NOT NULL,
    nombre_doc VARCHAR(150) NOT NULL,
    archivo_url VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_mascota) REFERENCES mascota(id_mascota) ON DELETE CASCADE,
    FOREIGN KEY (id_tipo_documento) REFERENCES tipo_documento(id_tipo_documento) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE ubicacion_extravio (
    id_ubicacion_extravio INT AUTO_INCREMENT PRIMARY KEY,
    id_mascota INT NOT NULL,
    reportado_extraviado BOOLEAN DEFAULT FALSE,
    ultima_ubicacion VARCHAR(255),
    fecha_registro DATETIME,
    notificaciones_activas BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_mascota) REFERENCES mascota(id_mascota) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE chat_mensaje (
    id_chat_mensaje INT AUTO_INCREMENT PRIMARY KEY,
    id_mascota INT NOT NULL,
    id_remitente INT NOT NULL,
    id_destinatario INT DEFAULT NULL,
    es_bot BOOLEAN DEFAULT FALSE,
    mensaje TEXT NOT NULL,
    leido BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_mascota) REFERENCES mascota(id_mascota) ON DELETE CASCADE,
    FOREIGN KEY (id_remitente) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_destinatario) REFERENCES usuario(id_usuario) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE suscripcion (
    id_suscripcion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_tipo_plan INT NOT NULL,
    id_tipo_estado_suscripcion INT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_tipo_plan) REFERENCES tipo_plan(id_tipo_plan) ON DELETE RESTRICT,
    FOREIGN KEY (id_tipo_estado_suscripcion) REFERENCES tipo_estado_suscripcion(id_tipo_estado_suscripcion) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE pago (
    id_pago INT AUTO_INCREMENT PRIMARY KEY,
    id_suscripcion INT NOT NULL,
    id_tipo_estado_pago INT NOT NULL,
    monto DECIMAL(10, 2) NOT NULL,
    metodo_pago VARCHAR(50) DEFAULT 'Tarjeta Crédito/Débito',
    fecha_pago DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_suscripcion) REFERENCES suscripcion(id_suscripcion) ON DELETE CASCADE,
    FOREIGN KEY (id_tipo_estado_pago) REFERENCES tipo_estado_pago(id_tipo_estado_pago) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ========================================================
-- 3. INSERCIÓN DE DATOS INICIALES EN TABLAS CATÁLOGO
-- ========================================================

INSERT INTO tipo_usuario (nombre_tipo, descripcion_tipo) VALUES
('Tutor', 'Dueño registrado de la mascota'),
('Veterinario', 'Médico veterinario verificado con permisos de edición sanitaria'),
('Administrador', 'Administrador global de la plataforma');

INSERT INTO tipo_especie (nombre_tipo, descripcion_tipo) VALUES
('Perro', 'Canino doméstico'),
('Gato', 'Felino doméstico'),
('Otro', 'Otras especies menores');

INSERT INTO tipo_estado_dispositivo (nombre_tipo, descripcion_tipo) VALUES
('Activo', 'Placa NFC/QR vinculada y operativa'),
('Inactivo', 'Placa no asignada o desactivada'),
('Perdido', 'Placa o collar reportado como extraviado');

INSERT INTO tipo_historial (nombre_tipo, descripcion_tipo) VALUES
('Vacuna', 'Registro de vacunas administradas'),
('Desparasitación', 'Tratamientos desparasitantes internos/externos'),
('Control', 'Chequeo médico veterinario general'),
('Urgencia', 'Atención médica por emergencia');

INSERT INTO tipo_documento (nombre_tipo, descripcion_tipo) VALUES
('Cartilla de vacunación', 'Carnet digital de vacunas de la mascota'),
('Certificado veterinario', 'Certificados de salud y viajes'),
('Documento de adopción', 'Certificado o ficha de adopción'),
('Seguro de mascota', 'Póliza de seguro médico veterinario');

INSERT INTO tipo_plan (nombre_tipo, descripcion_tipo) VALUES
('Gratis', 'Acceso básico, ficha NFC, citas y chatbot'),
('Premium', 'Almacenamiento ilimitado, chat con veterinarios y recordatorios');

INSERT INTO tipo_estado_suscripcion (nombre_tipo, descripcion_tipo) VALUES
('Activa', 'Suscripción vigente y pagada'),
('Cancelada', 'Suscripción cancelada por el usuario'),
('Morosa', 'Pago pendiente o rechazado');

INSERT INTO tipo_estado_pago (nombre_tipo, descripcion_tipo) VALUES
('Completado', 'Transacción aprobada con éxito'),
('Pendiente', 'Pago en proceso de validación'),
('Fallido', 'Transacción rechazada por la pasarela');