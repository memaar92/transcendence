import { api } from "./api.js";

document.getElementById("2fa").addEventListener("click", async (e) => {
  e.preventDefault();
  if (document.getElementById("qrPhoto")) return;
  const result = await api.get("/2fa/setup/");
  console.log("register call finished");
  console.log(result);
  const user_info = await result.json();
  console.log(user_info);
  const img = new Image();
  img.src = `data:image/png;base64,${user_info["qr_code"]}`;
  img.id = "qrPhoto";
  document.getElementById("qrCode").appendChild(img);
  document.getElementById("check-2fa").style.display = "inline";
});

document
  .getElementById("check-2fa-submit")
  .addEventListener("click", async (e) => {
    e.preventDefault();
    const result = await api.post("/token/2fa/verify/", {
      "code_2fa": document.getElementById("token").value,
    });
    const r = await result.json();
  });

function showAlert(message) {
  const alertContainer = document.getElementById("alertContainer");

  const alertElement = document.createElement("div");
  alertElement.classList.add(
    "alert",
    "alert-danger",
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
