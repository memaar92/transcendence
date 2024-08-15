import { api } from './api.js';
import { router } from './app.js'

document.getElementById('user-mail').innerText = localStorage.getItem("email");

document.getElementById("verify-email").addEventListener('click', async (e) => {
    e.preventDefault();
    const result = await api.post("/email/validate/",
        {
            "id": localStorage.getItem("uid"),
            "otp": document.getElementById('otp-code').value
        }
    );
    if (result.ok) {
        router.navigate("/main_menu");
    } else {
        document.getElementById('otp-code').classList.add("is-invalid");
    }
});