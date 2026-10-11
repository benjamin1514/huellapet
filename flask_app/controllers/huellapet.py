import hashlib
import hmac
import os
import secrets
from datetime import date, datetime, timedelta
from functools import wraps

import bcrypt
from flask import flash, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.utils import secure_filename

from flask_app import app
from flask_app.models.alergia_condicion import AlergiaCondicion
from flask_app.models.alerta_vacuna import AlertaVacuna
from flask_app.models.avistamiento import Avistamiento
from flask_app.models.catalogo import Catalogo
from flask_app.models.chat_mensaje import ChatMensaje
from flask_app.models.cita import Cita
from flask_app.models.clinica import Clinica
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
            return ('Página no encontrada', 404)  # el login no se muestra a quien no es veterinario
        return fn(*args, **kwargs)
    return wrapper


def role_required(nombre_rol):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if usuario_actual() is None:
                session.clear()
                return ('Página no encontrada', 404)  # el login no se muestra a quien no es veterinario
            if rol_actual() != nombre_rol.casefold():
                return ('Página no encontrada', 404)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


veterinario_required = role_required('veterinario')
admin_required = role_required('administrador')


def es_veterinario():
    return rol_actual() == 'veterinario'


def url_publica(endpoint, **valores):
    """Dirección completa de una página (para el QR). Si pones URL_PUBLICA en .env se usa esa base."""
    base = os.getenv('URL_PUBLICA', '').strip().rstrip('/') or request.host_url.rstrip('/')
    return base + url_for(endpoint, **valores)


# --- Plan Freemium (números del catálogo creado en esquema_huellapet.sql) ---
ID_PLAN_PREMIUM = 2          # tipo_plan: 1 = Gratis, 2 = Premium
ID_ESTADO_ACTIVA = 1         # tipo_estado_suscripcion: 1 = Activa
ID_ESTADO_CANCELADA = 2      # tipo_estado_suscripcion: 2 = Cancelada
ID_PAGO_COMPLETADO = 1       # tipo_estado_pago: 1 = Completado
PRECIO_PREMIUM = 4990        # pesos por mes
LIMITE_DOCUMENTOS_GRATIS = 3  # el plan Gratis guarda hasta 3 documentos; Premium es ilimitado
GRAVEDADES = ('Leve', 'Moderada', 'Grave')

# Permite usar rol_actual() dentro de las plantillas (la cabecera lo usa)
app.jinja_env.globals['rol_actual'] = rol_actual


def es_tutor():
    return rol_actual() == 'tutor'


def es_dueno(mascota):
    return mascota is not None and es_tutor() and session.get('id_usuario') == mascota.id_tutor


def puede_gestionar(mascota):
    """El veterinario o el tutor de la mascota pueden modificar su información."""
    return es_veterinario() or es_dueno(mascota)


def es_premium(id_usuario):
    for suscripcion in Suscripcion.get_by_usuario(id_usuario):
        vigente = suscripcion.fecha_fin is None or suscripcion.fecha_fin >= date.today()
        if suscripcion.id_tipo_plan == ID_PLAN_PREMIUM and suscripcion.id_tipo_estado_suscripcion == ID_ESTADO_ACTIVA and vigente:
            return True
    return False


def documentos_del_tutor(id_tutor):
    return sum(len(Documento.get_by_mascota(m.id_mascota)) for m in Mascota.get_by_tutor(id_tutor))


def limite_documentos_alcanzado(mascota):
    return not es_premium(mascota.id_tutor) and documentos_del_tutor(mascota.id_tutor) >= LIMITE_DOCUMENTOS_GRATIS


def tutor_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not es_tutor():
            flash('Inicia sesión como tutor.', 'warning')
            return redirect(url_for('login_tutor'))
        return fn(*args, **kwargs)
    return wrapper


