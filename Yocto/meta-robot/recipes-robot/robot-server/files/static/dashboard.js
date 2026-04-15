// ── Variables globales ────────────────────────────────────────────────────────
let currentVolumen = 50;
let currentVelocidad = 50;
let modoActual = 'manual';
let direccionActual = null;   // dirección que está activa ahora mismo
let estaReproduciendo = false;

// ── Música ────────────────────────────────────────────────────────────────────

async function cargarCanciones() {
    try {
        const res = await fetch('/audio/lista');
        const data = await res.json();
        const select = document.getElementById('song-select');
        // Limpiar opciones anteriores excepto la primera
        while (select.options.length > 1) select.remove(1);
        data.canciones.forEach(cancion => {
            const option = document.createElement('option');
            option.value = cancion;
            option.textContent = cancion.replace('.mp3', '');
            select.appendChild(option);
        });
    } catch { console.log('Error cargando canciones'); }
}

function actualizarIconoPlay(reproduciendo) {
    const icon = document.getElementById('play-icon');
    if (reproduciendo) {
        icon.className = 'fa-solid fa-pause';
    } else {
        icon.className = 'fa-solid fa-play';
    }
    estaReproduciendo = reproduciendo;
}

function actualizarNombreCancion(archivo) {
    document.getElementById('song-name').textContent = archivo
        ? archivo.replace('.mp3', '')
        : 'Sin canción';
    // Sincronizar el select
    const select = document.getElementById('song-select');
    for (let i = 0; i < select.options.length; i++) {
        if (select.options[i].value === archivo) {
            select.selectedIndex = i;
            break;
        }
    }
}

// Play / Pausa
document.getElementById('play-btn').addEventListener('click', async () => {
    const select = document.getElementById('song-select');
    const archivo = select.value;

    if (!estaReproduciendo && !archivo) {
        alert('Selecciona una canción primero');
        return;
    }

    if (!estaReproduciendo && archivo) {
        // Iniciar canción nueva
        const res = await fetch('/audio/reproducir', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ archivo })
        });
        const data = await res.json();
        actualizarNombreCancion(archivo);
        actualizarIconoPlay(true);
    } else {
        // Pausar o reanudar
        const res = await fetch('/audio/pausar', { method: 'POST' });
        const data = await res.json();
        actualizarIconoPlay(data.reproduciendo);
    }
});

// Anterior
document.getElementById('prev-btn').addEventListener('click', async () => {
    const res = await fetch('/audio/anterior', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'ok') {
        actualizarNombreCancion(data.archivo);
        actualizarIconoPlay(true);
    }
});

// Siguiente
document.getElementById('next-btn').addEventListener('click', async () => {
    const res = await fetch('/audio/siguiente', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'ok') {
        actualizarNombreCancion(data.archivo);
        actualizarIconoPlay(true);
    }
});

// Slider de volumen
const volumenSlider = document.getElementById('volumen-slider');
const volumenDisplay = document.getElementById('volumen-display');

volumenSlider.addEventListener('input', () => {
    currentVolumen = parseInt(volumenSlider.value);
    volumenDisplay.textContent = `Volumen: ${currentVolumen}%`;
});

volumenSlider.addEventListener('change', () => {
    fetch(`/audio/volumen/${currentVolumen}`, { method: 'POST' });
});

// ── Velocidad ─────────────────────────────────────────────────────────────────

const velocidadSlider = document.getElementById('velocidad-slider');
const velocidadDisplay = document.getElementById('velocidad-display');

velocidadSlider.addEventListener('input', () => {
    currentVelocidad = parseInt(velocidadSlider.value);
    velocidadDisplay.textContent = `${currentVelocidad}%`;
});

// Al soltar el slider, si hay una dirección activa, reenviar con nueva velocidad
velocidadSlider.addEventListener('change', () => {
    if (direccionActual && modoActual === 'manual') {
        fetch(`/motor/${direccionActual}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ velocidad: currentVelocidad })
        });
    }
});

// ── Motores ───────────────────────────────────────────────────────────────────

function moverRobot(direccion) {
    if (modoActual !== 'manual') return;

    direccionActual = direccion === 'detener' ? null : direccion;

    document.querySelectorAll('.control-btn').forEach(b => b.classList.remove('active'));
    const btnMap = {
        'adelante': 'forward-btn', 'atras': 'backward-btn',
        'izquierda': 'left-control-btn', 'derecha': 'right-control-btn',
        'detener': 'stop-btn'
    };
    document.getElementById(btnMap[direccion]).classList.add('active');

    fetch(`/motor/${direccion}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ velocidad: currentVelocidad })
    });
}

