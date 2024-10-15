import { api } from "./api.js";
import { router } from "./app.js";
import { showAlert } from "./app.js";

if (!localStorage.getItem("email")) {
  (localStorage.getItem("email"));
  alert("Error: No email provided");
  router.navigate("/home");
} else {
  (localStorage.getItem("email"))
  document.getElementById("email").value = localStorage.getItem("email");
  (document.getElementById("email").value)
}

document.getElementById("login-form-submit").addEventListener("click", async (e) => {
  e.preventDefault();
  if (!localStorage.getItem("email")) {
    (localStorage.getItem("email"));
    alert("Error: No email provided");
    router.navigate("/home");
  }
  const result = await api.post("/token/", {
    email: localStorage.getItem("email"),
    password: document.getElementById("password-field").value,
  });
  if (result && result.ok) {
    const user_info = await result.json();
    if (user_info["2fa"])
      router.navigate("/verify_2fa")
    else
      router.navigate("/main_menu");
  } else {
    showAlert("Wrong Password")
  }
});
