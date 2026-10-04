CREATE DATABASE IF NOT EXISTS huellapet_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE huellapet_db;

-- ========================================================
-- 1. TABLAS CATÁLOGO / TIPOS (3NF)
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

CREATE TABLE tipo_sexo (
    id_tipo_sexo INT AUTO_INCREMENT PRIMARY KEY,
    nombre_tipo VARCHAR(20) NOT NULL UNIQUE,
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
-- 2. USUARIOS Y ROLES (TUTOR Y VETERINARIO)
-- ========================================================

-- Cuenta universal de acceso (Gestionada por cada usuario)
CREATE TABLE usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    id_tipo_usuario INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    direccion VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_tipo_usuario) REFERENCES tipo_usuario(id_tipo_usuario) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Perfil profesional independiente para Veterinarios (Evita NULLs en tutores)
CREATE TABLE perfil_veterinario (
    id_perfil_veterinario INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE,
    numero_colegiado VARCHAR(50) NOT NULL,
    es_verificado BOOLEAN DEFAULT FALSE,
    especialidad VARCHAR(100) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ========================================================
-- 3. MASCOTAS Y DISPOSITIVOS (INFORMACIÓN DEL TUTOR)
-- ========================================================

CREATE TABLE mascota (
    id_mascota INT AUTO_INCREMENT PRIMARY KEY,
    id_tutor INT NOT NULL,
    id_tipo_especie INT NOT NULL,
    id_tipo_sexo INT NOT NULL,
    codigo_huellapet VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    raza VARCHAR(100),
    fecha_nacimiento DATE,
    peso_kg DECIMAL(5, 2),
    descripcion TEXT,
    foto_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_tutor) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_tipo_especie) REFERENCES tipo_especie(id_tipo_especie) ON DELETE RESTRICT,
    FOREIGN KEY (id_tipo_sexo) REFERENCES tipo_sexo(id_tipo_sexo) ON DELETE RESTRICT
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

-- ========================================================
-- 4. REGISTROS CLÍNICOS (EXCLUSIVO INGRESO VETERINARIO)
-- ========================================================

-- Historial Médico y Ficha de Salud (Firmado por el veterinario que lo registra)
CREATE TABLE historial_medico (
    id_historial_medico INT AUTO_INCREMENT PRIMARY KEY,
    id_mascota INT NOT NULL,
    id_veterinario INT NOT NULL, -- Clave al usuario profesional
    id_tipo_historial INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT NOT NULL,
    fecha_atencion DATE NOT NULL,
    proxima_fecha DATE DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_mascota) REFERENCES mascota(id_mascota) ON DELETE CASCADE,
    FOREIGN KEY (id_veterinario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT,
    FOREIGN KEY (id_tipo_historial) REFERENCES tipo_historial(id_tipo_historial) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Registro de Alergias y Condiciones Crónicas (Ingresado por Veterinario)
CREATE TABLE alergia_condicion (
    id_alergia_condicion INT AUTO_INCREMENT PRIMARY KEY,
    id_mascota INT NOT NULL,
    id_veterinario INT NOT NULL,
    nombre_condicion VARCHAR(150) NOT NULL,
    gravedad VARCHAR(50) DEFAULT 'Moderada',
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_mascota) REFERENCES mascota(id_mascota) ON DELETE CASCADE,
    FOREIGN KEY (id_veterinario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ========================================================
-- 5. DOCUMENTOS, EXTRAVÍO Y MENSAJERÍA
-- ========================================================

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

-- ========================================================
-- 6. MODELO FREEMIUM Y PAGOS
-- ========================================================

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
-- 7. CARGA DE DATOS SEMILLA EN CATALOGOS
-- ========================================================

INSERT INTO tipo_usuario (nombre_tipo, descripcion_tipo) VALUES
('Tutor', 'Dueño registrado de la mascota'),
('Veterinario', 'Médico profesional habilitado para ingresar registros de salud'),
('Administrador', 'Administrador general del sistema');

INSERT INTO tipo_especie (nombre_tipo, descripcion_tipo) VALUES
('Perro', 'Canino doméstico'),
('Gato', 'Felino doméstico'),
('Otro', 'Otras especies menores');

INSERT INTO tipo_sexo (nombre_tipo, descripcion_tipo) VALUES
('Macho', 'Sexo genético masculino'),
('Hembra', 'Sexo genético femenino');

INSERT INTO tipo_estado_dispositivo (nombre_tipo, descripcion_tipo) VALUES
('Activo', 'Placa NFC/QR vinculada y operativa'),
('Inactivo', 'Placa no asignada o desactivada'),
('Perdido', 'Placa o collar reportado como extraviado');

INSERT INTO tipo_historial (nombre_tipo, descripcion_tipo) VALUES
('Vacuna', 'Registro de vacunas aplicadas por un profesional'),
('Desparasitación', 'Tratamientos desparasitantes internos/externos'),
('Control', 'Chequeo médico de rutina o diagnóstico'),
('Urgencia', 'Atención médica por condición crítica');

INSERT INTO tipo_documento (nombre_tipo, descripcion_tipo) VALUES
('Cartilla de vacunación', 'Carnet digital de vacunas de la mascota'),
('Certificado veterinario', 'Certificados de salud y viajes'),
('Documento de adopción', 'Ficha o contrato de adopción'),
('Seguro de mascota', 'Póliza de seguro de salud veterinario');

INSERT INTO tipo_plan (nombre_tipo, descripcion_tipo) VALUES
('Gratis', 'Plan básico: ficha NFC y asistencia chatbot'),
('Premium', 'Plan avanzado: almacenamiento ilimitado, chat vet y recordatorios');

INSERT INTO tipo_estado_suscripcion (nombre_tipo, descripcion_tipo) VALUES
('Activa', 'Suscripción vigente'),
('Cancelada', 'Suscripción finalizada por el usuario'),
('Morosa', 'Suscripción suspendida por pago pendiente');

INSERT INTO tipo_estado_pago (nombre_tipo, descripcion_tipo) VALUES
('Completado', 'Transacción aprobada'),
('Pendiente', 'Pago en proceso de confirmación'),
('Fallido', 'Transacción rechazada');

-- ========================================================
-- 8. AVISTAMIENTOS POR ESCANEO DE MASCOTA EXTRAVIADA
-- ========================================================
CREATE TABLE avistamiento (
    id_avistamiento INT AUTO_INCREMENT PRIMARY KEY,
    id_mascota INT NOT NULL,
    latitud DECIMAL(10, 8) NOT NULL,
    longitud DECIMAL(11, 8) NOT NULL,
    precision_metros DECIMAL(10, 2) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_mascota) REFERENCES mascota(id_mascota) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Roles mínimos esperados por el controller.
INSERT IGNORE INTO tipo_usuario (id_tipo_usuario,nombre_tipo,descripcion_tipo) VALUES
(1,'Tutor','Dueño o tutor de mascotas'),
(2,'Veterinario','Profesional veterinario');
