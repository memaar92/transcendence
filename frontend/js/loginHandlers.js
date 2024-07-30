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
        let r = (Math.random() + 1).toString(36).substring(7);
        try {
            const result = await api.post('/register/', {
                "email": localStorage.getItem("email"),
                "password": document.getElementById('password').value,
                "displayname": r
            });
            // const result = await api.post('/email/', { "email": localStorage.getItem("email")});
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
        } catch (error) {
            console.error("Registration failed: ", error);
        }
    } else if (buttonId == "home") {
        router.navigate("/home")
    } else if (buttonId == "code-form-submit") {
        api.post("/email/validate/",
            {
                "id": localStorage.getItem("uid"),
                "otp": document.getElementById('otp-code').value
            }
        )
    }
    event.preventDefault();
    return;
};