import { api } from "./api.js";
import { router } from "./app.js";

document.getElementById("register").addEventListener("click", async (e) => {
  e.preventDefault();
  // TODO check password strength
  if (!localStorage.getItem("email")) {
    console.log(localStorage.getItem("email"));
    alert("Error: No email provided");
    router.navigate("/home");
  }
  const result = await api.post("/register/", {
    email: localStorage.getItem("email"),
    password: document.getElementById("password").value,
  });
  console.log("register call finished");
  const user_info = await result.json();
  console.log("uid " + user_info["id"]);
  if (result.ok) {
    localStorage.setItem("uid", user_info["id"]);
    router.navigate("/email_verification");
  } else {
    router.navigate("/home");
  }
});
