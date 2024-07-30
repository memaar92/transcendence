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

export const handleButtonClick = async (event) => {
    event.preventDefault();
    const buttonId = event.target.id;
    console.log(buttonId);
    console.log("BUTTON PRESSED")
    if (buttonId == "login") {
        if (!isValidEmail(document.getElementById('email').value)) {
            console.log("email is invalid");
            document.getElementById('email').classList.add("is-invalid")
            return;
        }
        const result = await api.post('/email/', { "email": document.getElementById('email').value});
        console.log("result received");
        if (result.ok)
            router.navigate("/login");
        else
        {
            localStorage.setItem("email", document.getElementById('email').value);
            router.navigate("/register");
        }
    } else if (buttonId == "register") {
        // TODO check password strength
        if (!localStorage.getItem("email"))
        {
            console.log(localStorage.getItem("email"));
            alert("Error: No email provided");
            router.navigate("/home");
        }
        const result = await api.post('/register/', {
            "email": localStorage.getItem("email"),
            "password": document.getElementById('password').value,
        });
        console.log("register call finished");
        const user_info = await result.json();
        console.log("uid " + user_info["id"]);
        if (result.ok) {
            localStorage.setItem("uid", user_info["id"])
            api.post("/email/otp/",
                {
                    "id": user_info["id"]
                }
            )
            router.navigate("/email_verification");
        } else {
            router.navigate("/home");
        }
    } else if (buttonId == "home") {
        router.navigate("/home")
    } else if (buttonId == "code-form-submit") {
        const result = await api.post("/email/validate/",
            {
                "id": localStorage.getItem("uid"),
                "otp": document.getElementById('otp-code').value
            }
        );
        if (result.ok) {
            router.navigate("/main_menu");
        } else {
            document.getElementById('otp-code').classList.add("is-invalid")
        }
    }
    return;
};