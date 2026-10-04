import os
import secrets
from functools import wraps

import bcrypt
from flask import flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from flask_app import app
from flask_app.models.alergia_condicion import AlergiaCondicion
from flask_app.models.avistamiento import Avistamiento
from flask_app.models.catalogo import Catalogo
from flask_app.models.dispositivo_nfc import DispositivoNFC
from flask_app.models.documento import Documento
from flask_app.models.historial_medico import HistorialMedico
from flask_app.models.mascota import Mascota
from flask_app.models.pago import Pago
from flask_app.models.perfil_veterinario import PerfilVeterinario
from flask_app.models.suscripcion import Suscripcion
from flask_app.models.ubicacion_extravio import UbicacionExtravio
from flask_app.models.usuario import Usuario

IMAGENES_PERMITIDAS = {'jpg', 'jpeg', 'png', 'webp'}
DOCUMENTOS_PERMITIDOS = {'pdf', 'jpg', 'jpeg', 'png', 'webp'}


def usuario_actual():
    id_usuario = session.get('id_usuario')
    return Usuario.get_with_type(id_usuario) if id_usuario else None


def rol_actual():
    usuario = usuario_actual()
    return str(getattr(usuario, 'tipo_nombre', '')).strip().casefold() if usuario else ''


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if usuario_actual() is None:
            session.clear()
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


