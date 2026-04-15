const loginForm = document.querySelector('#login-form form');
const errorMsg = document.getElementById('error-msg');

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorMsg.textContent = '';

    const username = document.getElementById("username-login").value;
    const password = document.getElementById("password-login").value;

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (data.success) {
            window.location.href = '/dashboard';
        } else {
            errorMsg.textContent = '❌ Usuario o contraseña incorrectos';
        }
    } catch {
        errorMsg.textContent = '❌ Error de conexión con el servidor';
    }

    loginForm.reset();
});
