let currentVolumen = 50;

// ── Música ────────────────────────────────────────────────────────────────────

async function cargarCanciones() {
    const res = await fetch('/audio/lista');
    const data = await res.json();
    const select = document.getElementById('song-select');
    data.canciones.forEach(cancion => {
        const option = document.createElement('option');
        option.value = cancion;
        option.textContent = cancion.replace('.mp3', '');
        select.appendChild(option);
    });
}

document.getElementById('play-btn').addEventListener('click', () => {
    const archivo = document.getElementById('song-select').value;
    if (!archivo) return;
    const playIcon = document.getElementById('play-icon');
    playIcon.classList.toggle('fa-circle-play');
    playIcon.classList.toggle('fa-circle-pause');
    fetch('/audio/reproducir', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ archivo })
    });
});

document.getElementById('left-btn').addEventListener('click', () => {
    fetch('/audio/detener', { method: 'POST' });
});

document.getElementById('right-btn').addEventListener('click', () => {
    fetch('/audio/detener', { method: 'POST' });
});

document.getElementById('high-btn').addEventListener('click', () => {
    currentVolumen = Math.min(100, currentVolumen + 10);
    fetch(`/audio/volumen/${currentVolumen}`, { method: 'POST' });
});

document.getElementById('low-btn').addEventListener('click', () => {
    currentVolumen = Math.max(0, currentVolumen - 10);
    fetch(`/audio/volumen/${currentVolumen}`, { method: 'POST' });
});

// ── Motores ───────────────────────────────────────────────────────────────────

document.getElementById('forward-btn').addEventListener('click', () => {
    fetch('/motor/adelante', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ velocidad: 50 })
    });
});

document.getElementById('backward-btn').addEventListener('click', () => {
    fetch('/motor/atras', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ velocidad: 50 })
    });
});

document.getElementById('left-control-btn').addEventListener('click', () => {
    fetch('/motor/izquierda', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ velocidad: 50 })
    });
});

document.getElementById('right-control-btn').addEventListener('click', () => {
    fetch('/motor/derecha', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ velocidad: 50 })
    });
});

document.getElementById('stop-btn').addEventListener('click', () => {
    fetch('/motor/detener', { method: 'POST' });
});

// ── Modos ─────────────────────────────────────────────────────────────────────

document.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('click', function () {
        document.querySelectorAll('.btn').forEach(b => b.classList.remove('selected'));
        this.classList.add('selected');
    });
});

document.getElementById('automatic-btn').addEventListener('click', () => {
    changeColor();
    fetch('/led/autonomo/1', { method: 'POST' });
    fetch('/led/manual/0', { method: 'POST' });
});

document.getElementById('manual-btn').addEventListener('click', () => {
    const controlBtns = document.querySelectorAll('.control-btn');
    controlBtns.forEach(btn => {
        btn.style.color = '#7494ec';
        btn.disabled = false;
    });
    fetch('/led/manual/1', { method: 'POST' });
    fetch('/led/autonomo/0', { method: 'POST' });
});

function changeColor() {
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.style.color = '#DEDCE0';
        btn.disabled = true;
    });
}

// ── Sensores ──────────────────────────────────────────────────────────────────

async function getSensorData() {
    try {
        const res = await fetch('/sensores');
        const data = await res.json();
        document.getElementById('sensors-info').textContent =
            `Frontal: ${data.frontal} cm | Lateral: ${data.lateral} cm`;
    } catch {
        document.getElementById('sensors-info').textContent = 'Error leyendo sensores';
    }
}

// ── Conexión ──────────────────────────────────────────────────────────────────

async function checkConnection() {
    try {
        const res = await fetch('/status');
        const data = await res.json();
        document.getElementById('connection-status').innerHTML =
            `<p>${data.message}</p>`;
    } catch {
        document.getElementById('connection-status').innerHTML =
            `<p>Sin conexión con la Raspberry</p>`;
    }
}

// ── Mapa ──────────────────────────────────────────────────────────────────────

const grid = document.getElementById('map-grid');
const totalCells = 30 * 8;

for (let i = 0; i < totalCells; i++) {
    const cell = document.createElement('div');
    cell.classList.add('map-cell');
    cell.addEventListener('click', function () {
        this.classList.toggle('painted');
    });
    grid.appendChild(cell);
}

// ── Inicialización ────────────────────────────────────────────────────────────

cargarCanciones();
checkConnection();
setInterval(getSensorData, 2000);