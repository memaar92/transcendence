import { api } from "./api.js";
import { router } from "./app.js";

let password = document.getElementById("password");
let power = document.getElementById("power-point");
password.oninput = function () {
    let result = zxcvbn(password.value);
    let widthPower = 
        ["1%", "25%", "50%", "75%", "100%"];
    let colorPower = 
        ["#D73F40", "#DC6551", "#F2B84F", "#BDE952", "#3ba62f"];

    power.style.width = widthPower[result.score];
    power.style.backgroundColor = colorPower[result.score];
};

if (!localStorage.getItem("email")) {
  (localStorage.getItem("email"));
  alert("Error: No email provided");
  router.navigate("/home");
} else {
  document.getElementById("email").name = localStorage.getItem("email");
}

document.getElementById("register").addEventListener("click", async (e) => {
  e.preventDefault();
  const result = await api.post("/register/", {
    email: localStorage.getItem("email"),
    password: document.getElementById("password").value,
  });
  const user_info = await result.json();
  if (result.ok) {
    localStorage.setItem("uid", user_info["id"]);
    router.navigate("/email_verification");
  } else {
    router.navigate("/home");
  }
});