def role_required(nombre_rol):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if usuario_actual() is None:
                session.clear()
                flash('Debes iniciar sesión.', 'warning')
                return redirect(url_for('login'))
            if rol_actual() != nombre_rol.casefold():
                return ('No autorizado', 403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


veterinario_required = role_required('veterinario')
admin_required = role_required('administrador')


def es_dueno(mascota):
    return mascota is not None and session.get('id_usuario') == mascota.id_tutor


def extension_permitida(nombre, permitidas):
    return '.' in nombre and nombre.rsplit('.', 1)[1].lower() in permitidas


def guardar_archivo(archivo, carpeta, permitidas):
    if not archivo or not archivo.filename:
        return None
    if not extension_permitida(archivo.filename, permitidas):
        raise ValueError('Tipo de archivo no permitido.')
    extension = secure_filename(archivo.filename).rsplit('.', 1)[1].lower()
    nombre = f"{secrets.token_hex(16)}.{extension}"
    archivo.save(os.path.join(carpeta, nombre))
    return nombre


def datos_mascota_form(id_tutor):
    return {
        'id_tutor': id_tutor,
        'id_tipo_especie': request.form.get('id_tipo_especie'),
        'id_tipo_sexo': request.form.get('id_tipo_sexo'),
        'nombre': request.form.get('nombre', '').strip(),
        'raza': request.form.get('raza', '').strip() or None,
        'fecha_nacimiento': request.form.get('fecha_nacimiento') or None,
        'peso_kg': request.form.get('peso_kg') or None,
        'descripcion': request.form.get('descripcion', '').strip() or None,
    }


@app.route('/')
def inicio():
    return redirect(url_for('acceso_dashboard'))


@app.route('/dashboard', methods=['GET', 'POST'])
def acceso_dashboard():
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        if codigo:
            return redirect(url_for('dashboard_publico', codigo=codigo))
        flash('Ingresa el código HuellaPet/NFC.', 'danger')
    return render_template('publico/acceso.html')


@app.route('/dashboard/<codigo>')
def dashboard_publico(codigo):
    mascota = Mascota.get_by_nfc(codigo)
    if mascota is None:
        return ('Mascota no encontrada', 404)
    return render_template(
        'publico/dashboard.html',
        mascota=mascota,
        salud=HistorialMedico.get_by_mascota(mascota.id_mascota),
        condiciones=AlergiaCondicion.get_by_mascota(mascota.id_mascota),
        extravio=UbicacionExtravio.get_active_by_mascota(mascota.id_mascota),
        es_dueno=es_dueno(mascota),
    )


@app.route('/api/dashboard/<codigo>/ubicacion', methods=['POST'])
def registrar_ubicacion(codigo):
    mascota = Mascota.get_by_nfc(codigo)
    if mascota is None:
        return jsonify({'ok': False, 'error': 'Mascota no encontrada'}), 404
    if UbicacionExtravio.get_active_by_mascota(mascota.id_mascota) is None:
        return jsonify({'ok': False, 'error': 'La mascota no está extraviada'}), 403
    payload = request.get_json(silent=True) or request.form
    try:
        latitud = float(payload.get('latitud'))
        longitud = float(payload.get('longitud'))
        precision = payload.get('precision_metros')
        precision = float(precision) if precision not in (None, '') else None
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'Ubicación inválida'}), 400
    if not (-90 <= latitud <= 90 and -180 <= longitud <= 180):
        return jsonify({'ok': False, 'error': 'Coordenadas fuera de rango'}), 400
    Avistamiento.save({'id_mascota': mascota.id_mascota, 'latitud': latitud, 'longitud': longitud, 'precision_metros': precision})
    return jsonify({'ok': True})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = Usuario.get_by_email(request.form.get('email', '').strip())
        password_texto = request.form.get('password', '')
        valido = False
        if usuario:
            try:
                valido = bcrypt.checkpw(password_texto.encode(), usuario.password.encode())
            except (ValueError, TypeError):
                valido = password_texto == usuario.password
                if valido:
                    Usuario.update_password(usuario.id_usuario, bcrypt.hashpw(password_texto.encode(), bcrypt.gensalt()).decode())
        if valido:
            session.clear()
            session.permanent = True
            session['id_usuario'] = usuario.id_usuario
            rol = rol_actual()
            if rol == 'veterinario':
                return redirect(url_for('panel_veterinario'))
            if rol == 'administrador':
                return redirect(url_for('panel_admin'))
            return redirect(url_for('mi_cuenta'))
        flash('Correo o contraseña incorrectos.', 'danger')
    return render_template('auth/login.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not nombre or not email or not password:
            flash('Nombre, correo y contraseña son obligatorios.', 'danger')
            return redirect(url_for('registro'))
        if Usuario.get_by_email(email):
            flash('Ese correo ya está registrado.', 'danger')
            return redirect(url_for('registro'))
        id_tutor = Usuario.get_role_id('Tutor')
        if id_tutor is None:
            return ('No existe el rol Tutor en la base de datos', 500)
        Usuario.save({
            'id_tipo_usuario': id_tutor, 'nombre': nombre, 'email': email,
            'password': bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            'telefono': request.form.get('telefono', '').strip() or None,
            'direccion': request.form.get('direccion', '').strip() or None,
        })
        flash('Cuenta creada. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/registro.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('acceso_dashboard'))


@app.route('/mi-cuenta')
@login_required
def mi_cuenta():
    if rol_actual() == 'veterinario':
        return redirect(url_for('panel_veterinario'))
    if rol_actual() == 'administrador':
        return redirect(url_for('panel_admin'))
    return render_template('dueno/mi_cuenta.html', mascotas=Mascota.get_by_tutor(session['id_usuario']))


@app.route('/mi-cuenta/mascotas')
@login_required
def mis_mascotas():
    return render_template('dueno/mascotas.html', mascotas=Mascota.get_by_tutor(session['id_usuario']))


@app.route('/mi-cuenta/mascotas/<int:id_mascota>')
@login_required
def mi_mascota(id_mascota):
    mascota = Mascota.get_by_id(id_mascota)
    if not es_dueno(mascota):
        return ('Mascota no encontrada' if mascota is None else 'No autorizado', 404 if mascota is None else 403)
    return render_template('dueno/mascota.html', mascota=mascota)


@app.route('/mi-cuenta/mascotas/crear', methods=['POST'])
@login_required
def crear_mi_mascota():
    data = datos_mascota_form(session['id_usuario'])
    if not data['nombre'] or not data['id_tipo_especie'] or not data['id_tipo_sexo']:
        flash('Nombre, especie y sexo son obligatorios.', 'danger')
        return redirect(url_for('mi_cuenta'))
    data['codigo_huellapet'] = Mascota.generar_codigo()
    data['foto_url'] = None
    foto = request.files.get('foto')
    try:
        nombre_foto = guardar_archivo(foto, app.config['UPLOAD_MASCOTAS'], IMAGENES_PERMITIDAS)
        if nombre_foto:
            data['foto_url'] = f"uploads/mascotas/{nombre_foto}"
    except ValueError as error:
        flash(str(error), 'danger')
        return redirect(url_for('mi_cuenta'))
    Mascota.save(data)
    flash('Mascota creada correctamente.', 'success')
    return redirect(url_for('mi_cuenta'))


@app.route('/mi-cuenta/mascotas/<int:id_mascota>/editar', methods=['POST'])
@login_required
def editar_mi_mascota(id_mascota):
    mascota = Mascota.get_by_id(id_mascota)
    if not es_dueno(mascota):
        return ('No autorizado', 403)
    data = datos_mascota_form(session['id_usuario'])
    data['id_mascota'] = id_mascota
    Mascota.update(data)
    flash('Mascota actualizada.', 'success')
    return redirect(url_for('mi_mascota', id_mascota=id_mascota))


@app.route('/mi-cuenta/mascotas/<int:id_mascota>/foto', methods=['POST'])
@login_required
def cambiar_foto_mascota(id_mascota):
    mascota = Mascota.get_by_id(id_mascota)
    if not es_dueno(mascota):
        return ('No autorizado', 403)
    try:
        nombre = guardar_archivo(request.files.get('foto'), app.config['UPLOAD_MASCOTAS'], IMAGENES_PERMITIDAS)
    except ValueError as error:
        flash(str(error), 'danger')
        return redirect(url_for('mi_mascota', id_mascota=id_mascota))
    if not nombre:
        flash('Debes seleccionar una fotografía.', 'danger')
    else:
        Mascota.update_foto(id_mascota, f"uploads/mascotas/{nombre}")
        flash('Fotografía actualizada.', 'success')
    return redirect(url_for('mi_mascota', id_mascota=id_mascota))


@app.route('/mi-cuenta/mascotas/<int:id_mascota>/documentos')
@login_required
def documentos_privados(id_mascota):
    mascota = Mascota.get_by_id(id_mascota)
    if not es_dueno(mascota):
        return ('No autorizado', 403)
    return render_template('dueno/documentos.html', mascota=mascota, documentos=Documento.get_by_mascota(id_mascota), tipos_documento=Catalogo.tipos_documento())


@app.route('/mi-cuenta/mascotas/<int:id_mascota>/documentos/crear', methods=['POST'])
@login_required
def crear_documento(id_mascota):
    mascota = Mascota.get_by_id(id_mascota)
    if not es_dueno(mascota):
        return ('No autorizado', 403)
    try:
        nombre = guardar_archivo(request.files.get('documento'), app.config['UPLOAD_DOCUMENTOS'], DOCUMENTOS_PERMITIDOS)
    except ValueError as error:
        flash(str(error), 'danger')
        return redirect(url_for('documentos_privados', id_mascota=id_mascota))
    if not nombre:
        flash('Debes seleccionar un documento.', 'danger')
        return redirect(url_for('documentos_privados', id_mascota=id_mascota))
    Documento.save({
        'id_mascota': id_mascota,
        'id_tipo_documento': request.form.get('id_tipo_documento'),
        'nombre_doc': request.form.get('nombre_doc', '').strip() or request.files['documento'].filename,
        'archivo_url': f"uploads/documentos/{nombre}",
    })
    flash('Documento guardado.', 'success')
    return redirect(url_for('documentos_privados', id_mascota=id_mascota))


@app.route('/mi-cuenta/mascotas/<int:id_mascota>/documentos/<int:id_documento>/eliminar', methods=['POST'])
@login_required
def eliminar_documento(id_mascota, id_documento):
    mascota = Mascota.get_by_id(id_mascota)
    documento = Documento.get_by_id(id_documento)
    if not es_dueno(mascota) or documento is None or documento.id_mascota != id_mascota:
        return ('No autorizado', 403)
    Documento.delete(id_documento)
    flash('Documento eliminado.', 'success')
    return redirect(url_for('documentos_privados', id_mascota=id_mascota))


@app.route('/mi-cuenta/mascotas/<int:id_mascota>/extravio', methods=['POST'])
@login_required
def cambiar_extravio(id_mascota):
    mascota = Mascota.get_by_id(id_mascota)
    if not es_dueno(mascota):
        return ('No autorizado', 403)
    activo = request.form.get('extraviado') == '1'
    UbicacionExtravio.set_estado({'id_mascota': id_mascota, 'reportado_extraviado': int(activo), 'notificaciones_activas': int(activo)})
    flash('Estado de extravío actualizado.', 'success')
    return redirect(url_for('mi_mascota', id_mascota=id_mascota))


@app.route('/mi-cuenta/mascotas/<int:id_mascota>/avistamientos')
@login_required
def avistamientos_mascota(id_mascota):
    mascota = Mascota.get_by_id(id_mascota)
    if not es_dueno(mascota):
        return ('No autorizado', 403)
    return render_template('dueno/avistamientos.html', mascota=mascota, avistamientos=Avistamiento.get_by_mascota(id_mascota))


@app.route('/veterinario')
@app.route('/veterinario/mascotas')
@veterinario_required
def panel_veterinario():
    return render_template('veterinario/mascotas.html', mascotas=Mascota.get_all_with_details(), tutores=Usuario.get_all_tutores(), especies=Catalogo.especies(), sexos=Catalogo.sexos())


@app.route('/veterinario/mascotas/<int:id_mascota>')
@veterinario_required
def veterinario_mascota(id_mascota):
    mascota = Mascota.get_by_id(id_mascota)
    if mascota is None:
        return ('Mascota no encontrada', 404)
    return render_template('veterinario/mascota.html', mascota=mascota, historial=HistorialMedico.get_by_mascota(id_mascota), condiciones=AlergiaCondicion.get_by_mascota(id_mascota), tutores=Usuario.get_all_tutores(), especies=Catalogo.especies(), sexos=Catalogo.sexos(), tipos_historial=Catalogo.tipos_historial())


@app.route('/veterinario/mascotas/crear', methods=['POST'])
@veterinario_required
def veterinario_crear_mascota():
    data = datos_mascota_form(request.form.get('id_tutor'))
    if not data['id_tutor'] or not data['nombre'] or not data['id_tipo_especie'] or not data['id_tipo_sexo']:
        flash('Tutor, nombre, especie y sexo son obligatorios.', 'danger')
        return redirect(url_for('panel_veterinario'))
    data['codigo_huellapet'] = Mascota.generar_codigo()
    data['foto_url'] = None
    try:
        nombre = guardar_archivo(request.files.get('foto'), app.config['UPLOAD_MASCOTAS'], IMAGENES_PERMITIDAS)
        if nombre:
            data['foto_url'] = f"uploads/mascotas/{nombre}"
    except ValueError as error:
        flash(str(error), 'danger')
        return redirect(url_for('panel_veterinario'))
    Mascota.save(data)
    flash('Mascota creada.', 'success')
    return redirect(url_for('panel_veterinario'))


@app.route('/veterinario/mascotas/<int:id_mascota>/editar', methods=['POST'])
@veterinario_required
def veterinario_editar_mascota(id_mascota):
    if Mascota.get_by_id(id_mascota) is None:
        return ('Mascota no encontrada', 404)
    data = datos_mascota_form(request.form.get('id_tutor'))
    data['id_mascota'] = id_mascota
    Mascota.update(data)
    flash('Mascota actualizada.', 'success')
    return redirect(url_for('veterinario_mascota', id_mascota=id_mascota))


@app.route('/veterinario/mascotas/<int:id_mascota>/eliminar', methods=['POST'])
@veterinario_required
def veterinario_eliminar_mascota(id_mascota):
    if Mascota.get_by_id(id_mascota) is None:
        return ('Mascota no encontrada', 404)
    Mascota.delete(id_mascota)
    flash('Mascota eliminada.', 'success')
    return redirect(url_for('panel_veterinario'))


@app.route('/veterinario/mascotas/<int:id_mascota>/historial')
@veterinario_required
def veterinario_historial(id_mascota):
    mascota = Mascota.get_by_id(id_mascota)
    if mascota is None:
        return ('Mascota no encontrada', 404)
    return render_template('veterinario/historial.html', mascota=mascota, historial=HistorialMedico.get_by_mascota(id_mascota), tipos_historial=Catalogo.tipos_historial())


@app.route('/veterinario/mascotas/<int:id_mascota>/historial/crear', methods=['POST'])
@veterinario_required
def veterinario_crear_historial(id_mascota):
    if Mascota.get_by_id(id_mascota) is None:
        return ('Mascota no encontrada', 404)
    HistorialMedico.save({'id_mascota': id_mascota, 'id_veterinario': session['id_usuario'], 'id_tipo_historial': request.form.get('id_tipo_historial'), 'titulo': request.form.get('titulo', '').strip(), 'descripcion': request.form.get('descripcion', '').strip(), 'fecha_atencion': request.form.get('fecha_atencion'), 'proxima_fecha': request.form.get('proxima_fecha') or None})
    flash('Registro clínico agregado.', 'success')
    return redirect(url_for('veterinario_historial', id_mascota=id_mascota))


@app.route('/veterinario/historial/<int:id_historial>/editar', methods=['POST'])
@veterinario_required
def veterinario_editar_historial(id_historial):
    historial = HistorialMedico.get_by_id(id_historial)
    if historial is None:
        return ('Registro no encontrado', 404)
    HistorialMedico.update({'id_historial_medico': id_historial, 'id_tipo_historial': request.form.get('id_tipo_historial'), 'titulo': request.form.get('titulo', '').strip(), 'descripcion': request.form.get('descripcion', '').strip(), 'fecha_atencion': request.form.get('fecha_atencion'), 'proxima_fecha': request.form.get('proxima_fecha') or None})
    flash('Registro actualizado.', 'success')
    return redirect(url_for('veterinario_historial', id_mascota=historial.id_mascota))


@app.route('/veterinario/historial/<int:id_historial>/eliminar', methods=['POST'])
@veterinario_required
def veterinario_eliminar_historial(id_historial):
    historial = HistorialMedico.get_by_id(id_historial)
    if historial is None:
        return ('Registro no encontrado', 404)
    HistorialMedico.delete(id_historial)
    flash('Registro eliminado.', 'success')
    return redirect(url_for('veterinario_historial', id_mascota=historial.id_mascota))


@app.route('/admin')
@admin_required
def panel_admin():
    return render_template('admin/index.html', usuarios=Usuario.get_all(), mascotas=Mascota.get_all_with_details(), veterinarios=PerfilVeterinario.get_all())


@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    return render_template('admin/usuarios.html', usuarios=Usuario.get_all())


@app.route('/admin/usuarios/<int:id_usuario>')
@admin_required
def admin_usuario(id_usuario):
    usuario = Usuario.get_with_type(id_usuario)
    if usuario is None:
        return ('Usuario no encontrado', 404)
    return render_template('admin/usuario.html', usuario=usuario)


@app.route('/admin/usuarios/<int:id_usuario>/editar', methods=['POST'])
@admin_required
def admin_editar_usuario(id_usuario):
    if Usuario.get_by_id(id_usuario) is None:
        return ('Usuario no encontrado', 404)
    Usuario.update({'id_usuario': id_usuario, 'id_tipo_usuario': request.form.get('id_tipo_usuario'), 'nombre': request.form.get('nombre', '').strip(), 'email': request.form.get('email', '').strip(), 'telefono': request.form.get('telefono', '').strip() or None, 'direccion': request.form.get('direccion', '').strip() or None})
    flash('Usuario actualizado.', 'success')
    return redirect(url_for('admin_usuario', id_usuario=id_usuario))


@app.route('/admin/usuarios/<int:id_usuario>/eliminar', methods=['POST'])
@admin_required
def admin_eliminar_usuario(id_usuario):
    if id_usuario == session.get('id_usuario'):
        flash('No puedes eliminar tu propia cuenta administrativa.', 'danger')
        return redirect(url_for('admin_usuarios'))
    Usuario.delete(id_usuario)
    flash('Usuario eliminado.', 'success')
    return redirect(url_for('admin_usuarios'))


@app.route('/admin/veterinarios')
@admin_required
def admin_veterinarios():
    return render_template('admin/veterinarios.html', veterinarios=PerfilVeterinario.get_all())


@app.route('/admin/veterinarios/crear', methods=['GET', 'POST'])
@admin_required
def admin_crear_veterinario():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if Usuario.get_by_email(email):
            flash('Ese correo ya existe.', 'danger')
            return redirect(url_for('admin_crear_veterinario'))
        id_rol = Usuario.get_role_id('Veterinario')
        if id_rol is None:
            return ('No existe el rol Veterinario', 500)
        password = request.form.get('password', '')
        id_usuario = Usuario.save({'id_tipo_usuario': id_rol, 'nombre': request.form.get('nombre', '').strip(), 'email': email, 'password': bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(), 'telefono': request.form.get('telefono', '').strip() or None, 'direccion': request.form.get('direccion', '').strip() or None})
        PerfilVeterinario.save({'id_usuario': id_usuario, 'numero_colegiado': request.form.get('numero_colegiado', '').strip(), 'es_verificado': 0, 'especialidad': request.form.get('especialidad', '').strip() or None})
        flash('Veterinario creado.', 'success')
        return redirect(url_for('admin_veterinarios'))
    return render_template('admin/veterinario_crear.html')


@app.route('/admin/veterinarios/<int:id_veterinario>')
@admin_required
def admin_veterinario(id_veterinario):
    perfil = PerfilVeterinario.get_by_id(id_veterinario)
    if perfil is None:
        return ('Veterinario no encontrado', 404)
    return render_template('admin/veterinario.html', veterinario=perfil, usuario=Usuario.get_with_type(perfil.id_usuario))


@app.route('/admin/veterinarios/<int:id_veterinario>/editar', methods=['POST'])
@admin_required
def admin_editar_veterinario(id_veterinario):
    if PerfilVeterinario.get_by_id(id_veterinario) is None:
        return ('Veterinario no encontrado', 404)
    PerfilVeterinario.update({'id_perfil_veterinario': id_veterinario, 'numero_colegiado': request.form.get('numero_colegiado', '').strip(), 'especialidad': request.form.get('especialidad', '').strip() or None})
    flash('Perfil veterinario actualizado.', 'success')
    return redirect(url_for('admin_veterinario', id_veterinario=id_veterinario))


@app.route('/admin/veterinarios/<int:id_veterinario>/verificar', methods=['POST'])
@admin_required
def admin_verificar_veterinario(id_veterinario):
    PerfilVeterinario.verify(id_veterinario, request.form.get('verificado') == '1')
    flash('Estado de verificación actualizado.', 'success')
    return redirect(url_for('admin_veterinario', id_veterinario=id_veterinario))


@app.route('/admin/mascotas')
@admin_required
def admin_mascotas():
    return render_template('admin/mascotas.html', mascotas=Mascota.get_all_with_details())


@app.route('/admin/mascotas/<int:id_mascota>')
@admin_required
def admin_mascota(id_mascota):
    mascota = Mascota.get_by_id(id_mascota)
    if mascota is None:
        return ('Mascota no encontrada', 404)
    return render_template('admin/mascota.html', mascota=mascota)


@app.route('/admin/dispositivos')
@admin_required
def admin_dispositivos():
    return render_template('admin/dispositivos.html', dispositivos=DispositivoNFC.get_all())


@app.route('/admin/suscripciones')
@admin_required
def admin_suscripciones():
    return render_template('admin/suscripciones.html', suscripciones=Suscripcion.get_all())


@app.route('/admin/pagos')
@admin_required
def admin_pagos():
    return render_template('admin/pagos.html', pagos=Pago.get_all())
