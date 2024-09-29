import { api } from "./api.js";
import { router } from "./app.js";

const result = await api.get("/profile/");
const profile_info = await result.json();

const photo = document.getElementById("profile-photo-icon");
photo.src = profile_info["profile_picture"];

const name = document.getElementById("username");
name.innerHTML = profile_info["displayname"];

document.getElementById("profile").addEventListener("click", async (e) => {
    e.preventDefault();
    router.navigate("/account");
});