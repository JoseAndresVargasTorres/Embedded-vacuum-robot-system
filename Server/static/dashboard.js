const playBtn = document.getElementById('play-btn');
const playIcon = document.getElementById('play-icon');
const leftBtn = document.getElementById('left-btn');
const rightBtn = document.getElementById('right-btn');
const highBtn = document.getElementById('high-btn'); 
const lowBtn = document.getElementById('low-btn');    

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