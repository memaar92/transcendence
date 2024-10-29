import { api } from "./api.js";
import { router } from "./app.js";
import { showAlert } from "./app.js"

function isValidEmail(email) {
  var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (email === "" || !emailRegex.test(email)) {
    return false;
  } else {
    return true;
  }
}

document.getElementById("login").addEventListener("click", async (e) => {
  e.preventDefault();
  if (!isValidEmail(document.getElementById("email").value)) {
    document.getElementById("email").classList.add("is-invalid");
    return;
  }
  const result = await api.post("/email/", {
    email: document.getElementById("email").value,
  });
  localStorage.setItem("email", document.getElementById("email").value);
  if (result.ok) {
    const json = await result.json();
    localStorage.setItem("uid", json["id"]);
    if (json["email_verified"] == true && json["42auth"] == false) {
        router.navigate("/login")
    } else if (json["email_verified"] == true && json["42auth"] == true) {
        showAlert('You are already registered with 42. Please login with 42.')
        router.navigate("/home")
    } else {
        router.navigate("/email_verification")
    }
  } else {
    router.navigate("/register");
  }
});
