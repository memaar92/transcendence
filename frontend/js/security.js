import { api } from "./api.js";
import { router } from "./app.js";

document.getElementById("back").addEventListener("click", async (e) => {
  router.navigate("/main_menu");
});

const fa2 = await api.get("/profile/");
const infos = await fa2.json();




async function handle_activation(e) {
  e.preventDefault();
  const result = await api.post("/token/2fa/verify/", {
    "code_2fa": document.getElementById("token").value,
  });
  if (result.ok)
  {
    document.getElementById("toggle-2fa").innerHTML = "Remove 2FA"
    document.getElementById("toggle-2fa").classList.remove("button");
    document.getElementById("toggle-2fa").classList.add("dangerous-button");
    document.getElementById("toggle-2fa").setAttribute("data-bs-toggle", "")
    document.getElementById("toggle-2fa").onclick = handle_deactivation;
    showAlert("2FA verification successfull", "alert-success");
    document.getElementById("close-modal").click();
  }
  else {
    const json = await result.json();
    showAlert(json["code_2fa"] ? json["code_2fa"] : json["detail"], "alert-danger");
  }
}

async function handle_deactivation(e) {
  e.preventDefault();
  const result = await api.patch("/profile/", {
    "is_2fa_enabled": false,
  });
  if (result.ok)
  {
    document.getElementById("toggle-2fa").innerHTML = "Add 2FA"
    document.getElementById("toggle-2fa").classList.add("button");
    document.getElementById("toggle-2fa").classList.remove("dangerous-button");
    document.getElementById("toggle-2fa").setAttribute("data-bs-toggle", "modal")
    showAlert("Deactivated 2FA", "alert-danger");
  }
  else {
    const json = await result.json();
    showAlert(json["code_2fa"] ? json["code_2fa"] : json["detail"], "alert-danger");
  }
}

document.getElementById("check-2fa-submit").onclick = handle_activation;

if (infos["is_2fa_enabled"] == true) {
  document.getElementById("toggle-2fa").innerHTML = "Remove 2FA"
  document.getElementById("toggle-2fa").classList.remove("button");
  document.getElementById("toggle-2fa").classList.add("dangerous-button");
  document.getElementById("toggle-2fa").setAttribute("data-bs-toggle", "")
  document.getElementById("toggle-2fa").onclick = handle_deactivation;
} else {
  document.getElementById("toggle-2fa").innerHTML = "Add 2FA"
  document.getElementById("toggle-2fa").classList.add("button");
  document.getElementById("toggle-2fa").classList.remove("dangerous-button");
  document.getElementById("toggle-2fa").setAttribute("data-bs-toggle", "modal")
}

const result = await api.get("/2fa/setup/");
const user_info = await result.json();
const img = new Image();
img.src = `data:image/png;base64,${user_info["qr_code"]}`;
img.id = "qrPhoto";
document.getElementById("qrCode").appendChild(img);



function showAlert(message, type) {
  const alertContainer = document.getElementById("alertContainer");

  const alertElement = document.createElement("div");
  alertElement.classList.add(
    "alert",
    type,
    "alert-dismissible",
    "fade",
    "show"
  );
  alertElement.setAttribute("role", "alert");
  alertElement.setAttribute("data-bs-autohide", "true");
  alertElement.setAttribute("data-bs-delay", "1000");

  alertElement.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;

  alertContainer.appendChild(alertElement);

  // Initialize the Bootstrap alert
  new bootstrap.Alert(alertElement);
}
