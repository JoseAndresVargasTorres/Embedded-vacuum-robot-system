// --- Dashboard.html ---

// El botón de play va a cambiar dependiendo de si se está reproduciendo o no la música
const playBtn = document.getElementById('play-btn');
const playIcon = document.getElementById('play-icon');

playBtn.addEventListener('click', function() {
    if (playIcon.classList.contains('fa-circle-play')) {
        playIcon.classList.remove('fa-circle-play');
        playIcon.classList.add('fa-circle-pause');
    } else {
        playIcon.classList.remove('fa-circle-pause');
        playIcon.classList.add('fa-circle-play');
    }
})