def gestor_required(fn):
    """Rutas de una mascota que puede modificar su tutor o un veterinario."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if usuario_actual() is None:
            flash('Inicia sesión para continuar.', 'warning')
            return redirect(url_for('login_tutor'))
        if not puede_gestionar(Mascota.get_by_id(kwargs['id_mascota'])):
            return ('Página no encontrada', 404)
        return fn(*args, **kwargs)
    return wrapper


def pagina_de_mascota(id_mascota):
    """Página de administración de la mascota: la del veterinario o la del tutor."""
    destino = 'veterinario_mascota' if es_veterinario() else 'mi_mascota'
    return url_for(destino, id_mascota=id_mascota)


# --- Firma digital de los registros clínicos ---
def firmar_registro(id_mascota, id_veterinario, id_tipo_historial, titulo, descripcion, fecha_atencion, proxima_fecha):
    """Firma el contenido del registro con la clave secreta del sitio (HMAC-SHA256)."""
    texto = '|'.join(str(x) for x in (id_mascota, id_veterinario, id_tipo_historial, titulo, descripcion, fecha_atencion, proxima_fecha or ''))
    return hmac.new(app.config['SECRET_KEY'].encode(), texto.encode(), hashlib.sha256).hexdigest()


def firma_valida(h):
    firma = getattr(h, 'firma_digital', None)
    if not firma:
        return False
    esperada = firmar_registro(h.id_mascota, h.id_veterinario, h.id_tipo_historial, h.titulo, h.descripcion, h.fecha_atencion, h.proxima_fecha)
    return hmac.compare_digest(firma, esperada)


def con_firmas(registros):
    for h in registros:
        h.firma_ok = firma_valida(h)
    return registros


# --- Alertas de vacuna ---
def alertas_de_mascota(id_mascota, premium):
    """Alertas que programó el tutor y, con plan Premium, recordatorios automáticos del historial."""
    hoy = date.today()
    alertas = []
    for a in AlertaVacuna.get_by_mascota(id_mascota):
        alertas.append({'id': a.id_alerta_vacuna, 'titulo': a.titulo, 'fecha': a.fecha_alerta, 'dias': (a.fecha_alerta - hoy).days, 'automatica': False})
    if premium:
        tipos_vistos = set()
        for h in HistorialMedico.get_by_mascota(id_mascota):   # del más nuevo al más antiguo
            if h.tipo in tipos_vistos:
                continue
            tipos_vistos.add(h.tipo)
            if h.proxima_fecha:
                alertas.append({'id': None, 'titulo': f'Próxima {h.tipo.lower()}: {h.titulo}', 'fecha': h.proxima_fecha, 'dias': (h.proxima_fecha - hoy).days, 'automatica': True})
    return sorted(alertas, key=lambda a: a['fecha'])


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


# =========================================================
# VISITANTES: solo ven la ficha escaneando el QR o el chip NFC
# =========================================================

@app.route('/dashboard')
def acceso_dashboard():
    # No hay formulario para escribir códigos: se entra escaneando la placa
    return render_template('publico/acceso.html')


def entrada_permitida(mascota, codigo):
    """Los visitantes solo entran con el UID del chip NFC o el token del QR.
    El código impreso en la ficha (HPET-xxxx) solo sirve para el tutor o un veterinario con sesión."""
    if mascota is None:
        return False
    return puede_gestionar(mascota) or codigo != mascota.codigo_huellapet


@app.route('/dashboard/<codigo>')
def dashboard_publico(codigo):
    mascota = Mascota.get_by_nfc(codigo)
    if not entrada_permitida(mascota, codigo):
        return ('Mascota no encontrada', 404)
    vet = es_veterinario()
    dueno = es_dueno(mascota)
    privado = vet or dueno          # solo ellos ven documentos, avistamientos y todos los datos del tutor
    chat_vet = puede_chatear_con(mascota)
    return render_template(
        'publico/dashboard.html',
        mascota=mascota,
        codigo=codigo,
        salud=con_firmas(HistorialMedico.get_by_mascota(mascota.id_mascota)),
        condiciones=AlergiaCondicion.get_by_mascota(mascota.id_mascota),
        extravio=UbicacionExtravio.get_active_by_mascota(mascota.id_mascota),
        es_vet=vet,
        es_dueno=dueno,
        ver_privado=privado,
        puede_chatear=chat_vet,
        tutor=Usuario.get_by_id(mascota.id_tutor),
        veterinarios=PerfilVeterinario.get_all(),
        documentos=Documento.get_by_mascota(mascota.id_mascota) if privado else [],
        avistamientos=Avistamiento.get_by_mascota(mascota.id_mascota) if privado else [],
        mensajes=ChatMensaje.get_by_mascota(mascota.id_mascota) if chat_vet else [],
        hoy=date.today(),
    )


# Chat directo: los veterinarios y los tutores con plan Premium (tabla chat_mensaje)
def puede_chatear_con(mascota):
    if usuario_actual() is None:
        return False
    return es_veterinario() or (es_dueno(mascota) and es_premium(session['id_usuario']))


@app.route('/dashboard/<codigo>/chat', methods=['POST'])
def enviar_mensaje_chat(codigo):
    mascota = Mascota.get_by_nfc(codigo)
    if mascota is None or not puede_chatear_con(mascota):
        return jsonify({'ok': False}), 403
    texto = request.form.get('mensaje', '').strip()
    if texto:
        ChatMensaje.save({
            'id_mascota': mascota.id_mascota,
            'id_remitente': session['id_usuario'],
            'id_destinatario': None,
            'es_bot': 0,
            'mensaje': texto,
            'leido': 0,
        })
    if request.headers.get('X-Requested-With') == 'fetch':   # lo envía el JavaScript del chat
        return jsonify({'ok': True})
    return redirect(url_for('dashboard_publico', codigo=codigo, _anchor='chat'))


# El chat se actualiza solo: el navegador pregunta cada pocos segundos por mensajes nuevos
@app.route('/dashboard/<codigo>/chat/mensajes')
def mensajes_chat(codigo):
    mascota = Mascota.get_by_nfc(codigo)
    if mascota is None or not puede_chatear_con(mascota):
        return jsonify([]), 403
    desde = request.args.get('desde', 0, type=int)
    nuevos = []
    for msg in ChatMensaje.get_by_mascota(mascota.id_mascota):
        if msg.id_chat_mensaje > desde:
            nuevos.append({
                'id': msg.id_chat_mensaje,
                'mio': msg.id_remitente == session['id_usuario'],
                'autor': 'Tutor' if msg.id_remitente == mascota.id_tutor else 'Veterinario',
                'texto': msg.mensaje,
                'hora': msg.created_at.strftime('%H:%M'),
            })
    return jsonify(sorted(nuevos, key=lambda m: m['id']))


@app.route('/api/dashboard/<codigo>/ubicacion', methods=['POST'])
def registrar_ubicacion(codigo):
    mascota = Mascota.get_by_nfc(codigo)
    if not entrada_permitida(mascota, codigo):
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


# =========================================================
# VETERINARIOS: identificación, inicio de sesión y registro
# Solo los veterinarios pueden iniciar sesión o registrarse.
# El login y el registro no tienen ningún enlace en el sitio: primero hay que
# identificarse en /veterinarios (número de colegiado o código de invitación).
# =========================================================

def buscar_perfil_por_colegiado(numero):
    for perfil in PerfilVeterinario.get_all():
        if perfil.numero_colegiado.strip().casefold() == numero.strip().casefold():
            return perfil
    return None


def password_correcta(usuario, texto):
    try:
        valido = bcrypt.checkpw(texto.encode(), usuario.password.encode())
    except (ValueError, TypeError):
        valido = texto == usuario.password
        if valido:  # contraseña antigua sin cifrar: se cifra ahora
            Usuario.update_password(usuario.id_usuario, bcrypt.hashpw(texto.encode(), bcrypt.gensalt()).decode())
    return valido


@app.route('/veterinarios', methods=['GET', 'POST'])
def puerta_veterinarios():
    codigo_invitacion = os.getenv('CODIGO_VETERINARIOS', '').strip()
    if request.method == 'POST':
        colegiado = request.form.get('numero_colegiado', '').strip()
        invitacion = request.form.get('codigo_invitacion', '').strip()
        if colegiado:
            perfil = buscar_perfil_por_colegiado(colegiado)
            if perfil and perfil.es_verificado:
                session.clear()
                session['puerta'] = 'login'
                session['colegiado'] = perfil.numero_colegiado
                return redirect(url_for('login'))
            flash('No encontramos un veterinario verificado con ese número.', 'danger')
        elif invitacion:
            if codigo_invitacion and secrets.compare_digest(invitacion, codigo_invitacion):
                session.clear()
                session['puerta'] = 'registro'
                return redirect(url_for('registro'))
            flash('Código de invitación incorrecto.', 'danger')
    return render_template('auth/puerta.html', registro_habilitado=bool(codigo_invitacion))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('puerta') != 'login':
        return ('Página no encontrada', 404)
    if request.method == 'POST':
        usuario = Usuario.get_by_email(request.form.get('email', '').strip())
        if usuario and password_correcta(usuario, request.form.get('password', '')):
            perfil = PerfilVeterinario.get_by_usuario(usuario.id_usuario)
            # La cuenta debe ser de veterinario, estar verificada y coincidir con el número de colegiado
            if perfil and perfil.es_verificado and perfil.numero_colegiado == session.get('colegiado'):
                session.clear()
                session.permanent = True
                session['id_usuario'] = usuario.id_usuario
                return redirect(url_for('panel_veterinario'))
        flash('Correo o contraseña incorrectos.', 'danger')
    return render_template('auth/login.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if session.get('puerta') != 'registro':
        return ('Página no encontrada', 404)
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        colegiado = request.form.get('numero_colegiado', '').strip()
        if not nombre or not email or not password or not colegiado:
            flash('Nombre, correo, contraseña y número de colegiado son obligatorios.', 'danger')
            return redirect(url_for('registro'))
        if Usuario.get_by_email(email):
            flash('Ese correo ya está registrado.', 'danger')
            return redirect(url_for('registro'))
        if buscar_perfil_por_colegiado(colegiado):
            flash('Ese número de colegiado ya está registrado.', 'danger')
            return redirect(url_for('registro'))
        id_rol = Usuario.get_role_id('Veterinario')
        if id_rol is None:
            return ('No existe el rol Veterinario en la base de datos', 500)
        id_usuario = Usuario.save({
            'id_tipo_usuario': id_rol, 'nombre': nombre, 'email': email,
            'password': bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            'telefono': request.form.get('telefono', '').strip() or None,
            'direccion': None,
        })
        PerfilVeterinario.save({
            'id_usuario': id_usuario, 'numero_colegiado': colegiado,
            'es_verificado': 1,  # entró con el código de invitación, por eso queda verificado
            'especialidad': request.form.get('especialidad', '').strip() or None,
        })
        flash('Cuenta creada. Ya puedes iniciar sesión.', 'success')
        session['puerta'] = 'login'
        session['colegiado'] = colegiado
        return redirect(url_for('login'))
    return render_template('auth/registro.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('acceso_dashboard'))


# =========================================================
# TUTORES: inicio de sesión, registro y portal del tutor
# =========================================================

@app.route('/ingresar', methods=['GET', 'POST'])
def login_tutor():
    if request.method == 'POST':
        usuario = Usuario.get_by_email(request.form.get('email', '').strip())
        if usuario and password_correcta(usuario, request.form.get('password', '')):
            tipo = Usuario.get_with_type(usuario.id_usuario)
            if str(tipo.tipo_nombre).strip().casefold() == 'tutor':   # los veterinarios entran por /veterinarios
                session.clear()
                session.permanent = True
                session['id_usuario'] = usuario.id_usuario
                return redirect(url_for('mi_cuenta'))
        flash('Correo o contraseña incorrectos.', 'danger')
    return render_template('auth/login_tutor.html')


@app.route('/crear-cuenta', methods=['GET', 'POST'])
def registro_tutor():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not nombre or not email or not password:
            flash('Nombre, correo y contraseña son obligatorios.', 'danger')
            return redirect(url_for('registro_tutor'))
        if Usuario.get_by_email(email):
            flash('Ese correo ya está registrado.', 'danger')
            return redirect(url_for('registro_tutor'))
        id_rol = Usuario.get_role_id('Tutor')
        if id_rol is None:
            return ('No existe el rol Tutor en la base de datos', 500)
        Usuario.save({
            'id_tipo_usuario': id_rol, 'nombre': nombre, 'email': email,
            'password': bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            'telefono': request.form.get('telefono', '').strip() or None,
            'direccion': request.form.get('direccion', '').strip() or None,
        })
        flash('Cuenta creada. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login_tutor'))
    return render_template('auth/registro_tutor.html')


@app.route('/mi-cuenta')
@tutor_required
def mi_cuenta():
    premium = es_premium(session['id_usuario'])
    mascotas = Mascota.get_by_tutor(session['id_usuario'])
    # Alertas de vacuna que vencen en los próximos 7 días (o que ya vencieron)
    proximas = []
    for m in mascotas:
        for alerta in alertas_de_mascota(m.id_mascota, premium):
            if alerta['dias'] <= 7:
                proximas.append(dict(alerta, mascota=m.nombre))
    return render_template('dueno/mi_cuenta.html', mascotas=mascotas, especies=Catalogo.especies(), sexos=Catalogo.sexos(), premium=premium, alertas=proximas)


@app.route('/mi-cuenta/mascotas/<int:id_mascota>')
@tutor_required
def mi_mascota(id_mascota):
    mascota = Mascota.get_by_id(id_mascota)
    if not es_dueno(mascota):
        return ('Página no encontrada', 404)
    return render_template('dueno/mascota.html', mascota=mascota, extravio=UbicacionExtravio.get_active_by_mascota(id_mascota))


# El tutor "vincula" a su mascota registrándola en su cuenta
@app.route('/mi-cuenta/mascotas/crear', methods=['POST'])
@tutor_required
def crear_mi_mascota():
    data = datos_mascota_form(session['id_usuario'])
    if not data['nombre'] or not data['id_tipo_especie'] or not data['id_tipo_sexo']:
        flash('Nombre, especie y sexo son obligatorios.', 'danger')
        return redirect(url_for('mi_cuenta'))
    data['codigo_huellapet'] = Mascota.generar_codigo()
    data['foto_url'] = None
    try:
        nombre_foto = guardar_archivo(request.files.get('foto'), app.config['UPLOAD_MASCOTAS'], IMAGENES_PERMITIDAS)
        if nombre_foto:
            data['foto_url'] = f"uploads/mascotas/{nombre_foto}"
    except ValueError as error:
        flash(str(error), 'danger')
        return redirect(url_for('mi_cuenta'))
    Mascota.save(data)
    flash('Mascota registrada en tu cuenta.', 'success')
    return redirect(url_for('mi_cuenta'))


@app.route('/mi-cuenta/mascotas/<int:id_mascota>/editar', methods=['POST'])
@tutor_required
def editar_mi_mascota(id_mascota):
    if not es_dueno(Mascota.get_by_id(id_mascota)):
        return ('Página no encontrada', 404)
    data = datos_mascota_form(session['id_usuario'])
    data['id_mascota'] = id_mascota
    Mascota.update(data)
    flash('Mascota actualizada.', 'success')
    return redirect(url_for('mi_mascota', id_mascota=id_mascota))


# --- Alertas de vacuna ---
@app.route('/mi-cuenta/mascotas/<int:id_mascota>/alertas')
@tutor_required
def alertas_mascota(id_mascota):
    mascota = Mascota.get_by_id(id_mascota)
    if not es_dueno(mascota):
        return ('Página no encontrada', 404)
    premium = es_premium(session['id_usuario'])
    return render_template('dueno/alertas.html', mascota=mascota, alertas=alertas_de_mascota(id_mascota, premium), premium=premium)


@app.route('/mi-cuenta/mascotas/<int:id_mascota>/alertas/crear', methods=['POST'])
@tutor_required
def crear_alerta(id_mascota):
    if not es_dueno(Mascota.get_by_id(id_mascota)):
        return ('Página no encontrada', 404)
    titulo = request.form.get('titulo', '').strip()
    fecha = request.form.get('fecha_alerta')
    if not titulo or not fecha:
        flash('Escribe el nombre de la vacuna y la fecha.', 'danger')
    else:
        AlertaVacuna.save({'id_mascota': id_mascota, 'titulo': titulo, 'fecha_alerta': fecha})
        flash('Alerta programada.', 'success')
    return redirect(url_for('alertas_mascota', id_mascota=id_mascota))


@app.route('/mi-cuenta/mascotas/<int:id_mascota>/alertas/<int:id_alerta>/eliminar', methods=['POST'])
@tutor_required
def eliminar_alerta(id_mascota, id_alerta):
    alerta = AlertaVacuna.get_by_id(id_alerta)
    if not es_dueno(Mascota.get_by_id(id_mascota)) or alerta is None or alerta.id_mascota != id_mascota:
        return ('Página no encontrada', 404)
    AlertaVacuna.delete(id_alerta)
    flash('Alerta eliminada.', 'success')
    return redirect(url_for('alertas_mascota', id_mascota=id_mascota))


# --- Citas médicas con clínicas asociadas ---
@app.route('/mi-cuenta/citas')
@tutor_required
def citas_tutor():
    return render_template('dueno/citas.html', citas=Cita.get_by_tutor(session['id_usuario']), mascotas=Mascota.get_by_tutor(session['id_usuario']), clinicas=Clinica.get_all())


@app.route('/mi-cuenta/citas/crear', methods=['POST'])
@tutor_required
def crear_cita():
    mascota = Mascota.get_by_id(request.form.get('id_mascota', type=int))
    clinica = Clinica.get_by_id(request.form.get('id_clinica', type=int))
    motivo = request.form.get('motivo', '').strip()
    try:
        fecha_hora = datetime.fromisoformat(request.form.get('fecha_hora', ''))
    except ValueError:
        fecha_hora = None
    if not es_dueno(mascota) or clinica is None or not motivo or fecha_hora is None:
        flash('Elige la mascota, la clínica, la fecha y escribe el motivo.', 'danger')
    elif fecha_hora < datetime.now():
        flash('La fecha de la cita debe ser futura.', 'danger')
    else:
        Cita.save({'id_mascota': mascota.id_mascota, 'id_clinica': clinica.id_clinica, 'fecha_hora': fecha_hora, 'motivo': motivo})
        flash('Cita solicitada. La clínica la confirmará.', 'success')
    return redirect(url_for('citas_tutor'))


@app.route('/mi-cuenta/citas/<int:id_cita>/cancelar', methods=['POST'])
@tutor_required
def cancelar_cita(id_cita):
    cita = Cita.get_by_id(id_cita)
    if cita is None or cita.id_tutor != session['id_usuario']:
        return ('Página no encontrada', 404)
    Cita.set_estado(id_cita, 'Cancelada')
    flash('Cita cancelada.', 'success')
    return redirect(url_for('citas_tutor'))


# --- Plan Gratis / Premium ---
@app.route('/mi-cuenta/plan')
@tutor_required
def mi_plan():
    id_tutor = session['id_usuario']
    return render_template('dueno/plan.html', premium=es_premium(id_tutor), precio=PRECIO_PREMIUM, limite=LIMITE_DOCUMENTOS_GRATIS, usados=documentos_del_tutor(id_tutor))


@app.route('/mi-cuenta/plan/premium', methods=['POST'])
@tutor_required
def activar_premium():
    id_tutor = session['id_usuario']
    if es_premium(id_tutor):
        flash('Ya tienes el plan Premium.', 'warning')
        return redirect(url_for('mi_plan'))
    hoy = date.today()
    id_suscripcion = Suscripcion.save({'id_usuario': id_tutor, 'id_tipo_plan': ID_PLAN_PREMIUM, 'id_tipo_estado_suscripcion': ID_ESTADO_ACTIVA, 'fecha_inicio': hoy, 'fecha_fin': hoy + timedelta(days=30)})
    # No hay pasarela de pago conectada: el pago se registra como simulado
    Pago.save({'id_suscripcion': id_suscripcion, 'id_tipo_estado_pago': ID_PAGO_COMPLETADO, 'monto': PRECIO_PREMIUM, 'metodo_pago': 'Pago simulado', 'fecha_pago': datetime.now()})
    flash('Plan Premium activado por 30 días.', 'success')
    return redirect(url_for('mi_plan'))


@app.route('/mi-cuenta/plan/cancelar', methods=['POST'])
@tutor_required
def cancelar_premium():
    for s in Suscripcion.get_by_usuario(session['id_usuario']):
        if s.id_tipo_plan == ID_PLAN_PREMIUM and s.id_tipo_estado_suscripcion == ID_ESTADO_ACTIVA:
            Suscripcion.update({'id_suscripcion': s.id_suscripcion, 'id_tipo_plan': s.id_tipo_plan, 'id_tipo_estado_suscripcion': ID_ESTADO_CANCELADA, 'fecha_inicio': s.fecha_inicio, 'fecha_fin': s.fecha_fin})
    flash('Plan Premium cancelado. Vuelves al plan Gratis.', 'success')
    return redirect(url_for('mi_plan'))


# =========================================================
# TUTOR O VETERINARIO: foto, documentos, extravío y avistamientos de la mascota
# =========================================================

@app.route('/mascotas/<int:id_mascota>/foto', methods=['POST'])
@gestor_required
def cambiar_foto_mascota(id_mascota):
    try:
        nombre = guardar_archivo(request.files.get('foto'), app.config['UPLOAD_MASCOTAS'], IMAGENES_PERMITIDAS)
    except ValueError as error:
        flash(str(error), 'danger')
        return redirect(pagina_de_mascota(id_mascota))
    if not nombre:
        flash('Debes seleccionar una fotografía.', 'danger')
    else:
        Mascota.update_foto(id_mascota, f"uploads/mascotas/{nombre}")
        flash('Fotografía actualizada.', 'success')
    return redirect(pagina_de_mascota(id_mascota))


@app.route('/mascotas/<int:id_mascota>/documentos')
@gestor_required
def documentos_privados(id_mascota):
    mascota = Mascota.get_by_id(id_mascota)
    return render_template('gestion/documentos.html', mascota=mascota, documentos=Documento.get_by_mascota(id_mascota), tipos_documento=Catalogo.tipos_documento(),
                           url_volver=pagina_de_mascota(id_mascota), premium=es_premium(mascota.id_tutor), limite=LIMITE_DOCUMENTOS_GRATIS, usados=documentos_del_tutor(mascota.id_tutor))


@app.route('/mascotas/<int:id_mascota>/documentos/crear', methods=['POST'])
@gestor_required
def crear_documento(id_mascota):
    if limite_documentos_alcanzado(Mascota.get_by_id(id_mascota)):
        flash(f'El plan Gratis guarda hasta {LIMITE_DOCUMENTOS_GRATIS} documentos. El plan Premium tiene almacenamiento ilimitado.', 'warning')
        return redirect(url_for('documentos_privados', id_mascota=id_mascota))
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


@app.route('/mascotas/<int:id_mascota>/documentos/<int:id_documento>/eliminar', methods=['POST'])
@gestor_required
def eliminar_documento(id_mascota, id_documento):
    documento = Documento.get_by_id(id_documento)
    if documento is None or documento.id_mascota != id_mascota:
        return ('Documento no encontrado', 404)
    Documento.delete(id_documento)
    flash('Documento eliminado.', 'success')
    return redirect(url_for('documentos_privados', id_mascota=id_mascota))


# Modo Mascota Perdida
@app.route('/mascotas/<int:id_mascota>/extravio', methods=['POST'])
@gestor_required
def cambiar_extravio(id_mascota):
    activo = request.form.get('extraviado') == '1'
    UbicacionExtravio.set_estado({'id_mascota': id_mascota, 'reportado_extraviado': int(activo), 'notificaciones_activas': int(activo)})
    flash('Modo Mascota Perdida activado.' if activo else 'Modo Mascota Perdida desactivado.', 'success')
    return redirect(pagina_de_mascota(id_mascota))


@app.route('/mascotas/<int:id_mascota>/avistamientos')
@gestor_required
def avistamientos_mascota(id_mascota):
    return render_template('gestion/avistamientos.html', mascota=Mascota.get_by_id(id_mascota), avistamientos=Avistamiento.get_by_mascota(id_mascota), url_volver=pagina_de_mascota(id_mascota))


# Placa NFC/QR: el veterinario crea el código que se imprime en el QR y se graba en el chip NFC
@app.route('/veterinario/mascotas/<int:id_mascota>/dispositivo/crear', methods=['POST'])
@veterinario_required
def veterinario_crear_dispositivo(id_mascota):
    if Mascota.get_by_id(id_mascota) is None:
        return ('Mascota no encontrada', 404)
    if DispositivoNFC.get_by_mascota(id_mascota):
        flash('Esta mascota ya tiene una placa NFC/QR.', 'warning')
    else:
        guardado = DispositivoNFC.save({
            'id_mascota': id_mascota,
            'id_tipo_estado_dispositivo': 1,  # 1 = Activo (primer valor del catálogo)
            'codigo_uid': request.form.get('codigo_uid', '').strip() or secrets.token_hex(7).upper(),
            'token_qr': secrets.token_urlsafe(24),
        })
        flash('Placa NFC/QR creada.' if guardado else 'No se pudo crear la placa (el UID ya existe).', 'success' if guardado else 'danger')
    return redirect(url_for('veterinario_mascota', id_mascota=id_mascota))


@app.route('/veterinario/mascotas/<int:id_mascota>/dispositivo/<int:id_dispositivo>/eliminar', methods=['POST'])
@veterinario_required
def veterinario_eliminar_dispositivo(id_mascota, id_dispositivo):
    dispositivo = DispositivoNFC.get_by_id(id_dispositivo)
    if dispositivo is None or dispositivo.id_mascota != id_mascota:
        return ('Placa no encontrada', 404)
    DispositivoNFC.delete(id_dispositivo)
    flash('Placa eliminada. El QR y el chip anteriores ya no abren la ficha.', 'success')
    return redirect(url_for('veterinario_mascota', id_mascota=id_mascota))


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
    dispositivo = DispositivoNFC.get_by_mascota(id_mascota)
    url_ficha = url_publica('dashboard_publico', codigo=dispositivo.token_qr) if dispositivo else None
    return render_template('veterinario/mascota.html', mascota=mascota, historial=HistorialMedico.get_by_mascota(id_mascota), condiciones=AlergiaCondicion.get_by_mascota(id_mascota), tutor=Usuario.get_by_id(mascota.id_tutor), tutores=Usuario.get_all_tutores(), especies=Catalogo.especies(), sexos=Catalogo.sexos(), tipos_historial=Catalogo.tipos_historial(), extravio=UbicacionExtravio.get_active_by_mascota(id_mascota), dispositivo=dispositivo, url_ficha=url_ficha)


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
    return render_template('veterinario/historial.html', mascota=mascota, historial=con_firmas(HistorialMedico.get_by_mascota(id_mascota)), tipos_historial=Catalogo.tipos_historial())


def datos_historial_form():
    return {
        'id_tipo_historial': request.form.get('id_tipo_historial'),
        'titulo': request.form.get('titulo', '').strip(),
        'descripcion': request.form.get('descripcion', '').strip(),
        'fecha_atencion': request.form.get('fecha_atencion'),
        'proxima_fecha': request.form.get('proxima_fecha') or None,
    }


def firmar_y_guardar(id_historial, id_mascota, id_veterinario, datos):
    firma = firmar_registro(id_mascota, id_veterinario, datos['id_tipo_historial'], datos['titulo'], datos['descripcion'], datos['fecha_atencion'], datos['proxima_fecha'])
    HistorialMedico.set_firma(id_historial, firma)


@app.route('/veterinario/mascotas/<int:id_mascota>/historial/crear', methods=['POST'])
@veterinario_required
def veterinario_crear_historial(id_mascota):
    if Mascota.get_by_id(id_mascota) is None:
        return ('Mascota no encontrada', 404)
    datos = datos_historial_form()
    id_historial = HistorialMedico.save(dict(datos, id_mascota=id_mascota, id_veterinario=session['id_usuario']))
    if id_historial:
        firmar_y_guardar(id_historial, id_mascota, session['id_usuario'], datos)
        flash('Registro clínico agregado y firmado.', 'success')
    else:
        flash('No se pudo guardar el registro.', 'danger')
    return redirect(url_for('veterinario_historial', id_mascota=id_mascota))


# Solo el veterinario que firmó un registro puede editarlo o eliminarlo
@app.route('/veterinario/historial/<int:id_historial>/editar', methods=['POST'])
@veterinario_required
def veterinario_editar_historial(id_historial):
    historial = HistorialMedico.get_by_id(id_historial)
    if historial is None:
        return ('Registro no encontrado', 404)
    if historial.id_veterinario != session['id_usuario']:
        flash('Solo el veterinario que firmó este registro puede editarlo.', 'danger')
        return redirect(url_for('veterinario_historial', id_mascota=historial.id_mascota))
    datos = datos_historial_form()
    HistorialMedico.update(dict(datos, id_historial_medico=id_historial))
    firmar_y_guardar(id_historial, historial.id_mascota, historial.id_veterinario, datos)
    flash('Registro actualizado y firmado de nuevo.', 'success')
    return redirect(url_for('veterinario_historial', id_mascota=historial.id_mascota))


@app.route('/veterinario/historial/<int:id_historial>/eliminar', methods=['POST'])
@veterinario_required
def veterinario_eliminar_historial(id_historial):
    historial = HistorialMedico.get_by_id(id_historial)
    if historial is None:
        return ('Registro no encontrado', 404)
    if historial.id_veterinario != session['id_usuario']:
        flash('Solo el veterinario que firmó este registro puede eliminarlo.', 'danger')
        return redirect(url_for('veterinario_historial', id_mascota=historial.id_mascota))
    HistorialMedico.delete(id_historial)
    flash('Registro eliminado.', 'success')
    return redirect(url_for('veterinario_historial', id_mascota=historial.id_mascota))


# Alergias, condiciones y cuidados especiales (lo que se ve primero en la vista de emergencia)
def datos_alergia_form():
    gravedad = request.form.get('gravedad')
    return {
        'nombre_condicion': request.form.get('nombre_condicion', '').strip(),
        'gravedad': gravedad if gravedad in GRAVEDADES else 'Moderada',
        'observaciones': request.form.get('observaciones', '').strip() or None,
    }


@app.route('/veterinario/mascotas/<int:id_mascota>/alergias/crear', methods=['POST'])
@veterinario_required
def veterinario_crear_alergia(id_mascota):
    if Mascota.get_by_id(id_mascota) is None:
        return ('Mascota no encontrada', 404)
    datos = datos_alergia_form()
    if not datos['nombre_condicion']:
        flash('Escribe el nombre de la alergia o condición.', 'danger')
    elif AlergiaCondicion.save(dict(datos, id_mascota=id_mascota, id_veterinario=session['id_usuario'])):
        flash('Alergia o condición registrada.', 'success')
    else:
        flash('No se pudo guardar.', 'danger')
    return redirect(url_for('veterinario_mascota', id_mascota=id_mascota))


@app.route('/veterinario/alergias/<int:id_alergia>/editar', methods=['POST'])
@veterinario_required
def veterinario_editar_alergia(id_alergia):
    alergia = AlergiaCondicion.get_by_id(id_alergia)
    if alergia is None:
        return ('Registro no encontrado', 404)
    AlergiaCondicion.update(dict(datos_alergia_form(), id_alergia_condicion=id_alergia))
    flash('Alergia o condición actualizada.', 'success')
    return redirect(url_for('veterinario_mascota', id_mascota=alergia.id_mascota))


@app.route('/veterinario/alergias/<int:id_alergia>/eliminar', methods=['POST'])
@veterinario_required
def veterinario_eliminar_alergia(id_alergia):
    alergia = AlergiaCondicion.get_by_id(id_alergia)
    if alergia is None:
        return ('Registro no encontrado', 404)
    AlergiaCondicion.delete(id_alergia)
    flash('Alergia o condición eliminada.', 'success')
    return redirect(url_for('veterinario_mascota', id_mascota=alergia.id_mascota))


# Citas y clínicas asociadas
@app.route('/veterinario/citas')
@veterinario_required
def panel_citas():
    return render_template('veterinario/citas.html', citas=Cita.get_all(), clinicas=Clinica.get_all())


@app.route('/veterinario/citas/<int:id_cita>/estado', methods=['POST'])
@veterinario_required
def veterinario_estado_cita(id_cita):
    estado = request.form.get('estado')
    if Cita.get_by_id(id_cita) is None or estado not in ('Pendiente', 'Confirmada', 'Cancelada'):
        return ('Cita no encontrada', 404)
    Cita.set_estado(id_cita, estado)
    flash('Estado de la cita actualizado.', 'success')
    return redirect(url_for('panel_citas'))


@app.route('/veterinario/clinicas/crear', methods=['POST'])
@veterinario_required
def veterinario_crear_clinica():
    nombre = request.form.get('nombre', '').strip()
    if not nombre:
        flash('Escribe el nombre de la clínica.', 'danger')
    else:
        Clinica.save({'nombre': nombre, 'direccion': request.form.get('direccion', '').strip() or None, 'telefono': request.form.get('telefono', '').strip() or None})
        flash('Clínica agregada.', 'success')
    return redirect(url_for('panel_citas'))


@app.route('/veterinario/clinicas/<int:id_clinica>/eliminar', methods=['POST'])
@veterinario_required
def veterinario_eliminar_clinica(id_clinica):
    if Clinica.delete(id_clinica):
        flash('Clínica eliminada.', 'success')
    else:
        flash('No se puede eliminar una clínica que tiene citas.', 'danger')
    return redirect(url_for('panel_citas'))


# PWA: el service worker se sirve desde la raíz para que cubra todo el sitio
@app.route('/sw.js')
def service_worker():
    respuesta = send_from_directory(os.path.join(app.root_path, 'static', 'js'), 'sw.js')
    respuesta.headers['Service-Worker-Allowed'] = '/'
    respuesta.headers['Cache-Control'] = 'no-cache'
    return respuesta


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
