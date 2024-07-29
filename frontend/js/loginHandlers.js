import { api } from './api.js';
import { router } from './app.js'

export const handleButtonClick = async (event) => {
    const buttonId = event.target.id;
    console.log(buttonId);
    console.log("BUTTON PRESSED")
    if (buttonId == "login") {
        const result = await api.post('/email/', { "email": document.getElementById('email').value});
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
            "displayname": "FbohlingTheOne"
        });
        if (result.ok) {
            router.navigate("/email_verification");
        } else {
            console.error(result);
        }
    } else if (buttonId == "home") {
        router.navigate("/home")
    }
    event.preventDefault();
    return;
};