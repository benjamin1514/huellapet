// =========================================================
// HUELLAPET - JavaScript del sitio
// Hace 5 cosas sencillas:
//   1) Cambiar de sección con el menú lateral
//   2) Abrir y cerrar el chat (veterinarios en vivo o HuellaBot)
//   3) Pedir confirmación antes de enviar ciertos formularios
//   4) Guardar el avistamiento de una mascota extraviada
//   5) Pequeños detalles (corazón)
// =========================================================


// ---------- 1) SECCIONES DEL MENÚ LATERAL ----------
var nombresVistas = ['resumen', 'perfil', 'salud', 'historial', 'documentos', 'contactos', 'ubicacion'];

function mostrarVista(nombre) {
    if (!nombresVistas.includes(nombre)) {
        nombre = 'resumen';
    }

    // Solo la sección elegida tiene la clase "activa"
    document.querySelectorAll('.vista').forEach(function (vista) {
        vista.classList.toggle('activa', vista.id === 'vista-' + nombre);
    });

    // Lo mismo con el botón del menú
    document.querySelectorAll('.menu-link').forEach(function (enlace) {
        enlace.classList.toggle('activo', enlace.dataset.vista === nombre);
    });
}

// Cualquier enlace con data-vista="..." cambia de sección
document.querySelectorAll('[data-vista]').forEach(function (enlace) {
    enlace.addEventListener('click', function (evento) {
        evento.preventDefault();
        mostrarVista(enlace.dataset.vista);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
});

// Al abrir la página, mostrar la sección que viene en la dirección (#salud, #historial, ...)
if (document.querySelector('.ficha')) {
    mostrarVista(window.location.hash.replace('#', ''));
}


// ---------- 2) CHAT ----------
var chat = document.getElementById('chat');

if (chat) {
    var cajaVet = document.getElementById('caja-vet');
    var cajaBot = document.getElementById('caja-bot');
    var formulario = document.getElementById('chat-form');
    var entrada = document.getElementById('chat-input');
    var tituloChat = document.getElementById('chat-titulo');
    var subtituloChat = document.getElementById('chat-sub');
    var iconoChat = document.querySelector('#chat-avatar use');

    var ficha = document.querySelector('.ficha');
    var botonFlotante = document.querySelector('.chat-flotante');
    var modoChat = chat.dataset.modo;              // 'vet' (veterinarios) o 'bot' (visitantes)
    var entradaBloqueada = entrada.disabled;       // true si no hay sesión de tutor/veterinario
    var nombreMascota = document.body.dataset.nombre;

    // Muestra siempre el último mensaje
    cajaVet.scrollTop = cajaVet.scrollHeight;

    // Cambia entre "veterinarios" y "HuellaBot"
    function cambiarModoChat(modo) {
        modoChat = modo;
        cajaVet.hidden = (modo !== 'vet');
        cajaBot.hidden = (modo !== 'bot');

        if (modo === 'bot') {
            tituloChat.textContent = 'Chat con HuellaBot';
            subtituloChat.textContent = 'Tu asistente virtual está aquí para ayudarte.';
            iconoChat.setAttribute('href', '#i-robot');
            entrada.disabled = false;
            if (cajaBot.children.length === 0) {
                agregarMensajeBot('¡Hola! Soy HuellaBot. ¿En qué puedo ayudarte con ' + nombreMascota + '?', false);
            }
        } else {
            tituloChat.textContent = 'Chat con veterinarios';
            subtituloChat.textContent = 'Resuelve tus dudas y recibe orientación profesional.';
            iconoChat.setAttribute('href', '#i-chat');
            entrada.disabled = entradaBloqueada;
        }
    }

    // Dibuja un mensaje dentro de la conversación con HuellaBot
    function agregarMensajeBot(texto, esMio) {
        var mensaje = document.createElement('div');
        mensaje.className = esMio ? 'msg msg-mio' : 'msg';

        var burbuja = document.createElement('div');
        burbuja.className = 'burbuja';
        var parrafo = document.createElement('p');
        parrafo.textContent = texto;
        burbuja.appendChild(parrafo);

        if (!esMio) {
            var avatar = document.createElement('span');
            avatar.className = 'msg-avatar';
            avatar.innerHTML = '<svg><use href="#i-robot"></use></svg>';
            mensaje.appendChild(avatar);
        }

        mensaje.appendChild(burbuja);
        cajaBot.appendChild(mensaje);
        cajaBot.scrollTop = cajaBot.scrollHeight;
    }

    // HuellaBot: orientación veterinaria básica. No reemplaza a un veterinario.
    var AVISO_BOT = ' Recuerda que HuellaBot solo da orientación básica y no reemplaza a un veterinario.';

    function respuestaBot(texto) {
        // Se pasa a minúsculas y sin tildes para entender "vómitos" igual que "vomitos"
        var t = texto.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

        // Urgencias: lo primero es ir al veterinario
        if (t.includes('atropell') || t.includes('convuls') || t.includes('sangr') || t.includes('envenen') ||
            t.includes('intoxic') || t.includes('chocolate') || t.includes('uva') || t.includes('respira') ||
            t.includes('desmay') || t.includes('golpe fuerte')) {
            return 'Esto puede ser una urgencia. Lleva a ' + nombreMascota + ' ahora mismo a una clínica veterinaria. ' +
                'Mantenlo tranquilo y abrigado, y no le des medicamentos humanos ni lo hagas vomitar sin que un veterinario lo indique.';
        }
        if (t.includes('vomit') || t.includes('diarrea')) {
            return 'Si fue un episodio aislado, ofrécele agua en pequeñas cantidades y deja el alimento unas horas. ' +
                'Si se repite, hay sangre, está decaído, o es cachorro o adulto mayor, consulta a un veterinario pronto.' + AVISO_BOT;
        }
        if (t.includes('no come') || t.includes('apetito') || t.includes('aliment') || t.includes('comida')) {
            return 'Si pasa más de 24 horas sin comer, consulta a un veterinario. Los cambios de alimento se hacen de a poco, mezclando ' +
                'el nuevo con el anterior durante 7 a 10 días. Revisa en la sección Salud si ' + nombreMascota + ' tiene alergias registradas.' + AVISO_BOT;
        }
        if (t.includes('calor') || t.includes('jadea') || t.includes('jadeo')) {
            return 'Llévalo a la sombra, ofrécele agua fresca (no helada) y moja sus patas y su vientre con agua tibia. ' +
                'Si el jadeo es intenso, babea mucho o está decaído, es una urgencia: acude a un veterinario.';
        }
        if (t.includes('fiebre') || t.includes('temperatura')) {
            return 'La temperatura normal de perros y gatos es de unos 38 a 39 °C. Si sospechas fiebre o está decaído, consulta a un veterinario. ' +
                'No le des paracetamol ni ibuprofeno: son tóxicos para ellos.';
        }
        if (t.includes('rasc') || t.includes('pulga') || t.includes('piel') || t.includes('picazon')) {
            return 'El rascado frecuente puede deberse a pulgas, alergias u hongos. Revisa su pelaje y, si persiste, pide a un veterinario que lo evalúe para darle el tratamiento adecuado.' + AVISO_BOT;
        }

        // Preguntas sobre la ficha y el sitio
        if (t.includes('vacun')) {
            return 'Puedes ver las vacunas de ' + nombreMascota + ' en las secciones Salud e Historial. Si eres su tutor, en tu portal puedes programar alertas de vacuna.';
        }
        if (t.includes('desparas') || t.includes('control') || t.includes('salud')) {
            return 'En la sección Salud está el último control y la última desparasitación de ' + nombreMascota + '. La desparasitación se repite según indique su veterinario.';
        }
        if (t.includes('alerg')) {
            return 'Las alergias y los cuidados especiales de ' + nombreMascota + ' aparecen al inicio de la ficha, en la vista de emergencia.';
        }
        if (t.includes('cita') || t.includes('hora') || t.includes('agendar')) {
            return 'Si eres tutor, puedes agendar una cita con una clínica asociada desde tu portal, en "Mis citas".';
        }
        if (t.includes('document')) {
            return 'Los documentos están en la sección Documentos. Solo el tutor y los veterinarios pueden verlos.';
        }
        if (t.includes('perd') || t.includes('extrav')) {
            return 'Si ' + nombreMascota + ' se pierde, el tutor puede activar el Modo Mascota Perdida. Quien encuentre su placa puede compartir su ubicación.';
        }
        if (t.includes('veterin') || t.includes('chat')) {
            return 'El chat directo con veterinarios es parte del plan Premium para tutores. Los veterinarios lo usan desde su panel.';
        }
        return 'Puedo darte orientación básica sobre vómitos, diarrea, alimentación, calor, fiebre y piel, y ayudarte con la ficha. Para cualquier urgencia, acude a un veterinario.';
    }

    // Dibuja un mensaje del chat con veterinarios (los trae el servidor)
    var ultimoMensaje = parseInt(cajaVet.dataset.ultimo, 10) || 0;

    function agregarMensajeVet(m) {
        var vacio = cajaVet.querySelector('.chat-vacio');
        if (vacio) {
            vacio.remove();
        }

        var mensaje = document.createElement('div');
        mensaje.className = m.mio ? 'msg msg-mio' : 'msg';
        var avatar = m.mio ? '' : '<span class="msg-avatar"><svg><use href="#i-vet"></use></svg></span>';
        mensaje.innerHTML = avatar +
            '<div class="burbuja"><div class="burbuja-top"><strong></strong><time></time></div><p></p></div>';

        mensaje.querySelector('strong').textContent = m.mio ? '' : m.autor;
        mensaje.querySelector('time').textContent = m.hora;
        mensaje.querySelector('p').textContent = m.texto;

        cajaVet.appendChild(mensaje);
        cajaVet.scrollTop = cajaVet.scrollHeight;
        ultimoMensaje = m.id;
    }

    // Chat en vivo: cada 3 segundos se piden los mensajes nuevos al servidor
    function buscarMensajes() {
        if (entradaBloqueada) {
            return;
        }
        fetch(chat.dataset.urlMensajes + '?desde=' + ultimoMensaje)
            .then(function (respuesta) { return respuesta.ok ? respuesta.json() : []; })
            .then(function (mensajes) { mensajes.forEach(agregarMensajeVet); });
    }

    setInterval(buscarMensajes, 3000);

    // Al enviar: HuellaBot responde aquí; el chat con veterinarios se envía al servidor sin recargar la página
    formulario.addEventListener('submit', function (evento) {
        evento.preventDefault();
        var texto = entrada.value.trim();
        if (texto === '') {
            return;
        }

        if (modoChat === 'bot') {
            agregarMensajeBot(texto, true);
            entrada.value = '';
            setTimeout(function () {
                agregarMensajeBot(respuestaBot(texto), false);
            }, 700);
            return;
        }

        var datos = new FormData();
        datos.append('mensaje', texto);
        fetch(chat.dataset.urlEnviar, {
            method: 'POST',
            body: datos,
            headers: { 'X-Requested-With': 'fetch' }
        }).then(function () {
            entrada.value = '';
            buscarMensajes();
        });
    });

    // Cierra el chat: la ficha usa todo el ancho y aparece el botón "Chat" para volver a abrirlo
    function cerrarChat() {
        ficha.classList.add('sin-chat');
        botonFlotante.hidden = false;
        try { sessionStorage.setItem('chatCerrado', '1'); } catch (error) { /* sin almacenamiento */ }
    }

    // Vuelve a mostrar el chat
    function mostrarChat() {
        ficha.classList.remove('sin-chat');
        botonFlotante.hidden = true;
        try { sessionStorage.removeItem('chatCerrado'); } catch (error) { /* sin almacenamiento */ }
    }

    // Abre el chat y lo resalta un momento
    function abrirChat(modo) {
        mostrarChat();
        cambiarModoChat(modo);
        chat.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        chat.classList.remove('destacado');
        void chat.offsetWidth;                 // reinicia la animación
        chat.classList.add('destacado');
        if (!entrada.disabled) {
            entrada.focus({ preventScroll: true });
        }
    }

    // Botones con data-accion="chat-vet" o "chat-bot"
    document.querySelectorAll('[data-accion="chat-vet"]').forEach(function (boton) {
        boton.addEventListener('click', function () { abrirChat('vet'); });
    });
    document.querySelectorAll('[data-accion="chat-bot"]').forEach(function (boton) {
        boton.addEventListener('click', function () { abrirChat('bot'); });
    });

    // Botón X del chat y botón flotante "Chat"
    document.querySelector('[data-accion="cerrar-chat"]').addEventListener('click', cerrarChat);
    botonFlotante.addEventListener('click', function () { abrirChat(modoChat); });

    // Al cargar: mostrar el modo que corresponde y recordar si el chat estaba cerrado
    cambiarModoChat(chat.dataset.modo);
    try {
        if (sessionStorage.getItem('chatCerrado') === '1') {
            cerrarChat();
        }
    } catch (error) { /* sin almacenamiento */ }
}


// ---------- 3) CONFIRMACIONES ----------
// Los formularios con data-confirmar="..." preguntan antes de enviarse
document.querySelectorAll('form[data-confirmar]').forEach(function (form) {
    form.addEventListener('submit', function (evento) {
        if (!confirm(form.dataset.confirmar)) {
            evento.preventDefault();
        }
    });
});


// ---------- 4) AVISTAMIENTO DE UNA MASCOTA EXTRAVIADA ----------
// La ficha solo pone data-url-ubicacion cuando la mascota está extraviada y quien mira no es el tutor
var urlUbicacion = document.body.dataset.urlUbicacion;

if (urlUbicacion && navigator.geolocation) {
    var estado = document.getElementById('estado-ubicacion');

    navigator.geolocation.getCurrentPosition(
        function (posicion) {
            fetch(urlUbicacion, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    latitud: posicion.coords.latitude,
                    longitud: posicion.coords.longitude,
                    precision_metros: posicion.coords.accuracy
                })
            }).then(function (respuesta) {
                if (estado) {
                    estado.textContent = respuesta.ok
                        ? 'Ubicación del avistamiento registrada. ¡Gracias por ayudar!'
                        : 'No se pudo registrar la ubicación.';
                }
            });
        },
        function () {
            if (estado) {
                estado.textContent = 'No se compartió la ubicación.';
            }
        }
    );
}


// ---------- 5) CORAZÓN DE "SOBRE LA MASCOTA" ----------
document.querySelectorAll('[data-accion="corazon"]').forEach(function (boton) {
    boton.addEventListener('click', function () {
        var activo = boton.getAttribute('aria-pressed') === 'true';
        boton.setAttribute('aria-pressed', activo ? 'false' : 'true');
    });
});


// ---------- 6) CÓDIGO QR (página de administrar mascota) ----------
// La librería qrcode.min.js se carga solo en esa página
var cajaQr = document.getElementById('qr');

if (cajaQr && window.QRCode) {
    new QRCode(cajaQr, { text: cajaQr.dataset.url, width: 160, height: 160 });
} else if (cajaQr) {
    cajaQr.textContent = 'No se pudo cargar el QR. Revisa tu conexión a internet.';
}


// ---------- 7) PWA ----------
// Registra el service worker para que el sitio se pueda instalar en el celular
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(function () { /* sin service worker */ });
}
