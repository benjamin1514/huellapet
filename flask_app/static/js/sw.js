// Service worker de HuellaPet (hace que el sitio se pueda instalar como app).
// Solo guarda los archivos del diseño; las fichas siempre se piden al servidor
// para no guardar datos de las mascotas en el celular.
var CACHE = 'huellapet-v1';
var ARCHIVOS = [
    '/static/css/huellapet.css',
    '/static/js/huellapet.js',
    '/static/manifest.json',
    '/static/image/icono-192.png',
    '/static/image/icono-512.png'
];

self.addEventListener('install', function (evento) {
    evento.waitUntil(
        caches.open(CACHE).then(function (cache) { return cache.addAll(ARCHIVOS); })
    );
});

self.addEventListener('activate', function (evento) {
    evento.waitUntil(
        caches.keys().then(function (nombres) {
            return Promise.all(nombres.filter(function (n) { return n !== CACHE; }).map(function (n) { return caches.delete(n); }));
        })
    );
});

self.addEventListener('fetch', function (evento) {
    var url = new URL(evento.request.url);
    // Para los archivos del diseño: primero internet, y si no hay conexión, lo guardado
    if (evento.request.method === 'GET' && url.pathname.startsWith('/static/')) {
        evento.respondWith(
            fetch(evento.request).catch(function () { return caches.match(evento.request); })
        );
    }
});
