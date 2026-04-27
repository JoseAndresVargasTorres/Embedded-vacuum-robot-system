let currentVolumen    = 50;
let currentVelocidad  = 50;
let autoScrollActivo  = true;
let modoActual        = 'manual';
let direccionActual   = null;
let estaReproduciendo = false;
let intervaloEstadoAutonomo = null;
let aspiradoraEncendida = false;

// ── Música ─────────────────────────────────────────────────────────────────────
async function cargarCanciones() {
    try {
        const res  = await fetch('/audio/lista');
        const data = await res.json();
        const select = document.getElementById('song-select');
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
    icon.className = reproduciendo ? 'fa-solid fa-pause' : 'fa-solid fa-play';
    estaReproduciendo = reproduciendo;
}

function actualizarNombreCancion(archivo) {
    document.getElementById('song-name').textContent = archivo
        ? archivo.replace('.mp3', '') : 'Sin canción';
    const select = document.getElementById('song-select');
    for (let i = 0; i < select.options.length; i++) {
        if (select.options[i].value === archivo) { select.selectedIndex = i; break; }
    }
}

document.getElementById('play-btn').addEventListener('click', async () => {
    const archivo = document.getElementById('song-select').value;
    if (!estaReproduciendo && !archivo) { alert('Selecciona una canción primero'); return; }
    if (!estaReproduciendo && archivo) {
        await fetch('/audio/reproducir', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ archivo })
        });
        actualizarNombreCancion(archivo);
        actualizarIconoPlay(true);
    } else {
        const res  = await fetch('/audio/pausar', { method: 'POST' });
        const data = await res.json();
        actualizarIconoPlay(data.reproduciendo);
    }
});

document.getElementById('prev-btn').addEventListener('click', async () => {
    const res  = await fetch('/audio/anterior', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'ok') { actualizarNombreCancion(data.archivo); actualizarIconoPlay(true); }
});

document.getElementById('next-btn').addEventListener('click', async () => {
    const res  = await fetch('/audio/siguiente', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'ok') { actualizarNombreCancion(data.archivo); actualizarIconoPlay(true); }
});

const volumenSlider  = document.getElementById('volumen-slider');
const volumenDisplay = document.getElementById('volumen-display');
volumenSlider.addEventListener('input', () => {
    currentVolumen = parseInt(volumenSlider.value);
    volumenDisplay.textContent = `Volumen: ${currentVolumen}%`;
});
volumenSlider.addEventListener('change', () => {
    fetch(`/audio/volumen/${currentVolumen}`, { method: 'POST' });
});

// ── Velocidad ──────────────────────────────────────────────────────────────────
const velocidadSlider  = document.getElementById('velocidad-slider');
const velocidadDisplay = document.getElementById('velocidad-display');

