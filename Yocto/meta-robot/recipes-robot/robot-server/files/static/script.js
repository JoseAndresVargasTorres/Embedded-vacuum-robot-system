const loginForm = document.querySelector('#login-form form');

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById("username-login").value;
    const password = document.getElementById("password-login").value;

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
        alert('Login incorrecto: ' + data.message);
    }

    loginForm.reset();
});