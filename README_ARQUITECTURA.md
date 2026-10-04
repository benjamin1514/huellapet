# HuellaPet - arquitectura implementada

## Acceso público
- `GET/POST /dashboard`: ingreso manual del código.
- `GET /dashboard/<codigo>`: ficha pública por `codigo_uid`, `token_qr` o `codigo_huellapet`.
- Salud, vacunas/historial y alergias/condiciones se muestran públicamente.
- Los documentos NO se consultan ni muestran salvo que la sesión corresponda al tutor.
- Si la mascota está extraviada, el navegador solicita geolocalización y, con permiso del visitante, registra un `avistamiento`.

## Tutor
- `/login`, `/registro`, `/logout`.
- `/mi-cuenta`: mascotas del tutor.
- Documentos privados protegidos por sesión + propiedad de la mascota.
- El tutor puede activar/desactivar el estado de extravío.

## Veterinario
- `/veterinario`: protegido por rol.
- CRUD backend de mascota: crear, editar y eliminar.
- Alta de historial médico firmada con el usuario veterinario de la sesión.

## Frontend
Las plantillas agregadas son deliberadamente mínimas/provisionales. Sirven para probar las rutas y permisos sin terminar ni reemplazar el frontend del wireframe.

## BD
Se agregó `avistamiento` para no sobrescribir una única ubicación: cada persona que escanea una mascota extraviada y acepta compartir ubicación genera un registro independiente.


## Correcciones de sesión y veterinario
- La sesión persistente guarda `id_usuario` durante 30 días.
- El rol se consulta desde MySQL en cada ruta protegida; no se confía en un texto de rol guardado en sesión.
- Las cuentas insertadas manualmente con contraseña en texto plano pueden iniciar sesión una vez en desarrollo; al hacerlo, la contraseña se migra automáticamente a bcrypt.
- El panel veterinario incluye formularios provisionales para crear/editar/eliminar mascotas y agregar historial clínico.
- En producción define una `SECRET_KEY` fija en `.env`. No la cambies entre reinicios o invalidarás las sesiones existentes.
