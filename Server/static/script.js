const container = document.querySelector('.container');
const registerBtn = document.querySelector('.register-btn');
const loginBtn = document.querySelector('.login-btn');


// Botones para cambiar entre login y registro, solo visual
registerBtn.addEventListener('click', () => {
    container.classList.add('active');
})

loginBtn.addEventListener('click', () => {
    container.classList.remove('active');
})

// Escuchar el formulario de login, en cuanto se presione el botón de submit, se capturan los datos ingresados y se envían al servidor
const loginForm = document.querySelector('#login-form');
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault(); // Evitar que el formulario se envíe de forma tradicional
    const username = document.getElementById("username-login").value;
    const password = document.getElementById("password-login").value;

    // Enviar los datos al servidor usando fetch
    const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    // Si todo salió bien, avanzar al a interfar
    if (response.ok ) {
        window.location.href = '/dashboard'; // Redirigir a la página del dashboard
    } else {
        alert('Login failed: ' + data.message); // Mostrar un mensaje de error
    }

    // Limpiar los campos del formulario, solo en caso de que faller
    loginForm.reset();
});


// Escuchar el formulario de registro, en cuanto se presione el botón de submit, se capturan los datos ingresados y se envían al servidor
const registerForm = document.querySelector('#register-form');
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault(); // Evitar que el formulario se envíe de forma tradicional
    const username = document.getElementById("username-register").value;
    const email = document.getElementById("email-register").value;
    const password = document.getElementById("password-register").value;

    // Enviar los datos al servidor usando fetch
    const response = await fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
    });

    const data = await response.json();

    // Si todo salió bien, avanzar al a interfar
    if (response.ok ) {
        window.location.href = '/dashboard'; // Redirigir a la página del dashboard
    } else {
        alert('Registration failed: ' + data.message); // Mostrar un mensaje de error
    }

    // Limpiar los campos del formulario, solo en caso de que falle
    registerForm.reset();
});
