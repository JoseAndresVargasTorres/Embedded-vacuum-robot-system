const playBtn = document.getElementById('play-btn');
const playIcon = document.getElementById('play-icon');
const leftBtn = document.getElementById('left-btn');
const rightBtn = document.getElementById('right-btn');
const highBtn = document.getElementById('high-btn'); 
const lowBtn = document.getElementById('low-btn'); 
const stopBtn = document.getElementById('stop-btn');  
const stopIcon = document.getElementById('stop-icon'); 
const grid = document.getElementById('map-grid');
const totalCells = 30 * 8; 
const controlBtns = document.querySelectorAll('.control-btn');

// Variables globales para la música
let currentVolumen = 15;
let songPlaying = '';
let songArtist = '';


// Obtener la información de la música del api
async function getMusicInfo() {
    const response = await fetch('/api/current');
    const data = await response.json();

    currentVolumen = data.device.volume_percent;
    songPlaying = data.item.name;
    songArtist = data.item.artists[0].name;

    document.getElementById('song-name').textContent = songPlaying;
    document.getElementById('song-artist').textContent = songArtist;
}


// El botón de play va a cambiar dependiendo de si se está reproduciendo o no la música
playBtn.addEventListener('click', function() {
    if (playIcon.classList.contains('fa-circle-play')) {
        playIcon.classList.remove('fa-circle-play');
        playIcon.classList.add('fa-circle-pause');
        fetch('/api/play');
    } else {
        playIcon.classList.remove('fa-circle-pause');
        playIcon.classList.add('fa-circle-play');
        fetch('/api/pause');
    }
})

leftBtn.addEventListener('click', function() {
    fetch('/api/previous');
})

rightBtn.addEventListener('click', function() {
    fetch('/api/next');
})

highBtn.addEventListener('click', function() {
    // Para que el volumen no pase de 100
    currentVolumen = Math.min(100, currentVolumen + 5);
    fetch(`/api/volume/${currentVolumen}`);
})

lowBtn.addEventListener('click', function() {
     // Para que el volumen no baje de 0
    currentVolumen = Math.max(0, currentVolumen - 5);
    fetch(`/api/volume/${currentVolumen}`);
})

// Llamada para que siempre se busque la información de la música al cargar la página
getMusicInfo();
setInterval(getMusicInfo, 5000); // Actualizar la información cada 5 segundos


// Para presionar un botón del modo de control manual y que este cambie de color
document.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('click', function() {
        // Eliminar la clase 'selected' de todos los botones
        document.querySelectorAll('.btn').forEach(b => b.classList.remove('selected'));
        // Agregar la clase 'selected' al botón presionado
        this.classList.add('selected');
    });
})

// El botón de play va a cambiar dependiendo de si la roomba está detenida o no
stopBtn.addEventListener('click', function() {
    if (stopIcon.classList.contains('fa-stop')) {
        stopIcon.classList.remove('fa-stop');
        stopIcon.classList.add('fa-play');
    } else {
        stopIcon.classList.remove('fa-play');
        stopIcon.classList.add('fa-stop');
    }
})

// Función para que cuando los botones se deshabilitene en modo automático
function changeColor() {
    controlBtns.forEach(btn => {
        btn.style.color = '#DEDCE0' //'#d3d3d3'; // Cambia el color a gris
        btn.disabled = true; // Deshabilita el botón
    });
}

// Para la cuadrícula del mapa
for (let i = 0; i < totalCells; i++) {
    const cell = document.createElement('div');
    cell.classList.add('map-cell');
    cell.addEventListener('click', function() {
        this.classList.toggle('painted');
    });
    grid.appendChild(cell);
}