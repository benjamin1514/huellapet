// ===== SIDEBAR NAVIGATION =====
document.querySelectorAll('.sidebar-item').forEach(item => {
    item.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active'));
        this.classList.add('active');
    });
});

// ===== HEADER NAV LINKS =====
document.querySelectorAll('.nav a').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelectorAll('.nav a').forEach(l => l.classList.remove('active'));
        this.classList.add('active');
    });
});

// ===== HEART BUTTON (LIKE) =====
const heartBtn = document.getElementById('heartBtn');
heartBtn.addEventListener('click', function() {
    this.classList.toggle('liked');
});

// ===== NOTIFICATION TOGGLE =====
const notifToggle = document.getElementById('notifToggle');
const notifLabel = document.getElementById('notifLabel');

notifToggle.addEventListener('change', function() {
    notifLabel.textContent = this.checked
        ? 'Notificaciones activadas'
        : 'Notificaciones desactivadas';
});

// ===== MODAL SYSTEM =====
const modalOverlay = document.getElementById('modalOverlay');
const modalTitle = document.getElementById('modalTitle');
const modalText = document.getElementById('modalText');
const modalClose = document.getElementById('modalClose');

function showModal(title, text) {
    modalTitle.textContent = title;
    modalText.textContent = text;
    modalOverlay.classList.add('show');
}

function closeModal() {
    modalOverlay.classList.remove('show');
}

modalClose.addEventListener('click', closeModal);

modalOverlay.addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// ===== REPORT BUTTON =====
document.getElementById('reportBtn').addEventListener('click', () => {
    showModal(
        ' Reporte de extravío',
        'Se ha reportado el extravío de Otto. Se notificará a los usuarios cercanos.'
    );
});

// ===== CHAT BUTTON =====
document.getElementById('chatBtn').addEventListener('click', (e) => {
    e.stopPropagation();
    showModal(
        '💬 Huellabot',
        '¡Hola! Soy Huellabot. ¿En qué puedo ayudarte hoy?'
    );
});

// ===== HUELLABOT CARD CLICK =====
document.getElementById('huellabotBtn').addEventListener('click', function(e) {
    if (e.target.id !== 'chatBtn') {
        showModal(
            '🤖 Huellabot',
            '¡Hola! Soy tu asistente virtual. Haz clic en "Iniciar chat" para comenzar.'
        );
    }
});

// ===== DOCUMENT ITEMS CLICK =====
document.querySelectorAll('.doc-item').forEach(item => {
    item.addEventListener('click', function(e) {
        e.preventDefault();
        const name = this.textContent.trim().replace('›', '').trim();
        showModal('📄 Documento', `Abriendo: ${name}`);
    });
});

// ===== PROFILE BUTTON =====
document.querySelector('.btn-profile').addEventListener('click', function(e) {
    e.preventDefault();
    showModal('👤 Perfil del tutor', 'Aquí se mostraría el perfil completo de Camila Rodríguez.');
});

// ===== HEALTH HISTORY BUTTON =====
document.querySelector('.btn-history').addEventListener('click', function(e) {
    e.preventDefault();
    showModal('❤️ Historial de salud', 'Aquí se mostraría el historial completo de salud de Otto.');
});

// ===== ALL DOCUMENTS BUTTON =====
document.querySelector('.btn-all-docs').addEventListener('click', function(e) {
    e.preventDefault();
    showModal('📄 Documentos', 'Aquí se mostrarían todos los documentos de Otto.');
});