-- ========================================================
-- CAMBIOS PARA CUMPLIR EL PITCH DE HUELLAPET
-- Ejecutar UNA SOLA VEZ, después de esquema_huellapet.sql.
-- No borra ni modifica datos existentes.
-- ========================================================

USE huellapet_db;

-- --------------------------------------------------------
-- 1. Firma digital del veterinario en cada registro clínico
-- --------------------------------------------------------
ALTER TABLE historial_medico
    ADD COLUMN firma_digital VARCHAR(64) DEFAULT NULL;

-- --------------------------------------------------------
-- 2. Seguridad a nivel de base de datos:
--    solo un usuario con perfil de veterinario puede firmar
--    registros clínicos y registrar alergias o condiciones.
--    (Si falla, hay registros con un id_veterinario sin perfil veterinario)
-- --------------------------------------------------------
ALTER TABLE historial_medico
    ADD CONSTRAINT fk_historial_solo_veterinario
    FOREIGN KEY (id_veterinario) REFERENCES perfil_veterinario(id_usuario) ON DELETE RESTRICT;

ALTER TABLE alergia_condicion
    ADD CONSTRAINT fk_alergia_solo_veterinario
    FOREIGN KEY (id_veterinario) REFERENCES perfil_veterinario(id_usuario) ON DELETE RESTRICT;

-- --------------------------------------------------------
-- 3. Alertas de vacuna que programa el tutor
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerta_vacuna (
    id_alerta_vacuna INT AUTO_INCREMENT PRIMARY KEY,
    id_mascota INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    fecha_alerta DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_mascota) REFERENCES mascota(id_mascota) ON DELETE CASCADE
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 4. Clínicas asociadas y citas médicas
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS clinica (
    id_clinica INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    direccion VARCHAR(255) DEFAULT NULL,
    telefono VARCHAR(30) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS cita (
    id_cita INT AUTO_INCREMENT PRIMARY KEY,
    id_mascota INT NOT NULL,
    id_clinica INT NOT NULL,
    fecha_hora DATETIME NOT NULL,
    motivo VARCHAR(255) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Pendiente',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_mascota) REFERENCES mascota(id_mascota) ON DELETE CASCADE,
    FOREIGN KEY (id_clinica) REFERENCES clinica(id_clinica) ON DELETE RESTRICT
) ENGINE=InnoDB;
