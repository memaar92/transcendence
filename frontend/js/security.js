import { api } from "./api.js";

document.getElementById("back").addEventListener("click", async (e) => {
  ("going back");
  history.back();
});

const result = await api.get("/2fa/setup/");
("register call finished");
(result);
const user_info = await result.json();
(user_info);
const img = new Image();
img.src = `data:image/png;base64,${user_info["qr_code"]}`;
img.id = "qrPhoto";
document.getElementById("qrCode").appendChild(img);

document
  .getElementById("check-2fa-submit")
  .addEventListener("click", async (e) => {
    e.preventDefault();
    const result = await api.post("/token/2fa/verify/", {
      "code_2fa": document.getElementById("token").value,
    });
    if (result.ok)
      showAlert("2FA verification successfull", "alert-success");
    else {
      const json = await result.json();
      showAlert(json["code_2fa"] ? json["code_2fa"] : json["detail"], "alert-danger");
    }
  });

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

  alertElement.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;

  alertContainer.appendChild(alertElement);

  // Initialize the Bootstrap alert
  new bootstrap.Alert(alertElement);
}
