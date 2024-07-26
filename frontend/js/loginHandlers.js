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
            router.navigate("/register");
    }
    event.preventDefault();
    return;
};