function aplicarVelocidadActual() {
    if (!direccionActual || modoActual !== 'manual') return;
    fetch(`/motor/${direccionActual}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ velocidad: currentVelocidad })
    });
}

velocidadSlider.addEventListener('input', () => {
    currentVelocidad = parseInt(velocidadSlider.value);
    velocidadDisplay.textContent = `${currentVelocidad}%`;
});
velocidadSlider.addEventListener('change', () => {
    aplicarVelocidadActual();
});

// ── Motores ────────────────────────────────────────────────────────────────────
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

document.getElementById('forward-btn').addEventListener('click',       () => moverRobot('adelante'));
document.getElementById('backward-btn').addEventListener('click',      () => moverRobot('atras'));
document.getElementById('left-control-btn').addEventListener('click',  () => moverRobot('izquierda'));
document.getElementById('right-control-btn').addEventListener('click', () => moverRobot('derecha'));
document.getElementById('stop-btn').addEventListener('click',          () => moverRobot('detener'));

document.addEventListener('keydown', (e) => {
    if (modoActual !== 'manual') return;
    const teclas = {
        'ArrowUp': 'adelante', 'ArrowDown': 'atras',
        'ArrowLeft': 'izquierda', 'ArrowRight': 'derecha', ' ': 'detener'
    };
    if (teclas[e.key]) { e.preventDefault(); moverRobot(teclas[e.key]); }
});

// ── Modos ──────────────────────────────────────────────────────────────────────
document.getElementById('manual-btn').addEventListener('click', async () => {
    modoActual = 'manual';
    direccionActual = null;

    if (intervaloEstadoAutonomo) {
        clearInterval(intervaloEstadoAutonomo);
        intervaloEstadoAutonomo = null;
    }

    await fetch('/autonomo/detener', { method: 'POST' });
    await fetch('/sonido/manual',    { method: 'POST' });

    document.querySelectorAll('.btn').forEach(b => b.classList.remove('selected'));
    document.getElementById('manual-btn').classList.add('selected');
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.style.color = ''; btn.disabled = false;
    });
    document.getElementById('velocidad-slider').disabled = false;
    actualizarLed('led-manual',    true);
    actualizarLed('led-autonomo',  false);

    document.getElementById('sensor-frontal').textContent   = '-- cm';
    document.getElementById('sensor-izquierda').textContent = '-- cm';
    document.getElementById('sensor-derecha').textContent   = '-- cm';
    document.getElementById('barra-frontal').style.width    = '0%';
    document.getElementById('barra-izquierda').style.width  = '0%';
    document.getElementById('barra-derecha').style.width    = '0%';
    document.getElementById('alerta-sensor').textContent    = '';
    actualizarLed('led-obstaculo', false);

    aspiradoraEncendida = false;
    actualizarBotonAspiradora(false);
    document.getElementById('aspiradora-btn').disabled = false;
    document.getElementById('aspiradora-btn').style.opacity = '1';
});

document.getElementById('automatic-btn').addEventListener('click', async () => {
    modoActual = 'automatico';
    direccionActual = null;

    document.querySelectorAll('.btn').forEach(b => b.classList.remove('selected'));
    document.getElementById('automatic-btn').classList.add('selected');
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.style.color = '#DEDCE0'; btn.disabled = true;
    });
    document.getElementById('velocidad-slider').disabled = true;
    actualizarLed('led-autonomo', true);
    actualizarLed('led-manual',   false);

    aspiradoraEncendida = false;
    actualizarBotonAspiradora(false);
    document.getElementById('aspiradora-btn').disabled = true;
    document.getElementById('aspiradora-btn').style.opacity = '0.4';

    await fetch('/autonomo/iniciar', { method: 'POST' });
    await fetch('/sonido/autonomo',  { method: 'POST' });

    intervaloEstadoAutonomo = setInterval(async () => {
        try {
            const res  = await fetch('/autonomo/estado');
            const data = await res.json();
            actualizarSensoresUI(data.frontal, data.izquierda, data.derecha);
        } catch { console.log('Error obteniendo estado autónomo'); }
    }, 200);
});

// ── LEDs ───────────────────────────────────────────────────────────────────────
function actualizarLed(id, encendido) {
    const el = document.getElementById(id);
    if (encendido) el.classList.add('encendido');
    else           el.classList.remove('encendido');
}

actualizarLed('led-sistema', true);

// ── Sensores — solo se actualizan en modo autónomo ────────────────────────────
function actualizarSensoresUI(frontal, izquierda, derecha) {
    document.getElementById('sensor-frontal').textContent   = `${frontal} cm`;
    document.getElementById('sensor-izquierda').textContent = `${izquierda} cm`;
    document.getElementById('sensor-derecha').textContent   = `${derecha} cm`;

    document.getElementById('barra-frontal').style.width   = `${Math.min(100, frontal)}%`;
    document.getElementById('barra-izquierda').style.width = `${Math.min(100, izquierda)}%`;
    document.getElementById('barra-derecha').style.width   = `${Math.min(100, derecha)}%`;

    const alerta     = document.getElementById('alerta-sensor');
    const hayObstaculo = (frontal   > 0 && frontal   < 15) ||
                         (izquierda > 0 && izquierda < 20) ||
                         (derecha   > 0 && derecha   < 20);
    if (hayObstaculo) {
        alerta.textContent = '⚠️ ¡Obstáculo detectado!';
        alerta.style.color = 'red';
        actualizarLed('led-obstaculo', true);
    } else {
        alerta.textContent = '';
        actualizarLed('led-obstaculo', false);
    }
}

// ── Conexión ───────────────────────────────────────────────────────────────────
async function checkConnection() {
    try {
        const res  = await fetch('/status');
        const data = await res.json();
        document.getElementById('connection-status').innerHTML =
            `<p style="color:green">✅ ${data.message}</p>`;
    } catch {
        document.getElementById('connection-status').innerHTML =
            `<p style="color:red">❌ Sin conexión con la Raspberry</p>`;
    }
}

// ── Aspiradora ─────────────────────────────────────────────────────────────────
document.getElementById('aspiradora-btn').addEventListener('click', async () => {
    if (modoActual !== 'manual') return;
    const res  = await fetch('/aspiradora/toggle', { method: 'POST' });
    const data = await res.json();
    aspiradoraEncendida = data.encendida;
    actualizarBotonAspiradora(aspiradoraEncendida);
});

function actualizarBotonAspiradora(encendida) {
    const btn    = document.getElementById('aspiradora-btn');
    const estado = document.getElementById('aspiradora-estado');
    if (encendida) {
        btn.classList.remove('aspiradora-off');
        btn.classList.add('aspiradora-on');
        estado.textContent = 'ON';
    } else {
        btn.classList.remove('aspiradora-on');
        btn.classList.add('aspiradora-off');
        estado.textContent = 'OFF';
    }
}

// ── Mapa ───────────────────────────────────────────────────────────────────────
function dibujarMapa(data) {
    const canvas = document.getElementById('mapa-canvas');
    const ctx    = canvas.getContext('2d');

    const OFFSET    = 10;
    const LONG      = 10;
    const TICK_H    = 8;   // altura del guión vertical de trayectoria
    const ANGULO_30 = Math.PI / 6;

    const BASE_ANGLE = [
        -Math.PI / 2,  // 0 = NORTE
         0,            // 1 = ESTE
         Math.PI / 2,  // 2 = SUR
         Math.PI       // 3 = OESTE
    ];

    const sensorOffset = {
        frontal:    0,
        derecho:   +ANGULO_30,
        izquierdo: -ANGULO_30
    };

    const colores = {
        frontal:   '#FF6B6B',
        derecho:   '#4ECDC4',
        izquierdo: '#95E1D3'
    };

    // 1. Limpiar
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 2. Trayectoria: guiones verticales en cada punto visitado
    if (data.trayectoria && data.trayectoria.length > 0) {
        ctx.strokeStyle = '#c9d6ff';
        ctx.lineWidth   = 2;
        ctx.lineCap     = 'round';
        data.trayectoria.forEach(p => {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y - TICK_H / 2);
            ctx.lineTo(p.x, p.y + TICK_H / 2);
            ctx.stroke();
        });
    }

    // 3. Líneas de obstáculo con geometría de 30°
    (data.obstaculos || []).forEach(obs => {
        const baseAngle   = BASE_ANGLE[obs.heading] ?? -Math.PI / 2;
        const sensorAngle = baseAngle + (sensorOffset[obs.sensor] ?? 0);
        const wx = obs.x + Math.cos(sensorAngle) * OFFSET;
        const wy = obs.y + Math.sin(sensorAngle) * OFFSET;
        const perpAngle = sensorAngle + Math.PI / 2;
        const x1 = wx + Math.cos(perpAngle) * (LONG / 2);
        const y1 = wy + Math.sin(perpAngle) * (LONG / 2);
        const x2 = wx - Math.cos(perpAngle) * (LONG / 2);
        const y2 = wy - Math.sin(perpAngle) * (LONG / 2);

        ctx.strokeStyle = colores[obs.sensor] || '#999';
        ctx.lineWidth   = 3;
        ctx.lineCap     = 'round';
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
    });

    // 4. Ícono del robot (triángulo apuntando al frente)
    const rx = data.pos_x ?? 600;
    const ry = data.pos_y ?? 300;
    const robotAngle = (BASE_ANGLE[data.heading ?? 0]) + Math.PI / 2;
    ctx.save();
    ctx.translate(rx, ry);
    ctx.rotate(robotAngle);
    ctx.fillStyle   = '#FFD700';
    ctx.strokeStyle = '#cc9900';
    ctx.lineWidth   = 1;
    ctx.beginPath();
    ctx.moveTo(0, -8);
    ctx.lineTo(-5, 6);
    ctx.lineTo(5, 6);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.restore();

    // 5. Estadísticas DOM
    const nF = (data.obstaculos || []).filter(o => o.sensor === 'frontal').length;
    const nD = (data.obstaculos || []).filter(o => o.sensor === 'derecho').length;
    const nI = (data.obstaculos || []).filter(o => o.sensor === 'izquierdo').length;
    document.getElementById('stat-segmentos').textContent = (data.obstaculos || []).length;
    document.getElementById('stat-frontal').textContent   = nF;
    document.getElementById('stat-derecha').textContent   = nD;
    document.getElementById('stat-izquierda').textContent = nI;

    // 6. Auto-scroll para mantener el robot visible (solo si no hay scroll manual activo)
    if (autoScrollActivo) {
        const scrollDiv = document.getElementById('mapa-scroll');
        const margin    = 60;
        const viewW     = scrollDiv.clientWidth;
        const viewH     = scrollDiv.clientHeight;

        if (rx < scrollDiv.scrollLeft + margin) {
            scrollDiv.scrollLeft = Math.max(0, rx - margin);
        } else if (rx > scrollDiv.scrollLeft + viewW - margin) {
            scrollDiv.scrollLeft = rx - viewW + margin;
        }

        if (ry < scrollDiv.scrollTop + margin) {
            scrollDiv.scrollTop = Math.max(0, ry - margin);
        } else if (ry > scrollDiv.scrollTop + viewH - margin) {
            scrollDiv.scrollTop = ry - viewH + margin;
        }
    }
}

async function actualizarMapa() {
    try {
        const res  = await fetch('/mapa/estado');
        const data = await res.json();
        dibujarMapa(data);
    } catch (e) { console.log('Error mapa:', e); }
}

document.getElementById('resetear-mapa-btn').addEventListener('click', async () => {
    const res  = await fetch('/mapa/reset', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'ok') actualizarMapa();
});

setInterval(actualizarMapa, 100);

// ── Scroll manual del mapa ─────────────────────────────────────────────────────
document.getElementById('mapa-scroll').addEventListener('scroll', () => {
    autoScrollActivo = false;
    clearTimeout(window._scrollTimeout);
    window._scrollTimeout = setTimeout(() => { autoScrollActivo = true; }, 3000);
});

// ── Inicialización ─────────────────────────────────────────────────────────────
cargarCanciones();
checkConnection();
actualizarMapa();
setInterval(checkConnection, 10000);
document.getElementById('manual-btn').click();