document.getElementById('forward-btn').addEventListener('click', () => moverRobot('adelante'));
document.getElementById('backward-btn').addEventListener('click', () => moverRobot('atras'));
document.getElementById('left-control-btn').addEventListener('click', () => moverRobot('izquierda'));
document.getElementById('right-control-btn').addEventListener('click', () => moverRobot('derecha'));
document.getElementById('stop-btn').addEventListener('click', () => moverRobot('detener'));

// Teclado
document.addEventListener('keydown', (e) => {
    if (modoActual !== 'manual') return;
    const teclas = {
        'ArrowUp': 'adelante', 'ArrowDown': 'atras',
        'ArrowLeft': 'izquierda', 'ArrowRight': 'derecha', ' ': 'detener'
    };
    if (teclas[e.key]) { e.preventDefault(); moverRobot(teclas[e.key]); }
});

// ── Modos ─────────────────────────────────────────────────────────────────────

document.getElementById('manual-btn').addEventListener('click', () => {
    modoActual = 'manual';
    direccionActual = null;
    document.querySelectorAll('.btn').forEach(b => b.classList.remove('selected'));
    document.getElementById('manual-btn').classList.add('selected');
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.style.color = ''; btn.disabled = false;
    });
    document.getElementById('velocidad-slider').disabled = false;
    fetch('/led/manual/1', { method: 'POST' });
    fetch('/led/autonomo/0', { method: 'POST' });
    actualizarLed('led-manual', true);
    actualizarLed('led-autonomo', false);
});

document.getElementById('automatic-btn').addEventListener('click', () => {
    modoActual = 'automatico';
    direccionActual = null;
    document.querySelectorAll('.btn').forEach(b => b.classList.remove('selected'));
    document.getElementById('automatic-btn').classList.add('selected');
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.style.color = '#DEDCE0'; btn.disabled = true;
    });
    document.getElementById('velocidad-slider').disabled = true;
    fetch('/led/autonomo/1', { method: 'POST' });
    fetch('/led/manual/0', { method: 'POST' });
    actualizarLed('led-autonomo', true);
    actualizarLed('led-manual', false);
});

// ── LEDs ──────────────────────────────────────────────────────────────────────

function actualizarLed(id, encendido) {
    const el = document.getElementById(id);
    if (encendido) el.classList.add('encendido');
    else el.classList.remove('encendido');
}

actualizarLed('led-sistema', true);

// ── Sensores ──────────────────────────────────────────────────────────────────

async function getSensorData() {
    try {
        const res = await fetch('/sensores');
        const data = await res.json();
        document.getElementById('sensor-frontal').textContent = `${data.frontal} cm`;
        document.getElementById('sensor-lateral').textContent = `${data.lateral} cm`;
        const pctFrontal = Math.min(100, (data.frontal / 100) * 100);
        const pctLateral = Math.min(100, (data.lateral / 100) * 100);
        document.getElementById('barra-frontal').style.width = `${pctFrontal}%`;
        document.getElementById('barra-lateral').style.width = `${pctLateral}%`;
        const alerta = document.getElementById('alerta-sensor');
        if (data.obstaculo_frontal || data.obstaculo_lateral) {
            alerta.textContent = '⚠️ ¡Obstáculo detectado!';
            alerta.style.color = 'red';
            fetch('/led/obstaculo/1', { method: 'POST' });
            actualizarLed('led-obstaculo', true);
        } else {
            alerta.textContent = '';
            fetch('/led/obstaculo/0', { method: 'POST' });
            actualizarLed('led-obstaculo', false);
        }
    } catch {
        document.getElementById('sensor-frontal').textContent = 'Error';
        document.getElementById('sensor-lateral').textContent = 'Error';
    }
}

// ── Conexión ──────────────────────────────────────────────────────────────────

async function checkConnection() {
    try {
        const res = await fetch('/status');
        const data = await res.json();
        document.getElementById('connection-status').innerHTML =
            `<p style="color:green">✅ ${data.message}</p>`;
    } catch {
        document.getElementById('connection-status').innerHTML =
            `<p style="color:red">❌ Sin conexión con la Raspberry</p>`;
    }
}

// ── Mapa ──────────────────────────────────────────────────────────────────────

const grid = document.getElementById('map-grid');
const totalCells = 30 * 8;
for (let i = 0; i < totalCells; i++) {
    const cell = document.createElement('div');
    cell.classList.add('map-cell');
    cell.addEventListener('click', function () { this.classList.toggle('painted'); });
    grid.appendChild(cell);
}

// ── Inicialización ────────────────────────────────────────────────────────────

cargarCanciones();
checkConnection();
setInterval(getSensorData, 2000);
setInterval(checkConnection, 10000);
document.getElementById('manual-btn').click();
