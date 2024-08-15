import { api } from './api.js';
import { router } from './app.js'


function isValidEmail(email) {
    var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (email === '' || !emailRegex.test(email)) {
        return false;
    } else {
        return true;
    }
}

document.getElementById("login").addEventListener('click', async (e) => {
    e.preventDefault();
    console.log("click event happened");
    if (!isValidEmail(document.getElementById('email').value)) {
        console.log("email is invalid");
        document.getElementById('email').classList.add("is-invalid")
        return;
    }
    const result = await api.post('/email/', { "email": document.getElementById('email').value});
    console.log("result received");
    localStorage.setItem("email", document.getElementById('email').value);
    if (result.ok)
    {
        const json = await result.json();
        localStorage.setItem("uid", json["id"])
        console.log(json);
        if (json["email_verified"] == true)
            router.navigate("/login");
        else
            router.navigate("/email_verification") ;
    }
    else
    {
        router.navigate("/register");
    }
});